"""Whitelisted issue-scoped patches; never arbitrary JSON/file edits."""
import copy
from .generation_schema import fields,validate_record,text
from .verification_model import item_map
from .optimization_model import canonical

ESCALATIONS={'needs_regeneration','needs_template_change','needs_reroute','needs_split','unsupported'}
OPERATIONS={'replace_title','replace_description','replace_label','replace_refs','replace_value','reverse_relation','remove_relation','replace_support_text','add_support'}


def apply_repairs(record,response,visual_id,issues,source,category,*,max_items=80,max_depth=6):
    fields(response,('visual_id','repairs','escalation'))
    if response['visual_id']!=visual_id or not isinstance(response['repairs'],list):raise ValueError('Wrong repair artifact')
    escalation=response['escalation']
    if escalation is not None:
        fields(escalation,('status','reason'));text(escalation['reason'],240)
        if escalation['status'] not in ESCALATIONS or response['repairs']:raise ValueError('Invalid repair escalation')
        return None,[],escalation
    if not response['repairs'] or len(response['repairs'])>32:raise ValueError('Empty or excessive repairs')
    revised=copy.deepcopy(record);by_issue={i['id']:i for i in issues};audit=[];seen=set();touched=set()
    for patch in response['repairs']:
        fields(patch,('issue_id','operation','item_id','value','refs'))
        if patch['issue_id'] not in by_issue or patch['operation'] not in OPERATIONS:raise ValueError('Unauthorized repair operation/issue')
        issue=by_issue[patch['issue_id']];identifier=patch['item_id']
        if identifier not in issue['item_ids']:raise ValueError('Repair targets unrelated content')
        if not isinstance(patch['refs'],list) or not patch['refs'] or any(r not in source for r in patch['refs']):raise ValueError('Unauthorized repair evidence')
        key=(identifier,patch['operation'])
        if key in seen:raise ValueError('Conflicting duplicate repair')
        seen.add(key)
        if patch['operation']=='replace_title':
            if identifier!='@title':raise ValueError('Title repair must target the identified title')
            text(patch['value'],160);old=dict(title=revised['title']);revised['title']=patch['value']
            audit.append(dict(issue_id=patch['issue_id'],operation='replace_title',item_id=identifier,before=old,
                after=dict(title=revised['title']),added_support=None,evidence_refs=patch['refs']))
            touched.add(identifier);continue
        current=item_map(revised)
        if identifier not in current:raise ValueError('Unknown repair item')
        item=current[identifier];old=copy.deepcopy(item);operation=patch['operation'];value=patch['value']
        if operation in {'replace_description','replace_label','replace_support_text','replace_value'}:
            field={'replace_description':'desc','replace_label':'label','replace_support_text':'text','replace_value':'value'}[operation]
            if field not in item:raise ValueError('Repair field is not supported by target')
            text(value,8000 if field=='text' else 600 if field=='desc' else 160)
            item[field]=value;item['refs']=patch['refs']
        elif operation=='replace_refs':
            if issue['type']!='source_reference_mismatch' or value!=patch['refs']:raise ValueError('Reference replacement requires an identified reference defect')
            item['refs']=value
        elif operation in {'reverse_relation','remove_relation'}:
            if value is not None or 'from' not in item or 'to' not in item or issue['type'] not in {'reversed_relationship','unsupported_relationship','unsupported_claim'}:raise ValueError('Invalid relationship repair')
            if operation=='reverse_relation':item['from'],item['to']=item['to'],item['from'];item['refs']=patch['refs']
            else:revised['data']['relations']=[r for r in revised['data']['relations'] if r['id']!=identifier]
        else:
            fields(value,('id','item_id','kind','text','refs'))
            if value['item_id']!=identifier or value['refs']!=patch['refs']:raise ValueError('Support association mismatch')
            revised['support'].append(value)
        audit.append(dict(issue_id=patch['issue_id'],operation=operation,item_id=identifier,before=old,
                          after=copy.deepcopy(item_map(revised).get(identifier)),added_support=copy.deepcopy(value) if operation=='add_support' else None,evidence_refs=patch['refs']))
        touched.add(identifier)
    original_items=item_map(record);repaired_items=item_map(revised)
    def own_fields(item):
        if item is None:return None
        return {k:([child['id'] for child in v] if k=='children' else v) for k,v in item.items()}
    for identifier,item in original_items.items():
        if identifier not in touched and canonical(own_fields(item))!=canonical(own_fields(repaired_items.get(identifier))):raise ValueError('Repair rewrote unaffected content')
    # Parent JSON objects include child nodes; child patches necessarily change
    # those container representations. Field-by-field semantic rechecking below
    # uses the complete revised visual, so every claim is re-evaluated.
    validate_record(revised,record['segment_id'],category,source,max_items=max_items,max_depth=max_depth)
    return revised,audit,None
