"""Versioned context-aware wire contract. Primary work accounting stays unchanged."""
import json
from app.extraction import grounded_fields as base
from app.extraction.quote_catalog import catalog, evidence_source_ids
from app.extraction.source_context import evidence_view

SYSTEM=base.SYSTEM+'''
PRIMARY units are extraction targets; CONTEXT units only clarify primary teaching.
Every item must cite at least one PRIMARY excerpt. Do not extract context-only topics.
Preserve conditions and uncertainty in every claim. Never add missing definitions or code.
Context is evidence only for claims actually supported by the explicitly cited excerpts.
Do not exclude CONTEXT excerpts. Overlapping context is not independently completed work.
For definitions, facts, examples, explanations and formulas, content MUST equal the main
category text exactly. Empty extraction leaves primary coverage unresolved for review.
'''

response_format=base.response_format


def chunk_prompt(chunk):
    entries=catalog(evidence_view(chunk))
    body={'primary_source_ids':evidence_source_ids(chunk),
        'context_source_ids':chunk.context_source_ids,'context_limitations':chunk.context_limitations,
        'excerpts':[{'ref':k,**v,'role':'primary' if v['source_id'] in chunk.source_units else 'context'}
                    for k,v in entries.items()]}
    if chunk.uninterpreted_source_ids:
        body['nonquotable_primary_sources']=[{'source_id':s,'state':chunk.source_states[s],
            'counts_as_completed':False} for s in chunk.uninterpreted_source_ids]
    return json.dumps(body,ensure_ascii=False,separators=(',',':'))


def resolve_response(content,chunk):
    view=evidence_view(chunk)
    resolved,audit=base.resolve_response(content,view)
    data=json.loads(resolved); entries=catalog(view)
    raw=json.loads(content)
    for exclusion in raw['excluded']:
        if entries[exclusion['ref']]['source_id'] not in chunk.source_units:
            raise ValueError('Context-only exclusion forbidden')
    main={'definitions':'definition_text','facts':'fact_text','examples':'example_text',
          'explanations':'explanation_text','formulas':'formula_text'}
    reviews=[]
    for category,items in data.items():
        for index,item in enumerate(items):
            if not set(item['source_unit_ids']) & set(chunk.source_units):
                raise ValueError('Context-only knowledge forbidden')
            if category in main and item['content']!=item[main[category]]:
                raise ValueError('Common/category text mismatch')
            from app.extraction.claim_review import review_claim
            for field,evidenced in raw[category][index].items():
                values=evidenced if isinstance(evidenced,list) else [evidenced]
                for value in values:
                    if isinstance(value,dict) and 'text' in value:
                        reviews.append({'category':category,'field':field,
                            **review_claim(value['text'],[entries[r]['quote'] for r in value['refs']])})
    for record in audit:
        record.update(primary_source_ids=chunk.source_units,context_source_ids=chunk.context_source_ids,
                      semantic_status='unverified',context_counts_as_completed=False,claim_reviews=reviews)
    return resolved,audit
