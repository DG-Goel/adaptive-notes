"""Lossless claim-table transport; decode through unchanged Task 12A validation."""
import copy
import json
from jsonschema import Draft202012Validator
from app.extraction import canonical_grounding as canonical

VERSION='compact_claim_table_v1'


def obj(properties):
    return dict(type='object',properties=properties,required=list(properties),additionalProperties=False)


def array(items): return dict(type='array',items=items)


def response_format():
    original=canonical.response_format()['json_schema']['schema']
    rich=original['$defs']['value']['anyOf'][1]
    claim=copy.deepcopy(rich['properties']['claims']['items'])
    claim['properties']['id']={'type':'string','minLength':1}; claim['required'].append('id')
    ids=array({'type':'string'})
    field=obj(dict(name={'type':'string'},is_null={'type':'boolean'},groups=array(ids),
                   variables=array(obj(dict(symbol=ids,description=ids)))))
    category={'type':'string','enum':list(canonical.MAIN.keys())+['concepts','procedures','relationships']}
    abstention=copy.deepcopy(original['$defs']['abstention'])
    abstention['properties']['category']=category; abstention['required'].append('category')
    schema=obj(dict(claims=array(claim),items=array(obj(dict(category=category,fields=array(field)))),
                    abstentions=array(abstention),excluded=copy.deepcopy(original['properties']['excluded'])))
    return dict(type='json_schema',json_schema=dict(name=VERSION,strict=True,schema=schema))


def system():
    original=canonical.response_format()['json_schema']['schema']
    fields={c:{'required':s['required'],'optional':[k for k in s['properties'] if k not in s['required']]}
            for c,s in original['$defs'].items() if c not in ('value','abstention')}
    # Original schemas require nullable optional properties too; expose nullability.
    for c in fields:
        shape=original['$defs'][c]
        optional=[k for k,v in shape['properties'].items() if any(x.get('type')=='null' for x in v.get('anyOf',[]))]
        fields[c]={'required':[k for k in shape['required'] if k not in optional],'nullable':optional}
    return canonical.SYSTEM+'''\nTransport encoding only: compact_claim_table_v1. Put atomic claims once in claims,
each with a unique id plus all original evidence/disposition fields. items has category
and fields. Use C-prefixed claim ids. Claim refs/related_refs MUST use the supplied
excerpts' ref values (Q0000 etc), NEVER source IDs (S..., V..., T...) or claim ids.
This is educational notes extraction, not copying every transcript excerpt into a
claim. Select concise supported teaching statements; do not enumerate all excerpts
or create unused claims. Preserve supported concepts without repeating wording.
items has category
and fields. A scalar field uses groups=[[claim IDs]]; aliases/steps/prerequisites use
one group per array element. Each group preserves claim order. Variables use variables
[{symbol:[IDs],description:[IDs]}] and groups=[]. Other fields use variables=[].
For unavailable optional fields use is_null=true,groups=[],variables=[]. Otherwise
is_null=false. Required fields must be present. Do not emit canonical category arrays:
the decoder reconstructs them without adding facts. Never repeat common content for
categories whose content is derived from their main field. Do not declare unused claims.
Abstentions have category plus the existing availability,source_ids,reason. excluded is
unchanged. This encoding does not change evidence permissions or permit OCR promotion.
Category fields: '''+json.dumps(fields,separators=(',',':'))


def decode(content):
    def unique(pairs):
        d={}
        for k,v in pairs:
            if k in d: raise ValueError('Duplicate compact field')
            d[k]=v
        return d
    data=json.loads(content,object_pairs_hook=unique)
    Draft202012Validator(response_format()['json_schema']['schema']).validate(data)
    claims={c['id']:{k:v for k,v in c.items() if k!='id'} for c in data['claims']}
    if len(claims)!=len(data['claims']): raise ValueError('Duplicate claim identity')
    used=set()
    def value(ids):
        if not ids or len(ids)!=len(set(ids)): raise ValueError('Empty or duplicate claim reference')
        if any(i not in claims for i in ids): raise ValueError('Unknown claim reference')
        used.update(ids); cs=[copy.deepcopy(claims[i]) for i in ids]
        refs=list(dict.fromkeys(r for c in cs for r in c['refs']+c['related_refs']))
        return dict(text=' '.join(c['text'] for c in cs),refs=refs,claims=cs)
    original=canonical.response_format()['json_schema']['schema']
    result={c:[] for c in original['properties']}; result['excluded']=data['excluded']
    for item in data['items']:
        cat=item['category']; shape=original['$defs'][cat]; row={}; fields=item['fields']
        for field in fields:
            name=field['name']
            if name in row or name not in shape['properties']: raise ValueError('Unknown/duplicate category field')
            if field['is_null']:
                if field['groups'] or field['variables']: raise ValueError('Null field contains hidden claims')
                row[name]=None
            elif name=='variables':
                if field['groups']: raise ValueError('Variables must use pairs')
                row[name]=[dict(symbol=value(p['symbol']),description=value(p['description'])) for p in field['variables']]
            else:
                if field['variables']: raise ValueError('Nonvariable field contains pairs')
                groups=field['groups']
                if name in ('aliases','steps','prerequisites'): row[name]=[value(g) for g in groups]
                else:
                    if len(groups)!=1: raise ValueError('Scalar field requires one group')
                    row[name]=value(groups[0])
        for name,field in shape['properties'].items():
            if name not in row:
                if any(v.get('type')=='null' for v in field.get('anyOf',[])): row[name]=None
                else: raise ValueError('Missing required category field')
        result[cat].append(row)
    for abstention in data['abstentions']:
        result[abstention['category']].append({k:v for k,v in abstention.items() if k!='category'})
    if used!=set(claims): raise ValueError('Unassigned claims would be lost')
    Draft202012Validator(original).validate(result)
    return result


def resolve_response(content,chunk):
    decoded=decode(content)
    result,audit=canonical.resolve_response(json.dumps(decoded,ensure_ascii=False),chunk)
    audit.append(dict(policy=VERSION,projection='Claim IDs expanded losslessly; unchanged Task 12A schema and resolver applied'))
    return result,audit
