"""Independent recomputation of artifact checks and a non-scored quality rubric."""
import json
import hashlib
import xml.etree.ElementTree as ET
from pathlib import Path
from collections import Counter
from app.models.knowledge import KnowledgeDocument
from app.evaluation.field_faithfulness import leaves

P=Path('data/output/task7_educational_completeness_20261109')
def read(name):return json.loads((P/name).read_text(encoding='utf-8'))
def write(name,data):(P/name).write_text(json.dumps(data,indent=2,ensure_ascii=False),encoding='utf-8')
def tests(name):
    return {
        key:sum(int(s.attrib.get(key,0)) for s in ET.parse(P/name).getroot().iter('testsuite'))
        for key in ('tests','failures','errors','skipped')}

comparison=read('before_after.json')
rows=read('field_review_queue.json')
mapping=read('mapping.json')
knowledge=KnowledgeDocument.model_validate(read('knowledge_v7.json'))
items={i.knowledge_id:i for i in knowledge.get_all_items()}
source=json.loads(Path('data/output/java_live_java-20261109_022409_842270/source_document.json').read_text(encoding='utf-8'))
units={u['source_id']:u for u in source['source_units']}
index={(r['knowledge_id'],r['path']):r for r in rows}
notes=(P/'student_notes_v7.md').read_text(encoding='utf-8')
errors=[]
for entry in mapping:
    actual=dict(leaves(items[entry['item_id']].model_dump(mode='json')))
    for path in entry['displayed_paths']:
        row=index[(entry['item_id'],path)]
        if row['status']!='SUPPORTED' or actual[path]!=row['original_output']:errors.append([entry['item_id'],path,'disposition mismatch'])
        if not row['evidence'] or any(q['source_id'] not in units or q['quote'] not in units[q['source_id']]['text'] for q in row['evidence']):errors.append([entry['item_id'],path,'invalid canonical evidence'])
        if actual[path] not in notes:errors.append([entry['item_id'],path,'missing rendered text'])
    alias=entry['equivalent_content_of']
    if alias and (alias not in items or 'Equivalent statement: see **'+alias+'**' not in notes):errors.append([entry['item_id'],'invalid cross-reference'])
checks=read('preservation_checks.json')
checks['changed_at_final_check']=[path for path,digest in read('preservation_before.json').items()
    if not Path(path).exists() or hashlib.sha256(Path(path).read_bytes()).hexdigest()!=digest]
write('preservation_checks.json',checks)
full=tests('regression_results_final.xml')
focused=tests('final_preview_tests.xml')
assert all(s[k]==0 for s in (full,focused) for k in ('failures','errors','skipped'))
assert not errors and not checks['changed_at_final_check'] and not checks['original_evidence_records_lost']

rubric={
    'content_completeness':dict(outcome='IMPROVED_INVENTORY_STILL_INCOMPLETE_PREVIEW',
        evidence='11 reviewed recovery items; primary inventory coverage 48 to 50 units. Unit presence is not exhaustive topic coverage. Only reviewed fields enter the student subset.',
        acceptance='All important topics and qualifications independently inventoried against source, with no material omission.',remaining='Full document topic inventory and 1,100 remaining unreviewed field leaves.'),
    'factual_faithfulness':dict(outcome='SCOPED_ASSISTANT_REVIEW_NO_INDEPENDENT_CERTIFICATION',
        evidence='Six overgeneralized or unsupported main assertions revised with original strings retained. The empty-string array-default assertion is withheld as INCONCLUSIVE.',
        acceptance='No unsupported or contradicted factual assertions after independent source and technical review.',remaining='Source correctness is distinct from source entailment; local Java probe timed out.'),
    'explanation_quality':dict(outcome='SCOPED_IMPROVEMENT',
        evidence='Restored package-registration qualification, counter-free loop context, value-comparison distinction, condition timing and normalization purpose.',
        acceptance='A learner can explain why the operations and qualifications matter using only supported material.',remaining='No learner comprehension study; broad explanations remain unreviewed.'),
    'organization':dict(outcome='EDITORIAL_IMPROVEMENT_OBSERVED',
        evidence='Topic headings, primary-source ordering, explicit error/correction roles, numbered steps and one equivalence cross-reference.',
        acceptance='Logical progression with prerequisites and correction relationships clear.',remaining='Source sequence is a conservative order, not a validated optimal curriculum.'),
    'examples':dict(outcome='REVIEWED_SUBSET_ONLY',
        evidence='Reviewed verbal examples and complete arithmetic displays retained; 40 nonliteral reconstructed snippets remain in the audit and are withheld.',
        acceptance='Examples are source-supported, correctly scoped and clearly marked when deliberately incorrect.',remaining='No restored literal code where source lacks exact code; incomplete mortgage formula still withheld.'),
    'traceability':dict(outcome='MECHANICAL_CHECKS_PASS_SEMANTICS_SEPARATE',
        evidence='Independent serialized-artifact check recomputes field values, SUPPORTED dispositions, exact canonical quotes, rendered text presence and alias targets.',
        acceptance='Every displayed factual field has a correct canonical source and reviewed support.',remaining='Matching references do not prove entailment or factual truth.'),
    'readability_and_usability':dict(outcome='CONCISE_REVIEW_SUBSET_NOT_A_COMPLETE_COURSE',
        evidence='Long evidence quotations moved to audit; student text uses topic headings and concise field citations.',
        acceptance='No material content loss and usable notes confirmed by an independent reader.',remaining='The restricted preview deliberately withholds most unreviewed knowledge. No independent reader or accessibility study.'),
}
benchmark=dict(score=None,independent_semantic_reviewer=None,live_model_quality_claim=False,
    mechanical_artifact_errors=errors,full_regressions=full,final_focused_regressions=focused,
    rubric=rubric,field_status_counts=dict(Counter(r['status'] for r in rows)),
    risk_counts=dict(Counter(r['risk'] for r in rows)),overall='NEEDS_MORE_SOURCE_AND_SEMANTIC_REVIEW')
write('quality_benchmark.json',benchmark)
write('remaining_gaps.json',dict(
    genuinely_required_live_requests_established=0,
    explanation='No remaining gap has been demonstrated to require another model request. Review existing knowledge first; source omissions/errors cannot be repaired by asking a model to invent them.',
    provider_completion='Still 48/50. Offline coverage recovery is not provider success or request reconciliation.',
    recovery_drafts='Four Task 6 drafts remain historically intact and unapproved; no dispatch or approval records created.',
    gaps=[dict(area='Full educational-topic coverage',next_action='Offline topic inventory and semantic review of existing items; request a narrowly bounded extraction only after proving information is absent from all saved outputs.'),
          dict(area='Literal code fidelity',next_action='Obtain exact original code/visual source where needed. Additional text-only extraction cannot establish missing literal code.'),
          dict(area='Incomplete mortgage formula',next_action='Obtain original visual/formula source; no reconstruction from incomplete transcript.'),
          dict(area='Source factual correctness',next_action='Independent technical review; local Java launcher did not complete. Hold the array-default claim.'),
          dict(area='Independent educational quality',next_action='Independent source/technical reviewer and learner usability review; no supported numeric score yet.')]))

b,a=comparison['before'],comparison['after']
table='\n'.join('| '+label+' | '+str(old)+' | '+str(new)+' |' for label,old,new in [
    ('Audit knowledge items',b['items'],a['items']),('Primary source units with audit knowledge',b['primary_units'],a['primary_units']),
    ('SUPPORTED field leaves',b['field_statuses']['SUPPORTED'],a['field_statuses']['SUPPORTED']),
    ('NOT_REVIEWED field leaves',b['field_statuses']['NOT_REVIEWED'],a['field_statuses']['NOT_REVIEWED']),
    ('Unresolved duplicate candidates',92,0),('Provider requests accepted','48/50','48/50'),
    ('Words in student preview',b['student_words'],a['student_words'])])
report=f'''# Task 7 — Educational completeness recovery and quality benchmark

Offline work completed against the Task 6 `student_notes` baseline. No provider requests, live authorizations, credential changes, model changes, or quota-accounting changes were made. This is a safer and better supported **review subset**, not publication approval or a complete course.

## Measured before / after

| Measure | Task 6 | Task 7 |
| --- | ---: | ---: |
{table}

All 458 baseline IDs remain in the 469-item derived knowledge document. All original active grounding evidence records survive. Changes to text preserve the original strings and exact source association in `changes.json` and metadata. {checks['checked']} historical/control files were checked by SHA-256, with no changes at final verification. Historical Task 6 artifacts, four recovery drafts, prior request packages and usage records remain intact. The 85% policy is unchanged.

**Coverage distinction:** 50 source units now have primary knowledge in the audit. This does not establish that every educational topic was recovered. The restricted student preview displays {a['displayed_items']} items (including the equivalence cross-reference), {a['displayed_fields']} distinct fields, {a['displayed_examples']} examples, and {a['student_primary_units']} primary source units. It withholds {a['withheld_fields']} field leaves. The shorter preview deliberately presents fewer total fields than Task 6; no claim of full student-facing completeness or zero material content loss is made.

## Missing-content recovery

T0004: five reviewed facts recover the recorded SDK setup, project/template workflow, command-line application description, package organization, and reversed-domain naming convention with the explicit no-registration qualification. JDK 12 is identified as the recorded setup, not a current requirement. Garbled package identifiers and unfinished boundary phrases are not reconstructed.

T0045: six reviewed facts recover string-value comparison and quit termination, scanner reuse, case normalization and its purpose, echo behavior, suitability of while for an unknown repetition count, and the zero-versus-at-least-once distinction between while and do-while. No invented scanner method, full program, or literal code is added. The scanner recommendation is scoped to the demonstrated loop.

Each recovery has an exact canonical quotation, reviewer rationale, explicit primary source, matching common/category fields and `origin=offline_source_review`, `provider_generated=false`. These are assistant source-reviewed additions, not Groq output. Adjacent/related prior knowledge was separately checked in `recovery_overlap_review.json`; overlapping details remain auditable. Provider completion remains FAIL at 48/50.

## All 92 duplicate candidates

78 are RELATED_BUT_DISTINCT; 13 are PARTIAL_OVERLAP; one is MEANINGFULLY_EQUIVALENT. Every pair has a retained rationale, original texts, both sets of source evidence, a reviewer identity and a quote-validity check in `duplicate_decisions.json`. None of these decisions certifies every auxiliary field's technical truth.

All original records remain. FCT_0326's equivalent assignment-operator statement is presented as a cross-reference to FCT_0016 after both content assertions were reviewed. Distinct auxiliary fields would remain independently visible if supported. Prefix/postfix operations, different arithmetic results, general rules and their scoped examples are not collapsed. Partial-overlap pairs retain their additional qualifications and outcomes.

## Semantic corrections and high-risk review

Six main assertions were revised in both common and category text fields: FCT_0224 removes the unsupported float-suffix confusion/preference claim; FCT_0017 scopes allocation to the Date-object demonstration; FCT_0339 scopes the declaration error to the demonstrated unbraced if body; FCT_0361 and FCT_0362 remove universal counter/update requirements contradicted by the same source's counter-free input loop; EXP_0133 distinguishes reference comparison from textual-value comparison rather than saying comparison is impossible. Exact before/after strings and evidence are preserved.

Two further assignment statements were source-reviewed for the equivalence link. FCT_0252 is INCONCLUSIVE in both fields: the full transcript states an empty-string default, so matching that source does not independently establish factual correctness. The local Java source-file execution probe timed out. Its result is retained without fabricated stdout, a claimed successful run, or a source-unsupported replacement fact.

Current dispositions are {json.dumps(a['field_statuses'])}. These count field leaves, not independent claims: common/category fields often repeat one assertion. The 80 UNSUPPORTED records remain the 40 reconstructed snippets duplicated across two fields; they establish a literal-source fidelity failure, not necessarily an incorrect algorithm. All are withheld from this student view. All remaining unreviewed/high-risk fields remain queued; no matching quote, context addition or heuristic signal promotes them to semantic correctness.

## Benchmark and acceptance findings

`quality_benchmark.json` defines acceptance criteria and separate findings for completeness, factual faithfulness, explanation, organization, examples, traceability and usability. `finalize_report.py` independently rereads serialized artifacts to verify displayed-field dispositions, actual text, canonical quotes, rendering and cross-reference targets. This is independent mechanical recomputation, **not independent human semantic review**.

Demonstrated improvements include restored qualifications and missing concepts, removal of six overgeneralizations, source-backed loop explanations, topic headings, primary-source ordering, error-before-correction sequencing, numbered procedure steps, arithmetic text blocks, and removal of long audit quotes from student prose. Exact quotations remain in the review queue and source document. Editorial headings are supplied as document-specific presentation metadata; production logic contains no Java-specific rules.

No numeric quality score is assigned. Full-document topic completeness, independent technical verification, learner comprehension, accessibility and usability remain unverified. Mechanical traceability passes; overall educational readiness remains NEEDS_MORE_SOURCE_AND_SEMANTIC_REVIEW. Existing pipeline semantic/completeness gates remain restrictive; offline additions do not turn failed provider operations into successes.

## Regression evidence

Complete applicable offline suite: {full['tests']} passed, 0 failed, 0 errors, 0 skipped. A final overlapping safeguard/renderer/recovery batch after presentation refinements: {focused['tests']} passed, 0 failed, 0 errors, 0 skipped. Do not add these as independent totals. New recovery tests include mathematics, science, history, research, technical instructions and uncertain content, plus invalid evidence, exclusion, identity, stale review, field withholding, equivalence and primary/context order.

The full launcher denies socket connections and removes API-key environment entries. Real-provider integration tests were explicitly excluded. The two ingestion suites were excluded because they are Windows-disabled Docling suites; they are not counted among these passes or skips. No new ingestion/OCR quality claim is made.

The initial expanded run had two failures: an obsolete layout-only exclusion assertion and a missing Windows multiprocessing guard in the Task 7 test launcher. The assertion now matches the established strict source policy, and the launcher is guarded. The final full suite passed. An initial new exclusion fixture also used an invalid policy status and was corrected to an explicitly reviewed noneducational status. All run logs are retained.

## Remaining gaps and live-extraction decision

No remaining gap has yet been shown to **require** another API request. T0004/T0045 educational points above were recoverable offline. Most remaining work is source/topic inventory and semantic review of existing saved knowledge. The incomplete mortgage expression needs original visual evidence; source errors need independent factual checking; absent literal code needs the original code/visual source. Another model response cannot establish those missing facts from the same inadequate source.

The four historical recovery drafts remain unapproved and untouched. If later review proves a supported educational topic is absent from every saved result, prepare a narrowly scoped, fresh hash-bound request with exact source/context evidence and separate authorization. Do not rerun the whole document, retry uncertain requests, or rotate credentials to bypass limits. No such request was authorized or sent here.

## Files and artifacts

Production addition: `app/evaluation/offline_recovery.py` (pure offline review/recovery and supported-field projection). Tests: new `tests/test_offline_completeness_recovery.py`; corrected obsolete assertion in `tests/test_extraction_unit.py`. Request prompts, extraction schemas, source-policy foundations, providers, authorizers and quota implementations were unchanged.

New artifacts live only under `data/output/task7_educational_completeness_20261109/`: `student_notes_v7.md`, `knowledge_v7.json`, `offline_review_plan.json`, `changes.json`, `duplicate_decisions.json`, `recovery_overlap_review.json`, `field_review_queue.json`, `mapping.json`, `withheld.json`, `before_after.json`, `quality_benchmark.json`, `remaining_gaps.json`, `pipeline_quality_gates.json`, preservation records, the inconclusive runtime probe, regression XML/logs and reproducible build/review scripts.
'''
(P/'quality_report.md').write_text(report,encoding='utf-8')
write('artifact_manifest.json',dict(version=7,artifacts={p.name:hashlib.sha256(p.read_bytes()).hexdigest()
    for p in P.iterdir() if p.is_file() and p.name!='artifact_manifest.json'},request_manifest_created=False))
print(json.dumps(dict(mechanical_errors=errors,full_regressions=full,final_focused=focused,historical_changes=checks['changed_at_final_check'])))
