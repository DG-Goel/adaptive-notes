"""Plan, render or resume Round 2 from a Round 1 output directory."""
import argparse
import json
from pathlib import Path
import time

from dotenv import dotenv_values

from app.extraction.llm_provider import GroqProviderError
from app.extraction.organization_scheduler import ExtractionConfiguration, SchedulerHold, digest
from app.round2.live import dispatch, open_scheduler
from app.round2.pipeline import VISUAL_TYPES, analyze_result, integrate, load_notes, plan, read_json
from app.round2.reading import reading_markdown
from run_authorized_java import save

ROOT = Path(__file__).resolve().parent
CONFIG = ExtractionConfiguration(max_retries=0, preferred_output_tokens=2000, reasoning_effort='low')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--demo', action='store_true', help='Run a local Java comparison fixture')
    mode.add_argument('--live', type=Path, metavar='APPROVAL_BUNDLE')
    mode.add_argument('--prepare-approvals', type=Path, metavar='REVIEWED_INVENTORY')
    parser.add_argument('--recover-from', type=Path, metavar='PREVIOUS_RUN')
    parser.add_argument('--java-reading-layout', action='store_true')
    parser.add_argument('--polish-notes', action='store_true',
                        help='Polish prose in an existing Round 2 Markdown file')
    parser.add_argument('--browser', type=Path, default=Path(
        'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'))
    args = parser.parse_args(argv)
    source, output = args.source.resolve(), args.output.resolve()
    if args.polish_notes:
        if args.demo or args.recover_from:
            parser.error('Text polishing takes an existing Markdown file')
        from app.round2.polish import run_polish
        run_polish(source, output, CONFIG, args.prepare_approvals, args.live, ROOT)
        return
    if output == source or source in output.parents:
        parser.error('Use a separate Round 2 output directory')
    markdown, notes = load_notes(source)
    requests = plan(notes, CONFIG)
    binding = digest({'notes': notes, 'markdown': markdown})
    for index, request in enumerate(requests, 1):
        request['request_id'] = f'round2-{binding[:12]}-{digest(request)[:12]}-{index:03d}'
    previous = args.recover_from.resolve() if args.recover_from else None
    if previous:
        if previous == output:
            parser.error('Use a separate output directory for recovery')
        prior_manifest = read_json(previous / 'manifest.json')
        if prior_manifest['source_sha256'] != binding or prior_manifest['requests'] != requests:
            raise SchedulerHold('Recovery requires the original notes and matching request plan')
        truncated = {attempt['request_id'] for attempt in read_json(previous / 'api_usage.json')
                     if attempt.get('http_status') == 200 and attempt.get('finish') == 'length'}
        for parent in prior_manifest['requests']:
            if parent['request_id'] not in truncated:
                continue
            children = plan(notes, CONFIG, recovery_ids=parent['primary'])
            for child in children:
                child['recovery_of'] = parent['request_id']
                child['request_id'] = f'round2-{binding[:12]}-repair-{digest(child)[:20]}'
                requests.append(child)
    manifest = dict(source_sha256=binding, configuration=CONFIG.model_dump(mode='json'), requests=requests)
    output.mkdir(parents=True, exist_ok=True)
    save(output / 'manifest.json', manifest)
    if args.prepare_approvals:
        from app.round2.live import prepare_approvals
        save(output / 'approvals.json', prepare_approvals(manifest, read_json(args.prepare_approvals), CONFIG))
        print('Prepared manifest-bound approvals from the supplied operator-reviewed inventory.')
        return
    visuals, issues, processed, teaching_units = [], [], [], []
    blocker = None
    if args.demo:
        ids = ['FCT_0202', 'FCT_0203']
        request = dict(primary=ids, context=[])
        comparison = dict(source_segment_ids=ids, needs_review=False, missing_information=[],
            evidence=[dict(note_id=key, quote=notes[key]['text'].split('\n\n')[-1]) for key in ids],
            payload=dict(type='table', title='Prefix and postfix increment',
                headers=['increment operator', 'value'],
                rows=[['postfix', 'original value'], ['prefix', 'new value']]))
        visuals, issues = analyze_result(dict(units=[dict(source_segment_ids=ids, remaining_text='',
            mode='text_and_visual', visuals=[comparison])]), request, notes)
    elif args.live:
        bundle = read_json(args.live)
        if bundle.get('manifest_sha256') != digest(manifest):
            raise SchedulerHold('Live approvals must bind the exact Round 2 manifest')
        scheduler = open_scheduler(ROOT, bundle['inventory'], dotenv_values(ROOT / '.env'),
                                   CONFIG, bundle.get('configuration_review'))
        for request in requests:
            request_id = request['request_id']
            if 'skipped' in request:
                issues.append(dict(request_id=request_id, reason=request['skipped']))
                continue
            checkpoint = output / (request_id + '.result.json')
            if previous and not checkpoint.exists():
                checkpoint = previous / checkpoint.name
            try:
                with scheduler.transaction() as db:
                    operation = db.execute('SELECT state FROM operations WHERE id=?', (request_id,)).fetchone()
                if checkpoint.exists() and operation and operation['state'] == 'success':
                    result = read_json(checkpoint)
                    proposal = {'units': result.get('teaching_units', [])}
                    result['visuals'], result['issues'] = analyze_result(proposal, request, notes)
                elif operation:
                    issues.append(dict(request_id=request_id, reason=operation['state']))
                    if operation['state'] in ('claimed', 'uncertain'):
                        raise SchedulerHold('Pending request needs reconciliation')
                    continue
                else:
                    def validate(content):
                        proposal = json.loads(content)
                        selected, rejected = analyze_result(proposal, request, notes)
                        return dict(visuals=selected, issues=rejected, teaching_units=proposal['units'])
                    approved = bundle['requests'][request_id]
                    deadline = time.monotonic() + 65
                    while True:
                        try:
                            result = dispatch(scheduler, request, approved, output, validate)
                            break
                        except SchedulerHold as error:
                            if 'headroom' not in str(error) or time.monotonic() >= deadline:
                                raise
                            time.sleep(5)
                processed.append(request_id)
                visuals.extend(result['visuals'])
                issues.extend(result['issues'])
                teaching_units.extend(result.get('teaching_units', []))
            except (SchedulerHold, GroqProviderError, KeyError) as error:
                with scheduler.transaction() as db:
                    attempt = db.execute('SELECT finish FROM attempts WHERE request_id=? ORDER BY number DESC LIMIT 1',
                                         (request_id,)).fetchone()
                if attempt and attempt['finish'] == 'length':
                    issues.append(dict(request_id=request_id, reason='Provider truncated response'))
                    continue
                blocker = dict(request_id=request_id, reason=str(error) if isinstance(error, SchedulerHold)
                               else type(error).__name__)
                if isinstance(error, GroqProviderError):
                    blocker.update(status=error.status_code, category=error.category)
                break
        with scheduler.transaction() as db:
            request_ids = {request['request_id'] for request in requests}
            usage = [dict(row) for row in db.execute(
                'SELECT a.*, o.slot FROM attempts a JOIN operations o ON o.id=a.request_id')
                if row['request_id'] in request_ids]
        save(output / 'api_usage.json', usage)
    if args.live and blocker is None:
        from app.round2.pipeline import topic_map_fallback
        visuals.extend(topic_map_fallback(notes, visuals))
    ordered = sorted(visuals, key=lambda visual: notes[visual['anchor_note_id']]['position'])
    visuals = list({visual['id']: visual for visual in reversed(ordered)}.values())[::-1]
    if visuals:
        from app.round2.render import render_visuals
        try:
            render_visuals(visuals, output, ROOT / 'data/round2-renderer', args.browser)
        except (OSError, RuntimeError, TimeoutError) as error:
            for visual in visuals:
                if 'render_status' not in visual:
                    visual.update(render_status='failed', render_error=str(error))
    refined = integrate(markdown, notes, visuals)
    save(output / 'renderer_inputs.json', {visual['id']: visual['payload'] for visual in visuals})
    save(output / 'teaching_unit_proposals.json', teaching_units)
    save(output / 'ordered_notes.json', [dict(note_id=key, **note, visuals=[
        visual for visual in visuals if visual['anchor_note_id'] == key]) for key, note in notes.items()])
    (output / 'refined_notes.md').write_text(refined, encoding='utf-8')
    (output / 'reading_notes.md').write_text(
        reading_markdown(refined, java_layout=args.java_reading_layout), encoding='utf-8')
    report = dict(mode='demo' if args.demo else 'live' if args.live else 'plan',
        skipped_requests=[request['request_id'] for request in requests if 'skipped' in request],
        source_gaps=[gap for note in notes.values() for gap in note.get('unanchored_source_gaps', [])],
        note_count=len(notes), planned_requests=len(requests), completed_requests=processed,
        analyzed_note_count=len({key for request in requests if request['request_id'] in processed
                                 for key in request['primary']}),
        recovery_requests=[dict(request_id=request['request_id'], parent=request['recovery_of'])
                           for request in requests if 'recovery_of' in request],
        visuals_rendered=sum(visual.get('render_status') == 'rendered' for visual in visuals),
        visual_counts={kind: sum(visual.get('render_status') == 'rendered' and visual['payload']['type'] == kind
                            for visual in visuals) for kind in VISUAL_TYPES},
        validation_issues=issues, blocker=blocker,
        render_errors=[dict(id=visual['id'], reason=visual['render_error']) for visual in visuals
                       if visual.get('render_status') == 'failed'])
    save(output / 'report.json', report)
    print(json.dumps(report))


if __name__ == '__main__':
    main()
