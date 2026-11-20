"""Persistent recovery and range integrity without existing database changes."""
from dataclasses import replace
import json
from pathlib import Path
import sqlite3

import pytest

from app.infographics.checkpoints import CheckpointConflict, SQLiteCheckpointStore
from app.infographics.contracts import Checkpoint
from app.infographics.reading import prepare_reading
from app.infographics.reading_windows import BoundaryDecision, ReadingSession
from app.infographics.source_index import FileSourceReader, build_index
from app.infographics.token_budget import ContextConfig, ModelLimits, TokenBudgetManager


@pytest.fixture
def setup(tmp_path):
    source=tmp_path/'lecture'/'generated_notes.md'
    source.parent.mkdir()
    source.write_text('\n\n'.join(f'Paragraph {i}: '+'x'*70 for i in range(50)),encoding='utf-8')
    reader=FileSourceReader({'lecture':source})
    budget=TokenBudgetManager(ModelLimits(8000,1000,10000),ContextConfig(
        target_source_tokens=400,max_source_tokens=2000,reserved_output_tokens=300,
        previous_context_tokens=200,lookahead_tokens=200))
    store=SQLiteCheckpointStore(tmp_path/'independent-infographics')
    session=ReadingSession(build_index(reader.snapshot('lecture')),budget)
    return source,reader,budget,store,session


def test_checkpoint_port_base_contract_and_lazy_storage(tmp_path):
    store=SQLiteCheckpointStore(tmp_path/'separate')
    assert not store.namespace.exists()
    assert store.latest('missing') is None
    assert not store.namespace.exists()
    checkpoint=Checkpoint(1,'run','future-stage',(('source','hash'),),'public-settings',())
    identifier=store.append(checkpoint)
    assert identifier.startswith('CP')
    assert store.latest('run')==checkpoint
    assert store.append(checkpoint)==identifier


def test_incompatible_checkpoint_schema_is_rejected(setup):
    _,reader,budget,store,s=setup
    s.save(store,'schema-source')
    record=store.latest('schema-source')
    store.append(replace(record,run_id='future-schema',schema_version=999,checkpoint_id=''))
    with pytest.raises(ValueError,match='compatible'):
        ReadingSession.resume(store,'future-schema',reader,'lecture',budget)


def test_stored_cursor_without_committed_coverage_is_rejected(setup):
    _,reader,budget,store,s=setup
    s.save(store,'source-state')
    record=store.latest('source-state')
    values=json.loads(record.state_json)
    values['state']['cursor']=5
    store.append(replace(record,run_id='bad-state',state_json=json.dumps(values),checkpoint_id=''))
    with pytest.raises(ValueError,match='Cursor'):
        ReadingSession.resume(store,'bad-state',reader,'lecture',budget)


def test_partial_commit_checkpoint_recovery_and_deterministic_window(setup):
    source,reader,budget,store,s=setup
    original=source.read_bytes()
    first=s.next_window().window
    s.apply(BoundaryDecision(first.id,first.source[1].id,first.source[2].id))
    expected=s.next_window().window
    identifier=s.save(store,'lecture-run')
    record=store.latest('lecture-run')
    assert record.checkpoint_id==identifier
    payload=json.loads(record.state_json)
    for key in ('source_artifact_id','source_sha256','source_index_version','index_fingerprint',
                'window_configuration','token_budget_configuration','state'):
        assert key in payload
    assert payload['state']['cursor']==2 and payload['state']['pending_range'][0]==2
    resumed=ReadingSession.resume(store,'lecture-run',reader,'lecture',budget)
    assert resumed.state==s.state
    actual=resumed.next_window().window
    assert actual==expected
    assert resumed.ledger()==s.ledger()
    resumed.apply(BoundaryDecision(actual.id,actual.source[-1].id))
    assert resumed.save(store,'lecture-run')!=identifier
    assert source.read_bytes()==original
    assert list(source.parent.iterdir())==[source]


def test_complete_resume_does_not_duplicate_any_source_range(setup):
    source,reader,budget,store,s=setup
    original=source.read_bytes()
    owned=[]
    while not s.ledger()['complete']:
        w=s.next_window().window
        assert w
        owned.extend(b.id for b in w.source)
        s.apply(BoundaryDecision(w.id,w.source[-1].id))
        s.save(store,'complete-run')
        s=ReadingSession.resume(store,'complete-run',reader,'lecture',budget)
    assert owned==[b.id for b in s.index.units]
    assert len(owned)==len(set(owned))
    assert s.next_window().status=='complete'
    assert source.read_bytes()==original


def test_no_progress_and_forced_boundary_counters_survive_restart(setup):
    _,reader,budget,store,s=setup
    while s.state.status not in {'oversized_concept','forced_boundary_required'}:
        w=s.next_window().window
        s.apply(BoundaryDecision(w.id))
    s.save(store,'pending')
    resumed=ReadingSession.resume(store,'pending',reader,'lecture',budget)
    assert resumed.state==s.state
    assert resumed.state.cursor==0 and resumed.state.no_progress>0
    assert resumed.state.repeated_pending>0
    assert resumed.next_window().window is None
    assert resumed.ledger()['uncommitted_source_blocks']==s.ledger()['uncommitted_source_blocks']


def test_source_mutation_invalidates_checkpoint_without_modifying_it(setup):
    source,reader,budget,store,s=setup
    s.save(store,'mutated')
    original_record=store.latest('mutated')
    source.write_bytes(source.read_bytes()+b'\nChanged.')
    with pytest.raises(ValueError,match='Source changed'):
        ReadingSession.resume(store,'mutated',reader,'lecture',budget)
    assert store.latest('mutated')==original_record


@pytest.mark.parametrize('change',['context','limits','parts','counter'])
def test_config_or_counter_mutation_invalidates_resume(setup,change):
    _,reader,budget,store,s=setup
    s.save(store,'config')
    parts=None
    if change=='context': budget=TokenBudgetManager(budget.limits,replace(budget.config,lookahead_tokens=0))
    elif change=='limits': budget=TokenBudgetManager(replace(budget.limits,input_tokens=7000),budget.config)
    elif change=='parts':
        from app.infographics.token_budget import RequestParts
        parts=RequestParts(segmentation_prompt='Caller changed prompt')
    else:
        from app.infographics.token_budget import TokenCount
        class Counter:
            def count(self,text): return TokenCount(len(text.encode('utf-8')),'measured','changed-method')
        budget=TokenBudgetManager(budget.limits,budget.config,Counter())
    with pytest.raises(ValueError,match='configuration changed'):
        ReadingSession.resume(store,'config',reader,'lecture',budget,parts)


def test_stale_writer_and_accidental_rewind_are_rejected(setup):
    _,reader,budget,store,s=setup
    original=s.save(store,'conflict')
    stale=ReadingSession.resume(store,'conflict',reader,'lecture',budget)
    w=s.next_window().window
    s.apply(BoundaryDecision(w.id,w.source[1].id))
    latest=s.save(store,'conflict')
    assert latest!=original
    other=stale.next_window().window
    stale.apply(BoundaryDecision(other.id,other.source[0].id))
    with pytest.raises(CheckpointConflict,match='Stale'):
        stale.save(store,'conflict')
    with pytest.raises(CheckpointConflict):
        s.restart().save(store,'conflict')
    assert store.latest('conflict').checkpoint_id==latest


def test_idempotent_save_adds_no_duplicate_revisions(setup):
    _,_,_,store,s=setup
    first=s.save(store,'idempotent')
    assert s.save(store,'idempotent')==first
    with sqlite3.connect(store.path) as db:
        assert db.execute('SELECT count(*) FROM checkpoints').fetchone()[0]==1


def test_corrupt_checkpoint_is_rejected_without_falling_back(setup):
    _,reader,budget,store,s=setup
    s.save(store,'corrupt')
    with sqlite3.connect(store.path) as db:
        db.execute("UPDATE checkpoints SET body='{}'")
    with pytest.raises(ValueError,match='integrity'):
        ReadingSession.resume(store,'corrupt',reader,'lecture',budget)


def test_interrupted_transaction_recovers_last_complete_revision(setup):
    _,reader,budget,store,s=setup
    identifier=s.save(store,'atomic')
    db=sqlite3.connect(store.path)
    db.execute('BEGIN IMMEDIATE')
    db.execute("INSERT INTO checkpoints VALUES ('atomic',2,'incomplete','partial','bad')")
    db.close()  # Simulated interruption before commit: SQLite rolls it back.
    assert store.latest('atomic').checkpoint_id==identifier
    assert ReadingSession.resume(store,'atomic',reader,'lecture',budget).state==s.state


@pytest.mark.parametrize('run_id',['../notes','a/b','', 'x'*81])
def test_invalid_storage_identifiers_cannot_escape_namespace(tmp_path,run_id):
    store=SQLiteCheckpointStore(tmp_path/'store')
    with pytest.raises(ValueError): store.latest(run_id)
    assert not store.namespace.exists()


def test_unrelated_database_is_never_reused(tmp_path):
    store=SQLiteCheckpointStore(tmp_path/'store')
    store.namespace.mkdir()
    with sqlite3.connect(store.path) as db:
        db.execute('CREATE TABLE existing_notes(content TEXT)')
        db.execute("INSERT INTO existing_notes VALUES ('untouched')")
    with pytest.raises(ValueError,match='unrelated'):
        store.append(Checkpoint(1,'run','stage',(),'config',()))
    with sqlite3.connect(store.path) as db:
        assert db.execute('SELECT * FROM existing_notes').fetchall()==[('untouched',)]
        assert db.execute("SELECT name FROM sqlite_master WHERE name='checkpoints'").fetchall()==[]


def test_enabled_phase2_entrypoint_needs_no_api_keys_and_makes_no_api_calls(setup,monkeypatch):
    source,reader,budget,_,_=setup
    import socket
    def forbidden(*_,**__): pytest.fail('Offline Phase 2 attempted network access')
    monkeypatch.setattr(socket,'socket',forbidden)
    original=source.read_bytes()
    s=prepare_reading(reader,'lecture',budget.limits,context=budget.config,
                      environment={'NOETRA_INFOGRAPHIC_ENGINE_ENABLED':'true'})
    assert s.next_window().window is not None
    assert source.read_bytes()==original


def test_real_existing_notes_formats_are_lossless_read_only():
    root=Path(__file__).resolve().parents[2]
    baseline=json.loads((root/'backend/app/infographics/PHASE2_BASELINE.json').read_text(encoding='utf-8'))
    paths={}
    for row in baseline['files']:
        for filename in ('generated_notes.md','polished_notes.md','ordered_notes.json'):
            if row['path'].endswith('/'+filename): paths[filename]=root/row['path']
    assert set(paths)=={'generated_notes.md','polished_notes.md','ordered_notes.json'}
    for name,path in paths.items():
        original=path.read_bytes()
        index=build_index(FileSourceReader({name:path}).snapshot(name))
        assert index.reconstruct().encode('utf-8')==original
        assert path.read_bytes()==original
        assert index.units


def test_existing_backend_starts_and_lists_videos_without_new_keys():
    import os
    import subprocess
    import sys
    code='''
import sys
def audit(event,args):
    if event in ('socket.connect','subprocess.Popen'):
        raise AssertionError('Unexpected network request or worker process')
sys.addaudithook(audit)
import video_notes_jobs as backend
assert isinstance(backend.videos(),list)
assert not backend.worker._threads
assert not any(name.startswith('app.infographics') for name in sys.modules)
backend.worker.shutdown(wait=True)
print('Existing backend import and video list passed; no worker or infographic startup')
'''
    env=dict(os.environ,NOETRA_INFOGRAPHIC_ENGINE_ENABLED='false',PYTHONDONTWRITEBYTECODE='1')
    for key in ('GEMINI_PLANNER_API_KEY','GEMINI_GENERATOR_API_KEY','GEMINI_VERIFIER_API_KEY'):
        env.pop(key,None)
    result=subprocess.run([sys.executable,'-c',code],cwd=Path(__file__).resolve().parents[1],
                          env=env,capture_output=True,text=True,timeout=30)
    assert result.returncode==0,result.stderr
