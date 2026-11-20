"""Document-specific review inventory; reusable logic lives in app.evaluation.
Run from backend. No network/provider imports or dispatch operations.
"""
import json
import hashlib
import subprocess
from pathlib import Path
from collections import Counter
from app.models.knowledge import KnowledgeDocument
from app.models.source import SourceDocument
from app.evaluation.offline_recovery import apply_offline_plan, reviewed_student_preview
from app.evaluation.notes_pipeline import build_preview
from app.evaluation.field_faithfulness import audit_fields

OUT = Path('data/output/task7_educational_completeness_20261109')
BASE = Path('data/output/task6_source_faithfulness_20261109')
RUN = Path('data/output/java_live_java-20261109_022409_842270')

def read(p): return json.loads(p.read_text(encoding='utf-8'))
def write(name, value): (OUT/name).write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding='utf-8')
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()

historical = read(BASE/'preservation_before.json')
paths = {Path(p) for p in historical}
paths |= {p for p in BASE.rglob('*') if p.is_file()}
paths |= {p for p in Path('data').glob('**/*') if p.is_file() and
          not any(part.startswith('task7') for part in p.parts) and
          any(t in p.name.lower() for t in ('ledger','reservation','approval','authorization'))}
paths.add(Path('QUOTA_POLICY.md'))
before = {str(p): digest(p) for p in sorted(paths) if p.exists()}
write('preservation_before.json', before)
source = SourceDocument.model_validate(read(RUN/'source_document.json'))
knowledge = KnowledgeDocument.model_validate(read(BASE/'student_notes/knowledge.json'))
units = {u.source_id:u for u in source.source_units}
items = {i.knowledge_id:i for i in knowledge.get_all_items()}
reviewer = 'assistant source-comparison review; not independent human certification'
plan = dict(recoveries=[], field_reviews=[], provider_dispatch=False, authorization_changes=False)

def recover(number, sid, heading, text, quote, rationale):
    assert quote in units[sid].text
    plan['recoveries'].append(dict(item=dict(knowledge_id=f'FCT_{number:04}', knowledge_type='fact',
        document_id=source.document_id, source_unit_ids=[sid], content=text, fact_text=text, section=heading),
        evidence=[dict(source_id=sid,quote=quote)], reviewer=reviewer, rationale=rationale))

recover(5001,'T0004','Project setup and packages',
    'In this recorded IntelliJ demonstration, the project uses JDK version 12. This identifies the tutorial setup, not a present-day version requirement.',
    'earlier we downloaded jdk or Java development kit version 12 that is why JDK version 12 is selected here',
    'Preserves historical setup scope; does not recommend a current SDK version.')
recover(5002,'T0004','Project setup and packages',
    'The tutorial creates a Java project in IntelliJ, checks the selected project SDK, and chooses a project template for a command-line application.',
    "on the left side select java and make sure project sdk is not black so earlier we downloaded jdk or Java development kit version 12 that is why JDK version 12 is selected here if you don't see that make sure to select it from this drop-down list alright now let's click on next on this page select create project from template so we're gonna create a command line application",
    'Faithful prose for source workflow; no invented UI labels, code, or missing visual details.')
recover(5003,'T0004','Project setup and packages',
    'A command-line application runs from the command line and has no graphical user interface in this explanation.',
    "a command line application which is an application that we can run from the command line it doesn't have a graphical user interface or a GUI",
    'Preserves the source definition.')
recover(5004,'T0004','Project setup and packages',
    'A package groups related classes, helping organize an application as its number of classes grows.',
    "we have a concept called package and we use a package to group related classes so as our applications grow we're gonna end up with hundreds or even thousands of classes so we should properly organize this class us into packages",
    'Recovers the organizational concept without reconstructing the garbled package identifier.')
recover(5005,'T0004','Project setup and packages',
    'The source describes a convention of reversing the company domain name for a base package. It explicitly says an actual registered Internet domain is not required; the purpose is a namespace for classes.',
    "now by convention the base package for a Java project is the domain name of your company in Reverse so my website is code with mass comm that is why I'm gonna set the base package for this project to come that code with Marsh now it doesn't mean that you should have an actual domain registered on an Internet this is just a way to create a namespace for our classes",
    'Preserves both convention and important registration qualification; omits phonetic identifiers.')
recover(5006,'T0045','Input loops and termination',
    'The input-loop example uses the equals method of string objects to compare values and repeats while the input does not equal quit.',
    "to compare their value instead we need to use the equals method of string objects so we want to check to see if the input equals quit now here we need to apply the not operator so as long as the input does not equal quit we're gonna continuously ask the user to enter something",
    'Recovers value comparison and negated termination condition without inventing literal syntax.')
recover(5007,'T0045','Input loops and termination',
    'In this example, create the scanner outside the while loop and reuse it, avoiding a new scanner object on each iteration.',
    "with this implementation in every iteration we're going to create a new scanner object so if the user enters 10 numbers we're gonna create 10 scanner objects in memory this is unnecessary and it's actually a bad practice because it's going to pollute our memory so it's better to create the scanner object outside of a while loop and then simply use it here",
    'Keeps recommendation scoped to the demonstrated program rather than all resource lifetimes.')
recover(5008,'T0045','Input loops and termination',
    'The example converts input to lowercase after reading it so uppercase or mixed-case versions of quit satisfy the intended termination check.',
    "here we are assuming that the user is typing everything in lowercase so if they type quit in uppercase or any combinations of lowercase and uppercase characters this logic is not gonna work the way we want so over here right after reading something from the terminal we're gonna call the to lowercase method of string objects to convert it to lowercase",
    'Preserves reason, order and scope; makes no broader locale guarantee.')
recover(5009,'T0045','Input loops and termination',
    'The demonstration echoes entered values back to the terminal and terminates when the user types quit.',
    "let's echo back whatever the user enters so we simply print that on the terminal now let's run this and see what happens so I'm going to enter if your numbers like 1 2 & 3 whatever we type gets a code back but the moment we type quit our program terminates",
    'Recovers demonstrated behavior, not an invented complete program or scanner method.')
recover(5010,'T0045','Input loops and termination',
    'The source presents while loops as useful when the required number of repetitions is not known ahead of time.',
    "while loops are useful in situations where we don't know ahead of time how many times we want to repeat something",
    'Preserves useful-when qualification rather than an exclusive rule.')
recover(5011,'T0045','Loop condition timing',
    'A while loop checks its condition first and may execute zero times if the condition is initially false. A do-while loop checks last and executes its body at least once.',
    'with while loops we check the condition first so if the condition is false the first time this loop will never get executed in contrast with do-while loops we check the condition last so do-while loops always get executed at least once even if the condition is false',
    'Preserves the important zero-versus-one-or-more contrast.')

def review(item_id, status, rationale, replacement=None, quote=None, mode=None):
    item=items[item_id]
    evidence=(item.extraction_metadata or {})['source_grounding']['evidence']
    if quote is None:
        q=next(e for e in evidence if '/content' in e.get('fields',[]))
        sid,quote=q['source_id'],q['quote']
    else: sid=item.source_unit_ids[0]
    category_path='/explanation_text' if item.knowledge_type=='explanation' else '/fact_text'
    for path in ('/content',category_path):
        record=dict(item_id=item_id,path=path,expected_text=getattr(item,path[1:]),status=status,
            mode=mode or ('faithful_paraphrase' if status=='SUPPORTED' else 'requires_review'),
            evidence=[dict(source_id=sid,quote=quote)],reviewer=reviewer,rationale=rationale)
        if replacement is not None:record['replacement']=replacement
        plan['field_reviews'].append(record)

review('FCT_0224','SUPPORTED',
    'Original confusion-with-1 and preference claim is unsupported by this quote (it refers to f, whereas confusion appears in the long-l discussion). Replacement retains only the explicit either-case permission.',
    'The source allows an uppercase or lowercase F suffix to represent a floating-point number as a float.')
review('FCT_0017','SUPPORTED',
    'Restricts the overgeneralized reference-variable allocation claim to the Date object demonstration actually described.',
    'In the demonstrated Date example, the source creates an object using the new operator followed by the class name and parentheses.')
review('FCT_0339','SUPPORTED',
    'Restores local-if-declaration context instead of claiming a universal rule about every Java variable declaration.',
    'In the demonstrated if statement, declaring the local variable directly as the unbraced body produces an error; the source adds braces to create a code block.')
review('FCT_0361','SUPPORTED',
    'The later part of the same source explicitly says the input loop has no counter variable. Restore example scope instead of requiring an explicit loop variable in every while loop.',
    'The source first demonstrates a counter-based while loop, then an input-driven while loop with no counter variable. The input loop checks whether the user has entered quit.',
    quote=units['T0044'].text)
review('FCT_0362','SUPPORTED',
    'Counter decrement belongs to the counting demonstration, not a universal obligation to update a counter inside every while loop. Source also contains a counter-free input example.',
    'In the counter-based while-loop rewrite, the source decrements the counter at the end of each iteration. The later input-driven example uses no counter variable.',
    quote=units['T0044'].text)
review('EXP_0133','SUPPORTED',
    'Restrict the claim to failure to compare textual values; remove wording suggesting reference comparison is impossible as an operation.',
    'In the input-loop explanation, comparing string references does not test their textual values; the source distinguishes the strings\' memory locations from their values.',
    quote=units['T0044'].text)
review('FCT_0252','INCONCLUSIVE',
    'The complete T0020 transcript states empty string. This source assertion needs independent technical verification; exact quotation is not factual certification. Withhold pending a successful independent check.',
    quote='if you have a string array all items get initialized to an empty string')
for iid in ('FCT_0016','FCT_0326'):
    review(iid,'SUPPORTED','Both source passages explicitly identify the single equals sign as assignment; same document, operator and scope. No additional facts are discarded.')

# Independent executable check of one source assertion, not an independent human review.
probe=OUT/'ArrayDefaultsProbe.java'
probe.write_text('class ArrayDefaultsProbe { public static void main(String[] args) { String[] values = new String[1]; System.out.println(values[0] == null); System.out.println("".equals(values[0])); } }\n',encoding='utf-8')
if (OUT/'independent_runtime_probe.json').exists():
    probe_result=read(OUT/'independent_runtime_probe.json')
    probe_result.pop('command',None)
    probe_result.pop('scope',None)
else:
    try:
        proc=subprocess.run(['java',str(probe)],capture_output=True,text=True,timeout=15)
        probe_result=dict(returncode=proc.returncode,stdout=proc.stdout,stderr=proc.stderr)
    except subprocess.TimeoutExpired:
        probe_result=dict(status='INCONCLUSIVE',reason='Local Java launcher timed out; no successful runtime observation.')
if probe_result.get('returncode')==0 and probe_result.get('stdout','').splitlines()==['true','false']:
    for record in plan['field_reviews']:
        if record['item_id']=='FCT_0252':
            record.update(status='CONTRADICTED',mode='contradicted',rationale='Source-faithful assertion contradicted by the saved local Java probe; retain original and withhold without inventing a source-backed replacement.')
write('independent_runtime_probe.json',dict(command=['java',str(probe)],**probe_result,
    scope='One technical source assertion only; not source evidence for replacement notes'))
plan['presentation_section_titles']={
    'T0004':'Project setup and packages', 'T0010':'Assignment, variables and literals',
    'T0011':'Assignment, variables and literals', 'T0012':'Assignment, variables and literals',
    'T0013':'Object creation', 'T0017':'String operations', 'T0023':'Arithmetic and precedence',
    'T0024':'Number conversions', 'T0025':'Number conversions', 'T0034':'Assignment and comparison',
    'T0036':'Conditional statements', 'T0038':'Conditional statements',
    'T0041':'Conditional ordering and alternative approaches', 'T0042':'Conditional ordering and alternative approaches'}
plan['presentation_section_titles']['T0044']='Counting loops and input-driven loops'
write('offline_review_plan.json',plan)
derived,changes=apply_offline_plan(knowledge,source,plan)
duplicates=read(BASE/'duplicate_review.json')
partial={5,10,21,22,23,24,48,49,69,76,79,88,91}
reasons={
5:'Method naming is a scoped application of the general camel-case convention; preserve both scopes.',
10:'Boolean expressions specialize expressions; retain the general definition and boolean result restriction.',
21:'Standalone increment versus postfix assignment; assignment additionally demonstrates the old value captured in Y.',
22:'Prefix standalone versus postfix assignment; preserve timing contrast and assignment result.',
23:'Postfix standalone versus prefix assignment; preserve timing contrast and assignment result.',
24:'Standalone prefix increment versus assigning its result; retain the additional Y outcome.',
48:'Same repeated output, but the first emphasizes avoiding repeated print statements; retain strategy and result.',
49:'Entry-function and containing-class statements overlap but containment is additional knowledge; broad wording still needs semantic review.',
69:'Precedence hierarchy additionally includes parentheses; retain both with scope review rather than equating all arithmetic rules.',
76:'Simple/complex contrast overlaps, but holding a reference is a material memory-semantics distinction; do not delete it.',
79:'General NOT operation versus the false-to-true special case; retain rule and worked case.',
88:'General block scope versus while-loop application; retain general rule and local application.',
91:'Initializer items overlap; inferred length and omission of new are distinct details.'}
for n,d in enumerate(duplicates,1):
    d['reviewer']=reviewer
    d['classification']='PARTIAL_OVERLAP' if n in partial else 'RELATED_BUT_DISTINCT'
    d['action']='RETAIN_BOTH'
    d['rationale']=reasons.get(n, 'Different subjects, operations, values, or instructional roles: '+d['left_content']+' | '+d['right_content']+' Retain both; similarity is not equivalence.')
    if n==77:
        d.update(classification='MEANINGFULLY_EQUIVALENT',action='PRESENTATION_CROSS_REFERENCE_ONLY',
            rationale='Both assert that the single equals sign is the assignment operator in the same language. Both content fields source-reviewed; both item IDs and evidence retained, with a cross-reference in the student view.')
    d['evidence_quotes_valid']=all(e['source_id'] in units and e['quote'] in units[e['source_id']].text for side in ('left_evidence','right_evidence') for e in d[side])
    d['semantic_scope']='Duplicate main-assertion classification; not technical certification of every auxiliary field'
assert len(duplicates)==92 and all(d['evidence_quotes_valid'] for d in duplicates)
write('duplicate_decisions.json',duplicates)
overlaps={5001:(['DEF_0001','FCT_0003'],'RELATED_BUT_DISTINCT','Recorded SDK selection/version is distinct from the JDK definition.'),
    5002:(['DEF_0001'],'RELATED_BUT_DISTINCT','Project/template workflow differs from JDK definition.'),
    5003:([],'NEW_SOURCE_SUPPORTED_POINT','Command-line versus GUI description missing from the accepted adjacent material.'),
    5004:(['DEF_0034','DEF_0037'],'RELATED_BUT_DISTINCT','Package groups classes; a class groups functions and a package declaration names membership.'),
    5005:(['DEF_0037'],'RELATED_BUT_DISTINCT','Naming convention and no-registration qualification differ from declaration purpose.'),
    5006:(['EXP_0133'],'PARTIAL_OVERLAP','Value comparison overlaps, while equals and negated quit condition add procedure context.'),
    5007:(['PRC_0397'],'RELATED_BUT_DISTINCT','Scanner reuse across iterations differs from initial scanner setup.'),
    5008:(['FCT_0239'],'PARTIAL_OVERLAP','Lowercase behavior overlaps; reason and timing in quit-input normalization are additional.'),
    5009:([],'NEW_SOURCE_SUPPORTED_POINT','Restores demonstrated echo and termination behavior.'),
    5010:(['EXP_0132'],'PARTIAL_OVERLAP','Restates while suitability in source T0045; accepted earlier explanation additionally contrasts for loops. Preserve both audit records.'),
    5011:(['FCT_0361'],'RELATED_BUT_DISTINCT','Shared while-loop setting; zero executions versus at least once adds condition timing and the do-while contrast beyond the revised counter/input discussion.')}
write('recovery_overlap_review.json',[dict(item_id=f'FCT_{n:04}',related_existing_ids=ids,
    classification=kind,rationale=reason,action='RETAIN_SOURCE_BOUND_RECORDS',reviewer=reviewer)
    for n,(ids,kind,reason) in overlaps.items()])
preview=reviewed_student_preview(derived,source,duplicates,section_titles=plan['presentation_section_titles'])
(OUT/'student_notes_v7.md').write_text(preview['markdown'],encoding='utf-8')
write('knowledge_v7.json',derived.model_dump(mode='json'))
write('changes.json',changes)
for name in ('mapping','withheld','field_review_queue'):write(name+'.json',preview[name])
required=read(BASE/'repair_plan.json')['required_primary_requests']
completed=[o['id'] for o in read(RUN/'request_audit.json')['operations'] if o['state']=='success']
pipeline=build_preview(derived,source,required_chunks=required,completed_chunks=completed)
write('pipeline_quality_gates.json',pipeline['report'])
old_rows=audit_fields(knowledge,source)
rows=preview['field_review_queue']
coverage=lambda k:sorted({s for i in k.get_all_items() for s in (i.extraction_metadata or {}).get('primary_source_ids',i.source_unit_ids)})
manifest=dict(version=7,api_requests=0,request_authorizations_created=0,quota_policy_modified=False,
    before=dict(items=len(items),primary_units=len(coverage(knowledge)),field_statuses=dict(Counter(r['status'] for r in old_rows)),
        unresolved_duplicate_candidates=92,student_words=len((BASE/'student_notes/notes.md').read_text(encoding='utf-8').split())),
    after=dict(items=len(derived.get_all_items()),offline_recovered_items=len(plan['recoveries']),primary_units=len(coverage(derived)),
        field_statuses=dict(Counter(r['status'] for r in rows)),duplicate_classifications=dict(Counter(d['classification'] for d in duplicates)),
        unresolved_duplicate_candidates=0,displayed_items=preview['displayed_items'],
        displayed_fields=sum(len(m['displayed_paths']) for m in preview['mapping']),withheld_fields=len(preview['withheld']),
        student_words=len(preview['markdown'].split()),equivalent_content_links=preview['aliases']),
    provider_completion=dict(accepted=len(completed),required=len(required),changed=False),
    semantic_review_scope='Assistant source comparison of explicit fields. Runtime probe outcome recorded separately; no independent human certification.',
    quality_score=None,publication_eligible=False,remaining_critical_fields=sum(r['risk']=='CRITICAL' for r in rows),
    missing_primary_units=sorted(set(units)-set(coverage(derived))))
manifest['after']['student_primary_units']=len({s for m in preview['mapping'] if m['displayed_paths'] or m['equivalent_content_of'] for s in m['primary_source_ids']})
manifest['after']['displayed_examples']=sum(i.knowledge_type=='example' and any(m['item_id']==i.knowledge_id and m['displayed_paths'] for m in preview['mapping']) for i in derived.get_all_items())
write('before_after.json',manifest)
derived_items={i.knowledge_id:i for i in derived.get_all_items()}
lost_evidence=[]
for iid, old in items.items():
    old_evidence=(old.extraction_metadata or {}).get('source_grounding',{}).get('evidence',[])
    new_evidence=(derived_items[iid].extraction_metadata or {}).get('source_grounding',{}).get('evidence',[])
    if any(e not in new_evidence for e in old_evidence):lost_evidence.append(iid)
write('preservation_checks.json',dict(checked=len(before),changed=[p for p,h in before.items() if not Path(p).exists() or digest(Path(p))!=h],
    original_item_ids_preserved=set(items)<= {i.knowledge_id for i in derived.get_all_items()},historical_authorization_and_usage_unchanged=True))
checks=read(OUT/'preservation_checks.json')
checks['original_evidence_records_lost']=lost_evidence
checks['task6_recorded_baseline_drift']=[p for p,h in historical.items()
    if not Path(p).exists() or digest(Path(p))!=h]
write('preservation_checks.json',checks)
assert not checks['changed'] and not lost_evidence and not checks['task6_recorded_baseline_drift']
print(json.dumps(manifest))
