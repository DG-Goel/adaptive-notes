"""Original synthetic educational examples; expected payloads are not model-quality evidence."""
from .template_registry import REGISTRY


def fixture(code):
    def node(id,label,desc='Concise source-grounded explanation',**extra):
        return dict(id=id,label=label,desc=desc,refs=['p0'],**extra)
    family=REGISTRY[code].family
    sources={
      'A1':'A cell contains a membrane and cytoplasm. The membrane encloses the cytoplasm; these are related aspects of cell organization.',
      'A2':'Vertebrates include mammals and birds. Mammals and birds are distinct classifications within vertebrates.',
      'A3':'A computing system includes a processor group and a storage group. Processor components include a control unit; storage includes memory.',
      'A4':'A queue preserves insertion order. A stack removes the most recently inserted item. These are separate definitions.',
      'A5':'A network protocol stack has an application level above a transport level. The levels have a meaningful conceptual order.',
      'B1':'First load a document, then divide its text into passages. Preserve the original document while preparing passages.',
      'B2':'Water evaporates, then condenses, then returns as precipitation. Evaporation begins the cycle again; the process repeats.',
      'B3':'In 2020 the pilot began. In 2021 the evaluation began. These events occurred in that chronological order.',
      'B4':'A successful validation permits storage. If validation fails, storage must not occur. Validation therefore precedes and controls storage.',
      'B5':'The client sends a request to the server. The server receives it and sends a response back to the client in that order.',
      'C1':'Steel has high density and aluminum has lower density. Density is a comparable attribute for both materials.',
      'C2':'Classify projects by cost (low or high) and risk (low or high). The four groups are low cost/low risk, high cost/low risk, high cost/high risk and low cost/high risk.',
      'C3':'Sample A has mass 2.00 kg. Sample B has mass 3.00 kg. Both masses are measured in kg and are comparable.',
      'C4':'At the first observation the mass was 2.00 kg; at the second observation it was 3.00 kg. The observations are ordered, with kg as the shared unit.',
      'C5':'A 5.00 kg mixture consists of mutually exclusive components: material A is 2.00 kg and material B is 3.00 kg. The two components form the whole mixture.',
    }
    if family=='hierarchy':
        labels=('Cell','Membrane','Cytoplasm') if code=='A1' else ('Vertebrates','Mammals','Birds')
        data=dict(root=node('root',labels[0],children=[node('a',labels[1]),node('b',labels[2])]))
    elif family=='grouped':data=dict(groups=[node('a','Processor group',children=[node('b','Control unit')]),node('c','Storage group',children=[node('d','Memory')])])
    elif family=='list':data=dict(items=[node('a','Queue','Preserves insertion order'),node('b','Stack','Removes the newest item first')])
    elif family=='sequence':
        labels={'A5':['Application','Transport'],'B1':['Load document','Divide into passages'],'B2':['Evaporation','Condensation','Precipitation'],'B3':['Pilot begins','Evaluation begins']}[code]
        data=dict(items=[node('n'+str(i),label,**({'time':str(2020+i)} if code=='B3' else {})) for i,label in enumerate(labels)],order_basis='Source-established conceptual or chronological order')
        if code=='B2':data['cycle_refs']=['p0']
    elif family=='graph':data=dict(nodes=[node('a','Validation'),node('b','Storage')],relations=[dict(id='r',**{'from':'a','to':'b'},label='Permits',desc='Only successful validation permits storage',refs=['p0'])])
    elif family=='interaction':data=dict(actors=[node('client','Client'),node('server','Server')],actions=[node('a','Request',actor='client',step=0),node('b','Response',actor='server',step=1)],relations=[dict(id='r',**{'from':'a','to':'b'},label='Reply',desc='The response follows the request',refs=['p0'])])
    elif family=='comparison':
        if code=='C1':data=dict(groups=[node('a','Steel',children=[node('a1','Density','High density')]),node('b','Aluminum',children=[node('b1','Density','Lower density')])])
        else:
            data=dict(groups=[node('q'+str(i),label,children=[node('c'+str(i),'Classification',label)]) for i,label in enumerate(['Low cost / low risk','High cost / low risk','High cost / high risk','Low cost / high risk'])],dimensions=[dict(label='Cost',low='low',high='high',refs=['p0']),dict(label='Risk',low='low',high='high',refs=['p0'])])
    else:
        data=dict(values=[node('a','Sample A','Measured mass',value='2.00'),node('b','Sample B','Measured mass',value='3.00')],unit='kg')
        if code=='C4':data['order_basis']='First observation, then second observation'
        if code=='C5':data.update(whole='Mixture',whole_refs=['p0'],exclusive_refs=['p0'])
    return dict(code=code,source=sources[code],record=dict(segment_id='g0',status='generated',type=code,title=REGISTRY[code].purpose,data=data,support=[]),
        unsuitable_source='This passage supplies neither the relationships nor the measurements required for '+REGISTRY[code].purpose,
        unsuitable_expected_status='unsupported')


def fixtures():return [fixture(code) for code in REGISTRY]
