"""Reconcile actual artifacts and prepare the independent-human pilot handoff."""
import json,re,subprocess
from pathlib import Path
from hashlib import sha256
from collections import Counter
from html.parser import HTMLParser
import xml.etree.ElementTree as ET

P=Path('data/output/task9_review_pilot_20261109');B=Path('data/output/task8_semantic_readiness_20261109')
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(name,value):(P/name).write_text(json.dumps(value,indent=2,ensure_ascii=False),encoding='utf-8')
def digest(p):return sha256(p.read_bytes()).hexdigest()
def tests(name):
    return {k:sum(int(s.attrib.get(k,0)) for s in ET.parse(P/name).getroot().iter('testsuite')) for k in ('tests','failures','errors','skipped')}

pilot=read(P/'pilot_workspace.json');selection=read(P/'pilot_selection_manifest.json')
accounting=read(P/'accounting.json');baseline=read(B/'review_workspace.json')
browser=read(P/'browser_checks.json');transport=read(P/'transport_validation.json')
full=tests('full_regressions_final.xml');targeted=tests('targeted_regressions.xml')
assert all(result[k]==0 for result in (full,targeted) for k in ('failures','errors','skipped'))
assert len(pilot['packets'])==30 and len(pilot['inventory'])==47
assert len({p['packet_id'] for p in pilot['packets']})==30
assert sum(len(p['members']) for p in pilot['packets'])==47
assert read(P/'independent_pilot_decisions.json')==[]
assert all(c['result'] is True for c in browser if c['test']!='baseline_layout')
assert transport['actual_pilot_decisions']==0 and transport['import_roundtrip_passed'] and transport['history_preserved']
index={r['key']:r for r in pilot['inventory']}
baseline_rows={r['key']:r for r in baseline['inventory']}
for row in pilot['inventory']:assert row==baseline_rows[row['key']]
assert all(p['source_version']==baseline['source_version'] for p in pilot['packets'])

# No real decision justifies an educational-content rewrite in this task.
notes_comparison=dict(task9_notes_rebuild=False,reason='No actual independent pilot judgments are available; user chose human review later.',
    reviewed_subset=dict(path=str(B/'reviewed_study_notes_v8.md'),sha256=digest(B/'reviewed_study_notes_v8.md'),item_ids=46,displayed_fields=62),
    comprehensive_draft=dict(path=str(B/'comprehensive_review_draft_v8.md'),sha256=digest(B/'comprehensive_review_draft_v8.md'),items=470,fields=1265),
    dimensions={key:'UNCHANGED_FROM_TASK8; no new semantic judgment or content revision' for key in
        ('educational_content_retained','confirmed_mistakes_corrected','important_topics','unresolved_warnings','repetition','chapter_organization','formula_and_code_fidelity','readability')},
    confirmed_new_educational_defects=0,whole_document_verified=False,quality_score=None)
write('notes_comparison.json',notes_comparison)
remaining=[dict(key=r['key'],packet_id=r['packet_id'],claim=r['claim'],source_ids=r['source_ids'],evidence=r['evidence'],
    current_status=r['semantic_status'],scope='Existing Task 8 disposition; no independent Task 9 finding.',risk_is_semantic_proof=False)
    for r in baseline['inventory'] if r['semantic_status'] in ('UNSUPPORTED','CONTRADICTED','PARTIALLY_SUPPORTED','INCONCLUSIVE')]
write('remaining_critical_inventory.json',dict(existing_non_supported_dispositions=remaining,
    counts=dict(Counter(r['semantic_status'] for r in baseline['inventory'])),
    known_literal_fidelity_fields=80,known_literal_snippets=40,
    categories=dict(nonliteral_code='Original code remains withheld; only provenance failure is established, not algorithmic behavior.',
        incomplete_formula='Original mortgage visual still required; reviewed component definitions do not complete the equation.',
        factual_source_uncertainty='Array-default source assertion needs independent technical assessment.',
        lost_qualifications='Partial definitions, procedural summaries and cited-method details need genuine review.',
        educational_completeness='Unit presence and note-item retention do not establish exhaustive topic coverage.'),
    task9_human_confirmed_defects=None,independent_pilot_status='AWAITING_HUMAN_REVIEW'))

efficiency=dict(actual_independent_bundles_reviewed=0,actual_independent_fields_reviewed=0,
    atomic_claims_in_sample=None,atomic_claims_independently_certified=None,
    actual_pilot_decisions={s:0 for s in ('SUPPORTED','PARTIALLY_SUPPORTED','UNSUPPORTED','CONTRADICTED','INCONCLUSIVE')},
    confirmed_critical_educational_defects_from_pilot=None,time_per_human_reviewed_bundle_seconds=None,
    actual_human_source_change_invalidations=0,remaining_unreviewed_fields=1066,
    synthetic_transport=dict(browser_export_records=1,imported_history_records=1,exact_replay_added_records=0,
        invalid_files_rejected=len(transport['invalid_files']),source_change_invalidated_records=1,unexpected_import_errors=0),
    browser_download_wait_tool_elapsed_seconds=910.0029,
    timing_caveat='Observed automation-tool return latency, not human review duration or a reliable browser-download performance measurement.',
    semantic_accuracy_percentage=None,quality_score=None)
write('review_efficiency.json',efficiency)

def fence(text):return '`'*(max((len(x) for x in re.findall(r'`+',text)),default=0)+3)
lines=['# Thirty-bundle independent semantic-review pilot','',
    '**AWAITING HUMAN REVIEW.** Existing dispositions below are historical assistant source comparisons. No independent pilot decisions have been completed.','',
    'Source version: `'+selection['source_version']+'`','',
    'The 30 bundles cover 47 field leaves, not an established number of atomic claims. Review every assertion and qualification in each bundle.','']
packets={p['packet_id']:p for p in pilot['packets']}
for selected in selection['bundles']:
    p=packets[selected['packet_id']];rows=[index[k] for k in p['members']]
    lines.extend(['## '+str(selected['rank'])+'. '+', '.join(p['members']),'',
        'Packet: `'+p['packet_id']+'`','',
        'Selected because: '+' '.join(selected['reasons']),'',
        'Current historical statuses: '+', '.join(r['key']+' = '+r['semantic_status'] for r in rows)+'.','',
        'Independent pilot judgment: **PENDING**.','',
        'Exact generated claim / unsplit field bundle:',fence(p['claim'])+'text',p['claim'],fence(p['claim']),'',
        'Primary sources: '+', '.join(p['source_scope']['primary'])+'. Context sources: '+(', '.join(p['source_scope']['contextual']) or 'none')+'.',''])
    if p['source_scope']['formula_status'] not in (None,'COMPLETE') and any(r['knowledge_type']=='formula' for r in rows):
        lines.extend(['**Warning: incomplete / visual-dependent formula. Do not approve a complete equation from its components.**',''])
    if any(r['semantic_status'] in ('UNSUPPORTED','CONTRADICTED') for r in rows):
        lines.extend(['**Warning: existing adverse disposition. Preserve the distinction between source fidelity and technical correctness.**',''])
    if p['source_scope']['role']!='unresolved':lines.extend(['Instructional role: '+p['source_scope']['role']+'.',''])
    seen=set()
    for q in p['evidence']:
        if (q['source_id'],q['quote']) in seen:continue
        seen.add((q['source_id'],q['quote']))
        lines.extend(['### Canonical quote — '+q['source_id'],'',fence(q['quote'])+'text',q['quote'],fence(q['quote']),''])
    lines.extend(['### Neighbor context — not newly authorized evidence',''])
    for c in p['neighbor_context']:
        lines.extend([c['source_id']+' · canonical characters '+str(c['start_char'])+'–'+str(c['end_char'])+' · '+c['evidence_permission'],
            fence(c['text'])+'text',c['text'],fence(c['text']),''])
    related=[x for r in rows for x in r['relationships']]
    lines.extend(['Relationships: '+json.dumps(related,ensure_ascii=False),'',
        'Mechanical results: '+json.dumps([r['mechanical_validation'] for r in rows],ensure_ascii=False),'',
        'Review controls: SUPPORTED / PARTIALLY_SUPPORTED / UNSUPPORTED / CONTRADICTED / INCONCLUSIVE. Record identity, rationale, evidence scope and this exact version.',''])
(P/'pilot_review_packets.md').write_text('\n'.join(lines),encoding='utf-8')

# Verify embedded HTML data and JavaScript without external requests.
class Parser(HTMLParser):
    def __init__(self):super().__init__();self.scripts=[];self.current=None;self.ids=[]
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if 'id' in attrs:self.ids.append(attrs['id'])
        if tag=='script':self.current=dict(attrs=attrs,text='')
    def handle_data(self,data):
        if self.current is not None:self.current['text']+=data
    def handle_endtag(self,tag):
        if tag=='script' and self.current is not None:self.scripts.append(self.current);self.current=None
parser=Parser();parser.feed((P/'pilot_desk.html').read_text(encoding='utf-8'))
assert len(parser.ids)==len(set(parser.ids))
embedded=json.loads(next(s['text'] for s in parser.scripts if s['attrs'].get('type')=='application/json'))
assert len(embedded['packets'])==30
script='\n'.join(s['text'] for s in parser.scripts if s['attrs'].get('type')!='application/json')
assert all(name in parser.ids for name in re.findall(r"el\('([^']+)'\)",script))
(P/'review_desk_script.js').write_text(script,encoding='utf-8')
checked=subprocess.run(['node','--check',str(P/'review_desk_script.js')],capture_output=True,text=True,timeout=15)
assert checked.returncode==0,checked.stderr
write('static_ui_checks.json',dict(unique_control_ids=True,embedded_pilot_data_valid=True,javascript_syntax_valid=True))

preservation=read(P/'preservation_before.json')
changed=[path for path,h in preservation.items() if not Path(path).exists() or digest(Path(path))!=h]
assert not changed
write('preservation_checks.json',dict(files_checked=len(preservation),changed=changed,actual_pilot_decisions=0,
    historical_review_history_unchanged=True,original_evidence_unchanged=True,authorization_and_quota_unchanged=True))

guide='''# Human reviewer handoff — Task 9

The pilot is awaiting a real independent reviewer, as requested by the user. Existing source-comparison statuses are historical assistant judgments, not completed pilot decisions. The sample contains difficult and easier cases across 30 exact-evidence bundles / 47 fields. Its atomic claim count is unknown.

Open pilot_desk.html locally in your normal browser. Alternatively, from the backend directory start the approved read-only loopback test server:

```powershell
.venv/Scripts/python.exe data/output/task9_review_pilot_20261109/serve_review_desk.py
```

Visit the printed pilot URL in the browser on that computer. Only three named HTML review pages are served, with no directory listing or write/upload route. It binds 127.0.0.1 only. Stop it with Ctrl+C when done. The agent's test server has already been stopped.

Search by claim, item/source ID or quotation; filter by current status and risk priority. Use Source buttons to jump to exact quotes, View item to inspect the other fields as context, and the Review controls link to return directly to the form. Full metadata remains in expandable panels. Prominent warnings distinguish incomplete equations, adverse dispositions and missing evidence. Neighbor context gives no new evidence permission.

Make your own source-backed judgment for the whole bundle: SUPPORTED, PARTIALLY_SUPPORTED, UNSUPPORTED, CONTRADICTED or INCONCLUSIVE. Do not mistake exact quotation for factual truth. Check all claims, scope, exceptions, source errors and deliberate-error/correction roles. Use INCONCLUSIVE when the needed original visual/code or technical verification is unavailable. NOT_REVIEWED is a reset, not a completed pilot judgment.

Enter your real identity and select Human only if a person is actually performing this review. Explain your judgment. Positive/partial decisions need the evidence/qualification checkboxes. Adding a draft does not certify the knowledge. Unsent form entries survive navigation in the current tab, but session drafts are not persisted to the server; export before closing/reloading. Revisiting a bundle can create a genuine follow-up record. Re-importing the same decision, including a different member order or equivalent timezone spelling, cannot inflate counts or restore an approval later withdrawn.

Export after completing the pilot and supply the file for validated import. A pilot completion count must use distinct, currently valid reviewed bundles; export rows, history records, fields and atomic claims are different measures. Any source/text/scope change requires renewed review of affected bindings. Extensive packets are also available in pilot_review_packets.md and pilot_evidence_packets.json.

The following command validates an actual future export into a NEW directory; it was not run with human decisions during Task 9:

```powershell
.venv/Scripts/python.exe import_semantic_reviews.py --knowledge data/output/task8_semantic_readiness_20261109/review_input_knowledge.json --source data/output/java_live_java-20261109_022409_842270/source_document.json --history data/output/task8_semantic_readiness_20261109/decision_history.json --relations data/output/task7_educational_completeness_20261109/duplicate_decisions.json --legacy-pin data/output/task8_semantic_readiness_20261109/legacy_provenance_pin.json --decisions PATH_TO_YOUR_EXPORT --output data/output/task9_human_review_round_01
```

Source comparison by a genuine independent person and independent technical verification of an erroneous source are different scopes. Record any technical checks honestly; do not mark a source-only comparison as an executed/independent technical check. A name entered into a local form is a self-declared identity, not cryptographic authentication. No release certification or quality score follows from the sample alone.
'''
(P/'human_review_handoff.md').write_text(guide,encoding='utf-8')

report=f'''# Task 9 — Review-desk validation and independent semantic-review pilot

The review desk was exercised in a permitted browser over an approved, read-only host-loopback server. Two necessary software issues were corrected: reviewer navigation/warning presentation, and replay of old decisions after withdrawal. The 30-bundle pilot is prepared and **AWAITING INDEPENDENT HUMAN REVIEW**, following the user's explicit preference. No actual pilot judgment was fabricated, no educational content was rewritten, and the full document remains NOT VERIFIED.

## Browser findings and targeted corrections

The original mortgage packet exposed approximately 17,500 characters of repeated scope/citation JSON. Its decision controls were approximately 6,542 pixels below the viewport, and the visual-context limitation appeared inside metadata rather than as a prominent warning. The revised desk shows deduplicated exact quotations as source cards, retains original records in expandable metadata, provides direct item/source and previous/next navigation, and links directly to review controls. At the measured 720-pixel viewport, the save control was visible at y=479.5–518.7 after using that link. Unsent form entries survive switching between bundles in the current tab.

Prominent warnings now distinguish incomplete formulas, reconstructed literal code, adverse dispositions, missing evidence and partial/inconclusive support. The 30-bundle header explicitly says awaiting human review. Source cards preserve primary versus contextual identity; neighbor context remains explicitly unauthorized for new evidence use. Search covers quotations as well as claims and IDs, and filters correctly handle zero results. A selected packet outside the current filter remains clearly identified rather than silently changing the decision target.

Actual browser checks passed for search, quote search, status/priority filters, empty results, item/source navigation, neighbor context, error/correction warnings, unsent form retention, and local draft/export controls. Missing identity and affirmative review without valid evidence were rejected in synthetic fixtures. A deliberately contradictory synthetic fixture displayed its warning. No real pilot decision was entered. Browser console checks reported no page errors on the pilot desk. Evidence is in browser_checks.json, baseline_browser.png and review_desk_validated.png.

The original sandboxed listener was unreachable because socket access was restricted. The explicitly authorized local test-server workflow was run on host loopback with approval, serving only named review HTML pages on 127.0.0.1, with no directory listing, POST or credential/source-tree access. No browser warning, local-file URL policy or security barrier was bypassed. The test listener was stopped after testing.

One automation download-wait call returned after 910.0029 seconds. The exported file was successfully retrieved and validated, but this observation is not a reliable browser-download performance measurement and is not human review time. Two selector/key automation attempts required different supported page actions; they did not create judgments. Testing was limited to the available in-app desktop browser; cross-browser/mobile and independent-person usability have not been established.

## Exact accounting

| Measure | Reconciled result |
| --- | ---: |
| Original knowledge items | 458 |
| Task 7 recovered source-supported items | 11 |
| Additional Task 8 item | 1 — PRC_5001 |
| Total Task 8 items preserved | 470 |
| Substantive field records | 1,265 |
| Exact-evidence bundles | 849 |
| NOT_REVIEWED field records | 1,066 |
| Existing SUPPORTED field dispositions | 102 |
| Reviewed subset item IDs | 46 |
| Distinct displayed reviewed fields | 62 |
| Item schemas with all substantive field dispositions SUPPORTED | 24 |
| Atomic factual claims | Not established |

PRC_5001 is the source-backed do-while construction procedure recovered offline in Task 8 from T0045. Its six fields and provenance are recorded in Task 8 changes.json and review_input_knowledge.json. It was not a new successful API request. The 46 displayed item IDs include partially retained items and the equivalence cross-reference; they are not 46 fully reviewed item schemas. Even the 24 all-supported schemas carry existing source-comparison dispositions, not independent whole-document certification. accounting.json recomputes these counts from actual rows/mappings.

## Thirty-bundle selection and evidence packets

The manifest records the seed, canonical source version, baseline workspace hash, population of 849 bundles, member fields and every selection rationale. Selection starts with predeclared difficult/critical categories, adds one hash-ranked unreviewed draw per available knowledge category, then fills with hash-ranked unreviewed bundles to exactly 30 unique bundles / 47 fields. This is a purposeful review pilot, not a representative population accuracy estimator.

The sample includes known nonliteral code and embedded procedure fragments; the incomplete mortgage equation; source-factual uncertainty and overgeneralization; deliberately incorrect demonstrations and their explanations/corrections; contrasting mathematical expressions; conditions/qualifications; multi-source associations; recovered points/procedures; definitions, explanations, numeric claims and lower-priority material. All available named critical categories are represented, but 30 bundles cannot cover every known problematic instance. The complete remaining-disposition inventory remains separate.

pilot_desk.html, pilot_review_packets.md and pilot_evidence_packets.json expose exact claims, field membership, canonical quotes, bounded neighboring context, instructional relationships, warnings and existing mechanical/current review results. Existing assistant dispositions are visible as history and are not counted as independent pilot decisions. The selection and source versions are fixed before human review. pilot_decision_template.json contains placeholders only, and independent_pilot_decisions.json is empty.

## Import/export, history and stale-version validation

An actual browser download from the synthetic test desk contained one assistant-labelled INCONCLUSIVE transport record. It was imported into a synthetic-only directory using the normal CLI. Re-import retained one record. Seven invalid files were rejected before output creation: stale source, unknown status, missing identity, missing rationale, incomplete membership, a non-list payload and malformed JSON. Changing the synthetic source invalidated its recorded decision without rewriting the history. These are software transport tests, not real-document semantic findings.

A regression first reproduced a safety defect: after a withdrawal, re-importing the old approval appended it again and restored the old state. The fix makes the same review input idempotent, normalizing packet-member order and equivalent timestamp timezones for replay comparison. Earlier hashed history is preserved, a withdrawal stays effective, and genuinely new rationale/time follow-ups still append. This prevents accidental approval resurrection and duplicate review-count inflation. It does not authenticate a self-declared reviewer or automatically establish that a person reviewed a claim.

## Actual review results and efficiency

Completed independent bundles: **0**. Completed independent fields: **0**. Human pilot judgments: **0**. Actual supported/partial/unsupported/contradicted/inconclusive pilot decision counts are all zero. Confirmed critical educational defects from this independent pilot and time per human-reviewed bundle are unassigned because the pilot has not been conducted. Atomic claim counts remain unknown. The existing unreviewed backlog remains 1,066 fields.

There was one synthetic browser export/import, zero unexpected synthetic import errors, seven expected invalid-file rejections, and one synthetic source-version invalidation. The replay fix is a confirmed workflow defect repair; it is not a new confirmed educational-content correction. Existing Task 8 invalidations and historical assistant judgments are not recounted as Task 9 human reviews. review_efficiency.json separates all of these measures and leaves every semantic accuracy/quality score unassigned.

## Remaining defects and notes comparison

The existing 80 adverse literal-fidelity field records (40 reconstructed snippets), 12 partially supported fields and five inconclusive fields remain in remaining_critical_inventory.json with source evidence and scope. These are existing dispositions, not new independent judgments. The incomplete original mortgage visual, source-factual checks, qualification/evidence gaps and comprehensive educational-topic review remain outstanding. High risk is not proof of a defect, and a matching quote is not proof of factual truth.

No new semantic judgment justifies a Task 9 study-notes rewrite. Task 8 reviewed_study_notes_v8.md and comprehensive_review_draft_v8.md remain byte-for-byte unchanged, separate and explicitly limited. Educational retention, known corrections, topics, warnings, repetition, chapter organization, formula/code fidelity and readability therefore have no new content change to claim. notes_comparison.json records their paths and hashes. The interface improvement must not be reported as increased educational accuracy.

## Regression results, preservation and readiness

The final applicable offline suite passed **{full['tests']} tests**, with 0 failures, 0 errors and 0 skips. The final overlapping review-targeted suite passed **{targeted['tests']} tests**, with no failures/errors/skips. Do not add overlapping totals. The first replay regression failed before the fix; it now passes. An older synthetic test was adjusted to distinguish a genuine follow-up rationale from an identical replay. The broad suite retains strict source/evidence, authorization, quota, renderer and recovery regressions. Real-provider tests and the Windows-disabled Docling suites were explicitly excluded. The launcher denies network connections and removes API-key environment entries.

{len(preservation)} historical/control files were verified unchanged, including all Task 8 artifacts and original evidence/history. No Groq/provider call, live extraction, authorization change or quota-accounting change was made. Production changes are confined to the review HTML/template renderer and the small replay-safety fix; no Java-specific production rule or new review framework was introduced.

**Next readiness: REVIEW DESK VALIDATED; INDEPENDENT PILOT AWAITING HUMAN REVIEW.** The next step is for the designated human to perform the 30-bundle review and export genuine decisions for version validation. Only those actual decisions can justify source-backed corrections and a separate notes preview. Full-document semantic, topic-completeness and usability release criteria remain unmet. No overall score is assigned.

human_review_handoff.md contains the local server, review and import steps. The package also includes the selection manifest, searchable desk, full packets, accounting, empty actual pilot ledger, synthetic transport evidence, remaining critical inventory, efficiency/notes comparison, regression logs/XML, screenshots and preservation checks.
'''
(P/'task9_report.md').write_text(report,encoding='utf-8')
write('readiness.json',dict(state='REVIEW_DESK_VALIDATED_AWAITING_INDEPENDENT_HUMAN_PILOT',
    human_review_requested_later=True,independent_bundles_reviewed=0,backlog_unreviewed_fields=1066,
    new_educational_preview_created=False,whole_document_verified=False,overall_quality_score=None))
write('artifact_manifest.json',dict(version=9,files={p.name:digest(p) for p in P.iterdir() if p.is_file() and p.name!='artifact_manifest.json'},
    actual_independent_pilot_decisions=0,no_api_calls=True))
print(json.dumps(dict(full_tests=full,targeted_tests=targeted,pilot_bundles=30,pilot_fields=47,
    human_reviewed=0,preservation_files=len(preservation),historical_changes=changed,readiness='AWAITING_HUMAN_REVIEW')))
