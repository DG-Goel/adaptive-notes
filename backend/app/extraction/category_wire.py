"""Native Task 12A objects, one category per request. No claim-ID indirection."""
import copy
import json
from jsonschema import Draft202012Validator
from app.extraction import canonical_grounding as canonical


def response_format(category):
    original=copy.deepcopy(canonical.response_format()['json_schema']['schema'])
    if category not in original['properties'] or category=='excluded': raise ValueError('Unknown extraction category')
    props=dict(items={'type':'array','items':{'$ref':'#/$defs/'+category}},
               abstentions={'type':'array','items':{'$ref':'#/$defs/abstention'}},excluded=original['properties']['excluded'])
    schema=dict(type='object',properties=props,required=list(props),additionalProperties=False)
    wanted={category,'value','abstention'}
    schema['$defs']={k:v for k,v in original['$defs'].items() if k in wanted}
    return dict(type='json_schema',json_schema=dict(name='evidence_first_12a_'+category,strict=True,schema=schema))


def system(category):
    return canonical.SYSTEM+f'''\nRequest partition: extract {category} ONLY from PRIMARY teaching.
Return items, abstentions, excluded. items uses the original {category} objects,
including per-field text,refs,claims. This is a task partition, not a policy change.
Do not use a global claim-ID pool. Every field contains its own original evidence
object. refs/related_refs use supplied excerpt refs Q0000 etc, NEVER source IDs.
Leave items empty if this category has no supported teaching. Abstain only for a
missing part of an actual teaching point, not merely an unused category.
Abstention source_ids must come from primary_source_ids only. Excluded may cite
PRIMARY excerpt refs only. Do not discard a supported concept because its literal
code/formula is unavailable; keep the supported explanation and identify the gap.'''


def resolve_response(content,chunk,category):
    def unique(pairs):
        d={}
        for k,v in pairs:
            if k in d: raise ValueError('Duplicate JSON field')
            d[k]=v
        return d
    data=json.loads(content,object_pairs_hook=unique)
    Draft202012Validator(response_format(category)['json_schema']['schema']).validate(data)
    original=canonical.response_format()['json_schema']['schema']
    expanded={c:[] for c in original['properties']}
    expanded[category]=data['items']+data['abstentions']; expanded['excluded']=data['excluded']
    result,audit=canonical.resolve_response(json.dumps(expanded,ensure_ascii=False),chunk)
    audit.append(dict(policy='category_bounded_12a_v1',category=category,original_schema_and_resolver=True))
    return result,audit
