"""Reviewer-facing offline packets, annotated drafts and coverage dimensions."""
from collections import Counter, defaultdict
from html import escape
import json
import re
from app.models.educational_review import EducationalReview, FieldReview


def materialize_reviews(knowledge, workspace):
    """Derived adapter for existing validators; the immutable ledger is authoritative."""
    result=knowledge.model_copy(deep=True)
    rows=defaultdict(list)
    for row in workspace['inventory']:rows[row['item_id']].append(row)
    for item in result.get_all_items():
        review=item.educational_review or EducationalReview()
        item.extraction_metadata=item.extraction_metadata or {}
        item.extraction_metadata['semantic_review_prior_record']=review.model_dump(mode='json')
        item.extraction_metadata['semantic_review_projection']={r['path']:r.get('review_provenance') for r in rows[item.knowledge_id]}
        review.field_reviews=[]
        for row in rows[item.knowledge_id]:
            status=row['semantic_status'];provenance=row.get('review_provenance') or {}
            if status=='NOT_REVIEWED':continue
            rationale=provenance.get('rationale') or 'Legacy review; see version-bound companion inventory.'
            mode='faithful_paraphrase' if status=='SUPPORTED' else 'requires_review'
            if status=='CONTRADICTED':mode='contradicted'
            if status=='UNSUPPORTED' and row['literal_code_form']:mode='unsupported_reconstruction'
            review.field_reviews.append(FieldReview(path=row['path'],mode=mode,status=status,
                evidence=[dict(source_id=e['source_id'],quote=e['quote']) for e in row['evidence']],
                reviewer=provenance.get('reviewer') or row['legacy_review']['reviewer'],rationale=rationale))
        item.educational_review=review
        if not all(r['semantic_status']=='SUPPORTED' for r in rows[item.knowledge_id]):
            review.status='NOT_REVIEWED';review.unresolved=True
    return result


def comprehensive_draft(knowledge, source, workspace, *, section_titles=None, representations=None):
    """Retain every field or an explicit withheld marker; never a verified artifact."""
    rows=defaultdict(list)
    for row in workspace['inventory']:rows[row['item_id']].append(row)
    units={u.source_id:u for u in source.source_units}
    known_nonliteral={r['claim'] for r in workspace['inventory']
        if r['semantic_status']=='UNSUPPORTED' and r['legacy_review'].get('mode')=='unsupported_reconstruction'}
    def redact_fragments(row):
        text=row['claim'];candidates=[]
        for snippet in known_nonliteral:
            for match in re.finditer(re.escape(snippet),text):candidates.append((match.start(),match.end()))
        if row['knowledge_type']!='formula':
            for pattern in (r'\b(?:[A-Za-z_]\w*(?:\[\])?\s+)?[A-Za-z_]\w*\s*(?<![=])=(?!=)[^;\n]+;',
                            r'\b[A-Za-z_]\w*(?:\.\w+)*\([^;\n]*\)\s*;'):
                candidates.extend((m.start(),m.end()) for m in re.finditer(pattern,text))
        spans=[]
        for start,end in sorted(set(candidates),key=lambda p:(p[0],-p[1])):
            if row['mechanical_validation']['active_field_evidence_valid'] and any(text[start:end] in e['quote'] for e in row['evidence']):continue
            if spans and start<spans[-1][1]:
                spans[-1]=(spans[-1][0],max(end,spans[-1][1]))
            else:spans.append((start,end))
        output=text
        for start,end in reversed(spans):output=output[:start]+'[literal fragment withheld; see evidence packet]'+output[end:]
        return output,[dict(start_char=a,end_char=b,original_text=text[a:b],reason='Literal source fidelity requires review; semantic status unchanged.') for a,b in spans]
    formats={r.knowledge_id:r.primary_format.value for r in representations.representations} if representations else {}
    lines=['# Comprehensive review draft', '',
        '> UNVERIFIED REVIEW DRAFT. Reviewed, uncertain, incomplete and withheld material are explicitly distinguished. This is not certified study material.', '',
        'Full source quotations, original withheld text and review history: companion review inventory and evidence desk.', '']
    retention=[];previous=None
    def order(item):
        ids=(item.extraction_metadata or {}).get('primary_source_ids',item.source_unit_ids)
        return min(units[s].position for s in ids),item.knowledge_id
    for item in sorted(knowledge.get_all_items(),key=order):
        primary=(item.extraction_metadata or {}).get('primary_source_ids',item.source_unit_ids)
        first=min(primary,key=lambda sid:units[sid].position)
        heading=(section_titles or {}).get(first) or units[first].section or item.section or 'Source '+first
        if heading!=previous:lines.extend(['## '+heading,'']);previous=heading
        lines.extend(['### '+item.knowledge_id+' — '+item.knowledge_type,'',
            'Primary sources: '+', '.join(primary)+'. Adaptive format: '+formats.get(item.knowledge_id,'standard_text')+'.',''])
        if item.educational_review:
            er=item.educational_review
            if er.role!='unresolved':lines.extend(['Instructional role: **'+er.role.replace('_',' ')+'**.',''])
            if item.knowledge_type=='formula' and er.formula_status!='COMPLETE':
                lines.extend(['**Incomplete / visual-context warning:** '+er.formula_status+'. No missing equation is reconstructed.',''])
            if er.links:lines.extend(['Related: '+', '.join(x.kind+' '+x.target_id for x in er.links)+'.',''])
        seen={}
        for row in sorted(rows[item.knowledge_id],key=lambda r:(r['path']!='/content',r['path'])):
            status=row['semantic_status'];text=row['claim']
            display_text,fragments=redact_fragments(row)
            withheld=(status in ('UNSUPPORTED','CONTRADICTED') or row['literal_code_form'] and not row['literal_substring'])
            representation='WITHHELD' if withheld else 'REVIEWED' if status=='SUPPORTED' else 'UNCERTAIN'
            if text in seen and seen[text]==(status,representation):
                lines.extend(['- `'+row['path']+'` mirrors the preceding identical field ('+status+').',''])
                disposition='MIRROR_REFERENCE'
            elif withheld:
                lines.extend(['- **WITHHELD · '+status+' · `'+row['path']+'`:** original content retained in evidence packet '+row['packet_id']+'.',''])
                disposition='WITHHELD_MARKER'
            else:
                lines.extend(['**'+representation+' · '+status+' · `'+row['path']+'`**',''])
                if item.knowledge_type=='formula' or row['literal_code_form']:
                    fence='`'*(max((len(x) for x in re.findall(r'`+',display_text)),default=0)+3)
                    lines.extend([fence+'text',display_text,fence,''])
                else:lines.extend([display_text,''])
                disposition='PARTIALLY_WITHHELD_MARKER' if fragments else 'DISPLAYED'
            seen[text]=(status,representation)
            retention.append(dict(key=row['key'],status=status,disposition=disposition,packet_id=row['packet_id'],withheld_fragments=fragments))
    return dict(markdown='\n'.join(lines),retention=retention,publication_eligible=False,
        item_ids=sorted(rows),field_count=len(retention),format_distribution=dict(Counter(formats.values())))


def coverage_report(knowledge, source, workspace, *, accepted_primary_ids=(), topic_inventory=(), retention=(), section_titles=None):
    """Presence, accepted operations, reviewed topics and retention never conflated."""
    rows=defaultdict(list);primary=defaultdict(list);context=defaultdict(list)
    for row in workspace['inventory']:rows[row['item_id']].append(row)
    items={i.knowledge_id:i for i in knowledge.get_all_items()}
    if not set(accepted_primary_ids)<={u.source_id for u in source.source_units}:
        raise ValueError('Accepted extraction references unknown canonical source units')
    for i in items.values():
        meta=i.extraction_metadata or {}
        for s in meta.get('primary_source_ids',i.source_unit_ids):primary[s].append(i.knowledge_id)
        for s in meta.get('context_source_ids',[]):context[s].append(i.knowledge_id)
    retained={r['key']:r for r in retention}
    topics=defaultdict(list)
    for topic in topic_inventory:
        unit=next((u for u in source.source_units if u.source_id==topic['source_id']),None)
        if not unit or not topic.get('quote') or topic['quote'] not in (unit.text or ''):
            raise ValueError('Topic inventory requires an exact canonical source quotation')
        keys=topic.get('represented_by',[])
        index={r['key']:r for r in workspace['inventory']}
        if any(k not in index for k in keys):raise ValueError('Unknown topic claim target')
        if any(topic['source_id'] not in index[k]['source_ids'] for k in keys):
            raise ValueError('Topic association lacks an authorized source relationship')
        topics[topic['source_id']].append({**topic,
            'represented_field_status':'SUPPORTED' if keys and all(index[k]['semantic_status']=='SUPPORTED' for k in keys) else 'NEEDS_REVIEW',
            'topic_coverage_status':'EXPLICIT_SCOPED_REVIEW' if topic.get('reviewer') and topic.get('rationale') and topic.get('scope_checked') else 'NEEDS_REVIEW',
            'final_notes_retention':[retained.get(k,dict(key=k,disposition='NOT_IN_DRAFT')) for k in keys]})
    sections=defaultdict(list)
    for unit in sorted(source.source_units,key=lambda u:(u.position,u.source_id)):
        records=[r for k in primary[unit.source_id] for r in rows[k]]
        sections[unit.section or (section_titles or {}).get(unit.source_id) or 'Unheaded source sequence'].append(dict(source_id=unit.source_id,
            document_source_unit_present=True,explicitly_excluded=unit.educational_assessment.excluded,
            accepted_extraction=unit.source_id in accepted_primary_ids,
            primary_knowledge_ids=primary[unit.source_id],context_only_ids=context[unit.source_id],
            topic_inventory_status='PARTIAL_REVIEWED_INVENTORY' if topics[unit.source_id] else 'NOT_INDEPENDENTLY_INVENTORIED',
            topics=topics[unit.source_id],knowledge_category_presence=dict(Counter(items[k].knowledge_type for k in primary[unit.source_id])),
            category_coverage='Presence alone does not establish topic completeness or that every category is required.',
            field_statuses=dict(Counter(r['semantic_status'] for r in records)),
            draft_retention=dict(Counter(retained[r['key']]['disposition'] for r in records if r['key'] in retained))))
    return dict(document_id=source.document_id,source_version=workspace['source_version'],sections=dict(sections),
        source_units=len(source.source_units),primary_units_with_knowledge=sum(bool(ids) for ids in primary.values()),
        accepted_extraction_units=len(set(accepted_primary_ids)),topic_inventory_exhaustive=False,
        atomic_claim_count=None,whole_document_verified=False,
        gaps=[dict(source_id=u.source_id,issue='Topic inventory incomplete; independently check important definitions, procedures, examples, formulas, explanations and qualifications.') for u in source.source_units])


def evidence_desk_html(workspace):
    """Render the existing desk with an inert JSON payload and escaped source text."""
    from pathlib import Path
    payload=json.dumps(workspace,ensure_ascii=False).replace('<','\\u003c').replace('&','\\u0026')
    template=Path(__file__).with_name('review_desk.html').read_text(encoding='utf-8')
    return template.replace('<!--REVIEW_WORKSPACE_JSON-->',payload)
