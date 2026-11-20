import json
from dataclasses import replace
from pathlib import Path
import pytest
from tests.test_infographics_segmentation import make,row,Transport
from tests.test_infographics_source_index import snapshot
from app.infographics.source_index import build_index,FileSourceReader
from app.infographics.planner_init import initialize_planner
from app.infographics.planner_integrity import CheckpointIntegrityError
from app.infographics.segmentation import SegmentationJob
from app.infographics.educational_content import educational_text
from app.infographics.segmentation_budget import recommendation,VisualizationBudgetConfig
from app.infographics.segmentation_evaluation import evaluate
from app.infographics.evaluate_planner import main


def test_planner_only_disabled_and_enabled():
    class Disabled(dict):
        def get(self,key,*args):
            assert key=='NOETRA_INFOGRAPHIC_ENGINE_ENABLED'
            return 'false'
    assert initialize_planner(Disabled()) is None
    with pytest.raises(ValueError,match='GEMINI_PLANNER'): initialize_planner({'NOETRA_INFOGRAPHIC_ENGINE_ENABLED':'true'})
    seen=[]
    def factory(config): seen.append(config.role); return Transport()
    client,meta=initialize_planner({'NOETRA_INFOGRAPHIC_ENGINE_ENABLED':'true','GEMINI_PLANNER_API_KEY':'fake'},transport_factory=factory)
    assert seen==['planner'] and meta.name.endswith('gemma-4-31b-it')
    client.close()


@pytest.mark.parametrize('field,value',[('id','bad'),('start','unknown'),('source_start',999),('source_end',999),
    ('source_tokens',999),('source_words',999),('category','Z'),('title',''),('continuation_group','bad'),
    ('supports_start','unknown'),('source_sha256','bad'),('source_artifact_id','bad'),('supplementary_ids',['unknown'])])
def test_corrupt_fields_rejected(tmp_path,field,value):
    job,t=make(tmp_path); ids=[b.id for b in job.reading.index.units]
    t.responses=[json.dumps(dict(segments=[row(ids[0],ids[-1],'A','document_end')],pending_from=None))]
    job.step(); record=job.store.latest('test'); payload=json.loads(record.state_json)
    payload['manifest'][0][field]=value
    # Recompute outer checksum via normal persistence to exercise independent validation.
    payload['state']['revision']+=1
    job.store.append(replace(record,state_json=json.dumps(payload),parent_checkpoint_id=record.checkpoint_id))
    path=tmp_path/'s.md'; path.write_bytes(job.reading.index.snapshot.content)
    with pytest.raises(CheckpointIntegrityError):
        SegmentationJob.resume(FileSourceReader({'lecture-1':path}),'lecture-1',job.planner,job.reading.budget,job.store,'test')


def test_json_educational_counts_exclude_storage_but_keep_unknown():
    text='A queue preserves insertion order.'
    data=[dict(note_id='internal identifiers '*100,text=text,timing=[dict(start=1,end=2)],visuals=[dict(text=text)])]
    index=build_index(snapshot(json.dumps(data),'application/json'))
    assert educational_text(index)==text
    config=VisualizationBudgetConfig(complexity_weight=0)
    assert recommendation(index,config)['source_words']==recommendation(build_index(snapshot(text)),config)['source_words']
    data[0]['novelTechnicalExplanation']='Important unfamiliar educational material'
    assert 'Important unfamiliar' in educational_text(build_index(snapshot(json.dumps(data),'application/json')))


def test_complete_request_reserves_dynamic_overhead(tmp_path):
    job,t=make(tmp_path,'\n\n'.join('Text '+str(i)+' '+'x'*80 for i in range(100)))
    job.settings=replace(job.settings,capacity=(('A','guidance '*500),))
    from app.infographics.planner_context import construct_request
    original=job.reading.state
    result,payload=construct_request(job,True,'validation feedback '*30)
    assert result.window and result.window.budget.fits
    assert job.reading.state==original
    body=json.loads(payload)
    assert json.loads(body['request_metadata'])['forced']
    assert len(payload.encode())+256<=result.window.budget.input_limit


def test_insufficient_capacity_no_request_or_cursor_change(tmp_path):
    job,t=make(tmp_path)
    job.settings=replace(job.settings,capacity=(('A','x'*50000),))
    assert job.step()=='paused_capacity_error'
    assert not t.calls and job.reading.state.cursor==0


def test_dataset_evaluator_and_dry_run():
    path=Path(__file__).resolve().parents[1]/'app/infographics/evaluation/fixtures_v1.json'
    data=json.loads(path.read_text(encoding='utf-8'))
    assert len(data['fixtures'])>=30 and len({f['discipline'] for f in data['fixtures']})>=9
    for fixture in data['fixtures']:
        manifest=[dict(start_position=0,end_position=1,category=fixture['acceptable_categories'][0][0],estimated_items=4),
                  dict(start_position=2,end_position=2,category=fixture['acceptable_categories'][2][0],estimated_items=2)]
        metrics=evaluate(fixture,manifest)
        assert metrics['source_range_coverage']==1 and metrics['boundary_f1']==1
        assert metrics['master_category_accuracy']==1
        bad=evaluate(fixture,[dict(start_position=0,end_position=2,category='N')])
        assert bad['required_boundaries_omitted']==1 and bad['independent_concepts_merged']==1
    assert main(['--dry-run'])['network_requests']==0


@pytest.mark.parametrize('fixture_number',range(30))
def test_discipline_fixtures_through_runner(tmp_path,fixture_number):
    path=Path(__file__).resolve().parents[1]/'app/infographics/evaluation/fixtures_v1.json'
    fixture=json.loads(path.read_text(encoding='utf-8'))['fixtures'][fixture_number]
    job,t=make(tmp_path,'\n\n'.join(fixture['blocks']))
    def respond(model,content,max_output_tokens):
        from app.infographics.contracts import Completion
        blocks=json.loads(content)['regions']['B']['blocks']
        return Completion(json.dumps(dict(segments=[row(blocks[0]['id'],blocks[-1]['id'],fixture['acceptable_categories'][0][0],'document_end')],pending_from=None)),100,50)
    t.complete=respond
    assert job.run()=='complete' and job.reading.ledger()['complete']


def test_many_windows_and_lookahead_attack(tmp_path):
    job,t=make(tmp_path,'\n\n'.join('Paragraph '+str(i)+' '+'x'*90 for i in range(250)))
    from app.infographics.contracts import Completion
    calls=[]
    def respond(model,content,max_output_tokens):
        body=json.loads(content); blocks=body['regions']['B']['blocks']; calls.append(body)
        return Completion(json.dumps(dict(segments=[row(blocks[0]['id'],blocks[-1]['id'])],pending_from=None)),100,50)
    t.complete=respond
    assert job.run(max_steps=100)=='complete' and len(calls)>10
    from app.infographics.segmentation_schema import parse_response,SegmentationValidationError
    job,t=make(tmp_path/'attack','\n\n'.join('Item '+str(i)+' '+'x'*90 for i in range(35)))
    w=job.reading.next_window().window
    assert w.lookahead
    with pytest.raises(SegmentationValidationError):
        parse_response(json.dumps(dict(segments=[row(w.source[0].id,w.lookahead[0].id)],pending_from=None)),w)


def test_provider_context_error_resizes(tmp_path):
    from app.infographics.clients import ProviderError
    job,t=make(tmp_path); ids=[b.id for b in job.reading.index.units]
    t.responses=[ProviderError('context_limit'),json.dumps(dict(segments=[row(ids[0],ids[-1])],pending_from=None))]
    assert job.step()=='complete'
    assert any(h['event']=='provider_context_resize' for h in job.history)


def test_transient_retry_stays_in_role_client(tmp_path):
    from app.infographics.clients import ProviderError
    job,t=make(tmp_path); ids=[b.id for b in job.reading.index.units]
    t.responses=[ProviderError('network_unavailable',retryable=True),json.dumps(dict(segments=[row(ids[0],ids[-1])],pending_from=None))]
    assert job.step()=='complete' and len(t.calls)==2
    assert job.metrics()['usage']['failures']==1
