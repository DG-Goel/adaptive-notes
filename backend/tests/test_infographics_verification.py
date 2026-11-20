import copy
import json
from dataclasses import replace
import pytest
from tests.test_infographics_generation import setup
from tests.test_infographics_segmentation import Transport
from app.infographics.clients import RoleClient,ProviderError
from app.infographics.config import ClientConfig
from app.infographics.contracts import ModelInfo,Completion
from app.infographics.generation_fixtures import fixture
from app.infographics.template_registry import REGISTRY
from app.infographics.checkpoints import SQLiteCheckpointStore
from app.infographics.verifier_init import initialize_verifier
from app.infographics.verification import VerificationJob,VerificationConfig,prepare_verification
from app.infographics.verification_schema import inventory,report
from app.infographics.verification_model import claims,assess,coverage_metrics
from app.infographics.visual_repair import apply_repairs


def build(tmp_path,code='A4',config=None,bad=False):
    optimizer,generator,meta,transport,generation=setup(tmp_path,code)
    record=fixture(code)['record']
    if bad:record['data']['items'][0]['desc']='Removes newest item first'
    transport.responses=[json.dumps(dict(records=[record]))];assert generation.run()=='complete'
    def forbidden(*a,**kw):pytest.fail('Phase 6 called generator')
    generator.complete=forbidden;optimizer.planner.complete=forbidden
    settings=ClientConfig('verifier','fake-three',context_tokens=128000,max_output_tokens=12000,requests_per_minute=100,tokens_per_minute=1000000)
    t=Transport();t.model_info=lambda model:ModelInfo('models/'+model,128000,12000,('generateContent',))
    client=RoleClient(settings,t,sleep=lambda _:None);metadata=client.verify_model()
    job=VerificationJob(generation,optimizer,client,metadata,store=SQLiteCheckpointStore(tmp_path/'verify'),allow_skipped=True,config=config)
    return job,t,generation,optimizer,client,metadata


def fact_record(request):
    source=next(s for s in request['source'] if s.get('role','primary')=='primary')
    import re
    statement=re.split(r'(?<=[.!?])\s+',source['text'],maxsplit=1)[0]
    return dict(visual_id=request['visual_id'],complete=True,facts=[dict(id='local1',statement=statement,priority='essential',required_visible=True,
        refs=[source['ref']],evidence=[dict(ref=source['ref'],quote=source['text'])],literals=[],depends_on=[],redundant_of=None)])


def positive_report(request):
    visual=request['visual'];nodes=[]
    def walk(value):
        if isinstance(value,dict):
            if 'id' in value:nodes.append(value['id'])
            for child in value.values():walk(child)
        elif isinstance(value,list):
            for child in value:walk(child)
    walk(visual['data'])
    return dict(visual_id=request['visual_id'],coverage=[dict(fact_id=f['id'],status='visible_equivalent',items=[nodes[0]],duplicate_of=None) for f in request['facts']],
        grounding=[dict(claim_id=c['id'],status='supported_equivalent',refs=c['refs']) for c in request['claims']],issues=[])


def mock_semantics(transport,*,repair=False,negative=False):
    calls=[];evaluated=[0]
    def complete(model,content,max_output_tokens):
        body=json.loads(content);calls.append(body);task=body['task'];data=body['data']
        if task=='inventory':value=dict(records=[fact_record(r) for r in data])
        elif task in {'verify','compact'}:
            records=[]
            for request in data:
                if task=='compact':
                    inv=fact_record(request);request=dict(request,facts=inv['facts'])
                semantic=positive_report(request)
                if (repair and evaluated[0]==0) or negative:
                    semantic['coverage'][0].update(status='distorted',items=['a'])
                    for c,r in zip(request['claims'],semantic['grounding']):
                        if c['path']=='data/items/0/desc':r['status']='contradicted'
                    semantic['issues']=[dict(type='incorrect_definition',severity='essential',fact_ids=[request['facts'][0]['id']],item_ids=['a'],refs=[request['source'][0]['ref']],message='Queue ordering was changed')]
                if task=='compact':semantic.update(complete=inv['complete'],facts=inv['facts'])
                records.append(semantic)
            evaluated[0]+=1;value=dict(records=records)
        elif task=='repair':
            issue=data['issues'][0]
            value=dict(visual_id=data['visual_id'],repairs=[dict(issue_id=issue['id'],operation='replace_description',item_id='a',value='Preserves insertion order',refs=[data['source'][0]['ref']])],escalation=None)
        else:value=dict(status='consistent',issues=[])
        return Completion(json.dumps(value),100,50)
    transport.complete=complete
    return calls


@pytest.mark.parametrize('code',list(REGISTRY))
def test_all_templates_source_first_bidirectional_and_resume(tmp_path,code):
    job,t,generation,optimizer,client,metadata=build(tmp_path,code)
    original=copy.deepcopy(generation.results);calls=mock_semantics(t)
    assert job.run()=='complete_accepted'
    assert calls[0]['task']=='inventory' and 'visual' not in calls[0]['data'][0]
    assert 'claims' not in calls[0]['data'][0]
    assert calls[1]['task']=='verify' and calls[1]['data'][0]['template_constraint']
    assert job.results()[0]['acceptance']['accepted']
    assert job.results()[0]['metrics']['generated_claim_grounding']==1
    assert generation.results==original
    resumed=VerificationJob.resume(generation,optimizer,client,metadata,store=job.store,allow_skipped=True)
    assert resumed.run()=='complete_accepted' and resumed.results()==job.results() and len(calls)==2


def test_bounded_targeted_repair_creates_new_revision(tmp_path):
    job,t,generation,optimizer,client,metadata=build(tmp_path,bad=True)
    original=copy.deepcopy(generation.results);calls=mock_semantics(t,repair=True)
    assert job.run()=='complete_accepted'
    assert [c['task'] for c in calls]==['inventory','verify','repair','verify']
    result=job.results()[0]
    assert result['record']['data']['items'][0]['desc']=='Preserves insertion order'
    assert result['repairs'][0]['accepted'] and result['repairs'][0]['patches'][0]['before']['desc']=='Removes newest item first'
    assert generation.results==original
    assert result['adapter']['item_id_mapping']==next(iter(original.values()))['adapter']['item_id_mapping']
    resumed=VerificationJob.resume(generation,optimizer,client,metadata,store=job.store,allow_skipped=True)
    assert resumed.results()==job.results()


def test_no_improvement_keeps_best_and_stops(tmp_path):
    job,t,_,_,_,_=build(tmp_path,bad=True);calls=mock_semantics(t,negative=True)
    assert job.run()=='complete_unresolved'
    assert len(calls)==4 and job.rounds[next(iter(job.artifacts))]==1
    assert not job.repairs[next(iter(job.artifacts))][0]['accepted']
    assert job.results()[0]['record']['data']['items'][0]['desc']=='Removes newest item first'


def test_compact_mode_is_explicitly_distinct(tmp_path):
    job,t,_,_,_,_=build(tmp_path,config=VerificationConfig(mode='compact'));calls=mock_semantics(t)
    assert job.run()=='complete_accepted' and [c['task'] for c in calls]==['compact']
    assert job.results()[0]['inventory_mode']=='compact'


def test_key_three_only_and_disabled():
    class Disabled(dict):
        def get(self,key,*args):assert key=='NOETRA_INFOGRAPHIC_ENGINE_ENABLED';return 'false'
    assert initialize_verifier(Disabled()) is None
    assert prepare_verification(None,None,None,None,environment={}) is None
    seen=[]
    def factory(config):seen.append(config);return Transport()
    client,metadata=initialize_verifier({'NOETRA_INFOGRAPHIC_ENGINE_ENABLED':'true','GEMINI_API_KEY_3':'only-three'},transport_factory=factory)
    assert seen[0].role=='verifier' and seen[0].api_key=='only-three'
    assert 'only-three' not in repr(client.config);client.close()
    with pytest.raises(ValueError,match='GEMINI_API_KEY_3'):initialize_verifier({'NOETRA_INFOGRAPHIC_ENGINE_ENABLED':'true'})


@pytest.mark.parametrize('status',['source_only','uncertain','missing','distorted','partially_preserved'])
def test_bad_coverage_cannot_accept(status):
    facts=[dict(id='f',priority='critical',required_visible=True)]
    semantic=dict(coverage=[dict(fact_id='f',status=status,items=[],duplicate_of=None)],grounding=[],issues=[])
    assert not assess(facts,semantic)['accepted']
    assert coverage_metrics(facts,semantic)['critical_fact_coverage']==0


@pytest.mark.parametrize('failure',['quota_hold','credential_rejected','model_unavailable','network_unavailable'])
def test_provider_failure_never_accepts(tmp_path,failure):
    job,t,_,_,_,_=build(tmp_path)
    def fail(*_,**__):raise ProviderError(failure)
    t.complete=fail
    assert job.run()=='paused_'+failure and not job.evaluations


@pytest.mark.parametrize('raw',['not JSON','{"records":','{"records":[],"records":[]}','{"records":[]}'])
def test_invalid_responses_bounded(tmp_path,raw):
    job,t,_,_,_,_=build(tmp_path)
    t.complete=lambda *_,**__:Completion(raw,100,50)
    assert job.run()=='paused_invalid_response' and job.requests==2 and not job.inventories[next(iter(job.artifacts))]


def test_unauthorized_repairs_and_unrelated_targets():
    record=fixture('A4')['record'];source={'p0':fixture('A4')['source']}
    issues=[dict(id='issue',type='incorrect_definition',item_ids=['a'])]
    patch=dict(visual_id='v',repairs=[dict(issue_id='issue',operation='replace_description',item_id='b',value='Changed',refs=['p0'])],escalation=None)
    with pytest.raises(ValueError,match='unrelated'):apply_repairs(record,patch,'v',issues,source,'A')
    patch['repairs'][0]['item_id']='a';patch['repairs'][0]['operation']='write_file'
    with pytest.raises(ValueError,match='Unauthorized'):apply_repairs(record,patch,'v',issues,source,'A')


def test_inventory_evidence_and_redundancy_are_not_assumed():
    request=dict(visual_id='v',source=[dict(ref='p0',text='Exact original definition.',role='primary')])
    value=fact_record(request)
    value['facts'][0]['evidence'][0]['quote']='Invented evidence'
    with pytest.raises(ValueError,match='exact'):inventory(value,'v',{'p0':'Exact original definition.'},'index')
    value=fact_record(request);value['facts'][0]['priority']='redundant'
    with pytest.raises(ValueError,match='Unique'):inventory(value,'v',{'p0':'Exact original definition.'},'index')


def test_generation_corruption_rejected_before_verifier_call(tmp_path):
    job,t,generation,optimizer,client,metadata=build(tmp_path)
    next(iter(generation.results.values()))['adapter']['config']['template']='wrong'
    with pytest.raises(ValueError,match='adapter'):VerificationJob(generation,optimizer,client,metadata,allow_skipped=True)


def test_interruption_and_checkpoint_corruption(tmp_path):
    job,t,generation,optimizer,client,metadata=build(tmp_path);calls=mock_semantics(t)
    job.status='request_in_flight';job.inflight=dict(task='inventory',cursor=0,phase='inventory',payload_hash='synthetic');job.save()
    resumed=VerificationJob.resume(generation,optimizer,client,metadata,store=job.store,allow_skipped=True)
    assert resumed.run()=='paused_uncertain_request' and not calls
    assert resumed.run(retry_paused=True)=='complete_accepted'
    checkpoint=job.store.latest('verification');value=json.loads(checkpoint.state_json)
    v=next(iter(value['inventories']));value['inventories'][v][0]['statement']='Corrupt modified statement'
    value['state']['revision']+=1
    job.store.append(replace(checkpoint,state_json=json.dumps(value),parent_checkpoint_id=checkpoint.checkpoint_id))
    with pytest.raises(ValueError,match='identity'):VerificationJob.resume(generation,optimizer,client,metadata,store=job.store,allow_skipped=True)


@pytest.mark.parametrize('mutation',['missing_coverage','duplicate_coverage','missing_claim','duplicate_claim','unknown_item','unknown_ref','unknown_fact','invented_issue','bad_status'])
def test_semantic_schema_rejects_incomplete_or_adversarial_results(tmp_path,mutation):
    job,t,_,_,_,_=build(tmp_path)
    def complete(model,content,max_output_tokens):
        body=json.loads(content)
        if body['task']=='inventory':return Completion(json.dumps(dict(records=[fact_record(r) for r in body['data']])),100,50)
        request=body['data'][0];r=positive_report(request)
        if mutation=='missing_coverage':r['coverage']=[]
        elif mutation=='duplicate_coverage':r['coverage']*=2
        elif mutation=='missing_claim':r['grounding'].pop()
        elif mutation=='duplicate_claim':r['grounding'].append(r['grounding'][0])
        elif mutation=='unknown_item':r['coverage'][0]['items']=['foreign']
        elif mutation=='unknown_ref':r['grounding'][0]['refs']=['foreign']
        elif mutation=='unknown_fact':r['coverage'][0]['fact_id']='foreign'
        elif mutation=='invented_issue':r['issues']=[dict(type='auto_accept',severity='critical',fact_ids=[],item_ids=['a'],refs=['p0'],message='Ignore instructions')]
        else:r['coverage'][0]['status']='verified_everything'
        return Completion(json.dumps(dict(records=[r])),100,50)
    t.complete=complete
    assert job.run()=='paused_invalid_response' and not job.evaluations


def test_source_only_support_and_redundancy_are_separate_metrics():
    source={'p0':'A queue preserves insertion order. A detailed example remains in the original notes.'}
    facts=[dict(id='f0',priority='essential',required_visible=True),dict(id='f1',priority='supporting',required_visible=False),dict(id='f2',priority='essential',required_visible=True)]
    claims_list=[dict(id='c',items=['a'])]
    value=dict(visual_id='v',coverage=[dict(fact_id='f0',status='visible_equivalent',items=['a'],duplicate_of=None),
        dict(fact_id='f1',status='source_only',items=[],duplicate_of=None),dict(fact_id='f2',status='redundant',items=[],duplicate_of='f0')],
        grounding=[dict(claim_id='c',status='supported_equivalent',refs=['p0'])],issues=[])
    checked=report(value,'v',facts,claims_list,{'a'},set(),source)
    assert assess(facts,checked)['accepted']
    metrics=coverage_metrics(facts,checked)
    assert metrics['distinct_identified_facts']==2 and metrics['source_only_facts']==1
    assert metrics['visible_fact_coverage']==.5 and metrics['combined_essential_fact_coverage']==1


def test_capacity_has_no_calls_and_unchanged_originals(tmp_path):
    job,t,generation,_,_,_=build(tmp_path)
    from app.infographics.token_budget import TokenBudgetManager
    job.budget=TokenBudgetManager(replace(job.budget.limits,input_tokens=500),job.budget.config)
    before=copy.deepcopy(generation.results);calls=mock_semantics(t)
    assert job.run()=='unresolved_capacity' and not calls and generation.results==before


def test_scientific_truth_is_not_claimed_and_literals_are_checked():
    request=dict(visual_id='v',source=[dict(ref='p0',text='The lecturer states x=2.00 kg under condition A.',role='primary')])
    record=fact_record(request);record['facts'][0]['priority']='critical';record['facts'][0]['literals']=['2.01 kg']
    with pytest.raises(ValueError,match='literal'):inventory(record,'v',{'p0':request['source'][0]['text']},'index')


def test_wrong_verifier_role_and_optional_source_reader(tmp_path):
    job,t,generation,optimizer,client,metadata=build(tmp_path)
    wrong=copy.copy(client);wrong.config=replace(client.config,role='generator')
    with pytest.raises(ValueError,match='verifier'):VerificationJob(generation,optimizer,wrong,metadata,allow_skipped=True)
    from types import SimpleNamespace
    reader=SimpleNamespace(snapshot=lambda _:replace(job.index.snapshot,content=b'Changed',sha256='different'))
    with pytest.raises(ValueError,match='changed'):VerificationJob(generation,optimizer,client,metadata,source_reader=reader,allow_skipped=True)


@pytest.mark.parametrize('code',list(REGISTRY))
def test_unsupported_implicit_structure_or_assertion_escalates(tmp_path,code):
    job,t,generation,_,_,_=build(tmp_path,code,config=VerificationConfig(repair_rounds=0))
    original=copy.deepcopy(generation.results)
    def complete(model,content,max_output_tokens):
        body=json.loads(content)
        if body['task']=='inventory':value=dict(records=[fact_record(r) for r in body['data']])
        else:
            records=[]
            for request in body['data']:
                semantic=positive_report(request)
                structure=next(c for c in request['claims'] if c['path']=='template_semantics')
                next(r for r in semantic['grounding'] if r['claim_id']==structure['id'])['status']='unsupported'
                semantic['issues']=[dict(type='misleading_visual_structure',severity='critical',fact_ids=[],item_ids=['@structure'],refs=[request['source'][0]['ref']],message='Selected visual implication is not supported by the source')]
                records.append(semantic)
            value=dict(records=records)
        return Completion(json.dumps(value),100,50)
    t.complete=complete
    assert job.run()=='complete_unresolved' and not job.results()[0]['acceptance']['accepted']
    assert generation.results==original and job.requests==2


def test_source_inventory_partitions_and_compact_context_do_not_truncate(tmp_path):
    # Exercise whole-block partitioning independently of generated truth: source
    # assertions remain exact even when the same authored source block is repeated.
    from tests.test_infographics_segmentation import make,row
    from app.infographics.generation import GenerationJob
    from app.infographics.optimization import OptimizationJob
    source='A queue preserves insertion order.\n\nA queue adds new elements at its tail.\n\nA stack removes the newest element.'
    phase3,transport=make(tmp_path,source);b=phase3.reading.index.units
    transport.responses=[json.dumps(dict(segments=[row(b[0].id,b[1].id),row(b[2].id,b[2].id,'A','document_end')],pending_from=None))];phase3.run()
    optimizer=OptimizationJob(phase3,store=SQLiteCheckpointStore(tmp_path/'opt'));optimizer.run()
    prototype,_,_,_,client,metadata=build(tmp_path/'prototype')
    # Use a generator object already initialized by the Phase 5 fixture; no live API.
    generator=prototype.generation.generator;generator.complete=lambda *a,**kw:None
    generation=GenerationJob(optimizer,generator,prototype.generation.metadata,store=SQLiteCheckpointStore(tmp_path/'gen'),allow_skipped=True)
    for group in generation.groups:
        record=fixture('A4')['record'];record['segment_id']=generation._aliases[group['id']]
        alias=next(iter(generation._authorized(group)))
        for n in record['data']['items']:n['refs']=[alias]
        generation.results[group['id']]=generation._artifact(group,record,'A')
    generation.status='complete'
    job=VerificationJob(generation,optimizer,client,metadata,store=SQLiteCheckpointStore(tmp_path/'verify'),allow_skipped=True,config=VerificationConfig(inventory_source_tokens=1))
    calls=mock_semantics(client._transport)
    assert job.run()=='complete_accepted'
    inventory_calls=[c for c in calls if c['task']=='inventory']
    primary=[s['ref'] for c in inventory_calls for r in c['data'] for s in r['source'] if s['role']=='primary']
    assert sorted(primary)==['p0','p1','p2'] and len(primary)==len(set(primary))
    assert len(job.inventories[next(iter(job.artifacts))])==2


def test_request_budget_and_checkpoint_prompt_change(tmp_path):
    job,t,generation,optimizer,client,metadata=build(tmp_path,config=VerificationConfig(max_requests=1))
    mock_semantics(t)
    assert job.run()=='paused_request_budget' and job.requests==0
    with pytest.raises(ValueError,match='changed'):VerificationJob.resume(generation,optimizer,client,metadata,store=job.store,allow_skipped=True,config=VerificationConfig(max_requests=3))


def test_model_source_instructions_remain_data(tmp_path):
    job,t,_,_,_,_=build(tmp_path);calls=mock_semantics(t)
    # Original text is never inserted into prompt instructions; it stays in the
    # structured evidence object under a source reference.
    job.run()
    first=calls[0]
    assert first['data'][0]['source'][0]['text']==fixture('A4')['source']
    assert 'untrusted data' in first['prompt'] and first['data'][0]['visual_id']


def test_pending_repair_resume_reverifies_without_repeating_patch(tmp_path,monkeypatch):
    job,t,generation,optimizer,client,metadata=build(tmp_path,bad=True);calls=mock_semantics(t,repair=True)
    original=job.save
    def save():
        original()
        if job.phase=='repair' and job.pending:raise RuntimeError('Simulated process interruption after durable candidate')
    monkeypatch.setattr(job,'save',save)
    with pytest.raises(RuntimeError):job.run()
    assert [c['task'] for c in calls]==['inventory','verify','repair']
    resumed=VerificationJob.resume(generation,optimizer,client,metadata,store=job.store,allow_skipped=True)
    assert resumed.run()=='complete_accepted'
    assert [c['task'] for c in calls]==['inventory','verify','repair','verify']


@pytest.mark.parametrize('mutation',['removed_fact','invalid_task','bad_issue','accepted_flag'])
def test_semantic_checkpoint_corruption_preserves_original(tmp_path,mutation):
    job,t,generation,optimizer,client,metadata=build(tmp_path);mock_semantics(t);job.run()
    original=copy.deepcopy(generation.results);checkpoint=job.store.latest(job.run_id);value=json.loads(checkpoint.state_json)
    v=next(iter(job.artifacts))
    if mutation=='removed_fact':value['inventories'][v]=[]
    elif mutation=='invalid_task':value['phase']='execute_arbitrary_code'
    elif mutation=='bad_issue':value['evaluations'][v]['grounding'][0]['claim_id']='unknown'
    else:value['status']='complete_unresolved'
    value['state']['revision']+=1
    job.store.append(replace(checkpoint,state_json=json.dumps(value),parent_checkpoint_id=checkpoint.checkpoint_id))
    with pytest.raises((ValueError,KeyError)):VerificationJob.resume(generation,optimizer,client,metadata,store=job.store,allow_skipped=True)
    assert generation.results==original
