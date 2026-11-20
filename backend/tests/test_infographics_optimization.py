import copy
import json
from dataclasses import replace
from pathlib import Path
import pytest
from tests.test_infographics_segmentation import make,row
from app.infographics.contracts import Completion
from app.infographics.optimization import OptimizationJob,prepare_optimization
from app.infographics.optimization_model import OptimizationConfig,canonical,compact,ownership
from app.infographics.checkpoints import SQLiteCheckpointStore


def setup(tmp_path,text=None):
    job,transport=make(tmp_path,text or 'A queue preserves order.\n\nA queue adds at the tail.\n\nA stack uses a different order.')
    blocks=job.reading.index.units
    transport.responses=[json.dumps(dict(segments=[row(b.id,b.id,'A','document_end' if i==len(blocks)-1 else 'objective_change') for i,b in enumerate(blocks)],pending_from=None))]
    assert job.run()=='complete'
    optimizer=OptimizationJob(job,store=SQLiteCheckpointStore(tmp_path/'optimization'),config=OptimizationConfig(max_rounds=1))
    return job,transport,optimizer


def responder(transport,merges=None,confirm=True):
    calls=[]
    def complete(model,content,max_output_tokens):
        body=json.loads(content);calls.append(body)
        if body['task']=='plan':
            data=body['data']; ids=data['eligible_segments']
            operations=merges(ids) if merges else [dict(segments=ids[:2],category='A',title='Queue structure',focus='Queue purpose and insertion',density='medium',estimated_items=8,reason='shared_objective')]
            answer=dict(merges=operations,attachments=[])
        else:
            answer=dict(confirmations=[dict(id=item['id'],supported=confirm,preserves_distinctions=confirm,readable=confirm,category=item['proposal'].get('category','N')) for item in body['data']])
        return Completion(json.dumps(answer),100,50)
    transport.complete=complete
    return calls


def test_merge_preserves_source_and_input(tmp_path):
    job,t,opt=setup(tmp_path); before=canonical(job.manifest); calls=responder(t)
    assert opt.run()=='complete'
    assert canonical(job.manifest)==before
    groups=json.loads(opt.manifest)
    assert len(groups)==2 and len(groups[0]['constituents'])==2
    assert groups[0]['source_start']==0 and groups[-1]['source_end']==len(opt.index.text)
    assert opt.metrics()['visual_count_reduction']==1
    assert opt.metrics()['source_range_coverage']==1 and not opt.metrics()['semantic_fact_coverage_verified']
    assert len(calls)==2 and all('text' not in r for r in calls[0]['data']['segments'])
    assert 'source' in calls[1]['data'][0]


@pytest.mark.parametrize('bad',['unknown','nonadjacent','duplicate','conflicting','category','extra','truncated','duplicate_json'])
def test_invalid_operations_preserve_input(tmp_path,bad):
    job,t,opt=setup(tmp_path); before=canonical(opt.groups)
    def complete(model,content,max_output_tokens):
        body=json.loads(content);ids=body['data']['eligible_segments']
        proposal=dict(segments=ids[:2],category='A',title='Title',focus='Objective',density='medium',estimated_items=5,reason='shared_objective')
        if bad=='unknown': proposal['segments']=['missing',ids[0]]
        if bad=='nonadjacent': proposal['segments']=[ids[0],ids[-1]]
        if bad=='duplicate': proposal['segments']=[ids[0],ids[0]]
        if bad=='category': proposal['category']='Z'
        if bad=='extra': proposal['facts']='invented'
        value=dict(merges=[proposal,proposal] if bad=='conflicting' else [proposal],attachments=[])
        text=json.dumps(value)
        if bad=='truncated': text=text[:-2]
        if bad=='duplicate_json': text='{"merges":[],"merges":[],"attachments":[]}'
        return Completion(text,50,20)
    t.complete=complete
    assert opt.run()=='paused_invalid_response'
    assert canonical(opt.groups)==before and opt.requests==2
    assert ownership(opt.groups,opt.index)


def test_semantic_rejection_keeps_original(tmp_path):
    _,t,opt=setup(tmp_path);responder(t,confirm=False)
    assert opt.run()=='complete'
    assert len(opt.groups)==3 and opt.metrics()['accepted_merges']==0 and opt.metrics()['rejected_merges']==1


def test_downstream_overflow_rejected_before_source_call(tmp_path):
    _,t,opt=setup(tmp_path);opt.config=replace(opt.config,generation_input_tokens=100)
    calls=responder(t)
    assert opt.run()=='complete' and len(calls)==1
    assert 'overflow' in opt.rejected[0]['reason'].lower()


def test_category_reassignment(tmp_path):
    _,t,opt=setup(tmp_path)
    responder(t,lambda ids:[dict(segments=ids[:2],category='B',title='Queue operations',focus='Adding and preserving order',density='medium',estimated_items=8,reason='complete_process')])
    assert opt.run()=='complete' and opt.groups[0]['category']=='B'
    assert opt.groups[0]['merge_history'][-1]['original_categories']==['A','A']


def test_resume_cache_and_corruption(tmp_path):
    job,t,opt=setup(tmp_path);calls=responder(t);opt.run()
    resumed=OptimizationJob.resume(job,store=opt.store,run_id=opt.run_id,config=opt.config)
    assert resumed.manifest==opt.manifest
    resumed.run();assert len(calls)==2 and resumed.cache_reuse>=1
    record=opt.store.latest(opt.run_id);value=json.loads(record.state_json)
    value['groups'][0]['source_end']=999
    value['state']['revision']+=1
    opt.store.append(replace(record,state_json=canonical(value),parent_checkpoint_id=record.checkpoint_id))
    with pytest.raises(ValueError,match='integrity'): OptimizationJob.resume(job,store=opt.store,run_id=opt.run_id,config=opt.config)


@pytest.mark.parametrize('change',['source','manifest','prompt','config','incomplete'])
def test_incompatible_input_rejected(tmp_path,change):
    job,t,opt=setup(tmp_path);responder(t);opt.run()
    options=dict(store=opt.store,run_id=opt.run_id,config=opt.config)
    if change=='source': job.manifest[0]['source_sha256']='bad'
    if change=='manifest': job.manifest[0]['id']='bad'
    if change=='prompt': options['prompt']='Changed'
    if change=='config': options['config']=replace(opt.config,generation_output_tokens=999)
    if change=='incomplete': job.status='ready'
    with pytest.raises(ValueError): OptimizationJob.resume(job,**options)


def test_disabled_and_single_no_calls(tmp_path):
    assert prepare_optimization(None,environment={}) is None
    job,t=make(tmp_path,'A single concept.'); b=job.reading.index.units[0]
    t.responses=[json.dumps(dict(segments=[row(b.id,b.id,'A','document_end')],pending_from=None))];job.run()
    opt=OptimizationJob(job,store=SQLiteCheckpointStore(tmp_path/'opt'))
    assert opt.run()=='optimization_skipped' and opt.requests==0


def test_provider_failure_pauses_with_provisional_intact(tmp_path):
    from app.infographics.clients import ProviderError
    job,t,opt=setup(tmp_path)
    def fail(*_,**__): raise ProviderError('quota_hold')
    t.complete=fail
    assert opt.run()=='paused_quota_hold' and len(opt.groups)==len(job.manifest)
    with pytest.raises(ValueError): _=opt.manifest


def test_capacity_unknown_is_provisional(tmp_path):
    _,t,opt=setup(tmp_path);responder(t);opt.run()
    assert opt.groups[0]['downstream_context']['status']=='provisional_limits'


def test_empty_input(tmp_path):
    job,t=make(tmp_path,''); opt=OptimizationJob(job,store=SQLiteCheckpointStore(tmp_path/'opt'))
    assert opt.run()=='optimization_skipped' and json.loads(opt.manifest)==[]


def test_nonvisual_attachment_remaps_merged_target(tmp_path):
    job,t=make(tmp_path,'A component.\n\nA related component.\n\nAn unrelated concept.\n\nA supporting proof.')
    b=job.reading.index.units
    t.responses=[json.dumps(dict(segments=[row(x.id,x.id,'N' if i==3 else 'A','document_end' if i==3 else 'objective_change') for i,x in enumerate(b)],pending_from=None))];job.run()
    opt=OptimizationJob(job,store=SQLiteCheckpointStore(tmp_path/'opt'),config=OptimizationConfig(max_rounds=1))
    def respond(model,content,max_output_tokens):
        body=json.loads(content)
        if body['task']=='plan':
            value=dict(merges=[dict(segments=['s0','s1'],category='A',title='Components',focus='System components',density='medium',estimated_items=8,reason='complementary_components')],
                       attachments=[dict(source='s3',target='s1',reason='supporting_derivation')])
        else:
            value=dict(confirmations=[dict(id=i['id'],supported=True,preserves_distinctions=True,readable=True,category=i['proposal'].get('category','N')) for i in body['data']])
        return Completion(json.dumps(value),100,50)
    t.complete=respond
    assert opt.run()=='complete' and len(opt.groups)==3
    assert opt.groups[-1]['category']=='N'
    assert opt.groups[-1]['supplementary_links'][0]['target']==opt.groups[0]['id']
    assert opt.groups[-1]['supplementary_links'][0]['semantically_represented'] is False
    resumed=OptimizationJob.resume(job,store=opt.store,config=opt.config)
    assert resumed.manifest==opt.manifest


def test_large_manifest_windows_overlap_and_source_batches(tmp_path):
    text='\n\n'.join('Shared system component '+str(i)+'.' for i in range(40))
    job,t=make(tmp_path,text)
    b=job.reading.index.units
    # Complete Phase 3 in one supplied response under a larger source target.
    def segment(model,content,max_output_tokens):
        blocks=json.loads(content)['regions']['B']['blocks']
        return Completion(json.dumps(dict(segments=[row(x['id'],x['id']) for x in blocks],pending_from=None)),100,50)
    t.complete=segment; assert job.run()=='complete'
    from app.infographics.token_budget import TokenBudgetManager
    job.reading.budget=TokenBudgetManager(replace(job.reading.budget.limits,input_tokens=7000),job.reading.budget.config)
    opt=OptimizationJob(job,store=SQLiteCheckpointStore(tmp_path/'opt'),config=OptimizationConfig(max_rounds=1,max_requests=100))
    tasks=opt._plan_tasks()
    assert len(tasks)>1
    pairs={tuple(c['segments']) for task in tasks for c in task['candidates']}
    assert all(('s'+str(i),'s'+str(i+1)) in pairs for i in range(len(b)-1))
    assert all(opt._fits(opt._body('plan',{k:v for k,v in task.items() if k!='mapping'})) for task in tasks)


def test_interrupted_request_requires_explicit_retry(tmp_path):
    job,t,opt=setup(tmp_path);responder(t)
    opt.status='request_in_flight';opt.request_resume_stage='plan';opt.save()
    resumed=OptimizationJob.resume(job,store=opt.store,config=opt.config)
    assert resumed.status=='paused_uncertain_request'
    assert resumed.run()=='paused_uncertain_request' and resumed.requests==0
    assert resumed.run(retry_paused=True)=='complete'


def test_source_confirmation_overflow_and_minimum_protected(tmp_path):
    _,t,opt=setup(tmp_path)
    opt.visual_budget['target_min']=3
    calls=responder(t)
    assert opt.run()=='optimization_skipped'
    assert len(calls)==0 and len(opt.groups)==3


@pytest.mark.parametrize('fixture_number',range(30))
def test_existing_fixture_before_after_comparison(tmp_path,fixture_number):
    from app.infographics.optimization_evaluation import fixture_set,fragmented_job,compare
    base,t=make(tmp_path)
    fixture=fixture_set()['fixtures'][fixture_number]
    job=fragmented_job(fixture,base.planner,base.reading.budget,base.store,'fixture')
    opt=OptimizationJob(job,store=SQLiteCheckpointStore(tmp_path/'opt'),config=OptimizationConfig(max_rounds=1))
    responder(t,lambda ids:[dict(segments=ids[:2],category=fixture['acceptable_categories'][0][0],title='Related educational objective',
        focus='Original concept and essential supporting explanation',density='medium',estimated_items=6,reason='shared_objective')])
    assert opt.run() in {'complete','optimization_skipped'}
    result=compare(fixture,job.manifest,opt.groups)
    assert result['optimized']['source_range_coverage']==1
    assert result['optimized']['required_boundaries_omitted']==0
    assert result['optimized']['duplicate_ownership_count']==0


def test_four_components_and_process_stages_become_one_group(tmp_path):
    job,t=make(tmp_path,'\n\n'.join('Pipeline component '+str(i)+'.' for i in range(5)))
    blocks=job.reading.index.units
    t.responses=[json.dumps(dict(segments=[row(b.id,b.id,'B','document_end' if i==4 else 'objective_change') for i,b in enumerate(blocks)],pending_from=None))]
    job.run()
    # Existing item estimates 4*4 exceed B's conservative default; explicitly
    # configured category guidance permits this synthetic 16-item case.
    config=OptimizationConfig(max_rounds=1,capacity_items=(('A',20),('B',20),('C',15),('N',20)))
    opt=OptimizationJob(job,store=SQLiteCheckpointStore(tmp_path/'opt'),config=config)
    responder(t,lambda ids:[dict(segments=ids[:4],category='B',title='Complete indexing process',focus='Loading, chunking, embedding and indexing',density='high',estimated_items=16,reason='complete_process')])
    assert opt.run()=='complete' and len(opt.groups[0]['constituents'])==4
    assert opt.metrics()['visual_count_reduction']==3


def test_oversized_continuation_preserved(tmp_path):
    job,t=make(tmp_path)
    ids=[b.id for b in job.reading.index.units]
    t.responses=[json.dumps(dict(segments=[],pending_from=ids[0])),
        json.dumps(dict(segments=[row(ids[0],ids[0],'A','context_limit')],pending_from=ids[1])),
        json.dumps(dict(segments=[row(ids[1],ids[1]),row(ids[2],ids[2],'A','document_end')],pending_from=None))]
    assert job.run()=='complete'
    opt=OptimizationJob(job,store=SQLiteCheckpointStore(tmp_path/'opt'),config=OptimizationConfig(max_rounds=1,generation_input_tokens=100))
    calls=responder(t);opt.run()
    assert opt.groups[0]['continuation_groups']==opt.groups[1]['continuation_groups']
    assert len(opt.groups)==3 and len(calls)==1


def test_opt_in_dry_run_and_no_wrong_role(tmp_path):
    from app.infographics.evaluate_optimization import main
    assert main(['--dry-run','--fixture','01-queue'])['requests']==0
    job,t,opt=setup(tmp_path)
    other=copy.copy(job.planner); other.config=replace(other.config,role='generator')
    with pytest.raises(ValueError,match='planner'): OptimizationJob(job,planner=other)


def test_continuation_recovery_success(tmp_path):
    job,t=make(tmp_path);ids=[b.id for b in job.reading.index.units]
    t.responses=[json.dumps(dict(segments=[],pending_from=ids[0])),
        json.dumps(dict(segments=[row(ids[0],ids[0],'A','context_limit')],pending_from=ids[1])),
        json.dumps(dict(segments=[row(ids[1],ids[1]),row(ids[2],ids[2],'A','document_end')],pending_from=None))]
    job.run();opt=OptimizationJob(job,store=SQLiteCheckpointStore(tmp_path/'opt'),config=OptimizationConfig(max_rounds=1))
    responder(t);opt.run()
    assert len(opt.groups)==2 and opt.metrics()['continuation_groups_consolidated']==1
    assert opt.groups[0]['continuation_groups']


def test_stale_checkpoint_and_failed_write_preserve_valid_result(tmp_path,monkeypatch):
    job,t,opt=setup(tmp_path);opt.save()
    stale=OptimizationJob.resume(job,store=opt.store,config=opt.config)
    responder(t);opt.run()
    from app.infographics.checkpoints import CheckpointConflict
    with pytest.raises(CheckpointConflict): stale.save()
    assert OptimizationJob.resume(job,store=opt.store,config=opt.config).manifest==opt.manifest


@pytest.mark.parametrize('bad',['gap','overlap','unknown_source'])
def test_provisional_range_corruption_rejected(tmp_path,bad):
    job,t,opt=setup(tmp_path)
    if bad=='gap': job.manifest.pop(1)
    if bad=='overlap': job.manifest[1]['start_position']=0
    if bad=='unknown_source': job.manifest[0]['source_artifact_id']='other'
    with pytest.raises(ValueError): OptimizationJob(job)


def test_second_round_reconciliation_is_bounded(tmp_path):
    text='\n\n'.join('Shared related component '+str(i)+'.' for i in range(6))
    job,t,opt=setup(tmp_path,text)
    # setup's fixture may require more than one Phase 3 request for longer input;
    # this six-block case fits its initial source target.
    opt.config=replace(opt.config,max_rounds=2)
    calls=responder(t)
    assert opt.run()=='complete' and opt.round<=2 and len(calls)<=4
    assert opt.metrics()['source_range_coverage']==1
