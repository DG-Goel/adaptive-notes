"""Resumable authorized Java run; single slot or explicitly pinned five-slot rotation."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import time

from dotenv import dotenv_values
from app.extraction.document_authorization import document_plan, planned_chunks, DocumentStageAAuthorization, confirmed_truncation
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
                AND (?='organization' OR project=?) AND (completed IS NULL OR completed>?)''',
                (identity.organization,w.scope,identity.project,time.time()-seconds)).fetchall()
            if w.metric in ('RPM','RPD'):
                used,planned=len(rows),1
            elif w.metric=='ITPM':
                used,planned=sum(r[0] for r in rows),budget.input_tokens
            elif w.metric=='OTPM':
                used,planned=sum(r[1] for r in rows),budget.max_output_tokens
            else:
                used,planned=sum(sum(r) for r in rows),budget.total_tokens
            if used+planned>min(w.limit*85//100,ceilings.get(w.metric,w.limit*85//100)):
                raise SchedulerHold('quota_exhausted: shared Stage A reservations')


def save(path, value):
    path = Path(path)
    temporary = path.with_suffix(path.suffix+'.tmp')
    temporary.write_text(json.dumps(value,indent=2,ensure_ascii=False,default=str),encoding='utf-8')
    temporary.replace(path)


def run(auth_dir, *, live=False, root=None, transport=None, max_wait=130, continue_validation_failures=False):
    root = Path(root or Path(__file__).resolve().parent)
    auth_dir = Path(auth_dir).resolve()
    manifest = json.loads((auth_dir/'manifest.json').read_text(encoding='utf-8'))
    approval_set = json.loads((auth_dir/'approvals.json').read_text(encoding='utf-8'))
    authority = json.loads((auth_dir/'authorization.json').read_text(encoding='utf-8'))
    config = ExtractionConfiguration.model_validate_json(json.dumps(manifest['configuration']))
    if config.max_retries != 0 or digest(manifest) != authority['approved_manifest_sha256']:
        raise SchedulerHold('Manifest approval/configuration mismatch')
    if document_plan(manifest['source_path'],config,manifest['run_id'],manifest.get('split_depth',0),manifest.get('output_policy'),parser_options=manifest.get('parser_options')) != manifest:
        raise SchedulerHold('Current source/production requests differ from approved manifest')
    if any(e['payload'].get('max_tokens',0)<config.preferred_output_tokens for e in manifest['requests']):
        raise SchedulerHold('Old manifest reduces output allowance; generate a reserve_preferred_v1 authorization')
    from app.extraction.document_authorization import request_slots
    selected=authority.get('selected_slots',[authority['selected_slot']])
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
        configuration_review=authority.get('configuration_review'))
    out=root/'data/output'/('java_live_'+manifest['run_id'] if live else 'java_offline_'+manifest['run_id'])
    out.mkdir(exist_ok=True)
    document=ingest_document(Path(manifest['source_path']),parser_options=manifest.get('parser_options'))
    chunks=planned_chunks(document,manifest.get('split_depth',0))
    chunks=[ExtractionChunk.model_validate(e['chunk']) for e in manifest['requests'] if e.get('parent_request_id') is None]
    save(out/'source_document.json',document.model_dump(mode='json'))
    save(out/'source_manifest.json',{'sha256':manifest['source_sha256'],'source_units':len(document.source_units),'chunks':len(chunks)})
    approvals={a['request_id']:a for a in approval_set}
    if len(approvals)!=len(approval_set) or set(approvals)!={e['request_id'] for e in manifest['requests']}:
        raise SchedulerHold('Missing or duplicate request approvals')
    errors=[]
    start=time.monotonic()
    completed=[]
    root_entries=[e for e in manifest['requests'] if not e.get('parent_request_id')]
    queue=list(zip(chunks,root_entries))
    recovered=[]
    def recover(entry):
        children=[e for e in manifest['requests'] if e.get('parent_request_id')==entry['request_id']]
        if children and confirmed_truncation(scheduler,entry['request_id']):
            queue[index+1:index+1]=[(ExtractionChunk.model_validate(e['chunk']),e) for e in children]
            recovered.append(entry['request_id'])
            save(out/'truncation_recovery.json',{'replaced_requests':recovered,'active_requests':[e['request_id'] for _,e in queue]})
            print('Recovering confirmed truncation with approved smaller requests',flush=True)
            return True
        return False
    def may_continue(request):
        if not continue_validation_failures:return False
        with scheduler.transaction() as db:
            op=db.execute('SELECT state FROM operations WHERE id=?',(request,)).fetchone()
            attempt=db.execute('SELECT http_status,finish,completed FROM attempts WHERE request_id=? ORDER BY number DESC LIMIT 1',(request,)).fetchone()
            diagnostics=[json.loads(r[0]) for r in db.execute("SELECT details FROM audit_events WHERE request_id=? AND event='provider_error'",(request,))]
        if (op and op['state']=='failed' and attempt and attempt['http_status']==400
                and attempt['completed'] is not None and diagnostics
                and diagnostics[-1].get('error_code')=='json_validate_failed'):
            return True  # Definite schema rejection; leave its charge and chunk unresolved.
        return bool(op and op['state']=='validation_failed' and attempt and attempt['http_status']==200
                    and attempt['finish']=='stop' and attempt['completed'] is not None)

    for index,(chunk,entry) in enumerate(queue):
        request=entry['request_id']
        identity=identities[assignments[request]]
        checkpoint=out/(request+'.json')
        with scheduler.transaction() as db:
            existing=db.execute('SELECT state,slot FROM operations WHERE id=?',(request,)).fetchone()
        if existing and existing['slot']!=identity.slot:
            raise SchedulerHold('Saved operation organization differs from pinned rotation')
        if checkpoint.exists():
            if not existing or existing['state']!='success':
                raise SchedulerHold('Checkpoint has no successful durable operation')
            completed.append(KnowledgeDocument.model_validate_json(checkpoint.read_text(encoding='utf-8')))
            continue
        if existing:
            if recover(entry):
                continue
            if existing['state'] in ('validation_failed','success') and (out/(request+'.response.json')).exists():
                from app.extraction.saved_response_recovery import recover_saved
                approved=approvals[request]
                gate=DocumentStageAAuthorization(approved['record'],approved['credential_approval'],manifest,authority['approved_manifest_sha256'],config,rotation_slots=selected if len(selected)>1 else None)
                try:
                    part=recover_saved(scheduler,gate,entry,chunk,document,out/(request+'.response.json'))
                    save(checkpoint,part.model_dump(mode='json'))
                    completed.append(part)
                    print(f'Validated saved response for chunk {index+1}; no redispatch',flush=True)
                    continue
                except Exception as exc:
                    organizations.check_metadata(str(exc))
                    errors.append({'request_id':request,'type':'offline_revalidation_failed','error':str(exc)})
            errors.append({'request_id':request,'error':'Existing operation requires review; automatic redispatch refused','state':existing['state']})
            if may_continue(request):
                print(f'Leaving rejected chunk {index+1} unresolved; continuing independent primary work',flush=True)
                continue
            break
        approved=approvals[request]
        gate=DocumentStageAAuthorization(approved['record'],approved['credential_approval'],manifest,authority['approved_manifest_sha256'],config,rotation_slots=selected if len(selected)>1 else None)
        payload,budget=prepare_request(chunk,config)
        admission=LocalQuotaAdmission(**{k:getattr(identity,k) for k in ('organization','project','credential_id','credential_sha256')},
            request_id=request,request_sha256=digest(payload),configuration_sha256=scheduler.config_hash,
            authorization=approved['record']['authorization'],windows=gate.record.limits)
        waited=time.monotonic()
        try:
            if budget.max_output_tokens<config.preferred_output_tokens:
                raise SchedulerHold('Insufficient output reserve: regenerate authorization with reserve_preferred_v1 before dispatch')
            while True:
                admission.check(identity,request,digest(payload),scheduler.config_hash,time.time())
                try:
                    with scheduler.transaction() as db:
                        scheduler._capacity(db,identity,admission,budget.input_tokens,budget.max_output_tokens,time.time())
                    check_stage_capacity(identity,admission,budget,dict(zip(('RPM','RPD','TPM','TPD'),config.scheduler_ceilings)))
                    break
                except SchedulerHold as exc:
                    if not str(exc).startswith('quota_exhausted') or time.monotonic()-waited>=max_wait:
                        raise
                    print(f'Waiting for local quota: chunk {index+1}/{len(chunks)}',flush=True)
                    time.sleep(5)
            print(f'Extracting chunk {index+1}/{len(chunks)} with NOTES {identity.slot}',flush=True)
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
            completed.append(part)
        except Exception as exc:
            message=str(exc)
            organizations.check_metadata(message)
            errors.append({'request_id':request,'chunk_number':index+1,'type':type(exc).__name__,'error':message})
            if recover(entry):
                continue
            if confirmed_truncation(scheduler,request):
                errors[-1]['recovery_status']='No smaller approved source-boundary split remains; identical retry prohibited'
            print(f'Stopped at chunk {index+1}: {type(exc).__name__}',flush=True)
            if may_continue(request):
                print('Rejected response retained; proceeding without retrying this chunk',flush=True)
                continue
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
    expected_leaves=len(queue)-len(recovered)
    summary={'classification':'Full live extraction completed' if live and len(completed)==expected_leaves else ('Partial live execution' if any(a['dispatched'] for a in attempts) else 'Blocked before live execution'),
        'selected_slots':selected,'rotation_policy':'pinned_primary_round_robin_recovery_same_org','continue_validation_failures':continue_validation_failures,'live':live,'source_sha256':manifest['source_sha256'],'total_chunks':expected_leaves,'completed_chunks':len(completed),'recovered_truncations':len(recovered),
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
    if completed:
        groups={c:[i for part in completed for i in getattr(part,c)] for c in CATEGORIES}
        knowledge=KnowledgeDocument(document_id=document.document_id,source_filename=document.filename,
            extraction_timestamp=datetime.now(timezone.utc).isoformat(),**groups)
        knowledge.update_statistics()
        normalized=normalize_knowledge_ids(knowledge,artifact_id=manifest['run_id'])
        knowledge=normalized.document
        save(out/'knowledge_id_mapping.json',[m.model_dump() for m in normalized.mappings])
        save(out/'extraction_results.json',knowledge.model_dump(mode='json'))
        assembled=NoteAssembler().assemble(RepresentationSelector().select(ContentAnalyzer().analyze(knowledge)))
        rendered=MarkdownRenderer().render(assembled)
        prefix='generated_notes' if len(completed)==expected_leaves else 'partial_notes'
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
