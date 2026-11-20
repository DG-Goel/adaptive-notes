"""Import the actual browser export into synthetic-only audit directories."""
import json
from pathlib import Path
from copy import deepcopy
from app.models.knowledge import KnowledgeDocument
from app.models.source import SourceDocument
from app.evaluation.semantic_review import build_review_inventory,resolve_reviews,verify_history
from import_semantic_reviews import import_reviews

P=Path('data/output/task9_review_pilot_20261109')
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(name,x):(P/name).write_text(json.dumps(x,indent=2),encoding='utf-8')
kp=P/'transport_fixture_knowledge.json';sp=P/'transport_fixture_source.json';export=P/'browser_transport_export.json'
actual=read(export)
assert len(actual)==1 and actual[0]['reviewer_kind']=='assistant' and actual[0]['status']=='INCONCLUSIVE'
round1=import_reviews(kp,sp,export,P/'transport_import_round1')
history_path=P/'transport_import_round1/decision_history.json'
round2=import_reviews(kp,sp,export,P/'transport_import_replay',history_path)
assert len(round1['review_history'])==len(round2['review_history'])==1
assert round1['review_history']==round2['review_history']
verify_history(round2['review_history'])
cases=[]
for name in ('wrong_source','bad_status','missing_reviewer','missing_rationale','partial_members','not_a_list','broken_json'):
    data=deepcopy(actual)
    if name=='wrong_source':data[0]['source_version']='stale'
    if name=='bad_status':data[0]['status']='VERIFIED'
    if name=='missing_reviewer':data[0]['reviewer']=''
    if name=='missing_rationale':data[0]['rationale']=' '
    if name=='partial_members':data[0]['members']=data[0]['members'][:1]
    if name=='not_a_list':data={'decisions':data}
    path=P/('invalid_'+name+'.json');path.write_text('{' if name=='broken_json' else json.dumps(data),encoding='utf-8')
    output=P/('rejected_'+name)
    try:import_reviews(kp,sp,path,output,history_path)
    except ValueError as exc:
        assert not output.exists()
        cases.append(dict(case=name,rejected=True,error_type=type(exc).__name__,no_output_written=True))
    else:raise AssertionError('Invalid import accepted: '+name)
source=SourceDocument.model_validate(read(sp));source.source_units[0].text+=' An additional source qualification changes the version.'
knowledge=KnowledgeDocument.model_validate(read(kp))
changed=resolve_reviews(build_review_inventory(knowledge,source),round1['review_history'])
assert len(changed['invalidated_decisions'])==1
assert not any(r['semantic_status']=='SUPPORTED' for r in changed['inventory'])
report=dict(scope='SYNTHETIC TRANSPORT TEST ONLY; no real pilot decision import',
    browser_export_records=1,import_roundtrip_passed=True,replayed_history_records=1,
    history_preserved=True,invalid_files=cases,source_change_invalidated_records=1,
    actual_pilot_decisions=0,human_decisions_created=0,unexpected_import_errors=0)
write('transport_validation.json',report)
print(json.dumps(report))
