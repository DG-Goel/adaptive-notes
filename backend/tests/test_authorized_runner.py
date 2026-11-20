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
def test_authorized_document_runs_and_resumes_offline(tmp_path,monkeypatch,failure,wire,rotate=False,continuation=False,defer=False,parallel=False):
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
    if wire == 'quiz':
        # Distinct source text keeps split request payloads distinguishable in
        # the fake transport, even when one paragraph needs budget splitting.
        source.write_text('\n\n'.join(' '.join(f'{text} Topic {p} example {n}.'
            for n in range(30)) for p in range(12)), encoding='utf-8')
    all_ids=registry((1,2,3,4,5) if rotate else (1,)).identities
    i=all_ids[0]
    save(root/'data/output/organization_inventory_20261106/inventory.json',[identity.model_dump() for identity in all_ids])
    (root/'.env').write_text(''.join(f'GROQ_ORG_{identity.slot}_ENABLED=true\nGROQ_ORG_{identity.slot}_ID={identity.organization}\nGROQ_ORG_{identity.slot}_API_KEY=test-secret-{identity.slot}\n' for identity in all_ids))
    # Keep an actual smaller recovery request available in this artificial legacy
    # fixture despite additional policy tokens. Production defaults stay unchanged.
    legacy_budget={'preferred_output_tokens':3000} if not wire and failure in ('400_truncation','length') else {}
    config=ExtractionConfiguration(max_retries=0,**(dict(prompt_policy="canonical_grounded_v4" if wire=="canonical" else ("context_grounded_v3" if wire=="context" else "grounded_fields_v2"),wire_format='compact_claim_table_v1' if wire=='canonical' else 'native',response_format="json_schema",reasoning_effort="low",preferred_output_tokens=2000) if wire else legacy_budget))
    if wire=='category':
        config=ExtractionConfiguration(max_retries=0,prompt_policy='canonical_grounded_v4',wire_format='category_bounded_12a_v1',target_category='concepts',response_format='json_schema',reasoning_effort='low',preferred_output_tokens=2000)
    if wire=='quiz':
        config=ExtractionConfiguration(max_retries=0,prompt_policy='canonical_grounded_v4',wire_format='compact_field_rows_quiz_v1',response_format='json_schema',reasoning_effort='low',preferred_output_tokens=3000)
    end_retries=3 if failure=='end_retries' else 0
    manifest=document_plan(source,config,'offline-java',output_policy='reserve_preferred_v1',
                           end_retries=end_retries)
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
    save(auth/'authorization.json',dict(selected_slot=1,selected_slots=selected,request_slots=assigned,parallel=parallel,approved_manifest_sha256=digest(manifest)))
    records=[]
    for entry in manifest['requests']:
        for owner in all_ids if parallel else [next(identity for identity in all_ids if identity.slot==assigned[entry['request_id']])]:
            binding={**{k:getattr(owner,k) for k in ('organization','project','credential_id','credential_sha256')},'run_id':entry['request_id'],'request_sha256':entry['request_sha256']}
            records.append(dict(slot=owner.slot,request_id=entry['request_id'],record={**record,**binding},credential_approval={**approval,**binding}))
    save(auth/'approvals.json',records)
    calls=[]
    import threading
    first_wave=threading.Barrier(5)
    sixth=threading.Event()
    seen={} 
    sixth_attempts=[]
    def respond(request):
        calls.append(request)
        entry=next(e for e in manifest['requests'] if e['payload']==json.loads(request.content))
        if parallel:
            slot=int(request.headers['authorization'][-1])
            primary=[e for e in manifest['requests'] if not e.get('parent_request_id')]
            serial=primary.index(entry)+1
            seen[serial]=slot
            if serial<=5:
                first_wave.wait(timeout=20)
                if serial!=4:
                    assert sixth.wait(timeout=30)
            elif serial==6:
                assert slot==4
                sixth.set()
                if failure=='end_retries':
                    sixth_attempts.append(len(calls))
                    if len(sixth_attempts)<4:
                        return httpx.Response(429,json={'error':{'message':'fixture rate limit'}},
                                              headers={'retry-after':'1'})
                if failure=='rate_limit':
                    return httpx.Response(429,json={'error':{'message':'fixture rate limit'}},headers={'retry-after':'60'})
                if failure=='uncertain':
                    raise httpx.ReadTimeout('fixture timeout',request=request)
        if not parallel and len(calls)==1 and failure:
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
            if wire=='quiz':
                body = dict(rows=[dict(item='I1', category='concepts', field=name,
                    element=0, part='value', text=value, refs=['Q0000'], basis='explicit',
                    availability='SOURCE_SUPPORTED', literal_kind='verbal',
                    instructional_role=None, related_refs=[])
                    for name,value in [('concept_name','expression'),('content',text)]],
                    abstentions=[], excluded=[], quiz=[dict(question=f'Question {n}?',
                    answer=text, explanation=text, bloom_level='Remember', refs=['Q0000'])
                    for n in range(4)])
            elif wire=='canonical':
                compact=dict(claims=[],items=[],abstentions=[],excluded=body['excluded'])
                for category,rows in body.items():
                    if category=='excluded': continue
                    for row in rows:
                        fields=[]
                        for name,val in row.items():
                            groups=[]
                            if val is not None:
                                values=val if isinstance(val,list) else [val]
                                for value in values:
                                    cid='C'+str(len(compact['claims']))
                                    compact['claims'].append(dict(id=cid,**value,basis='explicit',availability='SOURCE_SUPPORTED',literal_kind='verbal',instructional_role=None,related_refs=[]))
                                    groups.append([cid])
                            fields.append(dict(name=name,is_null=val is None,groups=groups,variables=[]))
                        compact['items'].append(dict(category=category,fields=fields))
                body=compact
            elif wire=='category':
                def rich(value):
                    if isinstance(value,dict) and set(value)=={'text','refs'}:
                        return {**value,'claims':[{**value,'basis':'explicit','availability':'SOURCE_SUPPORTED','literal_kind':'verbal','instructional_role':None,'related_refs':[]}]}
                    if isinstance(value,dict): return {k:rich(v) for k,v in value.items()}
                    if isinstance(value,list): return [rich(v) for v in value]
                    return value
                body=dict(items=rich(body['concepts']),excluded=body['excluded'],abstentions=[])
            return httpx.Response(200,json=envelope(json.dumps(body)))
        return httpx.Response(200,json=envelope(json.dumps({'concepts':[dict(concept_name='expression',content=text,source_unit_ids=[sid],source_evidence=[dict(source_id=sid,quote=text,fields=['/concept_name','/content'])]) for sid in entry['source_ids']]})))
    transport=httpx.MockTransport(respond)
    result=run(auth,root=root,transport=transport,continue_validation_failures=continuation or failure in ('validation','schema400'),defer_quota_waits=defer, max_wait=1 if parallel and failure and not end_retries else 130)
    if parallel:
        assert len(seen)>=6
        assert [seen[n] for n in range(1,6)]==[1,2,3,4,5]
        folder=root/'round 1'/'offline-java'
        report_dir=root/'data/output/java_offline_offline-java'
        events=[json.loads(line) for line in (report_dir/'round1_events.jsonl').read_text().splitlines()]
        assert any(event['chunk']==6 and event['key']=='NOTES 4' and event['event']=='request_start' for event in events)
        if end_retries:
            assert len(sixth_attempts)==4
            assert all(attempt > len(seen) for attempt in sixth_attempts[1:])
            passes = [event['detail']['attempt'] for event in events
                      if event['chunk']==6 and event['event']=='retry_pass']
            assert passes == [1, 2, 3]
        elif failure:
            assert 6 in result['missing_chunk_serials']
            assert not (folder/'notes_6.txt').exists()
            assert not (folder/'combined_responses.txt').exists()
            assert result['assembly']=='not_run'
            assert any(e['chunk_number']==6 for e in result['errors'])
            error_log=(report_dir/'round1_errors.jsonl').read_text()
            assert ('fixture rate limit' if failure=='rate_limit' else 'Request timed out') in error_log
            return
        assert not result['missing_chunk_serials'],result['errors']
        parts=[(folder/f'notes_{n}.txt').read_text() for n in range(1,len(seen)+1)]
        assert (folder/'combined_responses.txt').read_text()=='\n'.join(parts)
        count=len(calls)
        run(auth,root=root,transport=transport)
        assert len(calls)==count
        return
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
    if defer:
        import sqlite3
        with sqlite3.connect(root/'data/live_state/organization.sqlite') as db:
            sent=db.execute('SELECT id,slot FROM operations ORDER BY rowid').fetchall()
        assert sent[1][0] in {e['request_id'] for e in manifest['requests'] if not e.get('parent_request_id')}
        assert sent[1][1] != assigned[first_root['request_id']]
        assert all(assigned[e['request_id']]==assigned[first_root['request_id']] for e in recovery_children)
    expected_success=expected-1+len(recovery_children) if failure else expected
    assert result['completed_chunks']==expected_success and result['assembly']=='completed'
    assert result['recovered_truncations']==int(bool(failure))
    again=run(auth,root=root,transport=transport,defer_quota_waits=defer)
    assert again['completed_chunks']==result['completed_chunks'] and len(calls)==(expected_success+1 if failure else expected)
    assert again['elapsed_seconds']==result['elapsed_seconds']
    assert again['physical_call_seconds']==result['physical_call_seconds']

    # Simulate a crash after durable success but before checkpoint persistence.
    output=root/'data/output'/('java_offline_'+manifest['run_id'])
    first=next(e for e in manifest['requests'] if (output/(e['request_id']+'.json')).exists())
    (output/(first['request_id']+'.json')).unlink()
    recovered=run(auth,root=root,transport=transport,defer_quota_waits=defer)
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


def test_parallel_quiz_generation_and_resume(tmp_path, monkeypatch):
    test_authorized_document_runs_and_resumes_offline(
        tmp_path, monkeypatch, None, 'quiz', rotate=True, parallel=True)
    output = tmp_path/'backend/data/output/java_offline_offline-java'
    quiz = json.loads((output/'quiz.json').read_text())
    assert quiz['status'] == 'complete'
    assert quiz['question_count'] == quiz['successful_work_items'] * 4
    assert quiz['question_count'] >= 24
    serials = [q['chunk_serial'] for q in quiz['questions']]
    assert serials == sorted(serials)
    assert all(q['source_provenance'] for q in quiz['questions'])


def test_native_category_wire_rotation_checkpoint_and_saved_response_recovery(tmp_path,monkeypatch):
    test_authorized_document_runs_and_resumes_offline(tmp_path,monkeypatch,None,'category',rotate=True)


def test_recovery_leaves_other_keys_free_to_process_primaries(tmp_path,monkeypatch):
    test_authorized_document_runs_and_resumes_offline(tmp_path,monkeypatch,'length','canonical',rotate=True,defer=True)


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


@pytest.mark.parametrize('failure',[None,'rate_limit','uncertain'])
def test_parallel_next_free_key(tmp_path,monkeypatch,failure):
    test_authorized_document_runs_and_resumes_offline(tmp_path,monkeypatch,failure,False,rotate=True,parallel=True)


def test_parallel_attempts_three_end_of_queue_retries_after_no_progress(tmp_path,monkeypatch):
    test_authorized_document_runs_and_resumes_offline(tmp_path,monkeypatch,'end_retries',False,
                                                     rotate=True,parallel=True)
