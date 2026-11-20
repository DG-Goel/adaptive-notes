import json
import httpx
import pytest
import time
from pathlib import Path
from app.extraction import stage_a_bridge as bridge
from app.extraction.document_authorization import document_plan
from app.extraction.organization_scheduler import ExtractionConfiguration, digest
from tests.test_organization_scheduler import registry
from tests.test_organization_extraction import envelope
from run_authorized_java import run, save


@pytest.mark.parametrize('wire',[False,True,'empty','context','canonical'])
@pytest.mark.parametrize('failure',[None,'400_truncation','length','other_400'])
def test_authorized_document_runs_and_resumes_offline(tmp_path,monkeypatch,failure,wire,rotate=False,continuation=False):
    clock=[time.time()]
    monkeypatch.setattr(time,'time',lambda:clock[0])
    monkeypatch.setattr(time,'sleep',lambda seconds:clock.__setitem__(0,clock[0]+seconds))
    h=bridge.frozen_harness()
    h.LIVE_STATE=tmp_path/'stage_state'
    monkeypatch.setattr(bridge,'frozen_harness',lambda:h)
    root=tmp_path/'backend'
    (root/'data/output/organization_inventory_20261106').mkdir(parents=True)
    source=tmp_path/'java.txt'
    text='A value is an expression.'
    source.write_text((' '.join([text]*(100 if rotate else 20))+'\n\n')*(12 if rotate else 2),encoding='utf-8')
    all_ids=registry((1,2,3,4,5) if rotate else (1,)).identities
    i=all_ids[0]
    save(root/'data/output/organization_inventory_20261106/inventory.json',[identity.model_dump() for identity in all_ids])
    (root/'.env').write_text(''.join(f'GROQ_ORG_{identity.slot}_ENABLED=true\nGROQ_ORG_{identity.slot}_ID={identity.organization}\nGROQ_ORG_{identity.slot}_API_KEY=test-secret-{identity.slot}\n' for identity in all_ids))
    # Keep an actual smaller recovery request available in this artificial legacy
    # fixture despite additional policy tokens. Production defaults stay unchanged.
    legacy_budget={'preferred_output_tokens':3000} if not wire and failure in ('400_truncation','length') else {}
    config=ExtractionConfiguration(max_retries=0,**(dict(prompt_policy="canonical_grounded_v4" if wire=="canonical" else ("context_grounded_v3" if wire=="context" else "grounded_fields_v2"),response_format="json_schema",reasoning_effort="low",preferred_output_tokens=3000) if wire else legacy_budget))
    manifest=document_plan(source,config,'offline-java',output_policy='reserve_preferred_v1')
    auth=root/'auth'
    auth.mkdir()
    e=manifest['requests'][0]
    common={k:getattr(i,k) for k in ('organization','project','credential_id','credential_sha256')}
    common.update(provider='Groq',model=config.model,stage='A',operator='fixture',authorization='offline-only',run_id=e['request_id'],request_sha256=e['request_sha256'])
    record=dict(**common,decision='PASS',source_id='DOCUMENT',limits=[dict(scope='organization',metric=m,limit=v) for m,v in dict(RPM=30,RPD=1000,TPM=8000,TPD=200000).items()])
    approval=dict(**common,evidence_kind='operator_reviewed_console_inventory',ownership_evidence='fixture',verified_by='fixture',verified_at=0.0,expires_at=None,authorization_evidence='fixture')
    save(auth/'manifest.json',manifest)
    from app.extraction.document_authorization import request_slots
    selected=[identity.slot for identity in all_ids]
    assigned=request_slots(manifest,selected)
    save(auth/'authorization.json',dict(selected_slot=1,selected_slots=selected,request_slots=assigned,approved_manifest_sha256=digest(manifest)))
    records=[]
    for entry in manifest['requests']:
        owner=next(identity for identity in all_ids if identity.slot==assigned[entry['request_id']])
        binding={**{k:getattr(owner,k) for k in ('organization','project','credential_id','credential_sha256')},'run_id':entry['request_id'],'request_sha256':entry['request_sha256']}
        records.append(dict(request_id=entry['request_id'],record={**record,**binding},credential_approval={**approval,**binding}))
    save(auth/'approvals.json',records)
    calls=[]
    def respond(request):
        calls.append(request)
        entry=next(e for e in manifest['requests'] if e['payload']==json.loads(request.content))
        if len(calls)==1 and failure:
            if failure=='validation':
                return httpx.Response(200,json=envelope('{}'))
            if failure=='rate_limit':
                return httpx.Response(429,json={'error':{'message':'rate limit reached'}},headers={'retry-after':'60'})
            if failure=='uncertain':
                raise httpx.ReadTimeout('fixture timeout',request=request)
            if failure=='length':
                return httpx.Response(200,json=envelope('{',finish='length'))
            message='max completion tokens reached before generating a valid document' if failure=='400_truncation' else 'invalid schema'
            return httpx.Response(400,json={'error':{'message':message,'code':'json_validate_failed'}})
        if wire:
            from app.extraction.prompts import CATEGORY_FIELDS
            body={c:[] for c in CATEGORY_FIELDS}
            body['excluded']=[]
            v=lambda text:dict(text=text,refs=['Q0000'])
            if wire=='empty':
                from app.extraction.quote_catalog import catalog
                from app.models.knowledge import ExtractionChunk
                body['excluded']=[dict(ref=k,reason='promotion') for k in catalog(ExtractionChunk.model_validate(entry['chunk']))]
            else:
                body['concepts']=[dict(concept_name=v('expression'),content=v(text),aliases=None)]
            return httpx.Response(200,json=envelope(json.dumps(body)))
        return httpx.Response(200,json=envelope(json.dumps({'concepts':[dict(concept_name='expression',content=text,source_unit_ids=[sid],source_evidence=[dict(source_id=sid,quote=text,fields=['/concept_name','/content'])]) for sid in entry['source_ids']]})))
    transport=httpx.MockTransport(respond)
    result=run(auth,root=root,transport=transport,continue_validation_failures=continuation or failure in ('validation','schema400'))
    if failure in ('validation','schema400'):
        expected=sum(not e.get('parent_request_id') for e in manifest['requests'])
        assert result['completed_chunks']==expected-1 and len(calls)==expected
        resumed=run(auth,root=root,transport=transport,continue_validation_failures=True)
        assert resumed['completed_chunks']==expected-1 and len(calls)==expected
        return
    if failure in ('other_400','rate_limit','uncertain'):
        assert result['completed_chunks']==0 and len(calls)==1
        return
    expected=sum(not e.get('parent_request_id') for e in manifest['requests'])
    first_root=next(e for e in manifest['requests'] if not e.get('parent_request_id'))
    recovery_children=[e for e in manifest['requests'] if e.get('parent_request_id')==first_root['request_id']]
    expected_success=expected-1+len(recovery_children) if failure else expected
    assert result['completed_chunks']==expected_success and result['assembly']=='completed'
    assert result['recovered_truncations']==int(bool(failure))
    again=run(auth,root=root,transport=transport)
    assert again['completed_chunks']==result['completed_chunks'] and len(calls)==(expected_success+1 if failure else expected)
    assert again['elapsed_seconds']==result['elapsed_seconds']
    assert again['physical_call_seconds']==result['physical_call_seconds']

    # Simulate a crash after durable success but before checkpoint persistence.
    output=root/'data/output'/('java_offline_'+manifest['run_id'])
    first=next(e for e in manifest['requests'] if (output/(e['request_id']+'.json')).exists())
    (output/(first['request_id']+'.json')).unlink()
    recovered=run(auth,root=root,transport=transport)
    assert recovered['completed_chunks']==result['completed_chunks']
    assert len(calls)==(expected_success+1 if failure else expected)


def test_live_path_five_friend_rotation_and_resume_offline(tmp_path,monkeypatch):
    test_authorized_document_runs_and_resumes_offline(tmp_path,monkeypatch,None,'canonical',rotate=True)
    import sqlite3
    path=tmp_path/'backend/data/live_state/organization.sqlite'
    with sqlite3.connect(path) as db:
        slots=[r[0] for r in db.execute('select slot from operations order by rowid')]
    assert len(slots)>=5
    assert slots==[i%5+1 for i in range(len(slots))]


@pytest.mark.parametrize('failure',['rate_limit','uncertain'])
def test_five_rotation_never_switches_keys_to_retry_failure(tmp_path,monkeypatch,failure):
    test_authorized_document_runs_and_resumes_offline(tmp_path,monkeypatch,failure,'canonical',rotate=True,continuation=True)
    import sqlite3
    with sqlite3.connect(tmp_path/'backend/data/live_state/organization.sqlite') as db:
        assert db.execute('select count(*) from operations').fetchone()[0]==1
        assert db.execute('select slot from operations').fetchone()[0]==1
        if failure=='uncertain':
            assert db.execute('select state from operations').fetchone()[0]=='uncertain'


@pytest.mark.parametrize('failure',['validation','schema400'])
def test_validation_failure_continues_only_independent_work_without_redispatch(tmp_path,monkeypatch,failure):
    test_authorized_document_runs_and_resumes_offline(tmp_path,monkeypatch,failure,'canonical',rotate=True)
    import sqlite3
    with sqlite3.connect(tmp_path/'backend/data/live_state/organization.sqlite') as db:
        rows=db.execute('select slot,state from operations order by rowid').fetchall()
    assert rows[0]==(1,'validation_failed' if failure=='validation' else 'failed')
    assert len(rows)>=5 and rows[1]==(2,'success')
    assert [r[0] for r in rows]==[i%5+1 for i in range(len(rows))]
