"""Offline readiness audit. Never dispatches HTTP or changes live admission state."""
import hashlib
import json
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
import subprocess
import sys
import time

from dotenv import dotenv_values
from app.ingestion.transcript_parser import parse_transcript
from app.extraction.chunker import ContentChunker
from app.extraction.organization_extraction import prepare_request
from app.extraction.organization_scheduler import ExtractionConfiguration, digest, CONFIGURED_CEILINGS
from app.extraction.stage_a_bridge import frozen_harness


def main():
    started = time.monotonic()
    root = Path(__file__).resolve().parent
    source = root.parent / 'java.txt'
    stamp = datetime.now(timezone(timedelta(hours=5, minutes=30)))
    out = root / 'data/output' / ('java_real_api_test_' + stamp.strftime('%Y%m%d_%H%M%S_%f'))
    out.mkdir(parents=True)
    print('Readiness artifacts: ' + str(out), flush=True)

    def save(name, value):
        (out / name).write_text(json.dumps(value, indent=2, default=str), encoding='utf-8')

    def sha(path):
        return hashlib.sha256(path.read_bytes()).hexdigest()

    frozen_dirs = ['t0022_stage_a_admission_v2_20261104_125816', 't0022_safety_infrastructure_20261104_003405']
    frozen_files = [p for d in frozen_dirs for p in (root / 'data/output' / d).glob('*.py')]
    frozen_before = {str(p.relative_to(root)): sha(p) for p in frozen_files}
    source_hash = sha(source)
    document = parse_transcript(source, min_segment_words=50, max_segment_words=500, detect_timestamps=True)
    chunks = ContentChunker().chunk(document.source_units, document.document_id)
    source_ids = [u.source_id for u in document.source_units]
    chunk_ids = [sid for c in chunks for sid in c.source_units]
    assert chunk_ids == source_ids and len(set(source_ids)) == len(source_ids)
    save('source_document.json', document.model_dump(mode='json'))
    save('chunks.json', [c.model_dump(mode='json') for c in chunks])
    save('source_manifest.json', {'path': str(source), 'sha256': source_hash, 'bytes': source.stat().st_size,
        'parser': 'parse_transcript', 'parser_options': {'min_segment_words': 50, 'max_segment_words': 500, 'detect_timestamps': True},
        'source_units': len(source_ids), 'chunks': len(chunks), 'source_ids': source_ids,
        'source_order_preserved_by_chunker': True, 'duplicate_source_ids': [],
        'scope': 'Parser and chunker coverage only; not extracted-note coverage.'})
    frozen_payload, _, _ = frozen_harness().request_plan()
    config = ExtractionConfiguration(max_retries=0)
    plans = []
    for index, chunk in enumerate(chunks, 1):
        payload, budget = prepare_request(chunk, config)
        plans.append({'chunk_number': index, 'chunk_id': chunk.chunk_id, 'source_ids': chunk.source_units,
            'model': config.model, 'request_sha256': digest(payload), 'payload': payload,
            'budget_estimate_not_actual_usage': asdict(budget),
            'matches_frozen_stage_a_payload': payload == frozen_payload, 'status': 'not_dispatched',
            'credential_id': None, 'organization': None, 'project': None})
    save('request_plans.json', plans)
    inventory_path = root / 'data/output/organization_inventory_20261106/inventory.json'
    inventory = json.loads(inventory_path.read_text(encoding='utf-8')) if inventory_path.exists() else []
    fields = ('slot', 'credential_id', 'organization', 'project', 'enabled', 'verified_at', 'expires_at',
              'verification_status', 'verification_validity_status', 'quota_state')
    inventory_summary = [{k: row.get(k) for k in fields} for row in inventory]
    env = dotenv_values(root / '.env')
    env_summary = [{'slot': i, 'enabled_flag': env.get(f'GROQ_ORG_{i}_ENABLED', 'false'),
        'credential_present': bool(env.get(f'GROQ_ORG_{i}_API_KEY'))} for i in range(1, 6)]
    save('quota_report.json', {'configured_ceilings': CONFIGURED_CEILINGS, 'actual_current_usage': None,
        'actual_available_capacity': None, 'status': 'unverified_no_dispatch',
        'inventory_snapshot': inventory_summary, 'environment_nonsecret_status': env_summary,
        'credential_approval_file_exists': (root / 'data/output' / frozen_dirs[0] / 'credential_approval.json').exists(),
        'note': 'Configured ceilings are not proof of provider capacity. No live ledger was claimed or reset.'})
    groups = {
        'pipeline_scheduler': ['tests/' + n + '.py' for n in [
            'test_organization_scheduler', 'test_organization_extraction', 'test_organization_configured_ceilings',
            'test_organization_live_gate', 'test_stage_a_bridge', 'test_java_round_robin_pipeline',
            'test_chunk_splitting', 'test_assembly_unit', 'test_rendering_simple', 'test_serialization',
            'test_extraction_grounding', 'test_extraction_reliability', 'test_knowledge_merge', 'test_token_budget']],
        'frozen_stage_a': ['data/output/' + frozen_dirs[0] + '/' + n for n in ['test_admission_v2.py', 'test_live_stage_a.py']],
        'frozen_stage_ab': ['data/output/' + frozen_dirs[1] + '/test_control.py'],
    }
    regressions = []
    for label, paths in groups.items():
        command = [sys.executable, '-B', '-m', 'pytest', '-q', '-p', 'no:cacheprovider', *paths,
            '--basetemp=' + str(out / ('offline_' + label))]
        print('Running offline regressions: ' + label, flush=True)
        tick = time.monotonic()
        result = subprocess.run(command, cwd=root, capture_output=True, text=True)
        (out / (label + '.log')).write_text(result.stdout + result.stderr, encoding='utf-8')
        regressions.append({'group': label, 'exit_code': result.returncode, 'seconds': time.monotonic()-tick,
            'command': command, 'log': label + '.log'})
        print(label + ': exit ' + str(result.returncode), flush=True)
    save('regression_results.json', regressions)
    assert sha(source) == source_hash
    frozen_after = {str(p.relative_to(root)): sha(p) for p in frozen_files}
    assert frozen_before == frozen_after
    save('preservation_manifest.json', {'source_unchanged': True, 'frozen_python_files_unchanged': True,
        'frozen_file_hashes': frozen_after})
    blockers = [
        'All production Java request payloads differ from the exact payload accepted by frozen Stage A. The bridge refuses them before provider dispatch.',
        'No current verified quota admission for these request hashes was supplied. Unknown external usage cannot be assumed zero.',
        'Stored credential inventory validity and enablement must satisfy existing checks; see quota_report.json. Existing mappings were preserved, not replaced.',
        'Multi-organization provider permission is unestablished. No multi-organization live rotation was attempted.']
    summary = {'classification': 'Blocked before live execution', 'started_at': stamp.isoformat(),
        'preparation_and_regressions_seconds': time.monotonic()-started, 'live_execution_seconds': 0,
        'source_sha256': source_hash, 'document_chunks': len(chunks), 'source_units': len(source_ids),
        'real_requests_attempted': 0, 'successful_requests': 0, 'failed_requests': 0, 'http_429_errors': 0,
        'json_validation_failures': 0, 'actual_input_tokens': 0, 'actual_output_tokens': 0,
        'actual_total_tokens': 0, 'retries': 0, 'chunks_extracted': 0, 'chunks_failed_after_dispatch': 0,
        'chunks_not_dispatched': len(chunks), 'source_units_extracted': 0, 'assembly_status': 'not_run',
        'quality_score': None, 'blockers': blockers, 'regressions': regressions,
        'frozen_stage_a_matching_chunks': sum(p['matches_frozen_stage_a_payload'] for p in plans)}
    save('run_summary.json', summary)
    rubric = '# Quality evaluation plan — not scored\n\nNo real output exists for this run. All category scores and the weighted score are unavailable.\n\n'
    rubric += '| Category | Weight | Required evidence |\n|---|---:|---|\n'
    for category, weight, evidence in [
        ('Content completeness', 30, 'Source-to-notes matrix covering topics, definitions, explanations and code; report omissions.'),
        ('Factual accuracy', 25, 'Trace each important claim to source; separately check Java facts against authoritative references.'),
        ('Explanation quality', 15, 'Review context, depth and continuity with quoted source/output examples.'),
        ('Organization and readability', 10, 'Inspect heading order, code fences, topic grouping and repetition.'),
        ('Examples and code correctness', 10, 'Map demonstrations to source; compile/run suitable complete Java examples where available.'),
        ('Source traceability', 10, 'Verify source IDs, evidence quotes, claim attachment and final render manifest.')]:
        rubric += f'| {category} | {weight}% | {evidence} |\n'
    rubric += '\nFor each category use a 0–5 evidence-backed scale: 0 unusable/absent; 1 major failures; 2 substantial gaps; 3 usable with material corrections; 4 minor issues; 5 no material issue found in documented review scope. Weighted score = sum(weight * score / 5). These are review judgments, not measured accuracy probabilities.\n\nReport automated heuristic findings separately from manual review. Do not call an assistant review human-reviewed. Full quality pass requires complete extraction, source accounting, no unresolved material unsupported/incorrect claims or missing core topics, and documented evaluation scope. No pass threshold has been demonstrated by this blocked run.\n'
    (out / 'quality_evaluation_plan.md').write_text(rubric, encoding='utf-8')
    errors = '# Error and blocker report\n\nNo provider requests were attempted; HTTP, schema, latency and model-quality failures cannot be observed.\n\n'
    errors += '| Type | Scope | Established cause | Recovery | Impact | Correction |\n|---|---|---|---|---|---|\n'
    errors += '| Authorization HOLD | Every Java chunk | Exact production payload differs from frozen Stage A payload | None; no bypass | Entire live run blocked | Add a separately reviewed authorization procedure outside frozen files that binds exact Java requests while preserving Stage A/B guarantees. |\n'
    errors += '| Quota prerequisites | Every prospective live request | No fresh request-bound quota admission supplied | None | Dispatch eligibility unproven | Supply authoritative limits and current used/outstanding values, inventory completeness and traffic coordination; revalidate before each attempt. |\n'
    errors += '| Credential validity | Enabled organization | See actual inventory fields in quota_report.json | None | Live eligibility unproven | Obtain genuine validity records without inventing expiry. |\n'
    for r in regressions:
        if r['exit_code']:
            errors += f"| Offline regression failure | {r['group']} | See {r['log']} | Unresolved | Readiness not established | Diagnose saved failure before live testing. |\n"
    (out / 'error_report.md').write_text(errors, encoding='utf-8')
    report = f'''# Full Java real API test report

Classification: **Blocked before live execution**.

Source SHA-256: `{source_hash}`. Recomputed using the complete original file. Current parser produced {len(source_ids)} source units and {len(chunks)} chunks. Chunk source references preserve parser order with no missing or duplicate IDs. This does not prove educational coverage or parser semantic fidelity.

## API and extraction results

Real requests: 0. Successful: 0. Failed: 0. HTTP 429: 0. JSON failures: 0. Retries: 0. Actual input/output/total tokens: 0/0/0. Live execution duration: 0 seconds. Preparation and offline regression duration: {summary['preparation_and_regressions_seconds']:.2f} seconds. API latency is unavailable.

Extracted chunks: 0/{len(chunks)}. Not dispatched: {len(chunks)}. Extracted source units: 0/{len(source_ids)}. Final assembly: not run. Missing/duplicated note content and factual correctness: unevaluated.

## Exact blockers

''' + '\n'.join('- ' + b for b in blockers) + '''

The Stage A bridge checks payload equality before provider creation. Zero Java requests match the frozen request. A matching credential or fresh quota alone cannot resolve that mismatch. No frozen file, model, production prompt, quota ceiling, credential mapping, or live ledger was modified. This audit imports the offline request planner only and creates no provider client. No legacy runner was used to bypass admission.

The scheduler currently returns HOLD to callers rather than providing a document background queue. No worker or automatic reset/retry was invented. A future live orchestrator must preserve pending work and revalidate genuine evidence before dispatch, and cannot release uncertain reservations just because a window elapsed.

## Notes quality

No real notes were generated. Category and overall scores are unavailable. No prior output or mock test content was reused as real-run notes. See quality_evaluation_plan.md for the weighted rubric and evidence needed. Quality improvements cannot be established without real output.

## Artifacts and regressions

source_manifest.json, source_document.json, chunks.json, request_plans.json, quota_report.json, run_summary.json, preservation_manifest.json, regression_results.json, quality_evaluation_plan.md and error_report.md are actual preparation results. Regression logs and offline_* directories are explicitly offline fixtures, not real API evidence. request_plans.json contains production prompts with source text but no credentials or authorization records. There is no request audit or generated-notes/coverage/quality-score artifact because no corresponding live results exist.

'''
    report += '\n'.join(f"- {r['group']}: exit {r['exit_code']}; see {r['log']}." for r in regressions)
    (out / 'final_test_report.md').write_text(report, encoding='utf-8')
    print(json.dumps({'output': str(out), 'classification': summary['classification'],
        'chunks': len(chunks), 'source_units': len(source_ids), 'regression_exit_codes': [r['exit_code'] for r in regressions]}), flush=True)


if __name__ == '__main__':
    # The fixed-harness audit above is retained as historical code. The document
    # manifest path supersedes its old quota and T0022-only blocker assumptions.
    from prepare_java_authorization import main as prepare_document_authorization
    prepare_document_authorization()
