"""Recompute retention/provenance checks independently of artifact construction."""
import json
from pathlib import Path
from hashlib import sha256
from collections import Counter
import xml.etree.ElementTree as ET
from app.models.knowledge import KnowledgeDocument
from app.evaluation.field_faithfulness import leaves
from app.evaluation.semantic_review import verify_history
from app.representation.formats import RepresentationFormat

P=Path('data/output/task8_semantic_readiness_20261109')
B=Path('data/output/task7_educational_completeness_20261109')
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(name,value):(P/name).write_text(json.dumps(value,indent=2,ensure_ascii=False),encoding='utf-8')
def digest(p):return sha256(p.read_bytes()).hexdigest()
def test_results(name):
    return {key:sum(int(s.attrib.get(key,0)) for s in ET.parse(P/name).getroot().iter('testsuite'))
        for key in ('tests','failures','errors','skipped')}

summary=read(P/'summary.json');rows=read(P/'review_inventory.json');workspace=read(P/'review_workspace.json')
base=KnowledgeDocument.model_validate(read(B/'knowledge_v7.json'))
current=KnowledgeDocument.model_validate(read(P/'knowledge_v8.json'))
old_items={i.knowledge_id:i for i in base.get_all_items()};items={i.knowledge_id:i for i in current.get_all_items()}
reviewed=(P/'reviewed_study_notes_v8.md').read_text(encoding='utf-8')
draft=(P/'comprehensive_review_draft_v8.md').read_text(encoding='utf-8')
retention=read(P/'draft_retention.json');student=read(P/'reviewed_retention.json')
student_paths={m['item_id']+':'+p for m in student for p in m['displayed_paths']}
index={r['key']:r for r in rows}
verify_history(read(P/'decision_history.json'))
assert set(old_items)<=set(items) and len(items)==470
assert set(index)=={i.knowledge_id+':'+path for i in current.get_all_items() for path,_ in leaves(i.model_dump(mode='json'))}
assert len(retention)==len(index) and {r['key'] for r in retention}==set(index)
assert sum(len(p['members']) for p in workspace['packets'])==len(rows)
assert all(index[k]['semantic_status']=='SUPPORTED' for k in student_paths)
text_changes=[];lost_evidence=[];lost_reviews=[]
for key,old in old_items.items():
    now=items[key]
    if dict(leaves(old.model_dump(mode='json')))!=dict(leaves(now.model_dump(mode='json'))):text_changes.append(key)
    evidence=(old.extraction_metadata or {}).get('source_grounding',{}).get('evidence',[])
    actual=(now.extraction_metadata or {}).get('source_grounding',{}).get('evidence',[])
    if any(e not in actual for e in evidence):lost_evidence.append(key)
    if old.educational_review and old.educational_review.model_dump(mode='json')!=(now.extraction_metadata or {}).get('semantic_review_prior_record'):
        lost_reviews.append(key)
assert not text_changes and not lost_evidence and not lost_reviews

critical=[]
for row in rows:
    if row['legacy_review']['status'] in ('UNSUPPORTED','CONTRADICTED'):
        record=dict(key=row['key'],original_status=row['legacy_review']['status'],current_status=row['semantic_status'],
            source_ids=row['source_ids'],exact_evidence_valid=row['mechanical_validation']['active_field_evidence_valid'],
            literal_source_match=row['literal_substring'],withheld_from_reviewed_notes=row['key'] not in student_paths,
            assessment='Retained source-comparison literal-fidelity disposition; not an independent behavioral/algorithm verdict.')
        assert record['withheld_from_reviewed_notes'] and row['claim'] not in reviewed and row['claim'] not in draft
        critical.append(record)
assert len(critical)==80 and all(r['exact_evidence_valid'] for r in critical)
six=['FCT_0224','FCT_0017','FCT_0339','FCT_0361','FCT_0362','EXP_0133']
corrected=[]
for key in six:
    assert items[key].content==old_items[key].content and items[key].content in reviewed and items[key].content in draft
    corrected.append(dict(item_id=key,unchanged_task7_correction=True,retained_in_both_outputs=True))
assert reviewed.index('### EXM_0174')<reviewed.index('### EXP_0127')<reviewed.index('### PRC_0397')
assert 'visual-context warning' in reviewed and 'mortgage = P * R' not in reviewed
assert any(e['source_id']=='T0042' and '/steps/3' in e['fields'] for e in items['PRC_0397'].extraction_metadata['source_grounding']['evidence'])
relations=read(B/'duplicate_decisions.json')
assert Counter(d['classification'] for d in relations)=={'RELATED_BUT_DISTINCT':78,'PARTIAL_OVERLAP':13,'MEANINGFULLY_EQUIVALENT':1}
assert all(d['left'] in items and d['right'] in items for d in relations)
assert 'Equivalent statement: see **FCT_0016**' in reviewed
coverage=read(P/'coverage_report.json')
assert coverage['primary_units_with_knowledge']==50 and coverage['accepted_extraction_units']==48
unit_records={u['source_id']:u for values in coverage['sections'].values() for u in values}
assert not unit_records['T0004']['accepted_extraction'] and not unit_records['T0045']['accepted_extraction']
write('critical_defect_report.json',dict(literal_fidelity_census=critical,six_corrections=corrected,
    fizzbuzz=dict(incorrect_demo=True,explanation=True,correction=True,t0042_evidence=True,reviewed_order_checked=True),
    mortgage=dict(visual_warning_retained=True,complete_equation_approved=False,context_repaired_without_primary_inflation=True,
        invalidation_event=read(P/'invalidation_events.json')),
    recovered_sources=dict(task7_points_preserved=11,additional_source_backed_procedure='PRC_5001',
        coverage_exhaustive=False,unfinished_boundary_text_and_missing_visuals_not_reconstructed=True),
    duplicate_decisions_preserved=dict(Counter(d['classification'] for d in relations)),
    further_source_fact_cautions=['FCT_0252: source default-value assertion remains INCONCLUSIVE; prior runtime probe did not succeed.',
        'DEF_0060: immutability term supported, universal new-object claim PARTIALLY_SUPPORTED pending independent technical qualification.']))

before=read(P/'preservation_before.json')
preservation=dict(checked=len(before),changed=[path for path,h in before.items() if not Path(path).exists() or digest(Path(path))!=h],
    baseline_items_preserved=len(old_items),baseline_text_changes=text_changes,original_evidence_lost=lost_evidence,
    original_educational_reviews_lost=lost_reviews,authorization_and_quota_changed=False)
assert not preservation['changed']
write('preservation_checks.json',preservation)
full=test_results('full_regressions_verified.xml');focused=test_results('final_focused_regressions_v2.xml')
assert all(result[k]==0 for result in (full,focused) for k in ('failures','errors','skipped'))
ui=read(P/'static_ui_checks.json')
assert ui['javascript_syntax_valid'] and ui['html_ids_unique']
weights={'completeness':30,'accuracy_and_source_faithfulness':25,'explanation_quality':15,
    'organization_and_readability':10,'examples_and_code':10,'source_traceability':10}
assert sum(weights.values())==100
criteria={
    'completeness':'Independently inventory all material definitions, procedures, examples, formulas, explanations and qualifications; verify their retention. Unit presence is insufficient.',
    'accuracy_and_source_faithfulness':'Review every material claim against correct source context and, where needed, independently establish source factual correctness. No unresolved critical semantic defect.',
    'explanation_quality':'Check prerequisites, why/how, conditions, alternatives and error-to-correction explanations with a subject reviewer.',
    'organization_and_readability':'Independent reader checks logical progression, readability, terminology and navigation; preserve distinct information.',
    'examples_and_code':'Check literal provenance separately from behavioral correctness, compilation/execution where appropriate, deliberate-error labels, formulas and missing visuals.',
    'source_traceability':'Correct canonical source, quoted evidence, version, qualification scope, field binding and final-note retention for every approved claim.'}
protocol=dict(dimensions={name:dict(weight_percent=weight,acceptance=criteria[name],score=None) for name,weight in weights.items()},
    overall_score=None,independent_semantic_review_completed=False,independent_human_decisions=0,
    reproducible_sampling_plan=read(P/'sampling_plan.json'),
    sample_results=dict(risk=summary['sample_risk'],stratified_random=summary['sample_random'],
        reviewer_kind='assistant',scope='24 initially selected exact-evidence bundles only; not a population accuracy estimate.',
        scope_repair_follow_up='Three decisions were invalidated by the mortgage context repair and explicitly reviewed again. Initial sample findings and follow-up are separate records.'),
    critical_census='All 80 known adverse literal-fidelity field records checked for retained source evidence and withholding. This does not certify algorithm correctness.',
    full_regressions=full,final_overlapping_regressions=focused,visual_ui_test=ui['visual_browser_test'],
    supported_representation_types=[f.value for f in RepresentationFormat],readiness='NOT_VERIFIED_REVIEW_WORKFLOW_READY')
write('quality_benchmark_protocol.json',protocol)

policy='''# Review decisions, reuse and invalidation

The immutable review input and canonical source determine packet bindings. Every field remains an unsplit bundle; atomic claim counts are unknown until reviewers explicitly separate material assertions. Identical main/category text with identical evidence, full qualification context, instructional role, source version and primary/context permissions can share a packet. Auxiliary fields and superficially similar statements remain separate. The Task 7 equivalence link is preserved for presentation; its different wording/evidence does not receive an automatic shared approval.

An explicit decision targets the complete enumerated packet membership and includes reviewer identity/type, an aware timestamp, rationale, checked evidence/qualifications and a whole-bundle scope. Supported/partial decisions need valid, authorized quotations. Literal reconstructed code and incomplete equations cannot be approved as complete literal material. Partial status does not approve an entire field for the student subset.

Every decision appends to a hash-chained history; revisions and NOT_REVIEWED resets retain earlier records. This detects mutation but is not cryptographic authentication of a reviewer's identity. Names/type are explicitly supplied, not silently inferred. All actual new decisions in this delivery are assistant source comparisons, not human reviews.

Changing text, citations or offsets, item qualifications, roles/links, primary/context permissions or any canonical source-document content changes the binding. Source-version invalidation is deliberately conservative: a source-document change invalidates all its approvals. Stale records remain in history but do not approve current claims. In the real mortgage case, three earlier records were invalidated and three explicit follow-up reviews were recorded; no approval was auto-transferred.

Task 7 legacy records are pinned only after verifying the historical knowledge/source artifact hashes. Their original identity and rationale survive, with reviewed_at=null because no historical timestamp was recorded. Import time is separately recorded. Missing/invalid evidence permission or an incomplete equation cannot be grandfathered into a positive status.

Use review_input_knowledge.json as the continuing review input. knowledge_v8.json is a derived projection for existing field validators and rendering, not the ledger authority; its prior review records and per-field provenance are preserved in metadata. Re-ingesting a projection can conservatively change citation representations and require fresh bindings. The original source, immutable review input, decision history, legacy pin and relation records are the reproducible review package.

Neighbor context is bounded and explicitly context-only. It grants no new evidence permission. To use an additional passage, make an explicit source-backed citation repair, preserve primary identity, rebuild packets, then review affected bindings again. Quotes and mechanical validation do not establish entailment or factual truth.
'''
(P/'review_policy.md').write_text(policy,encoding='utf-8')
guide='''# Continue the offline review

Open evidence_desk.html locally in your browser. Search by text, item ID or source ID; filter by semantic status and risk priority. Open a packet to see the exact field bundle, source quotation, mechanical results, related claims, bounded context and prior provenance. The desk shows up to 120 matching packets at once; narrow the search to find more.

Review every assertion in the bundle. Supply your identity and explicitly choose the reviewer type. Choose a disposition and explain the reasoning, especially qualifications, missing support and contradictions. Supported/partial decisions require the evidence and qualification checkboxes. Adding/exporting a draft does not itself certify knowledge or authorize an API call. Downloads remain local.

From the backend directory, validate an exported batch into a NEW output directory:

```powershell
.venv/Scripts/python.exe import_semantic_reviews.py --knowledge data/output/task8_semantic_readiness_20261109/review_input_knowledge.json --source data/output/java_live_java-20261109_022409_842270/source_document.json --history data/output/task8_semantic_readiness_20261109/decision_history.json --relations data/output/task7_educational_completeness_20261109/duplicate_decisions.json --legacy-pin data/output/task8_semantic_readiness_20261109/legacy_provenance_pin.json --decisions PATH_TO_YOUR_EXPORTED_JSON --output data/output/task8_review_round_01
```

The importer validates current text/source bindings and hash-chain integrity before creating output. It never edits knowledge, authorization, credentials or quota files. It preserves previous history and writes a resolved workspace and another local evidence desk. Rejecting a stale decision requires renewed review of the changed packet; do not edit hashes to force acceptance.

This is a local static HTML tool. Static HTML/data/JavaScript checks passed, but visual browser testing was blocked by the available UI policies. Actual browser usability and an independent source/technical review remain outstanding.
'''
(P/'reviewer_guide.md').write_text(guide,encoding='utf-8')

b=read(B/'before_after.json')['after']
report=f'''# Task 8 — Evidence-backed semantic review and study-notes readiness

The safe offline workflow is implemented and tested. Both note outputs and the review desk are available. **The whole document is NOT VERIFIED**, no independent quality score is assigned, and no API request or live authorization was made.

## Before and after

| Measure | Task 7 | Task 8 |
| --- | ---: | ---: |
| Retained knowledge items | 469 | {summary['items']} |
| Substantive field leaves | 1,259 | {summary['fields']} |
| Source-comparison SUPPORTED fields | 75 | 102 |
| NOT_REVIEWED fields | 1,100 | 1,066 |
| Reviewed-subset item IDs | 35 | {summary['reviewed_items']} |
| Distinct displayed reviewed fields | 40 | {summary['reviewed_fields']} |
| Comprehensive-draft item IDs | No separate annotated full draft | 470 |
| Primary units with audit knowledge | 50 | 50 |
| Accepted historical extraction units | 48 | 48 |

There are {summary['exact_evidence_bundles']} exact-evidence review bundles for 1,265 fields: 416 repeated field presentations can be read together under strict identity constraints. **These are not counts of independent factual assertions.** A bundle may contain multiple material claims; the atomic count remains unassigned. The current statuses are {json.dumps(summary['statuses'])}. Common/category mirrors often repeat one assertion, so these totals must not be interpreted as accuracy percentages.

## Searchable inventory, evidence packets and decisions

`review_inventory.csv` and `review_inventory.json` cover every substantive field, including all 1,066 currently unreviewed fields. They retain exact item/path/text, canonical source IDs, quotes, original mechanical results, active evidence validity, semantic status, deterministic priority/reasons, related claims and same-source peers. `review_queue.json` is deterministic. `evidence_packets.json` and `evidence_desk.html` group only demonstrably identical reading tasks and provide explicit decision controls.

Priority order is previous adverse review, formulas/calculations, code/procedures, error/correction relationships, conditions/qualifications, multiple sources, uncertain transcription/OCR/visuals, and coverage priorities. Risk is scheduling metadata, never semantic proof. Default uncertain source assessments remain visible; they are not treated as confirmed source errors.

New decisions require a named actor/type, actual aware timestamp, explanation, evidence and qualification checks, source version and exact packet binding. The append-only ledger has {summary['explicit_decisions']} records, of which three became stale after a deliberate evidence-scope repair. Three fresh follow-up reviews were explicitly recorded. No human-review record was fabricated. Legacy reviews retain their recorded reviewer/rationale, unknown review timestamps and separately recorded import time, with baseline file hashes proving unchanged source/knowledge provenance.

No approval is transferred merely because a citation matches, a claim resembles another, or another field is supported. A source-document change invalidates the document's bindings conservatively. Text, citation, scope, instructional role or qualification changes also invalidate affected bindings. `review_policy.md` and `reviewer_guide.md` document reuse, invalidation and validated local imports. Hash chains detect history mutation; they do not authenticate a self-entered human identity.

## Actual source review and critical defects

The precommitted sample contains eight risk-selected bundles and 16 category-stratified, hash-ranked random bundles, without replacement. The seed, population, strata and exact IDs are preserved. Risk findings: {json.dumps(summary['sample_risk'])}. Random findings: {json.dumps(summary['sample_random'])}. These are assistant source-comparison findings for that sample only, not whole-document conclusions or independent review.

Partial/inconclusive findings include citations that omit a claimed return type, use a method name without explaining its behavior, omit a receiver/call spelling, or leave a procedural qualification unstated. The intended quit-loop summary in T0044 omits the source's warning that its initial string-comparison implementation does not work; it remains partial. The immutability term is supported, while DEF_0060's blanket new-object assertion remains partial pending independent technical qualification. The array-default source assertion FCT_0252 remains inconclusive; the prior local Java probe did not complete, so no successful runtime verification is claimed.

All 80 existing adverse literal-fidelity field records were revisited through their saved source evidence and checked for continued withholding. They correspond to 40 repeated reconstructed snippets, not 80 independently wrong algorithms. No unsupported snippet appears in either note output. This census confirms retention of the source-fidelity disposition and the withholding boundary; it does not newly certify each snippet's technical behavior.

FizzBuzz now retains the labelled incorrect example, the previously missing reviewed explanation EXP_0127, the corrected procedure/example and T0042 evidence. Full T0041 evidence was explicitly associated with the explanation, and its instructional role is recorded. The reviewed order is incorrect demonstration → explanation → correction. The mortgage field review had cited T0033 without an item-level source association. That context is now explicitly associated, with T0031 still primary; the invalidation/re-review trail is preserved. The equation remains partial and visually incomplete. Only separately reviewed P/R definitions enter the subset, under an explicit visual-context warning.

All six Task 7 corrected assertions remain unchanged and present in both outputs. All 92 duplicate relationships remain: 78 distinct, 13 partial overlaps and one presentation equivalence link. Every original item, quotation and educational-review record is retained. The equivalence does not silently share semantic approval across its different source scope/wording.

## Educational coverage and the additional recovery

The 11 Task 7 recovered points are preserved. They cover important T0004 setup/package concepts and T0045 behavior/timing, but did not retain the explicit do-while construction sequence. One new, source-backed prose procedure PRC_5001 now preserves do, the body/code block, the trailing while condition and terminating semicolon. Its six fields received explicit timestamped assistant review. No complete program, method name or missing formula was invented.

`coverage_report.json` is hierarchical and separates source-unit presence, actual accepted extraction (mapped from the saved request manifest/audit), explicitly inventoried educational topics, field-level review and final-note retention. It uses actual source headings where available and clearly editorial Task 7 headings otherwise. The source-backed topic inventory covers 12 named points in T0004/T0045 and is explicitly partial. All other source units still require an independent material-topic inventory, checking definitions, procedures, examples, formulas, explanations and qualifications. Absence of a typed knowledge category alone is not declared a missing teaching point.

Primary inventory presence remains 50/50, while accepted extraction remains 48/50. Context and offline recovery never become successful historical operations. Existing failed chunks and four unapproved recovery drafts are unchanged. No remaining gap has yet been proven to require a live request: inspect existing saved knowledge first. Missing original visuals/literal code or factual errors in the source cannot be repaired by inventing text in another model call.

## Two note outputs and adaptive representations

`reviewed_study_notes_v8.md` shows only adequately source-reviewed fields, with explicit coverage limitations and the incomplete-formula warning. It displays 46 item IDs and 62 distinct fields, including labels, independently reviewed procedure steps and an equivalence cross-reference; those item counts do not mean 46 complete item schemas are certified.

`comprehensive_review_draft_v8.md` retains all 470 items and accounts for every one of the 1,265 fields as displayed, mirrored or explicitly withheld. Reviewed, uncertain, withheld and incomplete content are labelled. Unsafe original text and extensive evidence stay in companion artifacts. The draft is explicitly UNVERIFIED; no mechanical item-retention total is presented as semantic completeness.

The existing nine representation types and renderer remain available and tested. `adaptive_representations.json`, `adaptive_pipeline_preview.md` and pipeline gates preserve the existing adaptive path; the annotated comprehensive draft adds field-level review states and retention accounting. No unsupported comparison/timeline/diagram is forced onto unsuitable content. This real document does not need to instantiate all nine types. No Java-specific production extraction or review rule was added.

## Independent-quality benchmark and tests

`quality_benchmark_protocol.json` defines completeness 30%, accuracy/source faithfulness 25%, explanation quality 15%, organization/readability 10%, examples/code 10%, and traceability 10%, with evidence requirements and acceptance criteria for each. All dimension scores and the overall score remain unassigned. There has been no independent human semantic/educational review, so no weighted quality score is justified. Deterministic artifact checks are distinct from the assistant source-review sample and from independent technical verification of the source itself.

The applicable broad offline suite passed {full['tests']} tests with 0 failures/errors/skips. The final overlapping workflow/safeguard/renderer batch passed {focused['tests']} tests with 0 failures/errors/skips, including the final formula-component warning refinement. Do not add overlapping totals. The suites cover authorization/quota controls, source/evidence contracts, review history, invalidation, atomic-count honesty, importer rejection, source/topic coverage separation and all nine representation contracts. New workflow fixtures cover mathematics, programming, biology, physics, history, research, manuals and lecture transcripts; they are labelled synthetic and do not establish quality on real documents from all eight domains.

The launcher denies network connections, removes API-key environment entries and guards Windows multiprocessing. Real-provider integration and the two Windows-disabled Docling suites were explicitly excluded, not counted among passes/skips. No OCR or live-model improvement is claimed. An initial targeted test found an empty defaultdict source entry inflating coverage; it was fixed by counting nonempty primary memberships. An initial build rejected the legacy mortgage scope rather than silently approving it; the source association was then repaired with a genuine invalidation trail.

Static HTML, embedded data, control references and JavaScript syntax checks passed. **Visual browser testing was not completed.** Automatic approval review rejected reading an existing unrelated Chrome window; a separate in-app browser then blocked local-file URLs. No browser-policy workaround was used. Browser usability and independent reader assessment remain outstanding.

## Preservation and next readiness decision

{preservation['checked']} historical/control files were hash-checked with no changes. All 469 Task 7 items, all their substantive text, grounding evidence and educational-review records survive. The original 458 items and 11 recovery points remain intact, plus the additional prose procedure. Credential, model/provider, authorization, request and quota accounting records were not changed; the configured 85% policy is untouched.

**Readiness: NOT VERIFIED — offline review workflow ready for continued review.** Outstanding work includes 1,066 unreviewed fields, partial/inconclusive assertions, comprehensive source-to-topic assessment, original visual/code evidence, independent factual checking and learner usability review. The next step is to open the local evidence desk and continue version-bound review, not to authorize a full rerun. The workflow steadily expands the supported subset while retaining the broader draft and all unresolved information.

## Modified files and deliverables

Production additions: `app/evaluation/semantic_review.py`, `app/evaluation/review_outputs.py`, and `import_semantic_reviews.py`. `app/evaluation/offline_recovery.py` adds a versioned heading and preserves incomplete-formula warnings when only components are reviewed. `tests/test_semantic_review_workflow.py` adds focused cross-domain and safety regressions. Prompts, extraction schema, source policy, providers, authorizers and quota code were not changed.

All new artifacts are under `data/output/task8_semantic_readiness_20261109/`: the two note outputs; searchable JSON/CSV inventory; risk queue; evidence packets/desk; immutable `review_input_knowledge.json`; projected `knowledge_v8.json`; decision inputs/history; legacy provenance pin; sampling plan/findings; invalidation events; critical-defect and coverage reports; benchmark protocol; reviewer guide/policy; adaptive representations/preview/gates; preservation checks; static UI checks; and regression XML/logs. Build, static-check and finalization scripts make the offline package reproducible.
'''
(P/'task8_report.md').write_text(report,encoding='utf-8')
write('artifact_manifest.json',dict(version=8,artifacts={p.name:digest(p) for p in P.iterdir() if p.is_file() and p.name!='artifact_manifest.json'},
    request_manifest_created=False,overall_quality_score=None))
print(json.dumps(dict(full_tests=full,focused_tests=focused,preservation=preservation,readiness='NOT_VERIFIED_REVIEW_WORKFLOW_READY')))
