"""Real Java regression review inventory. No provider, credential or quota calls."""
import csv
import json
from collections import Counter
from datetime import datetime,timezone
from hashlib import sha256
from pathlib import Path
from app.models.knowledge import KnowledgeDocument,Procedure
from app.models.source import SourceDocument
from app.models.educational_review import EducationalReview
from app.evaluation.citation_repair import add_reviewed_evidence
from app.evaluation.semantic_review import build_review_inventory,append_decision,resolve_reviews
from app.evaluation.review_outputs import materialize_reviews,comprehensive_draft,coverage_report,evidence_desk_html
from app.evaluation.offline_recovery import reviewed_student_preview
from app.evaluation.notes_pipeline import build_preview

P=Path('data/output/task8_semantic_readiness_20261109')
B=Path('data/output/task7_educational_completeness_20261109')
R=Path('data/output/java_live_java-20261109_022409_842270')
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(name,value):(P/name).write_text(json.dumps(value,indent=2,ensure_ascii=False),encoding='utf-8')
def digest(p):return sha256(p.read_bytes()).hexdigest()
knowledge=KnowledgeDocument.model_validate(read(B/'knowledge_v7.json'))
source=SourceDocument.model_validate(read(R/'source_document.json'))
units={u.source_id:u for u in source.source_units}
items={i.knowledge_id:i for i in knowledge.get_all_items()}
relations=read(B/'duplicate_decisions.json')
pin=read(P/'legacy_provenance_pin.json')
assert digest(B/'knowledge_v7.json')==pin['baseline_sha256'] and digest(R/'source_document.json')==pin['source_sha256']
reviewer='assistant Task 8 source-comparison review; no independent human certification'
changes=[]
explanation=items['EXP_0127']
for path in ('/content','/explanation_text','/topic'):
    changes.append(add_reviewed_evidence(explanation,path,source,'T0041',units['T0041'].text,reviewer=reviewer,
        rationale='Bind the skipped-branch explanation to both the earlier condition order and observed 15 outcome within the same canonical source.'))
explanation.educational_review=EducationalReview(role='explanation_of_mistake',
    evidence=[dict(source_id='T0041',quote=units['T0041'].text)],reviewer=reviewer,
    rationale='The source explicitly diagnoses the deliberately incorrect demonstration; field approval is separately recorded.')

quote="we start with a do keyword then we create a code block at the end of this code block we type while followed by our loop condition so not input dot equals quit and then we terminate this using a semicolon now inside the body of this loop we'll simply copy all these lines we have here"
assert quote in units['T0045'].text
raw=dict(knowledge_id='PRC_5001',knowledge_type='procedure',document_id=source.document_id,
    source_unit_ids=['T0045'],section='Loop condition timing',
    content='The source constructs a do-while loop with its condition after the body.',
    procedure_name='Constructing a do-while loop',steps=[
        'Begin with do and define a code block.',
        'Place the repeated actions inside the block.',
        'After the block, write while followed by the loop condition.',
        'Terminate the do-while statement with a semicolon.'])
assert raw['knowledge_id'] not in items and set(raw)=={'knowledge_id','knowledge_type','document_id','source_unit_ids','section','content','procedure_name','steps'}
procedure=Procedure.model_validate(raw,strict=True)
paths=['/content','/procedure_name']+['/steps/'+str(n) for n in range(4)]
procedure.extraction_metadata=dict(origin='offline_source_review',provider_generated=False,
    primary_source_ids=['T0045'],context_source_ids=[],source_grounding=dict(evidence=[dict(source_id='T0045',quote=quote,fields=paths)]))
procedure.educational_review=EducationalReview(role='continuation',code_kind='verbal',
    reviewer=reviewer,rationale='Source-backed structural procedure; contains no reconstructed literal program.')
knowledge.procedures.append(procedure);knowledge.update_statistics();items[procedure.knowledge_id]=procedure
changes.append(dict(kind='offline_source_recovery',item_id=procedure.knowledge_id,source_id='T0045',quote=quote,
    provider_history_changed=False,reason='Task 7 timing contrast did not cover the source-stated do/body/while/semicolon construction sequence.'))

w=build_review_inventory(knowledge,source,duplicate_relations=relations,coverage_priority_ids=['T0004','T0045'])
samples=read(P/'sample_evidence_packets.json')
packet_index={p['packet_id']:p for p in w['packets']}
# Decisions below follow direct comparison of the saved exact claim and quotes.
# This is a bounded assistant review sample, not an estimate or independent audit.
findings=[
('SUPPORTED','The quoted 10 plus 3 times 2 expression places 3 second. This is an operand label, not a newly introduced algebraic variable.'),
('INCONCLUSIVE','P times R is only a prefix, and the legacy field review also cites T0033 without listing it in the item source scope. This packet cannot authorize that context. Hold the formula until the evidence association is repaired and reviewed again; the original visual is still missing.'),
('SUPPORTED','The explicitly quoted 10 plus 3 times 2 expression places 2 third.'),
('SUPPORTED','The quote explicitly says the parenthesized expression yields 13 and is then multiplied by 2.'),
('INCONCLUSIVE','This field quotation does not explicitly restate the operands inside the parentheses. Expand the field evidence before certifying this label; a mechanically valid reference alone is insufficient.'),
('INCONCLUSIVE','The cited passage does not explicitly mention operand 3 within the parenthesized addition. The complete expression is elsewhere, but this field association should be strengthened rather than silently inherited.'),
('SUPPORTED','The expression is explicitly introduced as 10 plus 3 times 2, placing 10 first.'),
('SUPPORTED','The source explicitly identifies P as principal or the amount of the loan. This component definition does not certify the incomplete mortgage equation.'),
('PARTIALLY_SUPPORTED','The quote identifies the get time method, but does not itself establish the receiver spelling and dot-call syntax in this generated statement. Keep the statement out of the reviewed subset pending fuller field evidence.'),
('SUPPORTED','The source explicitly describes a user entering values that are echoed. Reading user input is a faithful high-level procedure step; no input API or exact code is invented.'),
('PARTIALLY_SUPPORTED','The excerpt supports avoiding repeated printing, but stops before explaining loops and does not establish the added or-other-constructs generalization. Neighbor context remains context-only.'),
('INCONCLUSIVE','The quote calls min straightforward without stating that it returns the smaller value. Do not certify its mathematical behavior from the name or similarity to max.'),
('SUPPORTED','The source explicitly uses immutable for strings and explains that the original cannot be changed. This term review does not certify every detail of the associated definition.'),
('SUPPORTED','The quoted source explicitly introduces if statements in Java. This is a topic label rather than one independently counted factual assertion.'),
('SUPPORTED','The source explicitly defines R as the monthly interest rate. The full equation remains incomplete.'),
('SUPPORTED','The source explicitly introduces the parse int method of the integer wrapper class. This approves the concept label, not unreviewed details or examples.'),
('PARTIALLY_SUPPORTED','The quote supports chaining format on a returned NumberFormat object without an intermediate stored variable, but does not identify getPercentInstance in this field excerpt.'),
('SUPPORTED','The source explicitly describes the tutorial main method as public, static, void and having a parameter used to pass values. Review is scoped to that main-method definition, not all program entry mechanisms.'),
('SUPPORTED','The source explicitly says boolean values can be true or false.'),
('PARTIALLY_SUPPORTED','Accessing object members with dot is explicit. This selected quotation does not itself distinguish the fields-or-methods taxonomy. Keep the fuller generated definition pending a stronger association.'),
('PARTIALLY_SUPPORTED','Rounding, overloading and the float input are stated, but the excerpt ends at returns an before the claimed int return type. Missing text cannot be supplied merely from background knowledge.'),
('SUPPORTED','The quote explicitly restricts this integer variable to whole numbers without a decimal point; the statement adds no unsupported range or sign rule.'),
('PARTIALLY_SUPPORTED','The source describes the intended quit loop, then says the initial string-comparison code will not work. The generated procedure summary omits this implementation qualification; corrected T0045 knowledge is separately reviewed.'),
('SUPPORTED','The source explicitly says void is a reserved keyword used when a function returns no value.')]

inputs=[];sample_results=[]
def add(packet,status,rationale,scope):
    inputs.append(dict(packet_id=packet['packet_id'],binding=packet['binding'],source_version=w['source_version'],members=packet['members'],
        status=status,reviewer=reviewer,reviewer_kind='assistant',reviewed_at=datetime.now(timezone.utc).isoformat(),
        rationale=rationale,review_scope='entire_field_bundle',qualifications_checked=True,evidence_checked=True,
        factual_verification='source_comparison_only'))
    sample_results.append(dict(packet_id=packet['packet_id'],members=packet['members'],status=status,rationale=rationale,scope=scope))
assert len(findings)==len(samples)==24
for n,(packet,(status,rationale)) in enumerate(zip(samples,findings),1):
    assert packet['packet_id'] in packet_index and packet['binding']==packet_index[packet['packet_id']]['binding']
    add(packet_index[packet['packet_id']],status,rationale,'RISK_SAMPLE' if n<=8 else 'STRATIFIED_RANDOM_SAMPLE')
for packet in w['packets']:
    if any(key.startswith('EXP_0127:') for key in packet['members']):
        add(packet,'SUPPORTED','Full T0041 now explicitly includes the first divisibility-by-5 condition, later combined branch and observed fizz result for 15, followed by the explanation that later else clauses are ignored. This is diagnosis of the incorrect example, not approval of its output.','TARGETED_CRITICAL_REVIEW')
    if any(key in ('DEF_0060:/content','DEF_0060:/definition_text') for key in packet['members']):
        add(packet,'PARTIALLY_SUPPORTED','Immutability is explicitly supported, but the blanket assertion that any method appearing to modify a string always returns a new object requires independent technical qualification. The source itself overgeneralizes; matching its words is not factual certification.','TARGETED_SOURCE_QUALITY_REVIEW')
    if any(key.startswith('PRC_5001:') for key in packet['members']):
        add(packet,'SUPPORTED','The exact T0045 quotation explicitly supplies do, the code block/body, the trailing while condition and terminating semicolon. This is a scoped prose reconstruction of the stated procedure, not invented literal code.','TARGETED_SOURCE_RECOVERY_REVIEW')
if (P/'review_decision_inputs_v2.json').exists():
    previous=read(P/'review_decision_inputs_v2.json')
    # A rebuild retains actual original review timestamps; it does not invent new visits.
    for new,old in zip(inputs,previous):new['reviewed_at']=old['reviewed_at']
    assert inputs==previous
else:write('review_decision_inputs_v2.json',inputs)
history=[]
for decision in inputs:history=append_decision(w,history,decision)
write('initial_accepted_decision_history.json',history)
# Repair a real legacy evidence-scope defect without expanding primary coverage.
old_workspace=w
mortgage=items['FRM_0007']
for path in ('/content','/formula_text'):
    changes.append(add_reviewed_evidence(mortgage,path,source,'T0033',units['T0033'].text,reviewer=reviewer,
        rationale='Explicitly associate the already cited T0033 explanation of multiplication/division as context. T0031 remains primary; no complete mortgage equation is inferred.'))
w=build_review_inventory(knowledge,source,duplicate_relations=relations,coverage_priority_ids=['T0004','T0045'])
stale=resolve_reviews(w,history,legacy_pin=pin)['invalidated_decisions']
fresh=[]
for packet in w['packets']:
    if any(k.startswith('FRM_0007:') for k in packet['members']):
        equation=any(k.endswith(':/content') or k.endswith(':/formula_text') for k in packet['members'])
        rationale=('The repaired T0031/T0033 scope supports only a product prefix and further unnamed factors/divisor. Retain PARTIALLY_SUPPORTED and the visual-context warning; do not reconstruct or approve the complete equation.' if equation else
            'Explicit re-review after T0033 was associated as context: the cited T0031 passage still defines this symbol as principal (P) or monthly interest rate (R). This component definition does not certify the incomplete equation. No approval was silently reused.')
        fresh.append(dict(packet_id=packet['packet_id'],binding=packet['binding'],source_version=w['source_version'],members=packet['members'],
            status='PARTIALLY_SUPPORTED' if equation else 'SUPPORTED',reviewer=reviewer,reviewer_kind='assistant',
            reviewed_at=datetime.now(timezone.utc).isoformat(),rationale=rationale,review_scope='entire_field_bundle',
            qualifications_checked=True,evidence_checked=True,factual_verification='source_comparison_only'))
if (P/'scope_repair_review_inputs.json').exists():
    previous=read(P/'scope_repair_review_inputs.json')
    for new,old in zip(fresh,previous):new['reviewed_at']=old['reviewed_at']
    assert fresh==previous
else:write('scope_repair_review_inputs.json',fresh)
for decision in fresh:history=append_decision(w,history,decision)
write('invalidation_events.json',dict(cause='Mortgage contextual evidence scope explicitly repaired; primary remains T0031.',
    invalidated_record_hashes=stale,explicit_re_review_records=len(fresh),automatic_approval_transfers=0))
resolved=resolve_reviews(w,history,legacy_pin=pin)
write('review_input_knowledge.json',knowledge.model_dump(mode='json'))
projected=materialize_reviews(knowledge,resolved)
titles=read(B/'offline_review_plan.json')['presentation_section_titles']
subset=reviewed_student_preview(projected,source,relations,section_titles=titles,version=8)
(P/'reviewed_study_notes_v8.md').write_text(subset['markdown'],encoding='utf-8')
required=read(Path('data/output/task6_source_faithfulness_20261109/repair_plan.json'))['required_primary_requests']
audit=read(R/'request_audit.json')
completed=[o['id'] for o in audit['operations'] if o['state']=='success']
pipeline=build_preview(projected,source,required_chunks=required,completed_chunks=completed)
draft=comprehensive_draft(projected,source,resolved,section_titles=titles,representations=pipeline['representations'])
(P/'comprehensive_review_draft_v8.md').write_text(draft['markdown'],encoding='utf-8')
(P/'adaptive_pipeline_preview.md').write_text(pipeline['markdown'],encoding='utf-8')
(P/'evidence_desk.html').write_text(evidence_desk_html(resolved),encoding='utf-8')
topic_inventory=[]
for recovery in read(B/'offline_review_plan.json')['recoveries']:
    item=recovery['item'];q=recovery['evidence'][0]
    topic_inventory.append(dict(topic=item['content'],source_id=q['source_id'],quote=q['quote'],
        represented_by=[item['knowledge_id']+':/content'],reviewer=recovery['reviewer'],scope_checked=True,
        rationale='Task 7 explicit source-comparison review retained; scope is this named point, not the entire source unit.'))
topic_inventory.append(dict(topic='Do-while construction sequence',source_id='T0045',quote=quote,
    represented_by=['PRC_5001:'+p for p in paths],reviewer=reviewer,scope_checked=True,
    rationale='Exact sequence reviewed offline; Task 7 timing fact alone did not retain these construction details.'))
manifest=read(Path('data/output/java_authorization_20261109_022409_842270/manifest.json'))
request_sources={r['request_id']:r['source_ids'] for r in manifest['requests']}
accepted=sorted({sid for operation in audit['operations'] if operation['state']=='success' for sid in request_sources[operation['id']]})
coverage=coverage_report(projected,source,resolved,accepted_primary_ids=accepted,topic_inventory=topic_inventory,retention=draft['retention'],section_titles=titles)
for name,value in [('knowledge_v8.json',projected.model_dump(mode='json')),('review_inventory.json',resolved['inventory']),
    ('review_workspace.json',resolved),('review_queue.json',resolved['queue']),('evidence_packets.json',resolved['packets']),
    ('decision_history.json',history),('sample_findings.json',sample_results),('changes.json',changes),
    ('topic_inventory.json',topic_inventory),('coverage_report.json',coverage),('draft_retention.json',draft['retention']),
    ('reviewed_retention.json',subset['mapping']),('pipeline_quality_gates.json',pipeline['report']),
    ('adaptive_representations.json',pipeline['representations'].model_dump(mode='json'))]:write(name,value)
with (P/'review_inventory.csv').open('w',encoding='utf-8-sig',newline='') as f:
    columns=['key','item_id','path','claim','source_ids','evidence','mechanical_validation','semantic_status','risk_priority','risk_reasons','packet_id','relationships','same_source_peer_ids']
    writer=csv.DictWriter(f,fieldnames=columns);writer.writeheader()
    for row in resolved['inventory']:writer.writerow({key:json.dumps(row[key],ensure_ascii=False) if isinstance(row[key],(list,dict)) else row[key] for key in columns})
summary=dict(items=len(projected.get_all_items()),fields=len(resolved['inventory']),exact_evidence_bundles=len(resolved['packets']),
    atomic_claim_count=None,statuses=dict(Counter(r['semantic_status'] for r in resolved['inventory'])),
    explicit_decisions=len(history),human_decisions=sum(d['reviewer_kind']=='human' for d in inputs),
    sample_risk=dict(Counter(r['status'] for r in sample_results if r['scope']=='RISK_SAMPLE')),
    sample_random=dict(Counter(r['status'] for r in sample_results if r['scope']=='STRATIFIED_RANDOM_SAMPLE')),
    reviewed_items=subset['displayed_items'],reviewed_fields=sum(len(m['displayed_paths']) for m in subset['mapping']),
    draft_items=len(draft['item_ids']),draft_fields=draft['field_count'],source_units=50,accepted_extraction=48,
    new_offline_recovery_items=1,api_requests=0,whole_document_verified=False,quality_score=None)
write('summary.json',summary)
print(json.dumps(summary))
