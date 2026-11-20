"""Single canonical text per claim; common content is a deterministic projection."""
import copy,json
from jsonschema import Draft202012Validator
from app.extraction import context_grounding as context

MAIN={'definitions':'definition_text','facts':'fact_text','examples':'example_text',
      'explanations':'explanation_text','formulas':'formula_text'}
from app.extraction.no_invention import SYSTEM as NO_INVENTION_SYSTEM
SYSTEM=NO_INVENTION_SYSTEM+'''
Canonical wire: output schema fields only; common content is copied from the main
evidenced field for definitions, explanations, examples, facts and formulas. Every
item needs a PRIMARY excerpt; CONTEXT may clarify it but is never independently
extracted, completed or excluded. Cite every excerpt needed by the whole field,
including boundaries. Retain noisy/mixed teaching. Exclude only wholly noneducational
excerpts, never cited excerpts. Review unused primary excerpts for omitted teaching.
'''
chunk_prompt=context.chunk_prompt


def response_format():
    result=copy.deepcopy(context.response_format())
    result['json_schema']['name']='canonical_grounded_v4'
    # Required arrays alone permit []; require actual evidence before generation.
    value=result['json_schema']['schema']['$defs']['value']
    value['properties']['refs']['minItems']=1
    value['properties']['text']['minLength']=1
    for category in MAIN:
        shape=result['json_schema']['schema']['$defs'][category]
        del shape['properties']['content']
        shape['required'].remove('content')
    from app.extraction.no_invention import extend_schema
    return extend_schema(result)


def resolve_response(content,chunk):
    def unique(pairs):
        d={}
        for key,value in pairs:
            if key in d: raise ValueError('Duplicate JSON field')
            d[key]=value
        return d
    data=json.loads(content,object_pairs_hook=unique)
    if not Draft202012Validator(response_format()['json_schema']['schema']).is_valid(data):
        raise ValueError('Invalid canonical wire schema')
    from app.extraction.no_invention import normalize_wire
    from app.extraction.quote_catalog import catalog
    from app.extraction.source_context import evidence_view
    data,generation_audit=normalize_wire(data,chunk,catalog(evidence_view(chunk)))
    for category,field in MAIN.items():
        for item in data[category]:item['content']=copy.deepcopy(item[field])
    resolved,audit=context.resolve_response(json.dumps(data,ensure_ascii=False),chunk)
    audit.append({'policy':'canonical_grounded_v4','projection':'common content copied from its evidenced main field; no factual repair'})
    audit.append(generation_audit)
    return resolved,audit
