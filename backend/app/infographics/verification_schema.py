"""Source-evidence inventories and complete bidirectional response validation."""
from .generation_schema import fields,text
from .optimization import strict_json
from .optimization_model import canonical
from .source_index import digest
import re

INVENTORY_VERSION='source-facts-v1'
VERIFICATION_VERSION='semantic-verification-v1'
PRIORITIES={'critical','essential','supporting','redundant'}
COVERAGE={'visible_exact','visible_equivalent','support_exact','support_equivalent','source_only','redundant','partially_preserved','missing','distorted','uncertain'}
PRESERVED={'visible_exact','visible_equivalent','support_exact','support_equivalent'}
GROUNDING={'supported_exact','supported_equivalent','unsupported','contradicted','overgeneralized','ambiguous','unverifiable'}
SUPPORTED={'supported_exact','supported_equivalent'}
ISSUES={'missing_fact','missing_condition','missing_exception','incorrect_definition','changed_numerical_value','incorrect_unit','altered_formula','unsupported_claim','contradicted_claim','overgeneralization','reversed_relationship','unsupported_relationship','incorrect_classification','invalid_sequence_order','misleading_visual_structure','excessive_compression','unnecessary_duplication','incorrect_support_association','source_reference_mismatch'}


def refs(values,source):
    if not isinstance(values,list) or not values or any(not isinstance(v,str) or v not in source for v in values) or len(values)!=len(set(values)):raise ValueError('Invalid verification source references')


def inventory(record,visual_id,source,index_id,*,max_facts=128,primary=None):
    fields(record,('visual_id','complete','facts'))
    if record['visual_id']!=visual_id or record['complete'] is not True:raise ValueError('Incomplete source inventory')
    if not isinstance(record['facts'],list) or not 0<len(record['facts'])<=max_facts:raise ValueError('Invalid inventory size')
    mapping={};facts=[]
    for row in record['facts']:
        fields(row,('id','statement','priority','required_visible','refs','evidence','literals','depends_on','redundant_of'))
        local=text(row['id'],60)
        if local in mapping:raise ValueError('Duplicate fact identity')
        text(row['statement'],1000);refs(row['refs'],source)
        for literal in re.findall(r'(?<![\w.])-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?',row['statement']):
            if not any(re.search(r'(?<![\w.])'+re.escape(literal)+r'(?![\w.])',source[r]) for r in row['refs']):raise ValueError('Inventory numerical literal absent from evidence')
        if primary is not None and not set(row['refs'])&set(primary):raise ValueError('Read-only context cannot own facts')
        if row['priority'] not in PRIORITIES or type(row['required_visible']) is not bool:raise ValueError('Invalid fact priority')
        if not isinstance(row['evidence'],list) or not row['evidence']:raise ValueError('Exact fact evidence required')
        evidence_refs=set()
        for evidence in row['evidence']:
            fields(evidence,('ref','quote'))
            if evidence['ref'] not in row['refs']:raise ValueError('Evidence reference mismatch')
            quote=text(evidence['quote'],8000)
            if quote not in source[evidence['ref']]:raise ValueError('Inventory evidence is not an exact source quote')
            evidence_refs.add(evidence['ref'])
        if evidence_refs!=set(row['refs']):raise ValueError('Every fact reference needs evidence')
        if not isinstance(row['literals'],list) or len(row['literals'])>64:raise ValueError('Invalid literals')
        for literal in row['literals']:
            text(literal,500)
            if not any(literal in source[r] for r in row['refs']):raise ValueError('Technical literal absent from source')
        stable='F'+digest(canonical([index_id,row['statement'],row['refs']]).encode())[:24]
        if stable in mapping.values():raise ValueError('Duplicate fact')
        mapping[local]=stable;facts.append(dict(row,id=stable))
    for row in facts:
        if not isinstance(row['depends_on'],list) or any(v not in mapping for v in row['depends_on']):raise ValueError('Unknown dependent fact')
        row['depends_on']=[mapping[v] for v in row['depends_on']]
        duplicate=row['redundant_of']
        if duplicate is not None:
            if duplicate not in mapping or mapping[duplicate]==row['id']:raise ValueError('Invalid redundancy evidence')
            row['redundant_of']=mapping[duplicate]
        if row['priority']=='redundant' and row['redundant_of'] is None:raise ValueError('Unique facts cannot be classified redundant')
    return facts,mapping


def report(record,visual_id,facts,claims,items,support_items,source,*,fact_mapping=None):
    fields(record,('visual_id','coverage','grounding','issues'))
    if record['visual_id']!=visual_id:raise ValueError('Wrong verification visual')
    fact_ids={f['id'] for f in facts};claim_ids={c['id'] for c in claims};seen=set()
    coverage=[];mapping=fact_mapping or {}
    for row in record['coverage']:
        fields(row,('fact_id','status','items','duplicate_of'))
        row=dict(row);row['fact_id']=mapping.get(row['fact_id'],row['fact_id'])
        if row['fact_id'] not in fact_ids or row['fact_id'] in seen or row['status'] not in COVERAGE:raise ValueError('Incomplete/duplicate coverage')
        seen.add(row['fact_id'])
        if not isinstance(row['items'],list) or any(i not in items for i in row['items']) or len(set(row['items']))!=len(row['items']):raise ValueError('Unknown coverage item')
        if row['status'] in PRESERVED and not row['items']:raise ValueError('Preservation needs generated item evidence')
        if row['status'].startswith('visible_') and any(i in support_items for i in row['items']):raise ValueError('Support cannot be counted visible')
        if row['status'].startswith('support_') and any(i not in support_items for i in row['items']):raise ValueError('Visible item cannot be counted support')
        if row['duplicate_of'] is not None:row['duplicate_of']=mapping.get(row['duplicate_of'],row['duplicate_of'])
        if row['status']=='redundant':
            if row['duplicate_of'] not in fact_ids or row['duplicate_of']==row['fact_id']:raise ValueError('Invalid duplicate fact target')
        elif row['duplicate_of'] is not None:raise ValueError('Unexpected redundancy link')
        coverage.append(row)
    if seen!=fact_ids:raise ValueError('Missing source fact outcomes')
    by_fact={r['fact_id']:r for r in coverage}
    for row in coverage:
        if row['status']=='redundant' and by_fact[row['duplicate_of']]['status'] not in PRESERVED:raise ValueError('Redundancy must point to a preserved fact')
    grounding=[];seen=set()
    for row in record['grounding']:
        fields(row,('claim_id','status','refs'))
        if row['claim_id'] not in claim_ids or row['claim_id'] in seen or row['status'] not in GROUNDING:raise ValueError('Invalid grounding result')
        refs(row['refs'],source);seen.add(row['claim_id']);grounding.append(row)
    if seen!=claim_ids:raise ValueError('Missing generated claim outcomes')
    issues=[];issue_ids=set()
    if not isinstance(record['issues'],list):raise ValueError('Invalid issues')
    for issue in record['issues']:
        fields(issue,('type','severity','fact_ids','item_ids','refs','message'))
        issue=dict(issue)
        if issue['type'] not in ISSUES or issue['severity'] not in {'critical','essential','supporting'}:raise ValueError('Invalid issue type/severity')
        text(issue['message'],500);refs(issue['refs'],source)
        if not isinstance(issue['fact_ids'],list) or not isinstance(issue['item_ids'],list):raise ValueError('Invalid issue links')
        issue['fact_ids']=[mapping.get(v,v) for v in issue['fact_ids']]
        if any(v not in fact_ids for v in issue['fact_ids']) or any(v not in items for v in issue['item_ids']):raise ValueError('Unknown issue fact/item')
        if not issue['fact_ids'] and not issue['item_ids']:raise ValueError('Unscoped issue')
        identifier='I'+digest(canonical([visual_id,issue]).encode())[:24]
        if identifier in issue_ids:raise ValueError('Duplicate issue')
        issue_ids.add(identifier);issues.append(dict(issue,id=identifier))
    for row in coverage:
        fact=next(f for f in facts if f['id']==row['fact_id'])
        permitted_source_support=row['status']=='source_only' and fact['priority']=='supporting' and not fact['required_visible']
        if row['status'] not in PRESERVED|{'redundant'} and not permitted_source_support and not any(row['fact_id'] in i['fact_ids'] for i in issues):raise ValueError('Deficient fact needs an issue')
    for row in grounding:
        claim=next(c for c in claims if c['id']==row['claim_id'])
        if row['status'] not in SUPPORTED and not any(set(claim['items'])&set(i['item_ids']) for i in issues):raise ValueError('Unsupported claim needs an issue')
    return dict(visual_id=visual_id,coverage=coverage,grounding=grounding,issues=issues)
