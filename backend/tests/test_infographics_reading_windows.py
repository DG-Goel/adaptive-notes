"""Offline token budgeting, ownership boundaries, carryover and loop prevention."""
from dataclasses import replace
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from app.infographics.config import ClientConfig
from app.infographics.contracts import ModelInfo
from app.infographics.reading import prepare_reading
from app.infographics.reading_windows import BoundaryDecision, InvalidBoundary, ReadingSession, ReadingState
from app.infographics.source_index import build_index
from app.infographics.token_budget import (ConservativeCounter, ContextConfig, ModelLimits,
    RequestParts, TokenBudgetManager, TokenCount)
from tests.test_infographics_source_index import snapshot


def session(text=None,*,config=None,limits=None,parts=None):
    text=text if text is not None else '\n\n'.join(f'Paragraph {i}: '+'x'*80 for i in range(35))
    config=config or ContextConfig(target_source_tokens=400,max_source_tokens=1800,
        lookahead_tokens=200,previous_context_tokens=200,reserved_output_tokens=300)
    limits=limits or ModelLimits(6000,1000,8000)
    return ReadingSession(build_index(snapshot(text)),TokenBudgetManager(limits,config),parts)


def test_adjustable_defaults_and_conservative_estimation():
    config=ContextConfig()
    assert (config.target_source_tokens,config.max_source_tokens,config.lookahead_tokens,
        config.previous_context_tokens,config.reserved_output_tokens,config.safety_margin_ratio)==(10000,16000,1500,500,3000,.1)
    count=ConservativeCounter().count('中文😀')
    assert count.value==10 and count.kind=='estimated'
    assert 'utf8' in count.method


def test_separate_hosted_input_output_shared_limits_and_margin():
    manager=TokenBudgetManager(ModelLimits(10000,2000,9000),
        ContextConfig(reserved_output_tokens=3000,thinking_tokens=200))
    assert manager.response_tokens==1800
    assert manager.input_capacity==9000-900-1800-200-256
    no_shared=TokenBudgetManager(ModelLimits(10000,2000))
    assert no_shared.input_capacity==10000-1000-256


def test_actual_metadata_and_missing_metadata_remain_distinct():
    client=ClientConfig('planner','not-a-real-key',context_tokens=12000,max_output_tokens=2000)
    metadata=ModelInfo('models/'+client.model,8000,1000,('generateContent',))
    limits=ModelLimits.from_client(client,metadata)
    assert limits.input_tokens==8000 and limits.output_tokens==1000
    assert limits.shared_context_tokens==12000 and limits.metadata_verified
    offline=ModelLimits.from_client(client)
    assert offline.input_tokens==12000 and not offline.metadata_verified
    assert offline.phase1_byte_guard
    with pytest.raises(ValueError): ModelLimits.from_client(client,replace(metadata,name='other'))
    with pytest.raises(ValueError): ModelLimits.from_client(client,replace(metadata,input_tokens=0))


@pytest.mark.parametrize('changes',[dict(target_source_tokens=0),dict(max_source_tokens=100),
    dict(previous_context_tokens=-1),dict(safety_margin_ratio=1),dict(safety_margin_ratio=float('nan')),
    dict(expansion_factor=1),dict(max_no_progress=0)])
def test_invalid_context_config(changes):
    with pytest.raises(ValueError): ContextConfig(**changes)


@pytest.mark.parametrize('values',[(0,100,None),(100,0,None),(100,100,0),(True,100,None)])
def test_invalid_explicit_limits(values):
    with pytest.raises(ValueError): ModelLimits(*values)


def test_thinking_cannot_consume_all_output_budget():
    with pytest.raises(ValueError,match='Thinking'):
        TokenBudgetManager(ModelLimits(10000,1000),ContextConfig(thinking_tokens=1000))


def test_all_request_components_and_final_serialized_payload_are_budgeted():
    parts=RequestParts('system','prompt','metadata','summary')
    s=session(parts=parts)
    w=s.next_window().window
    report=w.budget
    names=dict(report.components)
    assert set(names)=={'system_instructions','segmentation_prompt','request_metadata',
        'previous_context','current_source_window','forward_lookahead','serialized_request'}
    assert names['system_instructions'].value==len('system')
    assert report.input_count.value==len(w.payload.encode('utf-8'))
    assert report.input_with_framing==report.input_count.value+256
    assert report.fits
    assert not s.preflight(final_payload=w.payload+'x'*10000).fits


def test_measured_token_counter_is_explicit_and_phase1_guard_remains_compatible():
    class Measured:
        def count(self,text):
            return TokenCount(len(text),'measured','test-local-tokenizer')
    index=build_index(snapshot('中文讲义。'))
    manager=TokenBudgetManager(ModelLimits(6000,500,8000),counter=Measured())
    s=ReadingSession(index,manager)
    w=s.next_window().window
    assert w.budget.input_count.kind=='measured'
    guarded=TokenBudgetManager(replace(manager.limits,phase1_byte_guard=True),counter=Measured())
    report=guarded.check(s.index,s.parts,source=w.source)
    assert report.phase1_guard_tokens>report.input_count.value


def test_phase1_byte_guard_keeps_required_framing_even_if_config_requests_zero():
    config=ClientConfig('planner','not-real')
    manager=TokenBudgetManager(ModelLimits.from_client(config),ContextConfig(framing_tokens=0))
    assert manager.framing_tokens==256
    s=ReadingSession(build_index(snapshot('A short source.')),manager)
    w=s.next_window().window
    assert w.budget.input_with_framing==len(w.payload.encode('utf-8'))+256


def test_report_distinguishes_input_and_shared_safety_margins():
    s=session(limits=ModelLimits(6000,1000,8000))
    report=s.next_window().window.budget
    assert report.input_safety_margin_tokens==600
    assert report.shared_safety_margin_tokens==800


def test_source_target_reduces_to_effective_hosted_limit():
    text='\n\n'.join('Paragraph '+str(i)+' '+'x'*100 for i in range(100))
    config=ContextConfig(reserved_output_tokens=500)
    s=session(text,config=config,limits=ModelLimits(2500,500,3000))
    w=s.next_window().window
    assert w and w.budget.fits
    assert sum(b.token_count for b in w.source)<config.target_source_tokens
    assert w.budget.input_with_framing<=2500-250
    assert w.lookahead  # Source yields a whole group when budget needs space for C.


def test_preflight_rechecks_new_provider_metadata_without_requests():
    s=session()
    w=s.next_window().window
    smaller=ModelInfo('models/test',500,1000,('generateContent',))
    report=s.preflight(provider_metadata=smaller)
    assert not report.fits and report.metadata_verified
    larger=replace(smaller,input_tokens=10000)
    assert s.preflight(provider_metadata=larger).fits
    assert w.budget.input_count.kind=='estimated'


def test_regions_have_explicit_boundaries_and_ownership():
    s=session()
    w=s.next_window().window
    body=json.loads(w.payload)
    assert [body['regions'][r]['ownership'] for r in 'ABC']==['read_only','commit_eligible','lookahead_only']
    assert not w.previous and w.source and w.lookahead
    assert {b.id for b in w.source}.isdisjoint(b.id for b in w.lookahead)
    assert w.source[0].position==0 and w.lookahead[0].position==w.end
    assert s.state.cursor==0 and not s.ledger()['committed_source_blocks']


def test_partial_commit_carryover_and_previous_context_isolation():
    s=session()
    first=s.next_window().window
    boundary=first.source[1]
    s.apply(BoundaryDecision(first.id,boundary.id,first.source[2].id))
    assert s.state.cursor==2
    second=s.next_window().window
    assert second.source[0].id==first.source[2].id
    assert second.previous and all(b.position<2 for b in second.previous)
    assert all(b.position>=2 for b in second.source)
    assert len(s.ledger()['committed_source_blocks'])==2


@pytest.mark.parametrize('region',['previous','lookahead','unknown','pending','window'])
def test_invalid_decisions_never_advance_or_mutate_state(region):
    s=session()
    w=s.next_window().window
    s.apply(BoundaryDecision(w.id,w.source[1].id))
    w=s.next_window().window
    old=s.state
    if region=='previous': decision=BoundaryDecision(w.id,w.previous[-1].id)
    elif region=='lookahead': decision=BoundaryDecision(w.id,w.lookahead[0].id)
    elif region=='pending': decision=BoundaryDecision(w.id,w.source[0].id,w.source[-1].id)
    elif region=='window': decision=BoundaryDecision('stale',w.source[0].id)
    else: decision=BoundaryDecision(w.id,'does-not-exist')
    with pytest.raises(InvalidBoundary): s.apply(decision)
    assert s.state==old


def test_decision_cannot_be_replayed():
    s=session()
    w=s.next_window().window
    decision=BoundaryDecision(w.id,w.source[0].id)
    s.apply(decision)
    with pytest.raises(InvalidBoundary): s.apply(decision)


def test_no_progress_expands_but_never_advances_cursor():
    s=session()
    w=s.next_window().window
    old_end=w.end
    state=s.apply(BoundaryDecision(w.id,pending_from_id=w.source[0].id))
    assert state.cursor==0 and state.no_progress==1 and state.repeated_pending==1
    assert state.target_source_tokens>400
    next_w=s.next_window().window
    assert next_w.source[0].id==w.source[0].id
    assert next_w.end>old_end


def test_no_progress_is_bounded_and_never_skips_uncommitted_content():
    s=session()
    for _ in range(s.budget.config.max_no_progress):
        result=s.next_window()
        if result.window is None: break
        s.apply(BoundaryDecision(result.window.id))
    assert s.state.status in {'oversized_concept','forced_boundary_required'}
    assert s.state.cursor==0
    assert s.next_window().window is None
    ledger=s.ledger()
    assert len(ledger['uncommitted_source_blocks'])==len(s.index.units)
    assert ledger['committed_source_blocks']==()
    assert s.next_window(allow_forced_boundary=True).window is not None


def test_final_document_no_progress_requests_explicit_boundary():
    s=session('A short lecture.')
    w=s.next_window().window
    assert w.final_document_window
    s.apply(BoundaryDecision(w.id))
    assert s.state.status=='forced_boundary_required'
    assert not s.ledger()['complete'] and s.state.cursor==0


def test_empty_source_is_complete_without_window_or_model_call():
    s=session('')
    assert s.state.status=='complete' and s.next_window().status=='complete'
    assert s.ledger()['total_original_blocks']==0 and s.ledger()['complete']


def test_complete_processing_accounts_every_range_without_overlap():
    s=session()
    committed=[]
    windows=0
    while not s.ledger()['complete']:
        windows+=1
        assert windows<=len(s.index.units)
        w=s.next_window().window
        assert w and w.budget.fits
        count=max(1,len(w.source)//2)
        committed.extend(b.id for b in w.source[:count])
        s.apply(BoundaryDecision(w.id,w.source[count-1].id))
        ledger=s.ledger()
        assert len(ledger['committed_source_blocks'])+len(ledger['uncommitted_source_blocks'])==len(s.index.units)
        assert set(ledger['committed_source_blocks']).isdisjoint(ledger['uncommitted_source_blocks'])
    assert committed==[b.id for b in s.index.units]
    assert len(committed)==len(set(committed))
    assert all(status=='committed' for _,status in s.ledger()['original_block_status'])
    assert s.next_window().status=='complete'


def test_oversized_atomic_and_cohesive_groups_return_explicit_status():
    s=session('```python\n'+'x'*12000+'\n```')
    result=s.next_window()
    assert result.status=='unsupported_atomic_block' and result.block_ids
    assert s.state.cursor==0 and s.ledger()['unresolved_oversized_blocks']
    s=session('## Heading\n\n'+'x'*12000)
    assert s.next_window().status=='oversized_concept'
    assert s.state.cursor==0


def test_subdivided_list_complete_accounting():
    text=''.join('- Item '+str(i)+' '+'x'*100+'\n  - nested\n' for i in range(35))
    s=session(text)
    assert s.index.subdivisions
    assert s.index.reconstruct()==text
    # Use ample request space for the metadata of a subdivision leaf.
    while not s.ledger()['complete']:
        result=s.next_window()
        assert result.window is not None,result
        w=result.window
        s.apply(BoundaryDecision(w.id,w.source[-1].id))
    assert s.ledger()['original_block_status'][0][1]=='committed'


def test_previous_summary_is_separate_read_only_and_never_truncated():
    s=session(parts=RequestParts(previous_summary='Caller-supplied context summary.'))
    w=s.next_window().window
    assert not w.previous
    assert json.loads(w.payload)['regions']['A']['summary']=='Caller-supplied context summary.'
    s=session(parts=RequestParts(previous_summary='x'*201))
    assert s.next_window().status=='context_budget_exceeded'


def test_heading_cannot_be_stranded_by_request_boundary():
    s=session('# Heading\n\nFirst content.\n\n## Next\n\nSecond content.',
        config=ContextConfig(target_source_tokens=15,max_source_tokens=1000,reserved_output_tokens=100))
    w=s.next_window().window
    assert len(w.source)>=2 and w.source[0].type=='heading'


def test_restart_is_explicit_and_does_not_change_original_session():
    s=session()
    w=s.next_window().window
    s.apply(BoundaryDecision(w.id,w.source[-1].id))
    cursor=s.state.cursor
    restarted=s.restart()
    assert restarted.state.cursor==0 and s.state.cursor==cursor
    assert restarted.index.fingerprint==s.index.fingerprint


@pytest.mark.parametrize('state',[ReadingState(cursor=-1),ReadingState(cursor=2),
    ReadingState(cursor=1,committed_ranges=((0,2),(1,2))),ReadingState(status='complete'),
    ReadingState(pending_range=(1,3)),ReadingState(no_progress=-1),ReadingState(target_source_tokens=20000)])
def test_invalid_checkpoint_state_cannot_skip_or_rewind_ranges(state):
    base=session()
    with pytest.raises(ValueError): ReadingSession(base.index,base.budget,state=state)


def test_disabled_phase2_entrypoint_performs_no_source_reads_or_initialization():
    class ForbiddenReader:
        def snapshot(self,_): pytest.fail('Disabled feature read the source')
    assert prepare_reading(ForbiddenReader(),'x',None,environment={}) is None
    assert prepare_reading(ForbiddenReader(),'x',None,environment={'NOETRA_INFOGRAPHIC_ENGINE_ENABLED':'false'}) is None
    with pytest.raises(ValueError):
        prepare_reading(ForbiddenReader(),'x',None,environment={'NOETRA_INFOGRAPHIC_ENGINE_ENABLED':'yes'})


def test_disabled_phase2_imports_no_index_storage_sdk_or_worker(tmp_path):
    code='''
import sys, socket, os
def forbidden(*a,**k): raise AssertionError('Unexpected side effect')
socket.socket=forbidden
os.mkdir=forbidden
from app.infographics.reading import prepare_reading
assert prepare_reading(None,'source',None,environment={}) is None
for name in ('app.infographics.source_index','app.infographics.token_budget','app.infographics.reading_windows',
             'app.infographics.checkpoints','google.genai','video_notes_jobs'):
    assert name not in sys.modules, name
'''
    env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTHONPATH=str(Path(__file__).resolve().parents[1]))
    result=subprocess.run([sys.executable,'-c',code],cwd=tmp_path,env=env,capture_output=True,text=True,timeout=20)
    assert result.returncode==0,result.stderr
    assert list(tmp_path.iterdir())==[]
