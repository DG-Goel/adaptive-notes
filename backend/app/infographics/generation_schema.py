"""Strict eight-family intermediate validation. Structural checks are not semantic proof."""
from decimal import Decimal,InvalidOperation
import re
from .template_registry import REGISTRY
from .optimization import strict_json

SCHEMA_VERSION='noetra-generation-v1'
FAMILIES=('hierarchy','grouped','list','sequence','graph','interaction','comparison','numeric')


def fields(value,required,optional=()):
    if not isinstance(value,dict) or not set(required)<=set(value) or set(value)-set(required)-set(optional): raise ValueError('Invalid object fields')


def text(value,maximum=600):
    if not isinstance(value,str) or not 1<=len(value.strip())<=maximum or '\x00' in value: raise ValueError('Invalid text')
    return value


def validate_record(record,segment_id,category,source,*,max_items=80,max_depth=6):
    """source maps authorized reversible aliases to exact immutable block text."""
    if not isinstance(record,dict) or record.get('segment_id')!=segment_id: raise ValueError('Wrong segment ID')
    status=record.get('status')
    def refs(values):
        if not isinstance(values,list) or not values or any(not isinstance(v,str) or v not in source for v in values) or len(set(values))!=len(values): raise ValueError('Unauthorized source refs')
        return '\n'.join(source[v] for v in values)
    if status!='generated':
        if status=='needs_split':
            fields(record,('segment_id','status','boundaries','reason'))
            boundaries=record['boundaries']; ids=list(source)
            if not isinstance(boundaries,list) or not boundaries or any(not isinstance(b,str) or b not in ids[:-1] for b in boundaries): raise ValueError('Invalid split boundaries')
            positions=[ids.index(b) for b in boundaries]
            if positions!=sorted(set(positions)): raise ValueError('Unordered split boundaries')
        elif status=='reroute':
            fields(record,('segment_id','status','category','reason'))
            if record['category'] not in {'A','B','C'} or record['category']==category: raise ValueError('Invalid reroute')
        elif status=='unsupported':
            fields(record,('segment_id','status','refs','reason'));refs(record['refs'])
        else: raise ValueError('Invalid generation status')
        text(record['reason'],240)
        return record
    fields(record,('segment_id','status','type','title','data','support'))
    code=record['type']
    if not isinstance(code,str) or code not in REGISTRY or code[0]!=category: raise ValueError('Wrong category or template')
    text(record['title'],160);data=record['data']; family=REGISTRY[code].family
    ids=set(); all_nodes=[]
    def node(value,depth=1,children=False,extras=()):
        fields(value,('id','label','desc','refs'),(('children',) if children else ())+tuple(extras))
        identifier=text(value['id'],60)
        if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]*',identifier) or identifier in ids: raise ValueError('Duplicate or unsafe item ID')
        ids.add(identifier);all_nodes.append(value)
        if len(ids)>max_items or depth>max_depth: raise ValueError('Complexity or nesting limit')
        text(value['label'],160);text(value['desc'],600);refs(value['refs'])
        for child in value.get('children',[]): node(child,depth+1,True)
        if 'children' in value and not isinstance(value['children'],list): raise ValueError('Invalid children')
        # Exact formula claims use an explicit literal field and must occur verbatim
        # in referenced source. General wording remains for Phase 6 verification.
    def nodes(values,**kwargs):
        if not isinstance(values,list) or not values: raise ValueError('Empty item list')
        for value in values: node(value,**kwargs)
    def relation(value,endpoints):
        fields(value,('id','from','to','label','desc','refs'))
        if value['from'] not in endpoints or value['to'] not in endpoints: raise ValueError('Unknown relation endpoint')
        node(dict(id=value['id'],label=value['label'],desc=value['desc'],refs=value['refs']))
    if family=='hierarchy':
        fields(data,('root',));node(data['root'],children=True)
        if not data['root'].get('children'): raise ValueError('Hierarchy requires branches')
    elif family=='grouped':
        fields(data,('groups',));nodes(data['groups'],children=True)
        if any(not g.get('children') for g in data['groups']): raise ValueError('Grouped hierarchy requires subcomponents')
        def depth_of(n): return 1+max((depth_of(c) for c in n.get('children',[])),default=0)
        if any(depth_of(g)>3 for g in data['groups']): raise ValueError('A3 native mapping supports at most three levels')
    elif family in {'list','sequence'}:
        fields(data,REGISTRY[code].required);nodes(data['items'],extras=('time',) if code=='B3' else ())
        if family=='sequence': text(data['order_basis'],240)
        if code=='B2': refs(data['cycle_refs'])
        if code=='B3':
            for item in data['items']: text(item.get('time'),80)
    elif family=='graph':
        fields(data,('nodes','relations'));nodes(data['nodes']);endpoints=set(ids)
        if not isinstance(data['relations'],list) or not data['relations']: raise ValueError('Graph relationships required')
        for value in data['relations']: relation(value,endpoints)
    elif family=='interaction':
        fields(data,('actors','actions','relations'));nodes(data['actors']);actors=set(ids)
        nodes(data['actions'],extras=('actor','step'))
        steps=[];actions=set()
        for value in data['actions']:
            if value.get('actor') not in actors or type(value.get('step')) is not int or value['step']<0: raise ValueError('Invalid action order/actor')
            steps.append(value['step']);actions.add(value['id'])
        if steps!=sorted(steps): raise ValueError('Actions must retain chronological order')
        if not isinstance(data['relations'],list): raise ValueError('Invalid interaction relations')
        for value in data['relations']: relation(value,actions)
    elif family=='comparison':
        fields(data,REGISTRY[code].required);nodes(data['groups'],children=True)
        if len(data['groups'])!=(2 if code=='C1' else 4): raise ValueError('Incorrect comparison group count')
        if any(not g.get('children') for g in data['groups']): raise ValueError('Comparison attributes required')
        if any(c.get('children') for g in data['groups'] for c in g['children']): raise ValueError('Comparison supports entity and attribute levels')
        if code=='C1' and len({len(g['children']) for g in data['groups']})!=1: raise ValueError('Binary attributes must correspond')
        if code=='C1' and [v['label'].casefold() for v in data['groups'][0]['children']]!=[v['label'].casefold() for v in data['groups'][1]['children']]:raise ValueError('Binary attribute labels must correspond')
        if code=='C2':
            if not isinstance(data['dimensions'],list) or len(data['dimensions'])!=2: raise ValueError('Two quadrant dimensions required')
            for d in data['dimensions']:
                fields(d,('label','low','high','refs'));refs(d['refs'])
                for key in ('label','low','high'):text(d[key],100)
                if d['low'].casefold()==d['high'].casefold():raise ValueError('Quadrant dimension poles must differ')
            if data['dimensions'][0]['label'].casefold()==data['dimensions'][1]['label'].casefold():raise ValueError('Quadrant dimensions must differ')
    else:
        fields(data,REGISTRY[code].required)
        if not isinstance(data['unit'],str) or len(data['unit'])>80: raise ValueError('Invalid unit')
        nodes(data['values'],extras=('value',));numbers=[]
        for value in data['values']:
            literal=value.get('value')
            if not isinstance(literal,str) or not re.fullmatch(r'-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?',literal): raise ValueError('Numbers require exact decimal text')
            number=Decimal(literal)
            if not number.is_finite() or not float('-inf')<float(number)<float('inf'): raise ValueError('Nonfinite numeric value')
            if number!=0 and float(number)==0:raise ValueError('Numeric value underflows native double geometry')
            original=refs(value['refs'])
            if not re.search(r'(?<![\d.])'+re.escape(literal)+r'(?![\d.])',original): raise ValueError('Numerical literal absent from cited source')
            if data['unit'] and data['unit'] not in original: raise ValueError('Unit absent from cited source')
            numbers.append(number)
        if code=='C4':text(data['order_basis'],240)
        if code=='C5':
            text(data['whole'],160);refs(data['whole_refs']);refs(data['exclusive_refs'])
            if min(numbers)<0 or sum(numbers)<=0: raise ValueError('Invalid part-to-whole values')
    support=record['support']
    if not isinstance(support,list) or len(support)>max_items: raise ValueError('Invalid support list')
    support_ids=set()
    for item in support:
        fields(item,('id','item_id','kind','text','refs'))
        if item['item_id'] not in ids or item['kind'] not in {'explanation','example','derivation','code','qualification','table','formula'}: raise ValueError('Invalid support association')
        if not isinstance(item['id'],str) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]{0,59}',item['id']) or item['id'] in ids|support_ids: raise ValueError('Invalid support ID')
        support_ids.add(item['id']);text(item['text'],8000);original=refs(item['refs'])
        if item['kind']=='formula' and item['text'] not in original: raise ValueError('Exact formula absent from source')
    return record


def parse_batch(raw,requests,category,**limits):
    value=strict_json(raw)
    fields(value,('records',))
    if not isinstance(value['records'],list) or len(value['records'])!=len(requests): raise ValueError('Missing/extra batch records')
    seen=set();result=[]
    for record in value['records']:
        identifier=record.get('segment_id') if isinstance(record,dict) else None
        if not isinstance(identifier,str) or identifier not in requests or identifier in seen: raise ValueError('Unknown/duplicate segment')
        seen.add(identifier)
        result.append(validate_record(record,identifier,category,requests[identifier],**limits))
    return result
