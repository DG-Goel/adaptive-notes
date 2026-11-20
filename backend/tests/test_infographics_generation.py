import copy
import json
from dataclasses import replace
import pytest
from tests.test_infographics_segmentation import make,row,Transport
from app.infographics.generation_fixtures import fixture,fixtures
from app.infographics.generation_schema import validate_record,parse_batch,FAMILIES
from app.infographics.template_registry import REGISTRY,choices
from app.infographics.antv_adapter import convert
from app.infographics.generator_init import initialize_generator
from app.infographics.planner_init import initialize_planner
from app.infographics.generation import GenerationJob,GenerationConfig,prepare_generation,prompt_for
from app.infographics.optimization import OptimizationJob
from app.infographics.checkpoints import SQLiteCheckpointStore
from app.infographics.clients import RoleClient,ProviderError
from app.infographics.config import ClientConfig,load_config
from app.infographics.contracts import Completion,ModelInfo


def setup(tmp_path,code='A4',config=None):
    example=fixture(code)
    phase3,t=make(tmp_path,example['source']);b=phase3.reading.index.units[0]
    t.responses=[json.dumps(dict(segments=[row(b.id,b.id,code[0],'document_end')],pending_from=None))];phase3.run()
    optimizer=OptimizationJob(phase3,store=SQLiteCheckpointStore(tmp_path/'opt'));optimizer.run()
    settings=ClientConfig('generator','fake-generator',context_tokens=64000,max_output_tokens=12000,requests_per_minute=100,tokens_per_minute=1000000)
    transport=Transport();client=RoleClient(settings,transport,sleep=lambda _:None)
    metadata=client.verify_model()
    # The existing test transport reports 4000 output tokens, adequate for this fixture.
    job=GenerationJob(optimizer,client,metadata,store=SQLiteCheckpointStore(tmp_path/'gen'),allow_skipped=True,config=config)
    return optimizer,client,metadata,transport,job


@pytest.mark.parametrize('code',list(REGISTRY))
def test_all_fifteen_contracts_adapters_and_generation(tmp_path,code):
    f=fixture(code);record=f['record']
    assert validate_record(record,'g0',code[0],{'p0':f['source']})==record
    native=convert(record,'Vfixed')
    assert native['config']['template']==REGISTRY[code].antv
    assert native['source_references'] and not native['rendering_verified']
    opt,client,metadata,t,job=setup(tmp_path,code)
    t.responses=[json.dumps(dict(records=[record]))]
    before=opt.manifest
    assert job.run()=='complete'
    artifact=job.artifacts()[0]
    assert artifact['type']==code and artifact['semantic_verification']=='pending'
    assert opt.manifest==before and job.requests==1
    resumed=GenerationJob.resume(opt,client,metadata,store=job.store,allow_skipped=True)
    assert resumed.artifacts()==job.artifacts() and resumed.run()=='complete' and resumed.requests==1


def test_registry_families_and_prompt_separation():
    assert len(REGISTRY)==15 and {t.family for t in REGISTRY.values()}==set(FAMILIES)
    for category in 'ABC':
        assert len(choices(category))==5
        prompt=prompt_for(category)
        for code in REGISTRY:
            assert (code in prompt)==(code[0]==category)


def test_fixed_canonical_keys_and_disabled_isolation():
    for initializer,role,key in [(initialize_planner,'planner','GEMINI_API_KEY_1'),(initialize_generator,'generator','GEMINI_API_KEY_2')]:
        seen=[]
        def factory(config):seen.append(config);return Transport()
        client,info=initializer({'NOETRA_INFOGRAPHIC_ENGINE_ENABLED':'true',key:'canonical-secret','GEMINI_'+role.upper()+'_API_KEY':'legacy-secret'},transport_factory=factory)
        assert seen[0].api_key=='canonical-secret' and client.config.role==role
        assert 'canonical-secret' not in repr(client.config)
        client.close()
    class Disabled(dict):
        def get(self,key,*args):assert key=='NOETRA_INFOGRAPHIC_ENGINE_ENABLED';return 'false'
    assert initialize_generator(Disabled()) is None
    assert prepare_generation(None,None,None,environment={}) is None
    with pytest.raises(ValueError,match='GEMINI_API_KEY_2'):initialize_generator({'NOETRA_INFOGRAPHIC_ENGINE_ENABLED':'true'})
    config=load_config(dict(GEMINI_API_KEY_1='one',GEMINI_API_KEY_2='two',GEMINI_API_KEY_3='three'))
    assert [c.api_key for c in config.clients.values()]==['one','two','three']


@pytest.mark.parametrize('bad',['unknown','wrong_category','refs','duplicate_ids','extra','empty_desc','support','numeric_nan','numeric_precision','cycle_missing','graph_endpoint','binary_count','quadrant_count','interaction_actor','hierarchy_depth'])
def test_unsuitable_payloads_rejected(bad):
    code={'numeric_nan':'C3','numeric_precision':'C3','cycle_missing':'B2','graph_endpoint':'B4','binary_count':'C1','quadrant_count':'C2','interaction_actor':'B5','hierarchy_depth':'A1'}.get(bad,'A4')
    f=fixture(code);r=copy.deepcopy(f['record'])
    if bad=='unknown':r['type']='A9'
    elif bad=='wrong_category':r['type']='B1'
    elif bad=='refs':r['data']['items'][0]['refs']=['other']
    elif bad=='duplicate_ids':r['data']['items'][1]['id']=r['data']['items'][0]['id']
    elif bad=='extra':r['data']['items'][0]['url']='https://attacker.invalid'
    elif bad=='empty_desc':r['data']['items'][0]['desc']=''
    elif bad=='support':r['support']=[dict(id='s',item_id='missing',kind='example',text='Detail',refs=['p0'])]
    elif bad=='numeric_nan':r['data']['values'][0]['value']='NaN'
    elif bad=='numeric_precision':r['data']['values'][0]['value']='2.01'
    elif bad=='cycle_missing':del r['data']['cycle_refs']
    elif bad=='graph_endpoint':r['data']['relations'][0]['to']='missing'
    elif bad=='binary_count':r['data']['groups'].pop()
    elif bad=='quadrant_count':r['data']['groups'].pop()
    elif bad=='interaction_actor':r['data']['actions'][0]['actor']='missing'
    else:
        n=r['data']['root']
        for i in range(9):n['children']=[dict(id='deep'+str(i),label='Node',desc='Explanation',refs=['p0'])];n=n['children'][0]
    with pytest.raises((ValueError,TypeError)):validate_record(r,'g0',code[0],{'p0':f['source']})


@pytest.mark.parametrize('raw',['not json','{"records":','{"records":[],"records":[]}','{"records":[],"extra":true}'])
def test_strict_batch_json(raw):
    with pytest.raises(ValueError):parse_batch(raw,{'g0':{'p0':'Text'}},'A')


def test_support_formula_and_native_injection_data():
    f=fixture('A4');r=f['record'];r['data']['items'][0]['label']='theme\nbackground red <script>'
    r['support']=[dict(id='s1',item_id='a',kind='formula',text='E=mc^2',refs=['p0'])]
    validate_record(r,'g0','A',{'p0':f['source']+' Formula E=mc^2.'})
    result=convert(r,'Visual')
    assert result['config']['themeConfig']==dict(colorPrimary='#1677ff')
    assert result['config']['data']['lists'][0]['label']==r['data']['items'][0]['label']
    with pytest.raises(ValueError):validate_record(r,'g0','A',{'p0':f['source']})


@pytest.mark.parametrize('status',['needs_split','reroute','unsupported'])
def test_outcome_validation(status):
    record=dict(segment_id='g0',status=status,reason='A clear educational reason')
    if status=='needs_split':record['boundaries']=['p0']
    if status=='reroute':record['category']='B'
    if status=='unsupported':record['refs']=['p0','p1']
    assert validate_record(record,'g0','A',{'p0':'One','p1':'Two'})==record


def test_capacity_and_provider_failure_preserve_source(tmp_path):
    opt,client,meta,t,job=setup(tmp_path,config=GenerationConfig(output_per_item=10000))
    assert job.run()=='paused_capacity_issue' and job.requests==0 and not job.results
    opt,client,meta,t,job=setup(tmp_path/'provider')
    t.responses=[ProviderError('quota_hold')]
    assert job.run()=='paused_quota_hold' and not job.results


def test_corruption_versions_and_uncertain_resume(tmp_path):
    opt,client,meta,t,job=setup(tmp_path)
    t.responses=[json.dumps(dict(records=[fixture('A4')['record']]))];job.run()
    record=job.store.latest('generation');value=json.loads(record.state_json)
    value['results'][opt.groups[0]['id']]['adapter']['config']['template']='malicious'
    value['state']['revision']+=1
    job.store.append(replace(record,state_json=json.dumps(value),parent_checkpoint_id=record.checkpoint_id))
    with pytest.raises(ValueError,match='integrity'):GenerationJob.resume(opt,client,meta,store=job.store,allow_skipped=True)


def test_missing_and_duplicate_records_are_not_committed(tmp_path):
    _,_,_,t,job=setup(tmp_path)
    record=fixture('A4')['record']
    t.responses=[json.dumps(dict(records=[])),json.dumps(dict(records=[record,record]))]
    assert job.run()=='paused_invalid_response' and not job.results and job.requests==2


def test_category_batching_output_resizing_and_order(tmp_path):
    source='\n\n'.join([fixture('A4')['source']]*3)
    phase3,t=make(tmp_path,source);b=phase3.reading.index.units
    rows=[]
    for i,block in enumerate(b):
        r=row(block.id,block.id,'A','document_end' if i==2 else 'objective_change')
        r['title']=r['focus']=['Alpha','Beta','Gamma'][i];rows.append(r)
    t.responses=[json.dumps(dict(segments=rows,pending_from=None))];phase3.run()
    opt=OptimizationJob(phase3,store=SQLiteCheckpointStore(tmp_path/'opt'));assert opt.run()=='optimization_skipped'
    settings=ClientConfig('generator','fake',context_tokens=64000,max_output_tokens=6200,requests_per_minute=100,tokens_per_minute=1000000)
    transport=Transport();transport.model_info=lambda model:ModelInfo('models/'+model,64000,6200,('generateContent',))
    client=RoleClient(settings,transport);metadata=client.verify_model();calls=[]
    def respond(model,content,max_output_tokens):
        body=json.loads(content);calls.append(body)
        records=[]
        for segment in reversed(body['segments']):
            record=fixture('A4')['record'];record['segment_id']=segment['segment_id']
            for item in record['data']['items']:item['refs']=[segment['source'][0]['id']]
            records.append(record)
        return Completion(json.dumps(dict(records=records)),100,50)
    transport.complete=respond
    job=GenerationJob(opt,client,metadata,store=SQLiteCheckpointStore(tmp_path/'gen'),allow_skipped=True)
    assert job.run()=='complete' and [len(c['segments']) for c in calls]==[2,1]
    assert [a['optimized_segment_id'] for a in job.artifacts()]==[g['id'] for g in opt.groups]
    assert all(len(c['choices'])==5 for c in calls) and job.resizes>0


def test_nonvisual_pass_through_and_wrong_role(tmp_path):
    phase3,t=make(tmp_path,'A lengthy proof remains available.');b=phase3.reading.index.units[0]
    t.responses=[json.dumps(dict(segments=[row(b.id,b.id,'N','document_end')],pending_from=None))];phase3.run()
    opt=OptimizationJob(phase3,store=SQLiteCheckpointStore(tmp_path/'opt'));opt.run()
    _,client,meta,transport,_=setup(tmp_path/'client')
    job=GenerationJob(opt,client,meta,store=SQLiteCheckpointStore(tmp_path/'gen'),allow_skipped=True)
    assert job.run()=='complete' and job.requests==0 and job.artifacts()[0]['status']=='preserved_nonvisual'
    with pytest.raises(ValueError,match='generator'):GenerationJob(opt,phase3.planner,meta,allow_skipped=True)
    with pytest.raises(ValueError,match='skipped'):GenerationJob(opt,client,meta)


def test_reroute_at_most_once(tmp_path):
    _,_,_,t,job=setup(tmp_path,config=GenerationConfig(automatic_reroute=True))
    t.responses=[json.dumps(dict(records=[dict(segment_id='g0',status='reroute',category='B',reason='Procedure is central')])),
                 json.dumps(dict(records=[dict(segment_id='g0',status='reroute',category='A',reason='Second correction proposed')]))]
    assert job.run()=='complete' and job.requests==2
    assert job.artifacts()[0]['status']=='reroute' and job.reroutes[ job.groups[0]['id'] ]==1


def test_uncertain_request_and_prompt_binding(tmp_path):
    opt,client,meta,t,job=setup(tmp_path)
    job.status='request_in_flight';job.inflight=dict(category='A',segments=[opt.groups[0]['id']]);job.save()
    resumed=GenerationJob.resume(opt,client,meta,store=job.store,allow_skipped=True)
    assert resumed.run()=='paused_uncertain_request' and resumed.requests==0
    with pytest.raises(ValueError,match='changed'):GenerationJob.resume(opt,client,meta,store=job.store,allow_skipped=True,config=GenerationConfig(max_depth=5))
    t.responses=[json.dumps(dict(records=[fixture('A4')['record']]))]
    assert resumed.run(retry_paused=True)=='complete'


@pytest.mark.parametrize('code',list(REGISTRY))
def test_unsuitable_fixture_preserved_without_template_fabrication(tmp_path,code):
    f=fixture(code)
    record=dict(segment_id='g0',status='unsupported',refs=['p0'],reason='Source lacks the relationships or measurements required by this template')
    assert validate_record(record,'g0',code[0],{'p0':f['unsuitable_source']})['status']=='unsupported'


def test_generation_dry_run():
    from app.infographics.evaluate_generation import main
    assert main(['--dry-run'])['requests']==0


def test_segment_reference_isolation():
    record=fixture('A4')['record']
    with pytest.raises(ValueError,match='Unauthorized'):
        parse_batch(json.dumps(dict(records=[record])),{'g0':{'p7':fixture('A4')['source']}},'A')


@pytest.mark.parametrize('mutation',['negative','zero_total','infinity','underflow','unit'])
def test_numeric_specific_constraints(mutation):
    f=fixture('C5');record=f['record'];source=f['source']
    if mutation=='negative':record['data']['values'][0]['value']='-2.00';source+=' -2.00 kg.'
    elif mutation=='zero_total':
        for v in record['data']['values']:v['value']='0.00'
        source+=' 0.00 kg.'
    elif mutation=='infinity':record['data']['values'][0]['value']='1e9999';source+=' 1e9999 kg.'
    elif mutation=='underflow':record['data']['values'][0]['value']='1e-9999';source+=' 1e-9999 kg.'
    else:record['data']['unit']='meters'
    with pytest.raises(ValueError):validate_record(record,'g0','C',{'p0':source})


def test_sequence_order_and_failed_persistence(tmp_path,monkeypatch):
    f=fixture('B5');f['record']['data']['actions'].reverse()
    with pytest.raises(ValueError,match='order'):validate_record(f['record'],'g0','B',{'p0':f['source']})
    opt,client,metadata,t,job=setup(tmp_path)
    t.responses=[json.dumps(dict(records=[fixture('A4')['record']]))]
    original=job.store.append;count=[]
    def append(record):
        count.append(record)
        if len(count)==2:raise OSError('disk full')
        return original(record)
    monkeypatch.setattr(job.store,'append',append)
    with pytest.raises(OSError):job.run()
    assert not job.results and job.status=='paused_persistence'
    resumed=GenerationJob.resume(opt,client,metadata,store=job.store,allow_skipped=True)
    assert resumed.status=='paused_uncertain_request' and not resumed.results
