"""Conservative presentation safeguards; review evidence never supplies missing facts."""
import re
from app.representation.formats import RepresentationFormat as F


def apply_safeguards(knowledge,source,representations):
    from app.evaluation.field_faithfulness import audit_fields,literal_code_form
    field_queue=audit_fields(knowledge,source)
    units={u.source_id:u for u in source.source_units}
    items={i.knowledge_id:i for i in knowledge.get_all_items()}
    records=[];issues=[];active_heading=None;headings={};valid_reviews=set()
    for unit in sorted(source.source_units,key=lambda u:u.position):
        if unit.type=='heading' and unit.text:active_heading=unit.text
        headings[unit.source_id]=unit.section or active_heading
    labels={}
    for item in items.values():
        primary=(item.extraction_metadata or {}).get('primary_source_ids',item.source_unit_ids)
        for sid in primary:
            label=next((getattr(item,f,None) for f in ('term','concept_name','topic','procedure_name','exemplifies') if getattr(item,f,None)),None)
            if label and sid not in labels:labels[sid]=label
    for rep in representations.representations:
        item=items[rep.knowledge_id];review=item.educational_review
        fields=[r for r in field_queue if r['knowledge_id']==item.knowledge_id]
        prose_reviewed=any(r['path'] in ('/example_text','/content') and r['status']=='SUPPORTED' and r['classification'] in ('faithful_paraphrase','source_supported_synthesis') for r in fields)
        primary=(item.extraction_metadata or {}).get('primary_source_ids',item.source_unit_ids)
        sid=min((s for s in primary if s in units),key=lambda s:units[s].position,default=None)
        rep.source_position=units[sid].position if sid else None
        rep.section=item.section or (headings.get(sid) if sid else None) or labels.get(sid) or ('Source '+sid if sid else 'Unresolved source')
        notices=[];valid_review=True
        if review:
            quotes=list(review.evidence)+[q for link in review.links for q in link.evidence]
            valid_review=bool(quotes and review.reviewer and review.reviewer.strip() and review.rationale and review.rationale.strip())
            for quote in quotes:
                if quote.source_id not in units or quote.quote not in (units[quote.source_id].text or ''):valid_review=False
            for link in review.links:
                if link.target_id not in items:valid_review=False
            if not valid_review:issues.append(dict(item_id=item.knowledge_id,severity='critical',status='INCONCLUSIVE',reason='Review evidence/target/reviewer missing or invalid'))
            else:valid_reviews.add(item.knowledge_id)
            if valid_review and review.role!='unresolved':
                notices.append('Instructional role: '+review.role.replace('_',' '))
                for link in review.links:notices.append(link.kind.replace('_',' ')+': '+link.target_id)
            if valid_review and review.status!='SUPPORTED':
                notices.append('Claim review: '+review.status+' — '+review.rationale)
            if review.unresolved or review.status in ('UNSUPPORTED','CONTRADICTED','INCONCLUSIVE','NOT_REVIEWED'):
                issues.append(dict(item_id=item.knowledge_id,severity=review.severity,status=review.status,reason=review.rationale or 'Not reviewed',automated=review.automated))
        evidence=(item.extraction_metadata or {}).get('source_grounding',{}).get('evidence',[])
        quotes=[e['quote'] for e in evidence if e.get('source_id') in units and e.get('quote') and e['quote'] in (units[e['source_id']].text or '')]
        if item.knowledge_type=='procedure':
            if not review or not valid_review or review.role=='unresolved':notices.append('Procedure correctness not reviewed; do not assume this is a correct solution.')
            if review and valid_review and review.role=='deliberately_incorrect_demonstration':
                notices.append('INCORRECT DEMONSTRATION — not instructions to follow.')
                if not any(l.kind=='corrected_by' for l in review.links):notices.append('Correction not available in accepted knowledge.')
        if item.knowledge_type=='formula':
            status=review.formula_status if review and valid_review else 'NEEDS_REVIEW'
            if status=='COMPLETE' and review.status!='SUPPORTED' and not any(item.formula_text==quote.quote.strip() for quote in review.evidence):
                status='NEEDS_REVIEW'
            if status!='COMPLETE':
                notices.append('Formula fragment: '+status+'. Do not use as a complete equation.')
                rep.primary_format=F.STANDARD_TEXT;rep.format_content={'content':item.formula_text}
                issues.append(dict(item_id=item.knowledge_id,severity='critical',status=status,reason='Incomplete or unverified formula; available expression retained'))
        text=getattr(item,'example_text','')
        looks_code=bool(re.search(r'[;{}]|:=|\bdef\s+\w+\(|\b[A-Za-z_]\w*(?:\.\w+)*\(',text))
        if item.knowledge_type=='example' and not prose_reviewed and (literal_code_form(text) or (review and review.code_kind!='unclassified')):
            kind=review.code_kind if review and valid_review else 'unclassified'
            literal=any(text in (units[s].text or '') for s in item.source_unit_ids if s in units)
            if not literal or kind in ('reconstructed','verbal'):
                notices.append('Literal source code unavailable. Original generated snippet retained in the audit only.')
                rep.primary_format=F.STANDARD_TEXT
                rep.format_content={'content':'Example held for source-fidelity review. The original generated text and supporting passages remain in the evidence artifact.'}
                issues.append(dict(item_id=item.knowledge_id,severity='critical',status='PARTIALLY_SUPPORTED',reason='Generated code is not verbatim in the source; student display uses source passages'))
            else:notices.append('Source fidelity: literal substring. Syntax, runtime behavior and educational correctness are not certified.')
        rep.educational_context={'instructional_role':review.role if review and valid_review else 'unresolved','student_view':True,'suppressed_fields':['example_text','content'] if any('Literal source code unavailable' in n for n in notices) else [],'notices':notices,'review':review.model_dump(mode='json') if review else None}
        unsafe=[r for r in fields if (r['literal_code_form'] and not r['literal_substring'] and r['status']!='SUPPORTED')
                or r['classification'] in ('unsupported_reconstruction','contradicted') or r['status'] in ('UNSUPPORTED','CONTRADICTED')]
        if unsafe and item.knowledge_type!='example':
            notices.append('Technical fields held for source-fidelity review; this is not a confirmed semantic error.')
            withheld={r['path'].split('/')[1] for r in unsafe}
            rep.primary_format=F.STANDARD_TEXT
            bad={r['path'] for r in unsafe}
            safe=[]
            for r in fields:
                label=('Step '+str(int(r['path'].split('/')[2])+1)) if r['path'].startswith('/steps/') else r['path'].split('/')[1].replace('_',' ').capitalize()
                safe.append(label+': [requires source review]' if r['path'] in bad else r['original_output'])
            rep.format_content={'content':'\n'.join(dict.fromkeys(safe)) or 'Content held for source-fidelity review; consult the evidence artifact.'}
            rep.educational_context['suppressed_fields']=sorted(withheld)
        if unsafe:rep.educational_context['withheld_paths']=[r['path'] for r in unsafe]
        records.append(dict(item_id=item.knowledge_id,claim_text=item.content,
                            review_scope='Item content only; other substantive fields require their own review',
                            status=review.status if review and valid_review else 'NOT_REVIEWED',
                            reviewer=review.reviewer if review and valid_review else None,
                            rationale=review.rationale if review and valid_review else 'No semantic review performed',
                            severity=review.severity if review else 'major',
                            missing_evidence_or_qualification=review.rationale if review and review.unresolved else None,
                            supporting_sources=item.source_unit_ids,quotations=quotes,review=review.model_dump(mode='json') if review else None))
    for issue in issues:issue.setdefault('automated',True)
    by_id={r.knowledge_id:r for r in representations.representations}
    for item in items.values():
        if item.knowledge_id in valid_reviews:
            for link in item.educational_review.links:
                if link.kind in ('corrected_by','explained_by','alternative') and link.target_id in by_id:
                    target=items[link.target_id]
                    if not target.section and not any(headings.get(s) for s in target.source_unit_ids):
                        by_id[link.target_id].section=by_id[item.knowledge_id].section
                    role={'corrected_by':'corrected_approach','explained_by':'explanation_of_mistake','alternative':'alternative_valid_approach'}[link.kind]
                    if by_id[link.target_id].educational_context['instructional_role']=='unresolved':
                        by_id[link.target_id].educational_context['instructional_role']=role
    from app.extraction.no_invention import protect_representation
    for item in items.values():
        rep=by_id[item.knowledge_id]
        policy=protect_representation(item,rep,[r for r in field_queue if r['knowledge_id']==item.knowledge_id])
        if any(f['withheld'] for f in policy['fields']):
            issues.append(dict(item_id=item.knowledge_id,severity='major',status='REVIEW_REQUIRED',
                reason='Unresolved generation claims withheld; independently supported fields retained',automated=True))
    return dict(field_review_queue=field_queue,claim_reviews=records,issues=issues,readiness='NEEDS_MORE_CORRECTION' if issues else 'READY_FOR_MANUAL_REVIEW',
                semantic_certification=False)
