"""Resumable authorized Java run; single slot or explicitly pinned five-slot rotation."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import time
from concurrent.futures import ThreadPoolExecutor
from contextvars import copy_context
from queue import SimpleQueue
from threading import Lock
import traceback
from app.extraction.quota_policy import quota_ceiling

from dotenv import dotenv_values
from app.extraction.document_authorization import document_plan, planned_chunks, DocumentStageAAuthorization, confirmed_truncation
from app.extraction.document_authorization import (
    ROUND1_RECOVERY_PASSES, confirmed_end_retry, confirmed_recoverable_failure,
)
from app.extraction.organization_scheduler import Identity, load_organizations, OrganizationScheduler, ExtractionConfiguration, LocalQuotaAdmission, digest, SchedulerHold
from app.extraction.organization_extraction import extract_chunk, prepare_request
from app.ingestion.router import ingest_document
from app.extraction.chunker import ContentChunker
from app.extraction.knowledge_merge import CATEGORIES, normalize_knowledge_ids
from app.models.knowledge import KnowledgeDocument, ExtractionChunk
from app.analysis.analyzer import ContentAnalyzer
from app.representation.selector import RepresentationSelector
from app.assembly.assembler import NoteAssembler
from app.rendering.renderer import MarkdownRenderer
from app.evaluation.semantic_verifier import DeterministicSemanticVerifier


def check_stage_capacity(identity, admission, budget, ceilings):
    from app.extraction.stage_a_bridge import frozen_harness
    import sqlite3
    path=frozen_harness().LIVE_STATE/'quota.sqlite'
    if not path.exists():
        return
    with sqlite3.connect(path) as db:
        for w in admission.windows:
            seconds=86400 if w.metric in ('RPD','TPD') else 60
            rows=db.execute('''SELECT input_tokens,output_tokens FROM live_a_claims WHERE org=?
                AND (?='organization' OR project=?) AND COALESCE(completed,claimed)>?''',
                (identity.organization,w.scope,identity.project,time.time()-seconds)).fetchall()
            if w.metric in ('RPM','RPD'):
                used,planned=len(rows),1
            elif w.metric=='ITPM':
                used,planned=sum(r[0] for r in rows),budget.input_tokens
            elif w.metric=='OTPM':
                used,planned=sum(r[1] for r in rows),budget.max_output_tokens
            else:
                used,planned=sum(sum(r) for r in rows),budget.total_tokens
            if used+planned>quota_ceiling(w.limit,w.metric,ceilings):
                raise SchedulerHold(f'quota_exhausted: shared Stage A {w.metric} reservations')


def save(path, value):
    path = Path(path)
    temporary = path.with_suffix(path.suffix+'.tmp')
    temporary.write_text(json.dumps(value,indent=2,ensure_ascii=False,default=str),encoding='utf-8')
    temporary.replace(path)


def run(auth_dir, *, live=False, root=None, transport=None, max_wait=130, continue_validation_failures=False, output_dir=None, defer_quota_waits=False):
    root = Path(root or Path(__file__).resolve().parent)
    auth_dir = Path(auth_dir).resolve()
    manifest = json.loads((auth_dir/'manifest.json').read_text(encoding='utf-8'))
    approval_set = json.loads((auth_dir/'approvals.json').read_text(encoding='utf-8'))
    authority = json.loads((auth_dir/'authorization.json').read_text(encoding='utf-8'))
    config = ExtractionConfiguration.model_validate_json(json.dumps(manifest['configuration']))
    if config.max_retries != 0 or digest(manifest) != authority['approved_manifest_sha256']:
        raise SchedulerHold('Manifest approval/configuration mismatch')
    if document_plan(manifest['source_path'],config,manifest['run_id'],manifest.get('split_depth',0),manifest.get('output_policy'),parser_options=manifest.get('parser_options'),end_retries=manifest.get('end_retries',0)) != manifest:
        raise SchedulerHold('Current source/production requests differ from approved manifest')
    if any(e['payload'].get('max_tokens',0)<config.preferred_output_tokens for e in manifest['requests']):
        raise SchedulerHold('Old manifest reduces output allowance; generate a reserve_preferred_v1 authorization')
    from app.extraction.document_authorization import request_slots
    selected=authority.get('selected_slots',[authority['selected_slot']])
    parallel=authority.get('parallel',False)
    if parallel and selected != [1,2,3,4,5]:
        raise SchedulerHold('Parallel Round 1 requires five approved keys')
    assignments=request_slots(manifest,selected)
    if len(selected)>1 and authority.get('request_slots')!=assignments:
        raise SchedulerHold('Rotation assignment approval mismatch')
    if not live and transport is None:
        return {'status':'preflight_passed','initial_chunks':sum(not e.get('parent_request_id') for e in manifest['requests']),
                'authorized_requests_including_recovery':len(manifest['requests']),'live_calls':0}
    if live and transport is not None:
        raise ValueError('Live runs cannot use a supplied transport')
    rows=json.loads((root/'data/output/organization_inventory_20261106/inventory.json').read_text())
    identities={r['slot']:Identity(**{k:r[k] for k in Identity.model_fields}) for r in rows if r['slot'] in selected}
    if set(identities)!=set(selected):
        raise SchedulerHold('Selected organization inventory incomplete')
    env=dotenv_values(root/'.env')
    if any(env.get(f'GROQ_ORG_{slot}_ENABLED')!='true' for slot in selected):
        raise SchedulerHold('Selected organization is disabled')
    env.update({f'GROQ_ORG_{n}_ENABLED':str(n in selected).lower() for n in range(1,6)})
    organizations=load_organizations(list(identities.values()),env)
    identity=identities[selected[0]]
    state=root/'data/live_state'
    state.mkdir(exist_ok=True)
    scheduler=OrganizationScheduler(state/'organization.sqlite',organizations,config,
        configuration_review=authority.get('configuration_review'), parallel=parallel)
    out=Path(output_dir) if output_dir else root/'data/output'/('java_live_'+manifest['run_id'] if live else 'java_offline_'+manifest['run_id'])
    out.mkdir(exist_ok=True)
    document=ingest_document(Path(manifest['source_path']),parser_options=manifest.get('parser_options'))
    chunks=planned_chunks(document,manifest.get('split_depth',0))
    chunks=[ExtractionChunk.model_validate(e['chunk']) for e in manifest['requests'] if e.get('parent_request_id') is None]
    save(out/'source_document.json',document.model_dump(mode='json'))
    save(out/'source_manifest.json',{'sha256':manifest['source_sha256'],'source_units':len(document.source_units),'chunks':len(chunks)})
    approvals={(a['request_id'], a.get('slot', assignments[a['request_id']])): a for a in approval_set}
    expected_approvals={(request, slot) for request, pinned in assignments.items()
                        for slot in (selected if parallel else [pinned])}
    if len(approvals)!=len(approval_set) or set(approvals)!=expected_approvals:
        raise SchedulerHold('Missing or duplicate request approvals')
    errors=[]
    start=time.monotonic()
    completed={}
    root_entries=[e for e in manifest['requests'] if not e.get('parent_request_id')]
    queue=list(zip(chunks,root_entries))
    recovered=[]
    deferred=set()
    shared=Lock()
    children_by_parent={}
    for entry in manifest['requests']:
        children_by_parent.setdefault(entry.get('parent_request_id'), []).append(entry)

    def recover(entry, index):
        request = entry['request_id']
        contingencies = children_by_parent.get(request, [])
        children = [e for e in contingencies if not e.get('end_retry')]
        if children and (confirmed_recoverable_failure if parallel else confirmed_truncation)(scheduler,entry['request_id']):
            if parallel:
                return children
            insertion=len(queue) if defer_quota_waits else index+1
            queue[insertion:insertion]=[(ExtractionChunk.model_validate(e['chunk']),e) for e in children]
            recovered.append(entry['request_id'])
            save(out/'truncation_recovery.json',{'replaced_requests':recovered,'active_requests':[e['request_id'] for _,e in queue]})
            print('Recovering confirmed truncation with approved smaller requests',flush=True)
            return True
        retries = [e for e in contingencies if e.get('end_retry')]
        if parallel and retries and confirmed_end_retry(scheduler, request):
            return retries
        return False
    def may_continue(request):
        if not continue_validation_failures:return False
        with scheduler.transaction() as db:
            op=db.execute('SELECT state FROM operations WHERE id=?',(request,)).fetchone()
            attempt=db.execute('SELECT http_status,finish,completed FROM attempts WHERE request_id=? ORDER BY number DESC LIMIT 1',(request,)).fetchone()
            diagnostics=[json.loads(r[0]) for r in db.execute("SELECT details FROM audit_events WHERE request_id=? AND event='provider_error'",(request,))]
        if (op and op['state']=='failed' and attempt and attempt['http_status']==400
                and attempt['completed'] is not None and diagnostics
                and (diagnostics[-1].get('error_code')=='json_validate_failed'
                     or defer_quota_waits and diagnostics[-1].get('error_code')=='output_parse_failed')):
            return True  # Definite schema rejection; leave its charge and chunk unresolved.
        return bool(op and op['state']=='validation_failed' and attempt and attempt['http_status']==200
                    and attempt['finish']=='stop' and attempt['completed'] is not None)

    def log_event(index, slot, request, event, detail=''):
        organizations.check_metadata(detail)
        row=dict(timestamp=datetime.now(timezone.utc).isoformat(), chunk=index+1,
                 key=f'NOTES {slot}', request_id=request, event=event, detail=detail)
        with shared, (out/('round1_errors.jsonl' if event=='error' else 'round1_events.jsonl')).open('a',encoding='utf-8') as log:
            log.write(json.dumps(row,ensure_ascii=False)+'\n')

    def process(index, chunk, entry, slot):
        request=entry['request_id']
        identity=identities[slot]
        checkpoint=out/(request+'.json')
        with scheduler.transaction() as db:
            existing=db.execute('SELECT state,slot FROM operations WHERE id=?',(request,)).fetchone()
        if existing and existing['slot']!=identity.slot:
            raise SchedulerHold('Saved operation organization differs from pinned rotation')
        if checkpoint.exists():
            if not existing or existing['state']!='success':
                raise SchedulerHold('Checkpoint has no successful durable operation')
            completed[request]=KnowledgeDocument.model_validate_json(checkpoint.read_text(encoding='utf-8'))
            return True
        if existing:
            if children := recover(entry, index):
                return children
            if existing['state'] in ('validation_failed','success') and (out/(request+'.response.json')).exists():
                from app.extraction.saved_response_recovery import recover_saved
                approved=approvals[request, slot]
                gate=DocumentStageAAuthorization(approved['record'],approved['credential_approval'],manifest,authority['approved_manifest_sha256'],config,rotation_slots=selected if len(selected)>1 else None)
                try:
                    part=recover_saved(scheduler,gate,entry,chunk,document,out/(request+'.response.json'))
                    save(checkpoint,part.model_dump(mode='json'))
                    completed[request]=part
                    print(f'Validated saved response for chunk {index+1}; no redispatch',flush=True)
                    return True
                except Exception as exc:
                    organizations.check_metadata(str(exc))
                    errors.append({'request_id':request,'type':'offline_revalidation_failed','error':str(exc)})
            message='Existing operation requires review; automatic redispatch refused'
            if parallel:
                log_event(index,slot,request,'error',dict(reason=message,state=existing['state']))
            errors.append({'request_id':request,'chunk_number':index+1,'error':message,'state':existing['state']})
            if may_continue(request):
                print(f'Leaving rejected chunk {index+1} unresolved; continuing independent primary work',flush=True)
                return True
            return False
        approved=approvals[request, slot]
        gate=DocumentStageAAuthorization(approved['record'],approved['credential_approval'],manifest,authority['approved_manifest_sha256'],config,rotation_slots=selected if len(selected)>1 else None)
        payload,budget=prepare_request(chunk,config)
        admission=LocalQuotaAdmission(**{k:getattr(identity,k) for k in ('organization','project','credential_id','credential_sha256')},
            request_id=request,request_sha256=digest(payload),configuration_sha256=scheduler.config_hash,
            authorization=approved['record']['authorization'],windows=gate.record.limits)
        waited=time.monotonic()
        try:
            if budget.max_output_tokens<config.preferred_output_tokens:
                raise SchedulerHold('Insufficient output reserve: regenerate authorization with reserve_preferred_v1 before dispatch')
            postponed=False
            while True:
                admission.check(identity,request,digest(payload),scheduler.config_hash,time.time())
                try:
                    with scheduler.transaction() as db:
                        if parallel:
                            eligibility=db.execute(
                                'SELECT blocked,cooldown FROM organizations WHERE slot=?',(slot,)).fetchone()
                            if eligibility['blocked']:
                                raise SchedulerHold(f"Key blocked after HTTP {eligibility['blocked']}")
                            if eligibility['cooldown']>time.time():
                                seconds=eligibility['cooldown']-time.time()
                                raise SchedulerHold(f'quota_exhausted: provider cooldown ({seconds:.1f}s remaining)')
                        scheduler._capacity(db,identity,admission,budget.input_tokens,budget.max_output_tokens,time.time())
                    check_stage_capacity(identity,admission,budget,dict(zip(('RPM','RPD','TPM','TPD'),config.scheduler_ceilings)))
                    break
                except SchedulerHold as exc:
                    if (not parallel and defer_quota_waits and str(exc).startswith('quota_exhausted')
                            and request not in deferred and any(
                                assignments[pending['request_id']] != identity.slot
                                for _,pending in queue[index+1:])):
                        deferred.add(request)
                        queue.append((chunk,entry))
                        postponed=True
                        break
                    if not str(exc).startswith('quota_exhausted') or time.monotonic()-waited>=max_wait:
                        raise
                    if parallel:
                        log_event(index,slot,request,'quota_wait',dict(reason=str(exc),delay_seconds=5))
                    print(f'Waiting to dispatch work item {index+1}: {exc}',flush=True)
                    time.sleep(5)
            if postponed:
                return True
            if not parallel:
                deferred.clear()
            print(f'Extracting work item {index+1} ({len(chunks)} primary chunks) with NOTES {identity.slot}',flush=True)
            if parallel:
                log_event(index,slot,request,'request_start')
            items=extract_chunk(scheduler,request,chunk,document.source_units,document.document_id,
                {identity.organization:admission},transport=transport,stage_a=gate,
                response_sink=lambda body:save(out/(request+'.response.json'),body))
            groups={category:[] for category in CATEGORIES}
            for item in items:
                category=next(c for c in CATEGORIES if c.rstrip('s')==item.knowledge_type or (c=='procedures' and item.knowledge_type=='procedure'))
                groups[category].append(item)
            part=KnowledgeDocument(document_id=document.document_id,source_filename=document.filename,
                extraction_timestamp=datetime.now(timezone.utc).isoformat(),source_units_processed=len(chunk.source_units)-len(chunk.uninterpreted_source_ids),**groups)
            part.update_statistics()
            save(checkpoint,part.model_dump(mode='json'))
            completed[request]=part
            return True
        except Exception as exc:
            message=str(exc)
            if parallel:
                log_event(index, slot, request, 'error', dict(
                    traceback=traceback.format_exc(), http_status=getattr(exc,'status_code',None),
                    retry_after=getattr(exc,'retry_after',None), error_code=getattr(exc,'error_code',None)))
            organizations.check_metadata(message)
            errors.append({'request_id':request,'chunk_number':index+1,'type':type(exc).__name__,'error':message})
            if children := recover(entry, index):
                return children
            if confirmed_truncation(scheduler,request):
                errors[-1]['recovery_status']='No smaller approved source-boundary split remains; identical retry prohibited'
            print(f'Stopped at work item {index+1}: {type(exc).__name__}: {message}',flush=True)
            if may_continue(request):
                print('Saved rejection diagnostics; this work item remains unresolved',flush=True)
                return True
            return False
    if parallel:
        files=root/'round 1'/manifest['run_id']
        files.mkdir(parents=True,exist_ok=True)
        from app.extraction import quiz_mcq, quiz_optional, quiz_topics
        mcq_enabled = config.wire_format == quiz_mcq.VERSION
        optional_quiz = mcq_enabled or config.wire_format == quiz_optional.VERSION
        topic_enabled = config.wire_format == quiz_topics.VERSION
        quiz_enabled = optional_quiz or topic_enabled or config.wire_format == 'compact_field_rows_quiz_v1'
        sources = {unit.source_id: unit for unit in document.source_units}
        quiz_records = {}
        if quiz_enabled:
            (out/'quizzes').mkdir(exist_ok=True)
        pending=SimpleQueue()
        pinned={slot:SimpleQueue() for slot in selected}
        with scheduler.transaction() as db:
            prior={row['id']:row['slot'] for row in db.execute('SELECT id,slot FROM operations')}
        resuming=bool(prior.keys() & assignments.keys())
        for index,(chunk,entry) in enumerate(queue):
            slot=prior.get(entry['request_id'])
            if slot is None and not resuming and index<len(selected):
                slot=selected[index]
            elif slot is None and resuming:
                payload,budget=prepare_request(chunk,config)
                for candidate in selected:
                    identity=identities[candidate]
                    record=approvals[entry['request_id'],candidate]['record']
                    admission=LocalQuotaAdmission(
                        **{key:getattr(identity,key) for key in ('organization','project','credential_id','credential_sha256')},
                        request_id=entry['request_id'],request_sha256=digest(payload),
                        configuration_sha256=scheduler.config_hash,authorization=record['authorization'],
                        windows=tuple(record['limits']))
                    try:
                        with scheduler.transaction() as db:
                            scheduler._capacity(db,identity,admission,budget.input_tokens,budget.max_output_tokens,time.time())
                        check_stage_capacity(identity,admission,budget,dict(zip(('RPM','RPD','TPM','TPD'),config.scheduler_ceilings)))
                    except SchedulerHold:
                        continue
                    slot=candidate
                    break
            (pinned[slot] if slot else pending).put((index,chunk,entry))

        retry_pass = 0
        retry_roots = {}

        def run_tree(index, chunk, entry, slot):
            request=entry['request_id']
            log_event(index,slot,request,'assigned')
            started=time.monotonic()
            try:
                result=process(index,chunk,entry,slot)
                if isinstance(result,list):
                    if retry_pass == 0:
                        with shared:
                            retry_roots[index] = (chunk, entry, slot)
                        log_event(index, slot, request, 'retry_queued',
                                  'Recovery deferred until all primary chunks finish')
                        return None
                    if entry.get('end_retry') and request not in prior:
                        # One fresh retry per work item per end-of-run pass.
                        return None
                    with shared:
                        if request not in recovered:
                            recovered.append(request)
                            queue.extend((ExtractionChunk.model_validate(child['chunk']),child) for child in result)
                    parts=[run_tree(index,ExtractionChunk.model_validate(child['chunk']),child,slot) for child in result]
                    return [value for part in parts for value in part] if all(part is not None for part in parts) else None
                if request in completed:
                    part=read_response(request)
                    if quiz_enabled:
                        from app.extraction.quiz_wire import questions
                        from app.extraction.source_context import bind_context
                        quiz_content, topics = quiz_topics.split_topics(part) if topic_enabled else (part, [])
                        parse_questions = questions
                        if mcq_enabled:
                            parse_questions = quiz_mcq.questions
                        elif optional_quiz:
                            parse_questions = quiz_optional.questions
                        rows = parse_questions(quiz_content, bind_context(chunk, document.source_units))
                        for number, row in enumerate(rows, 1):
                            row.update(id=f'{request}-q{number}', chunk_serial=index+1,
                                       request_id=request)
                            if topic_enabled:
                                row['topic'] = topics[number-1]
                            row['review_timestamps'] = quiz_topics.review_timestamps(
                                row['evidence'], sources, chunk.source_spans)
                            row['source_provenance'] = [dict(source_id=sid,
                                provenance=sources[sid].provenance) for sid in
                                dict.fromkeys(e['source_id'] for e in row['evidence'])]
                        record = dict(chunk_serial=index+1, request_id=request,
                                      source_ids=chunk.source_units,
                                      source_spans=chunk.source_spans, questions=rows)
                        target = out/'quizzes'/f'{request}.json'
                        if not target.exists() or json.loads(target.read_bytes()) != record:
                            save(target, record)
                        with shared:
                            quiz_records[request] = record
                        log_event(index,slot,request,'quiz_saved',dict(path=str(target),questions=len(rows)))
                    return [part]
                return None
            except Exception as exc:
                log_event(index,slot,request,'error',traceback.format_exc())
                with shared:
                    errors.append(dict(request_id=request,chunk_number=index+1,error=str(exc)))
                return None
            finally:
                with scheduler.transaction() as db:
                    attempt=db.execute("SELECT number,dispatched,completed,duration,http_status,category FROM attempts WHERE request_id=? ORDER BY number DESC LIMIT 1",(request,)).fetchone()
                    provider_errors=[json.loads(row[0]) for row in db.execute(
                        "SELECT details FROM audit_events WHERE request_id=? AND event='provider_error'",(request,))]
                if provider_errors:
                    log_event(index,slot,request,'error',provider_errors)
                log_event(index,slot,request,'key_available',dict(attempt=dict(attempt) if attempt else None, elapsed_seconds=time.monotonic()-started))

        def read_response(request):
            evidence=json.loads((out/(request+'.response.json')).read_text(encoding='utf-8'))
            return evidence['choices'][0]['message']['content']

        saved=set()

        def worker(slot):
            from queue import Empty
            while True:
                try:
                    index,chunk,entry=pinned[slot].get_nowait()
                except Empty:
                    try:
                        index,chunk,entry=pending.get_nowait()
                    except Empty:
                        return
                parts=run_tree(index,chunk,entry,slot)
                if parts is None:
                    with shared:
                        retry_roots[index] = (chunk, entry, slot)
                if parts is not None:
                    target=files/f'notes_{index+1}.txt'
                    content='\n'.join(parts)
                    if not target.exists() or target.read_bytes()!=content.encode('utf-8'):
                        temporary=target.with_suffix('.tmp')
                        temporary.write_text(content,encoding='utf-8',newline='')
                        temporary.replace(target)
                    with shared:
                        saved.add(index+1)
                    log_event(index,slot,entry['request_id'],'saved',str(target))
        with ThreadPoolExecutor(max_workers=len(selected)) as executor:
            futures=[executor.submit(copy_context().run,worker,slot) for slot in selected]
            for future in futures:
                future.result()
        for retry_pass in range(1, ROUND1_RECOVERY_PASSES + 1):
            retries = [(index, value) for index, value in sorted(retry_roots.items())
                       if index + 1 not in saved]
            if not retries:
                break
            print(f'Round 1 end-of-queue recovery pass {retry_pass}/{ROUND1_RECOVERY_PASSES}: '
                  f'chunks {[index + 1 for index, _ in retries]}', flush=True)
            with scheduler.transaction() as db:
                prior = {row['id']: row['slot'] for row in db.execute(
                    'SELECT id,slot FROM operations') if row['id'] in assignments}
            for index, (chunk, entry, slot) in retries:
                log_event(index, slot, entry['request_id'], 'retry_pass',
                          dict(attempt=retry_pass, original_chunk=index+1))
                pinned[slot].put((index, chunk, entry))
            with ThreadPoolExecutor(max_workers=len(selected)) as executor:
                futures = [executor.submit(copy_context().run, worker, slot) for slot in selected]
                for future in futures:
                    future.result()
        missing=[i for i in range(1,len(root_entries)+1) if i not in saved]
        if not missing:
            target=files/'combined_responses.txt'
            temporary=target.with_suffix('.tmp')
            with temporary.open('w',encoding='utf-8',newline='') as combined:
                for serial in range(1,len(root_entries)+1):
                    if serial>1:
                        combined.write('\n')
                    combined.write((files/f'notes_{serial}.txt').read_bytes().decode('utf-8'))
            temporary.replace(target)
        if quiz_enabled:
            from app.extraction.quiz_export import export_quiz
            export_quiz(out, quiz_records.values(), document.source_units, missing,
                        allow_fewer=optional_quiz)
    else:
        missing=[]
        for index,(chunk,entry) in enumerate(queue):
            if not process(index,chunk,entry,assignments[entry['request_id']]):
                break
    requests={e['request_id'] for e in manifest['requests']}
    with scheduler.transaction() as db:
        operations=[dict(r) for r in db.execute('SELECT * FROM operations') if r['id'] in requests]
        attempts=[dict(r) for r in db.execute('SELECT * FROM attempts') if r['request_id'] in requests]
        events=[dict(r) for r in db.execute('SELECT * FROM audit_events') if r['request_id'] in requests]
    for op in operations:
        op.pop('admission',None)
    save(out/'request_audit.json',{'operations':operations,'attempts':attempts,'events':events})
    # Excerpt-level diagnostics complement source-ID coverage. A source ID with
    # one accepted item does not imply that every teaching point was retained.
    from app.extraction.quote_catalog import catalog
    evidence_coverage=[]
    entries_by_id={e['request_id']:e for e in manifest['requests']}
    for event in events:
        if event['event']!='quote_resolution':
            continue
        for resolution in json.loads(event['details']).get('resolutions',[]):
            if resolution.get('policy')!='grounded_fields_v2':
                continue
            entry=entries_by_id[event['request_id']]
            excerpts=catalog(ExtractionChunk.model_validate(entry['chunk']))
            evidence_coverage.append({'request_id':event['request_id'],**resolution,
                'excerpts':excerpts})
    save(out/'evidence_coverage.json',{'semantic_review_required':True,'requests':evidence_coverage})
    save(out/'errors.json',errors)
    save(out/'quota_report.json',scheduler.status())
    expected_leaves=len({entry['request_id'] for _,entry in queue})-len(set(recovered))
    summary={'classification':'Full live extraction completed' if live and len(completed)==expected_leaves and not missing else ('Partial live execution' if any(a['dispatched'] for a in attempts) else 'Blocked before live execution'),
        'selected_slots':selected,'rotation_policy':'next_free_key' if parallel else 'pinned_primary_round_robin_recovery_same_org','continue_validation_failures':continue_validation_failures,'live':live,'source_sha256':manifest['source_sha256'],'total_chunks':expected_leaves,'completed_chunks':len(completed),'recovered_truncations':len(recovered),
        'requests_attempted':sum(a['dispatched'] is not None for a in attempts),'http_successes':sum(a['http_status']==200 for a in attempts),
        'http_429':sum(a['http_status']==429 for a in attempts),'input_tokens':sum(a['input_actual'] or 0 for a in attempts),
        'output_tokens':sum(a['output_actual'] or 0 for a in attempts),'unknown_usage_attempts':sum(a['input_actual'] is None for a in attempts),
        'elapsed_seconds':time.monotonic()-start,'errors':errors,'assembly':'not_run','quality_score':None}
    summary['total_actual_tokens']=None if summary['unknown_usage_attempts'] else summary['input_tokens']+summary['output_tokens']
    summary['invocation_elapsed_seconds']=summary['elapsed_seconds']
    if operations:
        end=max(op['completed'] or op['created'] for op in operations)
        summary['elapsed_seconds']=end-min(op['created'] for op in operations)
    summary['elapsed_basis']='First durable claim to latest operation completion, including resume gaps and quota waits; invocation time is separate.'
    summary['physical_call_seconds']=sum(a['duration'] or 0 for a in attempts)
    summary['token_count_note']='Input/output sums include reported usage only; missing usage is not zero consumption.'
    summary['unresolved_source_ids']=[u.source_id for u in document.source_units if not u.text and u.representation_status not in ('structural','empty')]
    summary['ingestion_status']=document.ingestion.get('status','unknown')
    summary['source_representation_complete']=not summary['unresolved_source_ids'] and summary['ingestion_status']=='success'
    save(out/'run_summary.json',summary)
    summary['missing_chunk_serials']=missing
    if completed and (not parallel or (not missing and len(completed)==expected_leaves)):
        order = {}
        for index, entry in enumerate(manifest['requests']):
            parent = entry.get('parent_request_id')
            order[entry['request_id']] = order[parent] if entry.get('end_retry') else index
        ordered_parts = [completed[request] for request in sorted(completed, key=order.__getitem__)]
        groups={c:[i for part in ordered_parts for i in getattr(part,c)] for c in CATEGORIES}
        knowledge=KnowledgeDocument(document_id=document.document_id,source_filename=document.filename,
            extraction_timestamp=datetime.now(timezone.utc).isoformat(),**groups)
        knowledge.update_statistics()
        normalized=normalize_knowledge_ids(knowledge,artifact_id=manifest['run_id'])
        knowledge=normalized.document
        save(out/'knowledge_id_mapping.json',[m.model_dump() for m in normalized.mappings])
        save(out/'extraction_results.json',knowledge.model_dump(mode='json'))
        assembled=NoteAssembler().assemble(RepresentationSelector().select(ContentAnalyzer().analyze(knowledge)))
        rendered=MarkdownRenderer().render(assembled)
        prefix='generated_notes' if len(completed)==expected_leaves and not missing else 'partial_notes'
        (out/(prefix+'.md')).write_text(rendered.content,encoding='utf-8')
        save(out/(prefix+'.json'),assembled.model_dump(mode='json'))
        save(out/'render_manifest.json',rendered.manifest.model_dump(mode='json'))
        coverage={u.source_id:[i.knowledge_id for i in knowledge.get_all_items() if u.source_id in i.extraction_metadata.get('primary_source_ids',i.source_unit_ids)] for u in document.source_units}
        save(out/'source_coverage.json',coverage)
        save(out/'semantic_heuristics.json',DeterministicSemanticVerifier(verbose=False).verify(knowledge,document).model_dump(mode='json'))
        from app.evaluation.notes_pipeline import build_preview
        preview=build_preview(knowledge,document,
            required_chunks=[e['request_id'] for _,e in queue if e['request_id'] not in recovered],
            completed_chunks=[op['id'] for op in operations if op['state']=='success'])
        save(out/'notes_quality_gates.json',preview['report'])
        (out/(prefix+'.md')).write_text(preview['markdown'],encoding='utf-8')
        save(out/'consolidated_notes.json',preview['assembled'].model_dump(mode='json'))
        save(out/'consolidated_render_manifest.json',preview['rendered'].manifest.model_dump(mode='json'))
        summary['notes_status']='UNVERIFIED_PREVIEW'
        summary.update(assembly='completed',items=knowledge.total_items,source_units_with_items=sum(bool(v) for v in coverage.values()))
    save(out/'run_summary.json',summary)
    (out/'final_test_report.md').write_text('# Java run\n\n'+json.dumps(summary,indent=2)+'\n\nSemantic checks are heuristics. Educational quality has not yet been manually reviewed. No quality score is inferred from HTTP success.\n',encoding='utf-8')
    print(json.dumps({'output':str(out),**summary}),flush=True)
    return summary


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--authorization-dir',required=True)
    parser.add_argument('--live',action='store_true')
    parser.add_argument('--continue-validation-failures',action='store_true',help='Attempt independent remaining chunks after confirmed HTTP 200 validation failures; never retry the failed chunk')
    args=parser.parse_args()
    result=run(args.authorization_dir,live=args.live,continue_validation_failures=args.continue_validation_failures)
    if not args.live:
        print(json.dumps(result))
    elif result['classification']!='Full live extraction completed':
        raise SystemExit(1)
