"""Revalidate a saved real response without redispatch or quota changes."""
import json
from app.extraction.extractor import KnowledgeExtractor
from app.extraction.quote_catalog import resolve_response
from app.extraction.organization_scheduler import digest,SchedulerHold
from app.models.knowledge import KnowledgeDocument
from app.extraction.knowledge_merge import CATEGORIES


def recover_saved(scheduler,gate,entry,chunk,document,response_path):
    request=entry['request_id']
    gate.expected_payload(request)
    with scheduler.transaction() as db:
        op=db.execute('SELECT * FROM operations WHERE id=?',(request,)).fetchone()
        attempt=db.execute('SELECT * FROM attempts WHERE request_id=? ORDER BY number DESC LIMIT 1',(request,)).fetchone()
        bindings=[json.loads(r[0]) for r in db.execute("SELECT details FROM audit_events WHERE request_id=? AND event='response_saved'",(request,))]
    if (not op or op['state'] not in ('validation_failed','success') or not attempt or attempt['http_status']!=200
            or attempt['finish']!='stop' or attempt['completed'] is None or op['request_hash']!=entry['request_sha256']):
        raise SchedulerHold('Saved response is not eligible for offline validation recovery')
    response=json.loads(response_path.read_text(encoding='utf-8'))
    scheduler.organizations.check_metadata(response)
    if bindings and bindings[-1]['sha256']!=digest(response):
        raise SchedulerHold('Saved response changed since receipt')
    if response.get('model')!=scheduler.configuration.model or len(response.get('choices',[]))!=1 or response['choices'][0].get('finish_reason')!='stop':
        raise SchedulerHold('Saved response envelope mismatch')
    from app.extraction.organization_extraction import extraction_policy
    _,_,resolver,_=extraction_policy(scheduler.configuration)
    content,corrections=resolver(response['choices'][0]['message']['content'],chunk)
    parser=KnowledgeExtractor(None,strict_evidence=True,verbose=False)
    parser.valid_source_ids={u.source_id for u in document.source_units}
    parser._evidence_sources={u.source_id:u.text for u in document.source_units}
    from app.extraction.source_context import evidence_view
    validation_chunk=evidence_view(chunk) if scheduler.configuration.prompt_policy in ('context_grounded_v3','canonical_grounded_v4') else chunk
    items=parser._parse_response(content,validation_chunk,document.document_id)
    if not items and scheduler.configuration.prompt_policy not in ("grounded_fields_v2","context_grounded_v3","canonical_grounded_v4"):
        raise SchedulerHold('Saved response has no validated items')
    if scheduler.configuration.prompt_policy in ('context_grounded_v3','canonical_grounded_v4'):
        for item in items:
            item.extraction_metadata.update(primary_source_ids=list(chunk.source_units),context_source_ids=list(chunk.context_source_ids),semantic_verified=False)
    groups={c:[] for c in CATEGORIES}
    for item in items:
        groups[next(c for c in CATEGORIES if c.rstrip('s')==item.knowledge_type)].append(item)
    part=KnowledgeDocument(document_id=document.document_id,source_filename=document.filename,
        extraction_timestamp=str(attempt['completed']),source_units_processed=len(chunk.source_units),**groups)
    part.update_statistics()
    if op['state']=='success':
        if not bindings:
            raise SchedulerHold('Successful checkpoint recovery requires receipt hash')
        with scheduler.transaction() as db:
            scheduler._event(db,request,op['org'],'successful_checkpoint_recovery',{'response_sha256':digest(response),'items':len(items),'redispatched':False})
        return part
    with scheduler.transaction() as db:
        if db.execute('SELECT active FROM scheduler WHERE id=1').fetchone()[0] is not None:
            raise SchedulerHold('Cannot recover while another operation is active')
        updated=db.execute("UPDATE operations SET state='success',validation='offline_revalidated' WHERE id=? AND state='validation_failed'",(request,))
        if updated.rowcount!=1:
            raise SchedulerHold('Operation changed during offline review')
        scheduler._event(db,request,op['org'],'offline_validation_recovery',{
            'response_sha256':digest(response),'previous_state':'validation_failed',
            'response_hash_previously_recorded':bool(bindings),'corrections':corrections,'items':len(items),
            'semantic_entailment_verified':False})
    return part
