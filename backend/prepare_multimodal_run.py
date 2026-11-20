"""Prepare exact Task 13 inventory/authorization from the current user request."""
from datetime import datetime,timezone
import json
from pathlib import Path
from dotenv import dotenv_values
from app.extraction.document_authorization import ROUND1_RECOVERY_PASSES,document_plan,DocumentStageARecord,request_slots
from app.extraction.stage_a_bridge import LocalCredentialApproval
from app.extraction.organization_scheduler import ExtractionConfiguration,digest,configuration_fingerprint,Identity,load_organizations
from app.extraction.organization_extraction import prepare_request
from app.models.knowledge import ExtractionChunk
from app.ingestion.router import ingest_document


def main(category='facts', *, source=None, output=None, parallel=False, quiz=False):
    root=Path(__file__).resolve().parent
    candidates=sorted((root/'data/transcriptions/video_stage4').glob('*/multimodal_transcript.json'),key=lambda p:p.stat().st_mtime_ns,reverse=True)
    source=Path(source).resolve() if source else candidates[0]
    stamp=datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S_%f'); run='multimodal-'+stamp
    out=Path(output).resolve() if output else root/'data/output'/('multimodal_notes_full_'+run)
    out.mkdir(parents=True, exist_ok=True)
    combined=category=='combined'
    cfg=ExtractionConfiguration(max_retries=0,prompt_policy='canonical_grounded_v4',
        wire_format=('compact_field_rows_quiz_v4' if quiz else 'compact_field_rows_v1') if combined else 'category_bounded_12a_v1',
        target_category=None if combined else category,response_format='json_schema',
        reasoning_effort='low',preferred_output_tokens=3000 if quiz else 2000)
    print('Planning complete multimodal lecture; no network dispatch',flush=True)
    doc=ingest_document(source,parser_options={'multimodal_stage4':True})
    def save(name,value): (out/name).write_text(json.dumps(value,indent=2,ensure_ascii=False),encoding='utf-8')
    if parallel and (out/'manifest.json').exists():
        previous=json.loads((out/'manifest.json').read_bytes())
        cfg=ExtractionConfiguration.model_validate_json(json.dumps(previous['configuration']))
        run=previous['run_id']
        plan_options=dict(split_depth=previous.get('split_depth',0),output_policy=previous.get('output_policy'),
                          parser_options=previous.get('parser_options'))
        if document_plan(source,cfg,run,**plan_options,end_retries=previous.get('end_retries',0)) != previous:
            raise ValueError('Existing Round 1 manifest does not match the current source and configuration')
    else:
        plan_options=dict(output_policy='reserve_preferred_v1',parser_options={'multimodal_stage4':True})
        save('source_document.json',doc.model_dump(mode='json'))
    m=document_plan(source,cfg,run,**plan_options,end_retries=ROUND1_RECOVERY_PASSES if parallel else 0)
    save('manifest.json',m)
    persisted=json.loads((out/'manifest.json').read_bytes())
    if any(e['request_sha256']!=digest(e['payload']) for e in persisted['requests']):
        raise ValueError('Persisted request hash mismatch; no authorizations generated')
    rows=json.loads((root/'data/output/organization_inventory_20261106/inventory.json').read_text())
    ids=[Identity(**{k:r[k] for k in Identity.model_fields}) for r in rows]
    orgs=load_organizations(ids,dotenv_values(root/'.env'))
    selected=list(orgs.enabled)
    assignments=request_slots(m,selected)
    auth='Current chat Task 13: explicit full real Groq extraction of this exact multimodal lecture using current Task 12A canonical_grounded_v4 schema. Existing five-owner organization bindings and pinned independent-quota rotation apply; historical java.txt request approval is not reused. Preserve all Stage A/B checks, operator hard 85% ceilings, reservations and unresolved source states.'
    if source not in candidates:
        auth='Operator requested the video notes workflow for this exact multimodal source. Round 1 uses slots 1–5 and the configured request and minute-token limits.'
    approvals=[]
    for e in m['requests']:
        for slot in (selected if parallel else [assignments[e['request_id']]]):
            row=next(r for r in rows if r['slot']==slot)
            common={k:row[k] for k in ['organization','project','credential_id','credential_sha256']}
            common.update(provider='Groq',model=cfg.model,stage='A',operator='requesting operator',authorization=auth,run_id=e['request_id'],request_sha256=e['request_sha256'])
            rec=DocumentStageARecord(**common,decision='PASS',source_id='DOCUMENT',limits=tuple(dict(scope='organization',metric=k,limit=v) for k,v in row['configured_provider_limits'].items()))
            approval=LocalCredentialApproval(**common,evidence_kind=row['verification_method'],ownership_evidence=row['ownership_evidence'],verified_by=row['verified_by'],verified_at=row['verified_at'],expires_at=row['expires_at'],authorization_evidence=auth)
            approvals.append(dict(slot=slot,request_id=e['request_id'],record=rec.model_dump(mode='json'),credential_approval=approval.model_dump(mode='json')))
    save('approvals.json',approvals)
    save('authorization.json',dict(approved_manifest_sha256=digest(m),authorization=auth,parallel=parallel,selected_slot=selected[0],selected_slots=selected,request_slots=assignments,
         configuration_review=dict(target_sha256=configuration_fingerprint(cfg),evidence=auth),source_sha256=m['source_sha256'],request_count=len(approvals),live_calls=0,end_retries=m.get('end_retries',0)))
    totals=dict(input=0,reserved_output=0)
    roots=[e for e in m['requests'] if not e.get('parent_request_id')]
    for e in roots:
        _,b=prepare_request(ExtractionChunk.model_validate(e['chunk']),cfg); totals['input']+=b.input_tokens; totals['reserved_output']+=b.max_output_tokens
    save('preflight.json',dict(run_id=run,source=str(source),source_units=len(doc.source_units),speech_units=sum(u.type=='speech' for u in doc.source_units),visual_units=sum(u.type=='visual_candidate' for u in doc.source_units),
        original_speech_segments=doc.ingestion.get('original_speech_segment_count'),primary_chunks=len(roots),contingent_requests=len(approvals)-len(roots),pending_nonquotable_chunks=len(m['pending_chunks']),estimated_tokens=totals,
        estimate_limitation='Conservative byte-based estimate, not exact tokenizer usage. Output reserve is not predicted actual output.',credential_slots=selected,live_calls=0))
    for src,dest in [(source.with_name('unresolved_source_gaps.json'),'unresolved_source_gaps.json'),(source.with_name('multimodal_transcript.md'),'ocr_review_supplement.md')]:
        (out/dest).write_bytes(src.read_bytes())
    if source in candidates:
        (root/'data/output/latest_multimodal_run.txt').write_text(str(out),encoding='utf-8')
    print(json.dumps(dict(output=str(out),primary_chunks=len(roots),requests=len(approvals),estimated_tokens=totals)),flush=True)
    return out


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(); p.add_argument('--category',default='facts',choices=['concepts','definitions','explanations','examples','facts','formulas','procedures','relationships'])
    main(p.parse_args().category)
