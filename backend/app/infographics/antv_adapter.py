"""Native config mapping only: no DSL, code execution, resource URLs or rendering."""
from .template_registry import REGISTRY,ANTV_VERSION
from .source_index import digest

ADAPTER_VERSION='noetra-antv-native-v1'


def convert(record,visual_id):
    template=REGISTRY[record['type']]; data=record['data']; mapping={}; references={}
    def identifier(local):
        if local not in mapping: mapping[local]=visual_id+'-'+digest(local.encode())[:12]
        return mapping[local]
    def item(value,fold=False):
        result=dict(id=identifier(value['id']),label=value['label']+(': '+value['desc'] if fold else ''),desc=value['desc'])
        references[result['id']]=value['refs']
        if 'children' in value: result['children']=[item(child,fold) for child in value['children']]
        if 'time' in value: result['label']=value['time']+' — '+result['label']
        return result
    def relation(value):
        identifier(value['id']);references[mapping[value['id']]]=value['refs']
        return dict(id=mapping[value['id']],**{'from':identifier(value['from']),'to':identifier(value['to'])},
                    label=value['label']+': '+value['desc'],direction='forward')
    native=dict(title=record['title'])
    family=template.family
    if family=='hierarchy': native['root']=item(data['root'])
    elif family=='grouped': native['items']=[item(v,True) for v in data['groups']]
    elif family in {'list','sequence'}:
        native['lists' if family=='list' else 'sequences']=[item(v) for v in data['items']]
        if family=='sequence': native['order']='asc';native['desc']=data['order_basis']
    elif family=='graph':
        native['nodes']=[item(v) for v in data['nodes']]
        native['relations']=[relation(v) for v in data['relations']]
    elif family=='interaction':
        lanes=[]
        for actor in data['actors']:
            lane=item(actor)
            lane['children']=[dict(item(action,True),step=action['step']) for action in data['actions'] if action['actor']==actor['id']]
            lanes.append(lane)
        native['items']=lanes;native['relations']=[relation(v) for v in data['relations']]
    elif family=='comparison':
        native['compares']=[item(v) for v in data['groups']]
        if 'dimensions' in data:
            native['desc']='; '.join(d['label']+': '+d['low']+' / '+d['high'] for d in data['dimensions'])
    else:
        values=[]
        for v in data['values']:
            value=item(v)
            # JS double precision is used only for geometry. Exact decimal text
            # remains visible and in the immutable intermediate artifact.
            value['value']=float(v['value'])
            value['label']+=' ('+v['value']+(' '+data['unit'] if data['unit'] else '')+')'
            values.append(value)
        native['values']=values
        native['desc']='; '.join(data[k] for k in ('unit','order_basis','whole') if k in data)
    return dict(version=ADAPTER_VERSION,antv_version=ANTV_VERSION,
        config=dict(template=template.antv,data=native,themeConfig=dict(colorPrimary='#1677ff')),
        item_id_mapping=mapping,source_references=references,rendering_verified=False)
