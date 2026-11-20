"""Compact field rows: no dangling claim-table IDs, unchanged Task 12A resolver."""
import copy
import json
from jsonschema import Draft202012Validator
from app.extraction import canonical_grounding as canonical
from app.extraction.compact_claim_wire import obj,array

VERSION='compact_field_rows_v1'


def response_format():
    original=canonical.response_format()['json_schema']['schema']
    atomic=copy.deepcopy(original['$defs']['value']['anyOf'][1]['properties']['claims']['items'])
    categories=[c for c in original['properties'] if c!='excluded']
    fields=sorted({f for c in categories for f in original['$defs'][c]['properties']})
    atomic['properties'].update(item={'type':'string'},category={'type':'string','enum':categories},
        field={'type':'string','enum':fields},element={'type':'integer','minimum':0},part={'type':'string','enum':['value','symbol','description']})
    atomic['required']=list(atomic['properties'])
    abstention=copy.deepcopy(original['$defs']['abstention']); abstention['properties']['category']={'type':'string','enum':categories}; abstention['required'].append('category')
    return dict(type='json_schema',json_schema=dict(name=VERSION,strict=True,schema=obj(dict(rows=array(atomic),abstentions=array(abstention),excluded=original['properties']['excluded']))))


def system():
    original=canonical.response_format()['json_schema']['schema']
    fields={}
    for category in original['properties']:
        if category == 'excluded':
            continue
        properties=original['$defs'][category]['properties']
        nullable=[name for name,schema in properties.items()
                  if any(option.get('type')=='null' for option in schema.get('anyOf',[]))]
        fields[category]={'required':[name for name in properties if name not in nullable],
                          'nullable':nullable}
    return canonical.SYSTEM+'''\nWire encoding: compact_field_rows_v1. Return rows, abstentions, excluded only.
Each row is ONE atomic claim with text,refs,basis,availability,literal_kind,
instructional_role,related_refs and its item/category/field/element/part location.
Use the same item string for fields belonging to one knowledge item. refs and
related_refs contain excerpt refs Q0000 etc, never source IDs S/V/T or item IDs.
Scalar fields use element=0,part=value; multiple rows for the same scalar are
joined in output order. aliases,steps,prerequisites use contiguous element indices
starting at 0. variables use part=symbol or description with matching element.
Other fields use part=value. Omit rows for unavailable optional fields (null).
Supply at least one row for every required field of each item. In particular,
a concept needs both concept_name and content rows under the same item label.
If the excerpts do not support every required field, use an appropriate
abstention instead of emitting an incomplete item. Do not emit content when it is absent
from the category field list below. Extract concise notes, not all transcript
sentences. No unused claim pool exists. Excluded may cite PRIMARY excerpt refs
only; otherwise leave excluded empty. All original no-invention rules apply.
Category field lists: '''+json.dumps(fields,separators=(',',':'))


def decode(content):
    def unique(pairs):
        d={}
        for k,v in pairs:
            if k in d: raise ValueError('Duplicate JSON field')
            d[k]=v
        return d
    data=json.loads(content,object_pairs_hook=unique)
    Draft202012Validator(response_format()['json_schema']['schema']).validate(data)
    original=canonical.response_format()['json_schema']['schema']
    result={c:[] for c in original['properties']}; result['excluded']=data['excluded']; items={}
    for row in data['rows']:
        cat=row['category']; name=row['field']; item=row['item']
        # Item labels are scoped by category, as in the canonical category arrays.
        if name not in original['$defs'][cat]['properties']: raise ValueError('Unknown category field')
        if name=='variables':
            if row['part']=='value': raise ValueError('Variable requires symbol/description')
        elif row['part']!='value':
            raise ValueError('Invalid scalar/array location')
        claim={k:copy.deepcopy(v) for k,v in row.items() if k not in ('item','category','field','element','part')}
        index=row['element'] if name in ('variables','steps','aliases','prerequisites') else 0
        items.setdefault((cat,item),{}).setdefault(name,{}).setdefault((index,row['part']),[]).append(claim)
    def value(claims):
        return dict(text=' '.join(c['text'] for c in claims),refs=list(dict.fromkeys(r for c in claims for r in c['refs']+c['related_refs'])),claims=claims)
    for (cat,item),fields in items.items():
        shape=original['$defs'][cat]; output={}
        for name,locations in fields.items():
            indices=sorted({i for i,p in locations})
            if indices!=list(range(len(indices))): raise ValueError('Noncontiguous array elements')
            if name=='variables':
                if any((i,p) not in locations for i in indices for p in ('symbol','description')): raise ValueError('Incomplete variable pair')
                output[name]=[dict(symbol=value(locations[i,'symbol']),description=value(locations[i,'description'])) for i in indices]
            elif name in ('steps','aliases','prerequisites'): output[name]=[value(locations[i,'value']) for i in indices]
            else: output[name]=value(locations[0,'value'])
        for name,field in shape['properties'].items():
            if name not in output:
                if any(v.get('type')=='null' for v in field.get('anyOf',[])): output[name]=None
                else: raise ValueError(f'Missing required field: {cat}[{item!r}].{name}')
        result[cat].append(output)
    for row in data['abstentions']: result[row['category']].append({k:v for k,v in row.items() if k!='category'})
    Draft202012Validator(original).validate(result)
    return result


def resolve_response(content,chunk):
    result,audit=canonical.resolve_response(json.dumps(decode(content),ensure_ascii=False),chunk)
    audit.append(dict(policy=VERSION,projection='Field rows projected without adding/dropping claims; original schema/resolver applied'))
    return result,audit
