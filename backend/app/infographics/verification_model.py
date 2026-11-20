"""Deterministic claim enumeration, artifact integrity and explicit acceptance gates."""
import copy
from dataclasses import dataclass
from .generation import validate_optimized
from .generation_schema import validate_record
from .antv_adapter import convert
from .optimization_model import canonical
from .source_index import digest
from .verification_schema import PRESERVED,SUPPORTED


TEMPLATE_CONSTRAINTS={
 'A1':'Branches must meaningfully relate to the root, not imply unsupported classification.',
 'A2':'Every parent-child link must be a source-supported classification.',
 'A3':'Every component must belong to the displayed system/group.',
 'A4':'Definitions, unique qualifications and distinctions must be retained.',
 'A5':'The source must justify rank/ordered conceptual levels, not merely list items.',
 'B1':'Check step order, prerequisites and omitted essential process steps.',
 'B2':'The source must establish genuine repetition/feedback and closure.',
 'B3':'Literal date/period, event association and chronological order must be supported.',
 'B4':'Check edge existence, causal versus other relation meaning, direction and conditions.',
 'B5':'Check actors, action ownership, chronology and message relationships.',
 'C1':'Corresponding attributes must fairly and accurately compare both entities.',
 'C2':'Two meaningful dimensions/poles and every quadrant membership need evidence.',
 'C3':'Check exact values, shared units and comparability, not just literal citations.',
 'C4':'Check values/order/progression; native geometry uses equal index spacing, not continuous time spacing.',
 'C5':'Check nonnegative exclusive parts, genuine common whole, denominator and proportional meaning.'}


def validate_generation(generation,optimizer,*,allow_skipped=False):
    groups=validate_optimized(optimizer,allow_skipped)
    if generation.status!='complete' or canonical(groups)!=canonical(generation.groups):raise ValueError('Completed validated generation required')
    if generation.index.fingerprint!=optimizer.index.fingerprint or generation.optimized_hash!=digest(canonical(groups).encode()) or generation.provisional_hash!=optimizer.input_hash:raise ValueError('Generation manifest binding mismatch')
    generation.index.validate()
    expected_ids={g['id'] for g in groups}
    if set(generation.results)!=expected_ids:raise ValueError('Missing/unknown generated segment')
    for group in groups:
        artifact=generation.results[group['id']]
        if group['category']=='N':
            expected=dict(status='preserved_nonvisual',source_refs=[b.id for b in generation.index.units[group['start_position']:group['end_position']+1]])
            if artifact!=expected:raise ValueError('Corrupt nonvisual ownership')
            continue
        category=generation.category_overrides.get(group['id'],group['category'])
        source={k:b.text for k,b in generation._authorized(group).items()}
        validate_record(artifact['record'],generation._aliases[group['id']],category,source,max_items=generation.config.max_items,max_depth=generation.config.max_depth)
        expected=generation._artifact(group,artifact['record'],category)
        expected['token_usage']=artifact['token_usage']
        if canonical(expected)!=canonical(artifact):raise ValueError('Generation artifact identity/native adapter mismatch')
    return copy.deepcopy(generation.results)


def item_map(record):
    result={}
    def walk(value):
        if isinstance(value,dict):
            if 'id' in value:result[value['id']]=value
            for child in value.values():walk(child)
        elif isinstance(value,list):
            for child in value:walk(child)
    walk(record['data']);walk(record['support'])
    return result


def claims(record,visual_id,source):
    """Every text assertion and structural implication receives a backend identity."""
    result=[];items=item_map(record);support={s['id'] for s in record['support']};sequences=[]
    def orderings(value,path):
        if isinstance(value,dict):
            for key in sorted(value):orderings(value[key],path+'/'+key)
        elif isinstance(value,list):
            if value and all(isinstance(v,dict) and 'id' in v for v in value):sequences.append(dict(path=path,ids=[v['id'] for v in value]))
            for i,v in enumerate(value):orderings(v,path+'/'+str(i))
    orderings(record['data'],'data')
    def add(path,value,owners,refs,kind):
        identifier='C'+digest(canonical([visual_id,path,value]).encode())[:24]
        result.append(dict(id=identifier,path=path,statement=value,items=owners,refs=refs,kind=kind))
    add('title',record['title'],['@title'],list(source),'visible')
    def walk(value,path,parent=None,refs=None):
        if isinstance(value,dict):
            owner=value.get('id',parent or '@structure');evidence=value.get('refs',refs or list(source))
            for key,child in value.items():
                if key in {'id','refs','children'}:continue
                if isinstance(child,(str,int,float)) and key not in {'item_id'}:
                    add(path+'/'+key,child,[owner],evidence,'support' if owner in support else 'visible')
                elif isinstance(child,(dict,list)):walk(child,path+'/'+key,owner,evidence)
            for i,child in enumerate(value.get('children',[])):
                add(path+'/membership/'+str(i),dict(parent=owner,child=child['id'],template=record['type']),[owner,child['id']],list(dict.fromkeys(evidence+child['refs'])),'structure')
                walk(child,path+'/children/'+str(i),child['id'],child['refs'])
        elif isinstance(value,list):
            for i,child in enumerate(value):walk(child,path+'/'+str(i),parent,refs)
    walk(record['data'],'data');walk(record['support'],'support')
    add('template_semantics',dict(template=record['type'],constraint=TEMPLATE_CONSTRAINTS[record['type']],
        item_ids=sorted(i for i in items if i not in support),ordered_sequences=sequences),['@structure'],list(source),'structure')
    return result,set(items)|{'@title','@structure'},support


@dataclass(frozen=True)
class AcceptancePolicy:
    require_all_critical: bool=True
    require_all_essential: bool=True
    require_visible_when_flagged: bool=True
    require_all_claims_grounded: bool=True
    block_all_issues: bool=True

    def __post_init__(self):
        if any(type(value) is not bool for value in self.__dict__.values()):raise ValueError('Acceptance gates must be explicit booleans')


def assess(facts,report,policy=AcceptancePolicy()):
    by_id={r['fact_id']:r for r in report['coverage']}
    def preserved(f):
        row=by_id[f['id']]
        return row['status'] in PRESERVED or (row['status']=='redundant' and by_id[row['duplicate_of']]['status'] in PRESERVED)
    reasons=[]
    if policy.require_all_critical and any(not preserved(f) for f in facts if f['priority']=='critical'):reasons.append('critical_fact_not_preserved')
    if policy.require_all_essential and any(not preserved(f) for f in facts if f['priority']=='essential'):reasons.append('essential_fact_not_preserved')
    def visible(f):
        row=by_id[f['id']]
        if row['status']=='redundant':row=by_id[row['duplicate_of']]
        return row['status'].startswith('visible_')
    if policy.require_visible_when_flagged and any(f['required_visible'] and not visible(f) for f in facts):reasons.append('required_visible_fact_not_visible')
    if policy.require_all_claims_grounded and any(r['status'] not in SUPPORTED for r in report['grounding']):reasons.append('ungrounded_or_uncertain_claim')
    if policy.block_all_issues and report['issues']:reasons.append('unresolved_issues')
    return dict(accepted=not reasons,reasons=reasons,scope='identified_inventory_and_enumerated_claims',
                inventory_exhaustiveness_guaranteed=False,source_truth_independently_checked=False)


def coverage_metrics(facts,report):
    by_id={r['fact_id']:r for r in report['coverage']}
    rank={'critical':0,'essential':1,'supporting':2,'redundant':3}
    unique={}
    for fact in facts:
        row=by_id[fact['id']];root=row['duplicate_of'] if row['status']=='redundant' else fact['id']
        if root not in unique or rank[fact['priority']]<rank[unique[root]['priority']]:unique[root]=dict(fact,id=root)
    facts=list(unique.values())
    rate=lambda values:sum(values)/len(values) if values else None
    return dict(visible_fact_coverage=rate([by_id[f['id']]['status'].startswith('visible_') for f in facts]),
        supporting_fact_coverage=rate([by_id[f['id']]['status'].startswith('support_') for f in facts]),
        combined_essential_fact_coverage=rate([by_id[f['id']]['status'] in PRESERVED for f in facts if f['priority']=='essential']),
        critical_fact_coverage=rate([by_id[f['id']]['status'] in PRESERVED for f in facts if f['priority']=='critical']),
        generated_claim_grounding=rate([r['status'] in SUPPORTED for r in report['grounding']]),
        source_only_facts=sum(r['status']=='source_only' for r in report['coverage']),
        uncertain_facts=sum(r['status']=='uncertain' for r in report['coverage']),
        unresolved_facts=sum(r['status'] not in PRESERVED|{'redundant'} for r in report['coverage']),
        distinct_identified_facts=len(facts),inventory_exhaustiveness_guaranteed=False)
