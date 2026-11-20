"""Version-bound offline semantic review. Screening and quotation are not entailment.

All decisions are explicit reviewer input. Exact mirror grouping reduces repeated
reading, never the number of material assertions needing semantic consideration.
"""
from collections import defaultdict
from datetime import datetime, timezone
from hashlib import sha256
import json
import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.evaluation.field_faithfulness import audit_fields, leaves

STATUSES = ('SUPPORTED', 'PARTIALLY_SUPPORTED', 'UNSUPPORTED', 'CONTRADICTED', 'INCONCLUSIVE', 'NOT_REVIEWED')
MAIN = {'concept':'concept_name', 'definition':'definition_text', 'explanation':'explanation_text',
        'example':'example_text', 'fact':'fact_text', 'formula':'formula_text'}


def fingerprint(value):
    return sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()


def source_version(source):
    return fingerprint(source.model_dump(mode='json'))


def _scope(item):
    meta = item.extraction_metadata or {}
    review = item.educational_review
    return dict(document_id=item.document_id, source_ids=sorted(item.source_unit_ids),
        primary=sorted(meta.get('primary_source_ids', item.source_unit_ids)),
        contextual=sorted(meta.get('context_source_ids', [])),
        qualification_context=dict(leaves(item.model_dump(mode='json'))),
        role=review.role if review else 'unresolved',
        links=[x.model_dump(mode='json') for x in review.links] if review else [],
        formula_status=review.formula_status if review else None,
        code_kind=review.code_kind if review else None,
        declared_evidence=sorted(meta.get('source_grounding',{}).get('evidence',[]),key=lambda e:json.dumps(e,sort_keys=True)))


def build_review_inventory(knowledge, source, *, duplicate_relations=(), coverage_priority_ids=(), neighbor_chars=900):
    if not 0 <= neighbor_chars <= 4000:
        raise ValueError('Context budget must be between 0 and 4000 characters per neighbor')
    units = {u.source_id:u for u in source.source_units}
    items = {i.knowledge_id:i for i in knowledge.get_all_items()}
    if len(units) != len(source.source_units) or len(items) != len(knowledge.get_all_items()):
        raise ValueError('Canonical source and knowledge IDs must be unique')
    if source.document_id != knowledge.document_id:
        raise ValueError('Document identity mismatch')
    if any(i.document_id != source.document_id or not i.source_unit_ids or
           not set(i.source_unit_ids) <= units.keys() for i in items.values()):
        raise ValueError('Knowledge has invalid canonical source identity')
    version = source_version(source)
    ordered = sorted(source.source_units, key=lambda u:(u.position,u.source_id))
    positions = {u.source_id:n for n,u in enumerate(ordered)}
    relationships = defaultdict(list)
    source_peers=defaultdict(list)
    for i in items.values():
        for sid in i.source_unit_ids:source_peers[sid].append(i.knowledge_id)
    for d in duplicate_relations:
        if d['left'] not in items or d['right'] not in items:
            raise ValueError('Unknown duplicate relationship target')
        for own, other in ((d['left'],d['right']),(d['right'],d['left'])):
            relationships[own].append(dict(target_id=other, relation=d['classification'],
                rationale=d.get('rationale'), claim=items[other].content))
    for i in items.values():
        if i.educational_review:
            for link in i.educational_review.links:
                relationships[i.knowledge_id].append(dict(target_id=link.target_id, relation=link.kind,
                    claim=items[link.target_id].content if link.target_id in items else None))
    rows, groups = [], {}
    for original in audit_fields(knowledge,source):
        item = items[original['knowledge_id']]
        path, text = original['path'], original['original_output']
        raw = (item.extraction_metadata or {}).get('source_grounding', {})
        raw_evidence = [e for e in raw.get('evidence',[]) if path in e.get('fields',[])]
        # Review evidence may repair an incomplete original association. Preserve both.
        active = original['evidence']
        normalized = sorted([dict(source_id=e.get('source_id'), quote=e.get('quote'),
            start_char=e.get('start_char'), end_char=e.get('end_char'), offset_basis=e.get('offset_basis'))
            for e in active], key=lambda e:json.dumps(e,sort_keys=True))
        valid_quotes = bool(active) and all(e.get('source_id') in units and isinstance(e.get('quote'),str)
            and bool(e['quote'].strip()) and e['quote'] in (units[e['source_id']].text or '')
            and e['source_id'] in item.source_unit_ids and not units[e['source_id']].educational_assessment.excluded
            for e in active)
        original_valid = bool(raw_evidence) and all(e.get('source_id') in units and isinstance(e.get('quote'),str)
            and bool(e['quote'].strip()) and e['quote'] in (units[e['source_id']].text or '') for e in raw_evidence)
        context = []
        for sid in sorted({e['source_id'] for e in active if e.get('source_id') in units} or set(item.source_unit_ids),key=lambda s:positions[s]):
            p=positions[sid]
            for n in (p-1,p+1):
                if 0 <= n < len(ordered):
                    u=ordered[n]; value=u.text or ''
                    excerpt=value[-neighbor_chars:] if n<p else value[:neighbor_chars]
                    if not neighbor_chars:excerpt=''
                    context.append(dict(source_id=u.source_id,text=excerpt,source_version=fingerprint(u.model_dump(mode='json')),
                        contextual_only=True,evidence_permission='NOT_AUTHORIZED_BY_THIS_PACKET',
                        start_char=len(value)-len(excerpt) if n<p else 0,end_char=len(value) if n<p else len(excerpt),
                        truncated=len(value)>len(excerpt)))
        context=list({(c['source_id'],c['start_char'],c['end_char']):c for c in context}.values())
        multi_sources=len(set(item.source_unit_ids))>1
        uncertainty=any(units[s].interpretation_limitations or units[s].educational_assessment.status in
            ('noisy_educational','incomplete_educational','uncertain') for s in item.source_unit_ids)
        conditions=bool(re.search(r'\b(if|unless|only|except|always|never|must|may|under|assuming|otherwise|before|after)\b',text,re.I))
        role=item.educational_review.role if item.educational_review else 'unresolved'
        reasons=[]
        if original['status'] in ('UNSUPPORTED','CONTRADICTED'):reasons.append((0,'Previous adverse review'))
        if item.knowledge_type=='formula':reasons.append((1,'Formula or calculation'))
        if original['code_like'] or item.knowledge_type=='procedure':reasons.append((2,'Code-like field or procedure'))
        if role in ('deliberately_incorrect_demonstration','identified_mistake','explanation_of_mistake','corrected_approach'):reasons.append((3,'Incorrect demonstration or correction relationship'))
        if conditions:reasons.append((4,'Conditions, exceptions or qualifications'))
        if multi_sources:reasons.append((5,'Multiple source units'))
        if uncertainty:reasons.append((6,'Uncertain transcription, OCR or source context'))
        if set(item.source_unit_ids)&set(coverage_priority_ids):reasons.append((7,'Coverage review priority'))
        priority=min((r[0] for r in reasons),default=8)
        mirror = path in ('/content','/'+MAIN.get(item.knowledge_type,''))
        identity = dict(text=text,evidence=normalized,source_version=version,scope=_scope(item),
            review_role='main_text' if mirror else dict(item_id=item.knowledge_id,path=path))
        packet_id='PKT_'+fingerprint(identity)
        key=item.knowledge_id+':'+path
        defects=[]
        if original['literal_code_form'] and not original['literal_substring']:defects.append('possible_nonliteral_code')
        if conditions:defects.append('check_qualifications_and_quantifiers')
        if original['signals']['possible_contradiction']:defects.append('possible_conflict_not_verified')
        if not valid_quotes:defects.append('missing_or_invalid_field_evidence')
        if uncertainty:defects.append('check_transcription_and_missing_visuals')
        row=dict(key=key,item_id=item.knowledge_id,path=path,claim=text,claim_unit_kind='UNSPLIT_FIELD_BUNDLE',
            atomic_claim_count=None,knowledge_type=item.knowledge_type,source_ids=item.source_unit_ids,
            primary_source_ids=(item.extraction_metadata or {}).get('primary_source_ids',item.source_unit_ids),
            contextual_source_ids=(item.extraction_metadata or {}).get('context_source_ids',[]),
            source_version=version,packet_id=packet_id,binding=fingerprint(identity),
            mechanical_validation=dict(original_item_result=raw.get('mechanically_valid'),
                original_validation_scope=raw.get('validation_scope','not recorded'),
                original_field_evidence_valid=original_valid,active_field_evidence_valid=valid_quotes,
                semantic_entailment_proven=False),
            original_evidence=raw_evidence,evidence=active,neighbor_context=context,
            legacy_review=dict(status=original['status'],reviewer=original['reviewer'],rationale=original['rationale'],
                mode=original['classification'],reviewed_at=None,timestamp_recorded=False,automatically_certified=False),
            semantic_status='NOT_REVIEWED',decision_history=[],risk_priority=priority,
            risk_reasons=[r[1] for r in reasons],risk_is_semantic_proof=False,
            relationships=relationships[item.knowledge_id],suggested_defect_categories=defects,
            same_source_peer_ids=sorted({k for sid in item.source_unit_ids for k in source_peers[sid] if k!=item.knowledge_id}),
            literal_code_form=original['literal_code_form'],literal_substring=original['literal_substring'],
            instructional_role=role)
        row['formula_status']=item.educational_review.formula_status if item.educational_review else 'NEEDS_REVIEW'
        row['source_locations']=[{key:getattr(units[sid],key) for key in ('source_id','page','section','type','position','docling_ref','interpretation_limitations')}
            for sid in item.source_unit_ids]
        rows.append(row)
        packet=groups.setdefault(packet_id,dict(packet_id=packet_id,binding=row['binding'],source_version=version,
            claim=text,claim_unit_kind='UNSPLIT_FIELD_BUNDLE',atomic_claim_count=None,members=[],
            evidence=active,neighbor_context=context,source_scope=_scope(item),
            decision_controls=list(STATUSES),semantics_inferred=False))
        packet['members'].append(key)
    rows.sort(key=lambda r:(r['risk_priority'],r['item_id'],r['path']))
    for p in groups.values():p['members'].sort()
    queue=[dict(rank=n+1,key=r['key'],packet_id=r['packet_id'],priority=r['risk_priority'],
        reasons=r['risk_reasons'],status=r['semantic_status']) for n,r in enumerate(rows)]
    return dict(source_version=version,knowledge_version=fingerprint(knowledge.model_dump(mode='json')),
        inventory=rows,packets=sorted(groups.values(),key=lambda p:p['packet_id']),
        queue=queue,counts=dict(fields=len(rows),unreviewed_fields=sum(r['legacy_review']['status']=='NOT_REVIEWED' for r in rows),
            exact_evidence_bundles=len(groups),atomic_factual_claim_count=None),
        grouping_policy='Only identical text, evidence, source version, primary/context scope and full qualification context. Main/category mirrors only; all other field paths remain separate.')


class SemanticDecision(BaseModel):
    model_config=ConfigDict(extra='forbid')
    packet_id:str
    binding:str
    source_version:str
    members:list[str]=Field(min_length=1)
    status:Literal['SUPPORTED','PARTIALLY_SUPPORTED','UNSUPPORTED','CONTRADICTED','INCONCLUSIVE','NOT_REVIEWED']
    reviewer:str=Field(min_length=1,pattern=r'\S')
    reviewer_kind:Literal['human','assistant']
    reviewed_at:datetime
    rationale:str=Field(min_length=1,pattern=r'\S')
    review_scope:Literal['entire_field_bundle']='entire_field_bundle'
    qualifications_checked:bool
    evidence_checked:bool
    factual_verification:Literal['source_comparison_only','independent_technical_check','not_established']='source_comparison_only'

    @field_validator('reviewed_at')
    @classmethod
    def aware_timestamp(cls,value):
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError('Timezone-aware review timestamp required')
        if value.timestamp()>datetime.now(timezone.utc).timestamp()+300:
            raise ValueError('Review cannot be future-dated')
        return value


def append_decision(workspace, history, raw):
    """Append a real review input, bound to every target; no default approval."""
    decision=SemanticDecision.model_validate(raw)
    packets={p['packet_id']:p for p in workspace['packets']}
    packet=packets.get(decision.packet_id)
    if packet is None or decision.binding!=packet['binding'] or decision.source_version!=workspace['source_version']:
        raise ValueError('Stale claim, citation, qualification or source version')
    if sorted(decision.members)!=packet['members'] or len(set(decision.members))!=len(decision.members):
        raise ValueError('Explicit complete packet membership required')
    rows=[r for r in workspace['inventory'] if r['key'] in decision.members]
    if decision.status in ('SUPPORTED','PARTIALLY_SUPPORTED'):
        if not decision.qualifications_checked or not decision.evidence_checked or any(not r['mechanical_validation']['active_field_evidence_valid'] for r in rows):
            raise ValueError('Affirmative review requires valid evidence and checked qualifications')
        if decision.status=='SUPPORTED' and any(r['literal_code_form'] and not r['literal_substring'] for r in rows):
            raise ValueError('Nonliteral code cannot be approved as literal source content')
        if decision.status=='SUPPORTED' and any(r['knowledge_type']=='formula' and r['path'] in ('/content','/formula_text')
                and r['formula_status']!='COMPLETE' for r in rows):
            raise ValueError('Incomplete or visual-dependent formula requires completeness review first')
    verify_history(history)
    serialized=decision.model_dump(mode='json')
    # Re-importing an old export must neither inflate review counts nor restore
    # an approval that a later decision withdrew. New reviews carry new records.
    def review_identity(value):
        normalized=dict(value)
        normalized['members']=sorted(value['members'])
        normalized['reviewed_at']=datetime.fromisoformat(value['reviewed_at']).astimezone(timezone.utc).isoformat()
        return normalized
    if any(review_identity(record['decision'])==review_identity(serialized) for record in history):
        return list(history)
    record=dict(kind='semantic_decision',decision=serialized,
        previous_hash=history[-1]['record_hash'] if history else None)
    record['record_hash']=fingerprint(record)
    return [*history,record]


def verify_history(history):
    previous=None
    for record in history:
        payload={k:v for k,v in record.items() if k!='record_hash'}
        if record.get('previous_hash')!=previous or fingerprint(payload)!=record.get('record_hash'):
            raise ValueError('Decision history integrity failure')
        previous=record['record_hash']


def resolve_reviews(workspace, history, *, legacy_pin=None):
    """Re-evaluate bindings on every read. Stale approvals stay in history only.

    Legacy pin must be established from immutable baseline knowledge/source hashes
    by the caller; unknown historical timestamps remain unknown.
    """
    verify_history(history)
    result=json.loads(json.dumps(workspace))
    current={p['packet_id']:p for p in result['packets']}
    decisions={};invalidated=[]
    for record in history:
        d=record['decision'];p=current.get(d['packet_id'])
        if not p or d['binding']!=p['binding'] or d['source_version']!=result['source_version'] or sorted(d['members'])!=p['members']:
            invalidated.append(record['record_hash']);continue
        decisions[d['packet_id']]=record
    for row in result['inventory']:
        record=decisions.get(row['packet_id'])
        if record:
            row['semantic_status']=record['decision']['status']
            row['review_provenance']=dict(kind='explicit_version_bound_review',record_hash=record['record_hash'],**record['decision'])
        elif legacy_pin and legacy_pin.get('source_version')==result['source_version'] and legacy_pin.get('field_bindings',{}).get(row['key'])==row['binding']:
            legacy=row['legacy_review']
            row['semantic_status']=legacy['status']
            if legacy['status'] in ('SUPPORTED','PARTIALLY_SUPPORTED') and not row['mechanical_validation']['active_field_evidence_valid']:
                row['semantic_status']='INCONCLUSIVE'
            if legacy['status']=='SUPPORTED' and row['knowledge_type']=='formula' and row['path'] in ('/content','/formula_text') and row['formula_status']!='COMPLETE':
                row['semantic_status']='INCONCLUSIVE'
            row['review_provenance']=dict(kind='unchanged_legacy_source_review',baseline_artifact=legacy_pin['baseline_artifact'],
                baseline_sha256=legacy_pin['baseline_sha256'],imported_at=legacy_pin['imported_at'],
                reviewed_at=None,reviewer=legacy['reviewer'],reviewer_kind='legacy_actor_type_unrecorded',
                status=row['semantic_status'],original_recorded_status=legacy['status'],rationale=legacy['rationale'],historical_timestamp_unknown=True)
        else:row['review_provenance']=None
        row['decision_history']=[r['record_hash'] for r in history if row['key'] in r['decision']['members']]
    result['invalidated_decisions']=invalidated
    result['review_history']=history
    result['legacy_pin']=legacy_pin
    for q in result['queue']:
        q['status']=next(r['semantic_status'] for r in result['inventory'] if r['key']==q['key'])
    return result


def plan_sample(workspace, *, seed='educational-review-v1', risk_count=12, random_count=24):
    """Reproducible risk sample plus hash-ranked sample of remaining bundles."""
    grouped=defaultdict(list)
    for row in workspace['inventory']:
        if row['semantic_status'] in ('NOT_REVIEWED','INCONCLUSIVE','PARTIALLY_SUPPORTED'):
            grouped[row['packet_id']].append(row)
    candidates=sorted(grouped,key=lambda p:(min(r['risk_priority'] for r in grouped[p]),p))
    risk=candidates[:risk_count]
    rest=sorted(set(candidates)-set(risk),key=lambda p:fingerprint(dict(seed=seed,packet=p)))
    strata=defaultdict(list)
    for p in rest:strata[grouped[p][0]['knowledge_type']].append(p)
    # One reproducibly hash-ranked draw per available category, then hash-ranked fill.
    selected=[values[0] for _,values in sorted(strata.items())]
    selected=sorted(selected,key=lambda p:fingerprint(dict(seed=seed,packet=p)))[:random_count]
    random=selected+[p for p in rest if p not in selected][:max(0,random_count-len(selected))]
    return dict(seed=seed,source_version=workspace['source_version'],risk_sample=risk,random_sample=random,
        population_bundles=len(candidates),selection='Risk-first plus deterministic SHA-256 uniform-style ordering without replacement over the remaining exact-evidence bundles; not a whole-document accuracy estimate.',
        random_strata_population={kind:len(values) for kind,values in sorted(strata.items())},
        random_sample_categories={kind:sum(grouped[p][0]['knowledge_type']==kind for p in random) for kind in strata},
        findings_status='NOT_REVIEWED',overall_quality_score=None)
