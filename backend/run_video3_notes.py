"""Resume the video3 workflow after timestamped transcription and local OCR."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone

from app.extraction.quota_policy import daily_token_exception
from app.extraction.document_authorization import ROUND1_RECOVERY_PASSES
from run_authorized_java import save

from multimodal_transcript import run as integrate
from prepare_multimodal_run import main as prepare
from run_authorized_java import run as run_combined
from run_full_multimodal_categories import main as extract

ROOT = Path(__file__).resolve().parent
DATA = ROOT / 'data/transcriptions/video3_20261113'
OUT = ROOT / 'data/output/video3_20261113'
INVENTORY = ROOT / 'data/round2_organization_inventory.json'


def read(path):
    return json.loads(path.read_bytes())


def round2(source, output, *options):
    from app.extraction.quota_policy import active_quota_exception
    if active_quota_exception():
        from run_round2 import main
        args = [str(source), str(output), *options]
        main(args + ['--prepare-approvals', str(INVENTORY)])
        main(args + ['--live', str(output / 'approvals.json')])
        return
    command = [sys.executable, str(ROOT / 'run_round2.py'), str(source), str(output), *options]
    subprocess.run(command + ['--prepare-approvals', str(INVENTORY)], check=True, cwd=ROOT)
    subprocess.run(command + ['--live', str(output / 'approvals.json')], check=True, cwd=ROOT)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--legacy-category-passes', action='store_true',
                        help='Resume the original separate category run')
    parser.add_argument('--local-tpd-exception', action='store_true',
                        help='Apply an explicitly authorized TPD-only exception to this invocation')
    args = parser.parse_args()
    if args.local_tpd_exception:
        stamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S_%f')
        consent = 'Operator authorized bypassing only local TPD for the video3 run on keys 1–10'
        run_id = 'video3-tpd-' + stamp
        OUT.mkdir(parents=True, exist_ok=True)
        save(OUT / (run_id + '.json'), dict(run_id=run_id, authorization=consent,
             bypassed_local_metric='TPD', enforced_metrics=['RPM', 'RPD', 'TPM']))
        with daily_token_exception(authorization=consent, run_id=run_id):
            run_workflow(args)
    else:
        run_workflow(args)


def run_workflow(args, *, data=DATA, output=OUT, progress=lambda stage: None):
    paths = dict(speech=data / 'speech/transcript.json', risks=data / 'risks/risk_intervals.json',
                 stage3=data / 'ocr/visual_ocr_results.json')
    ocr = read(paths['stage3'])
    if ocr.get('blocker'):
        raise RuntimeError('OCR has a recorded blocker')
    frames = read(data / 'ocr/frame_manifest.json')
    events = [event for event in read(paths['risks'])['events'] if event['priority'] == 'HIGH']
    if {event['event_id'] for event in frames['events']} != {event['event_id'] for event in events}:
        raise RuntimeError('Wait for OCR to process both configured intervals')
    for event in frames['events']:
        interval = next(row for row in events if row['event_id'] == event['event_id'])
        tasks = {'Text Recognition:'}
        if 'FORMULA_VISUAL_DEPENDENCY' in interval['categories']:
            tasks.add('Formula Recognition:')
        if 'TABLE_CHART_VISUAL_DEPENDENCY' in interval['categories']:
            tasks.add('Table Recognition:')
        expected = {(frame['inference_sha256'], task) for frame in event['selected'] for task in tasks}
        actual = {(record['inference_sha256'], record['task']) for record in ocr['records']
                  if record['event_id'] == event['event_id']}
        if not expected <= actual:
            raise RuntimeError('OCR still has unprocessed frame tasks')
    source = data / 'multimodal/multimodal_transcript.json'
    if not source.exists():
        integrate(source.parent, paths, legacy_java=False)
    first = output / ('round1' if args.legacy_category_passes else 'round1_combined')
    progress('Round 1 extraction')
    if args.legacy_category_passes:
        extract(first, source=source)
        summary = read(first / 'run_summary.json')
        blocked = bool(summary.get('blocker'))
    else:
        authorization = read(first / 'authorization.json') if (first / 'authorization.json').exists() else {}
        if not authorization.get('parallel') or authorization.get('end_retries') != ROUND1_RECOVERY_PASSES:
            prepare('combined', source=source, output=first, parallel=True, quiz=True)
        summary = run_combined(first, live=True, max_wait=65, continue_validation_failures=True,
                               output_dir=first, defer_quota_waits=True)
        blocked = summary['classification'] != 'Full live extraction completed'
    if not args.legacy_category_passes and summary.get('rotation_policy') == 'next_free_key' and summary['classification'] != 'Full live extraction completed':
        raise RuntimeError(
            f"Round 1 incomplete after {ROUND1_RECOVERY_PASSES} end-of-run retry passes. "
            f"Missing chunks: {summary['missing_chunk_serials']}. See round1_errors.jsonl.")
    if blocked:
        print('Round 1 stopped. See its run summary for the blocker.', flush=True)
        return
    if not (first / 'extraction_results.json').exists():
        raise RuntimeError('Round 1 produced no notes for Round 2')
    for name in ('unresolved_source_gaps.json',):
        (first / name).write_bytes(source.with_name(name).read_bytes())
    suffix = '' if args.legacy_category_passes else '_combined'
    second = output / ('round2' + suffix)
    progress('Round 2 visual analysis')
    round2(first, second)
    report = read(second / 'report.json')
    if report.get('blocker'):
        print('Round 2 visual analysis stopped. See its report.', flush=True)
        return
    progress('Round 2 text polish')
    round2(second / 'reading_notes.md', output / ('polished' + suffix), '--polish-notes')


if __name__ == '__main__':
    main()
