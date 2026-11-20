# Controlled one-request preparation

## Identity and status
Request: `controlled-20261107_042242`
Request SHA-256: `03b8a07e1eb1c2d65bd8a8064b9d88f19a8c9a4172fecc99f67a55694c65f8bb`
Manifest SHA-256: `251501bd5b5185dffe1ec70ffb64338181384499e25c0848ff2601ed1a5167fc`
Status: PENDING EXACT-REQUEST AUTHORIZATION. No dispatch occurred.

Primary chunk: SYNTHETIC_CHUNK. Source snapshot: synthetic controlled_math.txt, not a real uploaded mathematics document. Primary S1: “Area equals pi times radius squared.” Context S2: “This applies only to circles.” S2 is evidence context, not independently completed work. Q0000 maps to S1; Q0001 to S2. No outside textbook definitions, formulas, dates or examples are authorized by these excerpts.

Model: openai/gpt-oss-120b; provider Groq; context_grounded_v3; temperature 0; max_tokens 4000; no explicit reasoning_effort override (provider default); max_retries 0; strict json_schema response format, schema name grounded_fields_v2. The exact full prompt and schema are in manifest.json, not summarized substitutes. The freshly reconstructed wire hash matches Task 3's payload because its content is unchanged. This manifest has a new run identity and current configuration fingerprint; its hash differs from the historical package. Nothing in a prior authorization approves this request.

## Selected organization
NOTES 1 only, slot 1, org `org_01k0m8r3x9f14b8qcaj4n8bffr`. Existing operator-reviewed ownership/model-access inventory is reused. Local key fingerprint and non-expiring approval checked successfully. No key is included in artifacts. Current provider acceptance, permissions and external usage are not established by these local checks. Other configured organizations are not eligible for this experiment, and their global settings were not changed.

## Readiness decision
Preparation and local contract verification are ready. LIVE DISPATCH IS BLOCKED pending separate exact-request and manifest approval. stage_a.pending.json deliberately has decision PENDING and is rejected by the authorization schema. credential_approval.pending.json has pending request-authorization evidence. authorization.pending.json has no approved manifest hash or configuration-review evidence. No PASS records were manufactured. The existing shared scheduler configuration differs and needs an explicit reviewed migration preserving all usage. Dispatch-time admission on both ledgers remains mandatory.

The document runner is unsuitable for this boundary because it iterates primary and recovery chunks. The added SingleRequestStageAAuthorization supports exactly the prepared source snapshot, request ID, payload hash, current configuration fingerprint and boundary. After approval, a dedicated invocation of the existing extract_chunk operation must supply this gate, only NOTES 1, max_retries=0 and a durable request ID; it must execute once and return for review. Do not invoke the full-document runner, split on failure, create another request ID, or continue automatically. Existing scheduler duplicate/uncertain-operation protection and Stage A shared accounting remain enforced. This package itself is not a live executable runner.

## Quota and failure behavior
Estimated input 2081, completion reservation 4000, combined 6081 <= 6800. Limits remain RPM 25, RPD 850, TPM 6800, TPD 170000, subject to stricter applicable total limits and outstanding usage. Before dispatch, check organization and shared Stage A ledgers; HOLD if insufficient, without deleting or clearing usage. The estimate is not an exact tokenizer measurement or proof of currently available quota.

Known successful usage reconciles to provider-reported input/output. HTTP 200 with invalid grounding still incurs usage and stops. HTTP 400/401/403/429 stop without retries. Truncation stops without child requests. Uncertain network/server outcomes retain the existing reservation and require review; never repeat the request automatically. Complete raw response, response receipt hash, attempts, exceptions and audit events must be saved even when validation fails. No SDK retries, proxy retries, fallback model or credential rotation.

## Review rubric and acceptance
benchmark.json contains an empty claim ledger with five separate semantic statuses, explicit reviewer/evidence/reason fields and the source-derived topic inventory. After receiving a response, enumerate every substantive field as atomic claims, including titles, names, formula components, conditions, procedure steps and classifications. Mark exact citation validation separately from semantic support. Record partial support, contradiction, unsupported additions and inconclusive transcription/scope separately. Matching excerpt IDs alone cannot establish correctness.

For this trial the main teaching point and its circle-only restriction must survive extraction, consolidation, representation and rendering. Do not require an unsupported worked example or reconstruct literal code/formula syntax. Any unsupported/contradicted claim or unresolved critical semantic issue prevents expansion. Compare final notes to both accepted knowledge and the source; inspect duplicate information, formatting, representation suitability and lost qualifications. All five quality gates remain independent. A usable-looking preview is still unverified until reviewed. Expansion needs a new explicit authorization, never automatic continuation.

## Planned artifacts
Preparation directory: C:\Projects\adaptive-notes\backend\data\output\task4_controlled_benchmark
Future run output: C:\Projects\adaptive-notes\backend\data\output\task4_controlled_benchmark/execution/controlled-20261107_042242/
Planned files: raw_response.json, response_receipt.json, request_audit.json, validation.json, accepted_knowledge.json (only after acceptance), consolidation.json, representations.json, assembled_preview.json, preview.md, render_manifest.json, coverage.json, quality_gates.json, claim_review.json and manual_review.md. The persistent organization/shared quota ledgers remain at their existing locations, not copied/replaced for a fresh run.

## Changes and limitations
Code: app/extraction/single_request_authorization.py (new), app/extraction/organization_extraction.py (allow the exact new gate type), tests/test_single_request_preparation.py (new). No model, prompt, source policy, quota ceilings, credentials or historical records changed. This tiny synthetic example tests the context/evidence contract, not real-document breadth or live educational quality. General entailment, duplicate paraphrases, long-range context and topic inventories remain manual/research limitations. All live benchmark outcomes remain NOT_EVALUATED.

Validation: 59 tests passed, 0 failed, 0 skipped. Organization ledger byte hash unchanged; frozen Stage A/control files unchanged. Tests validate altered payload/source/configuration/boundary rejection, pending-record rejection and existing extraction, context, Stage A and quota controls. See ../task4_preparation_tests.xml.
