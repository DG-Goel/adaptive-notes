"""Typed category objects plus one shared claim pool; unchanged local evidence rules."""
import copy
import json
from jsonschema import Draft202012Validator
from app.extraction import canonical_grounding as canonical
from app.extraction.compact_claim_wire import obj,array

VERSION='typed_claim_refs_v1'


def response_format():
    original=copy.deepcopy(canonical.response_format()['json_schema']['schema'])
    atomic=copy.deepcopy(original['$defs']['value']['anyOf'][1]['properties']['claims']['items'])
    atomic['properties']['id']={'type':'string'}; atomic['required'].append('id')
    original['$defs']['value']={**array({'type':'string'}),'minItems':1}
    categories=[c for c in original['properties'] if c!='excluded']
    for cat in categories:
        original['properties'][cat]['items']={'$ref':'#/$defs/'+cat}
        for name,shape in list(original['$defs'][cat]['properties'].items()):
            if any(s.get('type')=='null' for s in shape.get('anyOf',[])):
                value=copy.deepcopy(next(s for s in shape['anyOf'] if s.get('type')!='null'))
                if value.get('$ref')=='#/$defs/value': value=array({'type':'string'})
                original['$defs'][cat]['properties'][name]=obj(dict(is_null={'type':'boolean'},value=value))
    original['properties']['claims']=array(atomic)
    abstention=original['$defs'].pop('abstention')
    abstention['properties']['category']={'type':'string','enum':categories}; abstention['required'].append('category')
    original['properties']['abstentions']=array(abstention)
    original['required']=list(original['properties'])
    return dict(type='json_schema',json_schema=dict(name=VERSION,strict=True,schema=original))


def system():
    example={c:[] for c in canonical.response_format()['json_schema']['schema']['properties']}
    example.update(claims=[dict(id='C1',text='__SUPPORTED_TEXT_FROM_EXCERPTS__',refs=['Q_EXAMPLE'],basis='explicit',availability='SOURCE_SUPPORTED',literal_kind='verbal',instructional_role=None,related_refs=[])],abstentions=[])
    example['facts']=[dict(fact_text=['C1'],fact_type=dict(is_null=True,value=[]))]
    return canonical.SYSTEM+'''\nWire encoding typed_claim_refs_v1: category objects retain their original fields.
Put atomic claims ONCE in top-level claims, each with unique id C1,C2,etc and all
evidence/disposition fields. Each scalar category field is a nonempty list of
claim IDs, e.g. fact_text:["C1"]. Multiple IDs join claim texts in order. Array
fields such as steps contain one claim-ID list per element. Variables contain
symbol/description claim-ID lists. Optional fields use {is_null,value}: unavailable
means is_null=true,value=[]; available means is_null=false,value=the usual list.
Claim refs/related_refs contain ONLY supplied excerpt refs Q0000 etc, never source
IDs S/V/T or claim IDs. Do not confuse claims' id with their evidence refs.
Every required item field must be present. Do not duplicate derived content fields.
Abstentions are a separate array of category,availability,source_ids,reason.
Excluded may cite PRIMARY excerpt refs only; otherwise leave excluded empty.
Write concise supported teaching notes, not a copy of all excerpts. Empty category
arrays are valid; do not invent claims to populate them. Each usable teaching claim
MUST be referenced by a category item's field, rather than left only in claims.
Do not put all teaching in the unassigned review pool. Avoid abstentions for
unrelated categories: leave them empty. Abstain only for an actual missing part
of a teaching point; source_ids must be a subset of primary_source_ids, NEVER
context IDs. Preserve supported explanations while the literal code is missing.
Unassigned pool claims remain review-only, not student notes. All Task 12A rules
remain unchanged. The following is FORMAT ONLY, not evidence. Replace placeholders
and use actual excerpt refs; never output Q_EXAMPLE or the placeholder text:
'''+json.dumps(example,separators=(',',':'))


def decode(content):
    def unique(pairs):
        d={}
        for k,v in pairs:
            if k in d: raise ValueError('Duplicate wire property')
            d[k]=v
        return d
    data=json.loads(content,object_pairs_hook=unique)
    schema=response_format()['json_schema']['schema']
    Draft202012Validator(schema).validate(data)
    claims={r['id']:{k:copy.deepcopy(v) for k,v in r.items() if k!='id'} for r in data['claims']}
    if len(claims)!=len(data['claims']): raise ValueError('Duplicate claim ID')
    used=set()
    original=canonical.response_format()['json_schema']['schema']
    def transform(shape,value):
        if '$ref' in shape:
            name=shape['$ref'].split('/')[-1]
            if name=='value':
                if len(value)!=len(set(value)) or any(i not in claims for i in value): raise ValueError('Duplicate or unknown claim reference')
                used.update(value); cs=[copy.deepcopy(claims[i]) for i in value]
                return dict(text=' '.join(c['text'] for c in cs),refs=list(dict.fromkeys(r for c in cs for r in c['refs']+c['related_refs'])),claims=cs)
            return transform(original['$defs'][name],value)
        if 'anyOf' in shape:
            if not any(s.get('type')=='null' for s in shape['anyOf']):
                return transform(shape['anyOf'][0],value)
            if value['is_null']:
                if value['value']: raise ValueError('Null wrapper contains hidden claims')
                return None
            return transform(next(s for s in shape['anyOf'] if s.get('type')!='null'),value['value'])
        if shape.get('type')=='object': return {k:transform(shape['properties'][k],v) for k,v in value.items()}
        if shape.get('type')=='array': return [transform(shape['items'],v) for v in value]
        return value
    result={cat:transform(original['properties'][cat],data[cat]) for cat in original['properties']}
    for row in data['abstentions']: result[row['category']].append({k:v for k,v in row.items() if k!='category'})
    Draft202012Validator(original).validate(result)
    return result,[dict(id=i,**claims[i]) for i in claims if i not in used]


def resolve_response(content,chunk):
    decoded,unassigned=decode(content)
    # Validate even review-only refs: no invented evidence identifiers are allowed.
    from app.extraction.quote_catalog import catalog
    from app.extraction.source_context import evidence_view
    refs=set(catalog(evidence_view(chunk)))
    if any(r not in refs for c in unassigned for r in c['refs']+c['related_refs']): raise ValueError('Unknown review-claim evidence reference')
    result,audit=canonical.resolve_response(json.dumps(decoded,ensure_ascii=False),chunk)
    audit.append(dict(policy=VERSION,unassigned_review_claims=unassigned,unassigned_claims_approved=False,
                      projection='Typed claim references expanded; unchanged Task 12A schema and resolver applied'))
    return result,audit
