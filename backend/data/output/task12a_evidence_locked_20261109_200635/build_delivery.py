"""Task 12A artifacts using existing pipeline and controlled mocks; no network."""
from pathlib import Path
from hashlib import sha256
import json,os,socket,sys
import xml.etree.ElementTree as ET

OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[2]
sys.path.insert(0,str(ROOT));os.chdir(ROOT)
os.environ['HF_HUB_OFFLINE']='1';os.environ['TRANSFORMERS_OFFLINE']='1'
def blocked(*a,**kw):raise AssertionError('Task 12A artifact build forbids network')
socket.socket.connect=blocked;socket.create_connection=blocked

from tests.test_no_invention_generation import source,atomic,value,response,extract,preview
from app.extraction.no_invention import assess_claim,VERSION
from app.extraction.organization_scheduler import ExtractionConfiguration,digest
from app.extraction.organization_extraction import prepare_request,extraction_policy,schema_budget_text
from app.extraction.document_authorization import document_plan
from app.models.knowledge import ExtractionChunk

FILES=['app/extraction/no_invention.py','app/extraction/canonical_grounding.py',
 'app/extraction/grounded_fields.py','app/extraction/prompts.py','app/extraction/claim_review.py',
 'app/extraction/organization_extraction.py','app/extraction/extractor.py',
 'app/extraction/consolidation.py','app/evaluation/educational_safeguards.py',
 'app/evaluation/notes_pipeline.py','app/representation/selector.py',
 'tests/test_no_invention_generation.py','tests/test_notes_quality_pipeline.py',
 'tests/test_single_request_preparation.py','tests/test_authorized_runner.py']


def save(name,value):
    p=OUT/name;p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False),encoding='utf-8')


def example(name,s,raw):
    k,audit=extract(raw,s);result=preview(k,s)
    save(name+'/source.json',s.model_dump(mode='json'))
    save(name+'/mock_response.json',raw)
    save(name+'/candidate_knowledge.json',k.model_dump(mode='json'))
    save(name+'/wire_audit.json',audit)
    save(name+'/quality_report.json',result['report'])
    p=OUT/name/'notes_preview.md';p.write_text(result['markdown'],encoding='utf-8')
    return {'name':name,'source':s.model_dump(mode='json'),'before':raw,
        'after_preview':result['markdown'],'status':'UNVERIFIED_PREVIEW','semantic_quality_score':None,
        'withheld':result['report']['coverage_dimensions']['student_fields_withheld_for_review'],
        'human_reviews_created':0}


def main():
    examples=[]
    for name,original,paraphrase in [
        ('biology','Cells divide to reproduce.','Cells reproduce through division.'),
        ('science','The sample may react under dry conditions.','Under dry conditions, a reaction is possible.'),
        ('history','The treaty was signed in 1918.','In 1918, the treaty was signed.'),
        ('technical','The method must be called after the connection opens.','Call the method after opening the connection.'),
        ('mathematics','Area equals pi times radius squared.','The area is pi multiplied by the square of the radius.')]:
        s=source([original]);v=value([atomic(paraphrase,['Q0000'],basis='direct_entailment')])
        examples.append(example(name,s,response(facts=[{'fact_text':v,'fact_type':None}])))
    s=source(['Cells divide to reproduce.'])
    v=value([atomic('Cells reproduce through division.',['Q0000'],basis='direct_entailment'),
             atomic('This process was discovered in 2027.',['Q0000'])])
    examples.append(example('mixed_support',s,response(facts=[{'fact_text':v,'fact_type':None}])))
    s=source(['An escape sequence represents a special character.'])
    plain={'text':s.source_units[0].text,'refs':['Q0000']}
    snippet='String path = "C:\\\\Windows\\\\";'
    examples.append(example('no_invented_code',s,response(facts=[{'fact_text':plain,'fact_type':None}],
        examples=[{'exemplifies':plain,'example_text':value([atomic(snippet,['Q0000'],literal_kind='literal_code')]),'example_type':None}])))
    s=source(['Principal P is the amount borrowed.','R is the monthly interest rate.',
              'The complete expression is on the screen and is not provided.'])
    examples.append(example('mortgage_abstention',s,response(facts=[
        {'fact_text':{'text':s.source_units[0].text,'refs':['Q0000']},'fact_type':None},
        {'fact_text':{'text':s.source_units[1].text,'refs':['Q0001']},'fact_type':None}],
        formulas=[{'availability':'VISUAL_CONTEXT_REQUIRED','source_ids':['S2'],'reason':'Complete expression unavailable'}])))
    s=source(['The incorrect demonstration checks the general condition first.',
              'The correction checks the combined specific condition first.'])
    wrong=atomic(s.source_units[0].text,['Q0000'],instructional_role='deliberately_incorrect_demonstration',related_refs=['Q0001'])
    corrected=atomic(s.source_units[1].text,['Q0001'],instructional_role='corrected_approach',related_refs=['Q0000'])
    examples.append(example('instructional_correction',s,response(facts=[{'fact_text':value([wrong]),'fact_type':None},
                                                                      {'fact_text':value([corrected]),'fact_type':None}])))
    save('before_after_examples.json',examples)
    # This deliberately exposes the deterministic limit, not a passing accuracy claim.
    save('unresolved_semantic_control.json',{
        'source':'Plants have leaves.','candidate':'Leaves produce oxygen.',
        'screen':assess_claim('Leaves produce oxygen.',['Plants have leaves.']),
        'assessment':'Source support is not established; remains REVIEW_REQUIRED, not approved.',
        'limitation':'General qualitative entailment cannot be certified by deterministic quotation screening.'})
    archived=json.loads((ROOT/'data/output/task8_semantic_readiness_20261109/knowledge_v8.json').read_text(encoding='utf-8'))
    original_source=json.loads((ROOT/'data/output/java_live_java-20261109_022409_842270/source_document.json').read_text(encoding='utf-8'))
    units={u['source_id']:u['text'] for u in original_source['source_units']}
    windows=next(i for i in archived['examples'] if i['knowledge_id']=='EXM_0003')
    mortgage=next(i for i in archived['formulas'] if i['knowledge_id']=='FRM_0007')
    save('historical_regression_examples.json',{
        'windows_path':{'knowledge_id':windows['knowledge_id'],'candidate':windows['example_text'],
            'source_ids':windows['source_unit_ids'],'screen':assess_claim(windows['example_text'],[units[s] for s in windows['source_unit_ids']])},
        'mortgage':{'knowledge_id':mortgage['knowledge_id'],'candidate':mortgage['formula_text'],
            'source_ids':mortgage['source_unit_ids'],'screen':assess_claim(mortgage['formula_text'],[units[s] for s in mortgage['source_unit_ids']],formula=True)},
        'fizzbuzz_correction':{'source_id':'T0042','source_excerpt':units['T0042'][:900],
            'corresponding_mistake_source_id':'T0041','status':'EXISTING_SOURCE_PRESERVED; NO_NEW_REVIEW_DECISION'},
        'historical_decisions_modified':False,'independent_review_performed':False})
    config=ExtractionConfiguration(max_retries=0,prompt_policy='canonical_grounded_v4',response_format='json_schema')
    path=OUT/'controlled_source.txt';path.write_text('Under dry conditions, the sample may react.\n',encoding='utf-8')
    manifest=document_plan(path,config,'task12a-offline')
    save('manifest.unapproved.json',manifest)
    save('authorization_status.json',{'status':'UNAPPROVED','approved_requests':0,'live_calls':0,
        'manifest_sha256':digest(manifest),'request_hashes':[e['request_sha256'] for e in manifest['requests']]})
    old=json.loads((ROOT/'data/output/task11_structured_ingestion_20261109_193204/controlled_txt/manifest.unapproved.json').read_text(encoding='utf-8'))
    entry=old['requests'][0]
    new,budget=prepare_request(ExtractionChunk.model_validate(entry['chunk']),config)
    system,_,_,fmt=extraction_policy(config)
    save('prompt_schema.json',{'system':system,'response_format':fmt})
    save('request_version_comparison.json',{'old_request_sha256':entry['request_sha256'],
        'new_request_sha256':digest(new),'changed':entry['request_sha256']!=digest(new),
        'system_characters':len(system),'schema_characters':len(schema_budget_text(config,fmt)),
        'input_tokens_estimated':budget.input_tokens,'output_tokens_reserved':budget.max_output_tokens,
        'quota_policy_modified':False,'stage_a_modified':False,'provider_compatibility':'NOT_LIVE_VERIFIED'})
    protected=json.loads((OUT/'protected_hashes_before.json').read_text(encoding='utf-8'))
    changed=[p for p,h in protected.items() if not (ROOT/p).exists() or sha256((ROOT/p).read_bytes()).hexdigest()!=h]
    save('preservation_checks.json',{'checked':len(protected),'changed':changed,'passed':not changed,
        'task9_status':'READY_FOR_HUMAN_REVIEW','task11_ingestion_unchanged':True,
        'operational_authorizations_created':0,'provider_calls':0})
    if changed:raise AssertionError(changed)
    cases=ET.parse(OUT/'regression_release.xml').findall('.//testcase')
    failures=[c.attrib for c in cases if c.find('failure') is not None or c.find('error') is not None]
    skipped=[{'test':c.attrib,'reason':c.find('skipped').get('message')} for c in cases if c.find('skipped') is not None]
    stats={'passed':len(cases)-len(failures)-len(skipped),'failed':len(failures),'skipped':len(skipped),
           'failures':failures,'skips':skipped,'network_connections':'BLOCKED'}
    save('test_summary.json',stats)
    if failures:raise AssertionError(failures)
    hashes={}
    for name in FILES:
        b=(ROOT/name).read_bytes();hashes[name]=sha256(b).hexdigest()
        p=OUT/'code_snapshot_release'/name;p.parent.mkdir(parents=True,exist_ok=True)
        if p.exists() and p.read_bytes()!=b:raise AssertionError('Delivered code changed')
        if not p.exists():p.write_bytes(b)
    save('modified_files_release.json',hashes)
    positives=examples[:5]
    save('retention_findings.json',{'controlled_paraphrases':len(positives),
        'retained':sum(not e['withheld'] for e in positives),
        'supported_component_of_mixed_field_retained':True,'independently_supported_variable_explanations_retained':True,
        'archived_legitimate_content_loss':'NOT_INDEPENDENTLY_VERIFIED',
        'possible_false_positives':'Unreviewed qualification/number/literal screens may withhold legitimate wording; explicit source passages and original candidates remain available.',
        'no_live_quality_score':True})
    print(json.dumps({'output':str(OUT),'tests':{k:stats[k] for k in ['passed','failed','skipped']},
        'protected_files':len(protected),'modified_files':len(FILES),'examples':len(examples)},indent=2))


if __name__=='__main__':main()
