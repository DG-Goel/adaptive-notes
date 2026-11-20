"""Task 9: deterministic human-review package; creates no semantic decisions."""
import json
from pathlib import Path
from collections import Counter
from hashlib import sha256
from copy import deepcopy
from app.models.source import SourceDocument,SourceUnit
from app.models.knowledge import KnowledgeDocument,Fact
from app.models.educational_review import EducationalReview,FieldReview
from app.evaluation.semantic_review import build_review_inventory,resolve_reviews,fingerprint
from app.evaluation.review_outputs import evidence_desk_html

P=Path('data/output/task9_review_pilot_20261109');B=Path('data/output/task8_semantic_readiness_20261109')
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(name,v):(P/name).write_text(json.dumps(v,indent=2,ensure_ascii=False),encoding='utf-8')
def digest(p):return sha256(p.read_bytes()).hexdigest()
paths={Path(p) for p in read(B/'preservation_before.json')}
paths|={p for p in B.rglob('*') if p.is_file()}
if not (P/'preservation_before.json').exists():write('preservation_before.json',{str(p):digest(p) for p in sorted(paths)})
w=read(B/'review_workspace.json');summary=read(B/'summary.json')
manifest8=read(B/'artifact_manifest.json')['artifacts']
for name in ('review_workspace.json','review_input_knowledge.json','knowledge_v8.json','decision_history.json'):
    assert digest(B/name)==manifest8[name]
index={r['key']:r for r in w['inventory']};packets={p['packet_id']:p for p in w['packets']}
seed='Task9-independent-human-pilot-20261109-v1';selected={}
def add(key,category,reason):
    row=index[key];p=row['packet_id']
    selection=selected.setdefault(p,dict(packet_id=p,reasons=[],categories=[],members=packets[p]['members']))
    selection['reasons'].append(reason)
    if category not in selection['categories']:selection['categories'].append(category)

mandatory=[
('FRM_0007:/content','incomplete_visual_formula','Unresolved mortgage equation and repaired multi-source context; keep visual limitation.'),
('FCT_0252:/content','source_factual_uncertainty','Transcript factual assertion still inconclusive; quote matching is insufficient.'),
('DEF_0060:/content','source_overgeneralization','Universal new-object claim remains only partially supported.'),
('EXM_0003:/content','nonliteral_code','Known reconstructed code with preserved adverse disposition.'),
('EXM_0174:/content','incorrect_demonstration','Check that the intentionally incorrect output is not taught as the correct rule.'),
('EXP_0127:/content','explanation_and_correction','Check the explanation of the earlier conditional branch error.'),
('PRC_0397:/steps/3','multi_source_procedure','Check the combined-condition correction and explicit T0042 support.'),
('FRM_0014:/content','mathematical_expression','Source expression and multiplication precedence.'),
('FRM_0015:/content','mathematical_expression','Contrasting parenthesized arithmetic; do not conflate results.'),
('FCT_5005:/content','recovered_qualification','Recovered package convention with no-registration qualification.'),
('FCT_5011:/content','recovered_educational_content','Recovered zero-execution versus at-least-once condition timing.'),
('PRC_5001:/steps/3','recovered_procedure','Additional Task 8 source-backed construction sequence.'),
('FCT_0352:/content','conditions_and_qualifications','Nested-conditional advice must retain its scoped trade-off.'),
('FCT_0361:/content','conditions_and_qualifications','Counting example must not become a universal counter requirement.'),
('EXP_0133:/content','general_explanation','Distinguish reference comparison from comparison of textual values.'),
('FCT_0213:/content','numeric_source_claim','Unreviewed numeric/range assertion; requires careful source and technical assessment.')]
for args in mandatory:add(*args)
fragment_rows=[r for r in read(B/'draft_retention.json') if r['disposition']=='PARTIALLY_WITHHELD_MARKER']
assert fragment_rows
add(sorted(fragment_rows,key=lambda r:r['key'])[0]['key'],'embedded_code_fidelity','Literal code also occurs inside procedure prose; verify fragment withholding and retained instructions.')

# Fill with unresolved bundles only, stratifying across all available knowledge types.
rank=lambda p:fingerprint(dict(seed=seed,packet_id=p))
unresolved={r['packet_id'] for r in w['inventory'] if r['semantic_status']=='NOT_REVIEWED'}-selected.keys()
for kind in sorted({r['knowledge_type'] for r in w['inventory']}):
    candidates=sorted({r['packet_id'] for r in w['inventory'] if r['knowledge_type']==kind}&unresolved,key=rank)
    if candidates:
        p=candidates[0];add(packets[p]['members'][0],'stratified_unreviewed_'+kind,'Precommitted hash-ranked draw from unreviewed '+kind+' bundles.')
        unresolved.discard(p)
for p in sorted(unresolved,key=rank):
    if len(selected)>=30:break
    add(packets[p]['members'][0],'representative_unreviewed','Hash-ranked unreviewed fill; no semantic judgment used for selection.')
assert len(selected)==30
chosen=sorted(selected,key=rank)
members={key for p in chosen for key in packets[p]['members']}
pilot=deepcopy(w);pilot['inventory']=[r for r in pilot['inventory'] if r['key'] in members]
pilot['packets']=[packets[p] for p in chosen];pilot['queue']=[q for q in pilot['queue'] if q['key'] in members]
pilot['review_session']=dict(title='30-bundle independent semantic-review pilot',status='AWAITING_HUMAN_REVIEW',
    notice='Existing dispositions are historical assistant source comparisons. They are not completed independent pilot judgments.')
pilot['counts']=dict(fields=len(members),exact_evidence_bundles=30,atomic_factual_claim_count=None)
selection=dict(seed=seed,source_version=w['source_version'],knowledge_version=w['knowledge_version'],
    baseline_workspace_sha256=digest(B/'review_workspace.json'),population_bundles=len(packets),
    selection_method='17 predeclared difficult/category cases (deduplicated by packet), one hash-ranked unreviewed draw per knowledge category, then hash-ranked unreviewed fill to 30. Purposeful pilot, not a population accuracy estimator.',
    boundaries='One real regression document, saved canonical source and Task 8 evidence scopes. All original packet members travel together; no automatic atomic claim splitting.',
    pilot_status='AWAITING_INDEPENDENT_HUMAN_REVIEW',reviewer_preference='Prepare for a human reviewer later, as explicitly chosen by the user.',
    bundles=[dict(rank=n+1,**selected[p]) for n,p in enumerate(chosen)],fields=len(members),atomic_claim_count=None,
    current_field_statuses=dict(Counter(r['semantic_status'] for r in pilot['inventory'])),
    knowledge_categories=dict(Counter(r['knowledge_type'] for r in pilot['inventory'])),
    critical_categories_covered=sorted({c for d in selected.values() for c in d['categories']}),
    independent_decisions_completed=0,quality_score=None)
write('pilot_selection_manifest.json',selection);write('pilot_workspace.json',pilot)
write('pilot_evidence_packets.json',[packets[p] for p in chosen]);write('independent_pilot_decisions.json',[])
(P/'pilot_desk.html').write_text(evidence_desk_html(pilot),encoding='utf-8')
(P/'baseline_desk.html').write_bytes((B/'evidence_desk.html').read_bytes())
write('pilot_decision_template.json',[dict(packet_id=p,binding=packets[p]['binding'],source_version=w['source_version'],
    members=packets[p]['members'],status=None,reviewer=None,reviewer_kind=None,reviewed_at=None,rationale=None,
    review_scope='entire_field_bundle',qualifications_checked=False,evidence_checked=False,
    factual_verification='not_established') for p in chosen])

# Strictly synthetic data for browser transport controls; never a real pilot judgment.
source=SourceDocument(document_id='TRANSPORT_TEST',filename='synthetic-review-control',page_count=0,source_units=[
    SourceUnit(source_id='S1',document_id='TRANSPORT_TEST',type='paragraph',position=0,text='Synthetic control: a sample may react only under dry conditions.'),
    SourceUnit(source_id='S2',document_id='TRANSPORT_TEST',type='paragraph',position=1,text='Synthetic context: a wet sample is excluded.')])
fact=Fact(knowledge_id='FCT_TEST',document_id=source.document_id,source_unit_ids=['S1'],
    content=source.source_units[0].text,fact_text=source.source_units[0].text,
    extraction_metadata=dict(primary_source_ids=['S1'],source_grounding=dict(mechanically_valid=True,evidence=[
        dict(source_id='S1',quote=source.source_units[0].text,fields=['/content','/fact_text'])])))
missing=Fact(knowledge_id='FCT_MISSING',document_id=source.document_id,source_unit_ids=['S1'],
    content='Synthetic unsupported association fixture.',fact_text='Synthetic unsupported association fixture.')
conflict=Fact(knowledge_id='FCT_CONFLICT',document_id=source.document_id,source_unit_ids=['S2'],
    content='A wet sample is included.',fact_text='A wet sample is included.',
    extraction_metadata=dict(primary_source_ids=['S2'],source_grounding=dict(evidence=[dict(source_id='S2',quote=source.source_units[1].text,fields=['/content','/fact_text'])])),
    educational_review=EducationalReview(field_reviews=[FieldReview(path=path,mode='contradicted',status='CONTRADICTED',
        reviewer='Synthetic fixture author; not a human review',rationale='Deliberately conflicting test text; verifies warning display only.',
        evidence=[dict(source_id='S2',quote=source.source_units[1].text)]) for path in ('/content','/fact_text')]))
knowledge=KnowledgeDocument(document_id=source.document_id,source_filename=source.filename,extraction_timestamp='synthetic transport fixture',facts=[fact,missing,conflict])
fixture_input=build_review_inventory(knowledge,source)
fixture_pin=dict(source_version=fixture_input['source_version'],field_bindings={r['key']:r['binding'] for r in fixture_input['inventory']},
    baseline_artifact='SYNTHETIC FIXTURE ONLY',baseline_sha256='synthetic',imported_at=None)
fixture=resolve_reviews(fixture_input,[],legacy_pin=fixture_pin)
fixture['review_session']=dict(title='Synthetic transport test desk',status='TEST_FIXTURE_ONLY',notice='No real pilot judgments are recorded here.')
write('transport_fixture_source.json',source.model_dump(mode='json'));write('transport_fixture_knowledge.json',knowledge.model_dump(mode='json'))
write('transport_fixture_workspace.json',fixture)
(P/'transport_fixture_desk.html').write_text(evidence_desk_html(fixture),encoding='utf-8')
accounting=dict(original_items=458,task7_recoveries=11,task8_additional_recovery=dict(item_id='PRC_5001',origin='offline_source_review',
    source_ids=['T0045'],fields=6,provenance_file=str(B/'changes.json')),total_items=458+11+1,
    total_fields=len(w['inventory']),total_bundles=len(w['packets']),atomic_claim_count=None,
    unreviewed_fields=sum(r['semantic_status']=='NOT_REVIEWED' for r in w['inventory']),
    reviewed_note_item_ids=sum(bool(m['displayed_paths']) or bool(m['equivalent_content_of']) for m in read(B/'reviewed_retention.json')),
    reviewed_displayed_fields=sum(len(m['displayed_paths']) for m in read(B/'reviewed_retention.json')),
    supported_field_dispositions=sum(r['semantic_status']=='SUPPORTED' for r in w['inventory']),
    fully_supported_item_schemas=sum(all(r['semantic_status']=='SUPPORTED' for r in w['inventory'] if r['item_id']==i)
        for i in {r['item_id'] for r in w['inventory']}),
    note='Item presence, partial field retention, field dispositions, exact-evidence bundles and atomic factual claims are different measures.')
assert accounting['total_items']==470 and accounting['total_fields']==1265 and accounting['total_bundles']==849 and accounting['unreviewed_fields']==1066 and accounting['reviewed_note_item_ids']==46
write('accounting.json',accounting)
print(json.dumps(dict(pilot_bundles=30,fields=len(members),accounting=accounting)))
