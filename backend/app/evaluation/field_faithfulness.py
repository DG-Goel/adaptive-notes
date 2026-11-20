"""All-field screening and explicit source-bound review. No automatic entailment."""
import re
from app.extraction.claim_review import review_claim

IGNORED={'knowledge_id','document_id','knowledge_type','source_unit_ids','section','page_range','confidence','extraction_metadata','educational_review'}


def leaves(value,path=''):
    if isinstance(value,dict):
        for key,child in value.items():
            if not path and key in IGNORED:continue
            pointer=path+'/'+str(key).replace('~','~0').replace('/','~1')
            yield from leaves(child,pointer)
    elif isinstance(value,list):
        for i,child in enumerate(value):yield from leaves(child,path+'/'+str(i))
    elif isinstance(value,str) and value.strip():yield path,value


def code_shape(text):
    # Syntax signals, not proof of reconstruction or factual error.
    return bool(re.search(r';|:=|\bdef\s+\w+\(|\b(?:[A-Za-z_]\w*\.)*[A-Za-z_]\w*\([^)]*\)|\{[^}]*\}',text))


def literal_code_form(text):
    """Presentation form only. Technical prose is not implicitly a literal quote."""
    t=text.strip()
    return bool(t.startswith('```') or re.match(r'^(?:def |function |class |for\s*\(|while\s*\(|if\s*\()',t)
        or re.match(r'^(?:(?:[A-Za-z_]\w*(?:\[\])?)\s+){0,2}[A-Za-z_]\w*\s*(?:=|\+=|-=|:=)',t)
        or re.fullmatch(r'[A-Za-z_]\w*(?:\.\w+)*\(.*\)\s*;?',t,re.S))


def audit_fields(knowledge,source):
    units={u.source_id:u for u in source.source_units};rows=[]
    for item in knowledge.get_all_items():
        grounding=(item.extraction_metadata or {}).get('source_grounding',{}).get('evidence',[])
        supplied={r.path:r for r in (item.educational_review.field_reviews if item.educational_review else [])}
        values=dict(leaves(item.model_dump(mode='json')))
        if set(supplied)-set(values):raise ValueError('Field review targets unknown substantive path')
        for path,text in values.items():
            evidence=[e for e in grounding if path in e.get('fields',[]) and e.get('source_id') in units and e.get('quote') in (units[e['source_id']].text or '')]
            quotes=[e['quote'] for e in evidence];record=supplied.get(path)
            kind='requires_review';status='NOT_REVIEWED';reviewer=None;rationale='No semantic review performed';confirmed=False
            if record:
                valid=bool(record.reviewer and record.reviewer.strip() and record.rationale and record.rationale.strip() and record.evidence)
                valid=valid and all(q.source_id in units and q.quote in (units[q.source_id].text or '') for q in record.evidence)
                if record.mode=='literal':valid=valid and any(text in q.quote for q in record.evidence)
                if valid:
                    kind=record.mode;status=record.status;reviewer=record.reviewer;rationale=record.rationale;confirmed=status not in ('NOT_REVIEWED','INCONCLUSIVE')
                    evidence=[dict(source_id=q.source_id,quote=q.quote,fields=[path]) for q in record.evidence];quotes=[q['quote'] for q in evidence]
                else:rationale='Invalid or unsupported field-review evidence; not accepted'
            signals=review_claim(text,quotes)['signals']
            code=code_shape(text);literal=any(text in (units[s].text or '') for s in item.source_unit_ids if s in units)
            risk='MEDIUM'
            if status in ('UNSUPPORTED','CONTRADICTED') or kind=='unsupported_reconstruction':risk='CRITICAL'
            elif code or item.knowledge_type in ('procedure','formula','relationship') or re.search(r'\d',text) or len(evidence)>1 or signals['possible_contradiction'] or signals['possibly_lost_qualifiers']:risk='HIGH'
            rows.append(dict(knowledge_id=item.knowledge_id,path=path,original_output=text,source_ids=item.source_unit_ids,evidence=evidence,
                classification=kind,status=status,reviewer=reviewer,rationale=rationale,confirmed_defect=confirmed and status in ('UNSUPPORTED','CONTRADICTED'),
                code_like=code,literal_code_form=literal_code_form(text) and item.knowledge_type!='formula',literal_substring=literal,risk=risk,responsible_stage='extraction_or_evidence_association' if code and not literal else 'not_established',
                signals=signals,automatic_signals_are_not_semantic_verification=True,safe_offline_action='Use explicit reviewed field disposition; otherwise retain for review',manual_review_required=status not in ('SUPPORTED',),targeted_reextraction_required=None))
    ranks={'CRITICAL':0,'HIGH':1,'MEDIUM':2,'LOW':3}
    return sorted(rows,key=lambda r:(ranks[r['risk']],r['knowledge_id'],r['path']))
