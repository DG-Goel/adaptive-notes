"""Write the delivery report from release results; never touch historical records."""
from pathlib import Path
import json

OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[2]


def main():
    stats=json.loads((OUT/'test_summary.json').read_text(encoding='utf-8'))
    preservation=json.loads((OUT/'preservation_checks.json').read_text(encoding='utf-8'))
    hashes=json.loads((OUT/'modified_files_release.json').read_text(encoding='utf-8'))
    profile=json.loads((OUT/'request_version_comparison.json').read_text(encoding='utf-8'))
    files='\n'.join('- ['+p+']('+str(ROOT/p).replace('\\','/')+')' for p in hashes)
    report=f'''# Task 12A — Evidence-locked, no-invention generation

**Status: feasible offline implementation complete. Outputs remain UNVERIFIED_PREVIEW.**
This is Step 1 only. No multimedia recovery, new parser, external evaluator or later
implementation phase was introduced. The Task 9 pilot remains READY_FOR_HUMAN_REVIEW.

## Root causes found

1. The existing exact-quote/field validators established mechanical provenance, not
   whether every assertion in a field followed from its quotation. Unsupported
   additions could therefore hide inside otherwise supported prose.
2. Required factual fields encouraged completion when code, an expression or a label
   was missing. There was no dedicated factual-row alternative for abstention.
3. Generation did not carry an atomic distinction between explicit statements,
   proposed direct entailments and assumptions, or persist content availability
   independently of human semantic decisions.
4. Code/formula safeguards primarily lived in the reviewed-preview flow. The direct
   selector/assembler/renderer route could run first. Citation to a nearby passage
   could be mistaken for proof of literal code; separate fragments could be joined
   into a block absent from the source.
5. Some selector paths synthesized generic comparison properties, hierarchy roots or
   timeline labels. These were formatting structures unsupported by typed knowledge.
6. Exact consolidation ignored generation dispositions, risking the loss of distinct
   mistake/correction, availability or abstention context.

## Prompt and schema changes

The current canonical policy now uses schema name **canonical_evidence_first_12a_v1**
and generation policy **evidence_first_12a_v1**. The existing configuration selector
`canonical_grounded_v4` is retained for interface compatibility; regenerated messages,
schema bytes and request hashes change. No Stage A code was changed.

- Source-only prompts explicitly permit faithful paraphrases and simplification while
  prohibiting new facts, assumed results, reconstructed code/equations and forced fields.
- Values may carry atomic `claims`, each with text, supplied refs, basis, availability,
  literal kind, instructional role and related refs. The outer text must equal the
  claim texts joined by one space, so additions cannot escape the claim inventory.
- Basis distinguishes explicit, direct_entailment, assumed and unresolved. A model's
  label is a proposal, not a semantic certificate.
- A missing required value may instead be a category abstention with availability,
  primary source IDs and reason. Unsupported optional fields remain null. No fake
  quotation or required-field placeholder is manufactured.
- Closed objects, complete required-property lists and existing strict schemas remain.
  The older evidenced value shape remains readable; it does not bypass deterministic
  screening. New refs are checked against the existing quote catalog and field scope.
- Contradictory exclusions, context-only extraction/exclusion, bad markers, fake refs,
  unknown fields, stale annotations and missing source spans remain rejected.

The schema uses nested unions and reusable definitions described by the official
[Groq structured-output documentation](https://console.groq.com/docs/structured-outputs).
Local JSON Schema validity does **not** establish acceptance by the deployed provider;
the exact new schema has not been tested live.

Prompt budgeting counts the complete system prompt and schema. In the saved
same-chunk comparison, system length is {profile['system_characters']} characters and
schema length is {profile['schema_characters']} characters. Estimated input is
{profile['input_tokens_estimated']} tokens with {profile['output_tokens_reserved']}
output tokens reserved. These are existing local estimates, not measured provider
token usage. No quota ceiling, tokenizer assumption or 85% policy was changed.

## Availability versus semantic review

The eight availability labels are SOURCE_SUPPORTED, PARTIALLY_SUPPORTED,
SOURCE_MISSING, VISUAL_CONTEXT_REQUIRED, AMBIGUOUS_SOURCE, CONTRADICTORY_SOURCE,
INCOMPLETE_LITERAL and REVIEW_REQUIRED. They live inside existing
`extraction_metadata.source_grounding`, alongside original evidence and generation
annotations. They do not replace EducationalReview/FieldReview decisions.

SOURCE_SUPPORTED can mean observed literal source availability; it does not certify
world truth, instructional correctness or semantic entailment. All new generation
claims remain semantically unverified. Existing validated review decisions are read,
never generated or rewritten. Semantic support and literal fidelity remain distinct:
a reviewed paraphrase cannot turn non-source code into a literal source block.

Abstentions do not exclude a unit, complete its coverage or consume another concept.
When independently supported items exist, their notes retain the unavailable-category
notice and source IDs. All-abstention responses retain their records in the extraction
audit, with source coverage unresolved.

## Evidence preservation and no-reconstruction behavior

- Mechanical quotation, source-ID, chunk-membership, field-path and exact-span checks
  run before disposition attachment. Their original evidence records remain intact.
- Atomic claims preserve their specific source IDs, quotations and supplied character
  offsets. Related refs must already be authorized field evidence; neighboring text
  is never silently promoted into evidence.
- Clear unsupported numbers, lost qualification signals, absent literal code,
  reconstructed/incomplete expressions, assumptions and unsourced placeholders are
  quarantined. Signals do not claim to prove general semantic contradiction.
- Qualification matching recognizes ordinary equivalents such as may/possible and
  under/when/if, reducing avoidable paraphrase suppression.
- Literal code requires the whole presented block to occur in its cited evidence.
  Individually valid fragments cannot establish a newly concatenated program.
- Formula fragments cannot become complete formulas. Variable meanings and other
  supported fields remain available. A reviewed complete formula can retain its
  display while unconfirmed optional variable descriptions are withheld.
- Original candidate text is retained in knowledge/audit artifacts. Student display
  keeps eligible claims and explicitly identified source passages, rather than
  silently repairing unsupported text from model knowledge.

## Instructional context and final representations

The existing role vocabulary and relationships are reused. New role/related-ref
annotations remain proposals, not human review links. Source references to a mistake
and its correction are retained together; incorrect demonstrations receive an explicit
do-not-follow notice and a simple presentation. Existing reviewed links stay intact.
No correction is invented when its relationship or content is unresolved.

Both the direct selector → assembler → renderer route and the source-aware preview
apply the generation dispositions. Consolidation keeps different availability and
instructional contexts distinct, merges abstention records without losing them, and
does not drop originals during uncertain deduplication.

All nine rendering contracts remain: text, definition, comparison, flowchart,
timeline, cause-effect, hierarchy, example and formula. Automatic structure is only
selected where the knowledge supports it. Generic comparison properties and hierarchy
roots are not displayed; timeline dates are extracted from actual event text, not
invented from step numbers. Otherwise the existing text fallback is used. Existing
conditions/prerequisites/outcomes continue through source-grounded supplemental details.

## Before/after examples

Nine controlled examples are stored in `before_after_examples.json`, each with its
source, raw mock output, candidate knowledge, wire audit, quality report and notes.

| Case | Candidate before | Source-only preview after |
|---|---|---|
| Biology paraphrase | Cells reproduce through division | Retained as an unreviewed paraphrase candidate |
| Qualified science | Under dry conditions, a reaction is possible | Qualification retained; no semantic approval inferred |
| History | In 1918, the treaty was signed | Retained with source evidence |
| Technical explanation | Call the method after opening the connection | Retained without inventing source code |
| Verbal mathematics | Area is pi multiplied by the square of the radius | Retained as prose, not a reconstructed missing equation |
| Mixed support | Supported cell explanation plus invented 2027 discovery date | Supported clause retained; 2027 absent from student preview |
| Windows-path reconstruction | Generated String declaration from escape-sequence prose | Snippet quarantined; source explanation retained |
| Missing mortgage equation | Required formula unavailable | Principal and monthly-interest explanations retained; VISUAL_CONTEXT_REQUIRED notice |
| Incorrect conditional order and correction | Two teaching passages with associated roles/refs | Both passages retained together with an incorrect-demonstration warning |

The additional fragment-splicing regression confirms that separate code statements
are retained as source passages without presenting their invented concatenation as
literal code. See `tests/test_no_invention_generation.py` in the release snapshot.

Archived Java checks reuse EXM_0003, FRM_0007 and T0041/T0042. The Windows snippet is
not literal in its transcript evidence; the mortgage product is not established as
a complete expression. The existing specific-before-general correction passage
remains available. Historical knowledge, teaching links and decisions are unchanged.

## Educational retention and honest limitations

All five controlled paraphrases remain available; the supported part of the mixed
field and the independent mortgage variable explanations remain. Original candidates
are not deleted. The prior procedure-rendering test had no procedure teaching in its
source; its fixture was corrected to include actual evidence rather than weakening
the policy to display unsourced prerequisites/outcomes.

This does not establish zero legitimate loss across the archived corpus. Conservative
number, qualification and literal screens can withhold legitimate unreviewed wording.
When explicit evidence exists, authorized source passages remain available as passages;
they are not represented as semantic proof of the rejected candidate. The full originals
remain in audit artifacts. Independent educational retention assessment is **NOT_VERIFIED**.

The negative control in `unresolved_semantic_control.json` deliberately shows the
remaining semantic limit: a qualitative addition such as “Leaves produce oxygen”
does not follow from “Plants have leaves,” but general entailment cannot be decided
by quotation screening. It remains REVIEW_REQUIRED and unapproved. Such candidate
wording may appear only in the visibly unverified preview/review flow; it is not a
verified source fact. A model's explicit/direct_entailment proposal can itself be wrong.
There is no new semantic evaluator, automatic approval or educational-quality score.

## Regression results and preservation

Release applicable offline suite: **{stats['passed']} passed, {stats['failed']} failed,
{stats['skipped']} skipped**. See `regression_release.xml` and `test_summary.json`.
Skips are 18 pre-existing Windows model-conversion tests and one deliberately disabled
real OpenAI integration test. Physical network connections were blocked during tests
and artifact generation. The public provider documentation was read separately;
no model API request was sent.

The suite includes the November 7 rejected-response regression; corrected fixtures;
Task 11's 42-reference recovery and serialization; actual TXT/DOCX/PPTX and model-free
PDF routes; OCR failure/restart tests; all nine formats; strict schemas/source permissions;
Stage A, one-time claims, configured ceilings and five-organization safety.

Earlier failed test attempts are retained. Prompt compaction assertions were preserved.
The synthetic legacy recovery fixture uses an existing 3,000-token output option so
it actually has an approved smaller test split after policy overhead; production
defaults and recovery logic are unchanged. The fixed-request test prepares a fresh
fixture in memory, never rewrites or approves the historical package.

SHA-256 checks confirm **{preservation['checked']} protected files unchanged**, including
Task 8/9/11 artifacts, the Task 11 ingestion/source/chunking implementations, Stage A
and quota code, credentials and live-state records. No operational approval, API-key
change, quota edit, model download, package installation, source-ID rewrite or historical
artifact overwrite occurred. Test-only mock approval records remain isolated in temporary
test directories. Task 11 remains functional.

## Request identity and readiness

`manifest.unapproved.json` is a new offline preparation only; `authorization_status.json`
records zero approved requests. `request_version_comparison.json` confirms that the
same Task 11 source chunk now receives a new request hash. The source parser and model/
provider remain unchanged. Old operational bindings cannot authorize changed bytes.

Ready for a **separately authorized, tightly controlled provider-schema and quality
pilot**, with genuine semantic review of its response before expansion. This task
does not authorize that pilot, establish live Groq quality, certify semantic entailment,
or make the notes ready for verified publication. No Task 12B work was started.

## Files changed

{files}

Exact release code bytes and SHA-256 hashes are in `code_snapshot_release` and
`modified_files_release.json`. Earlier preparation snapshots and test attempts are
preserved. A Git checkout was unavailable. All delivery scripts and examples are
confined to this new Task 12A artifact directory.
'''
    (OUT/'task12a_report.md').write_text(report,encoding='utf-8')
    print(str(OUT/'task12a_report.md'))


if __name__=='__main__':main()
