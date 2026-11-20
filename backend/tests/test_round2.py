from hashlib import sha256

import pytest

from app.extraction.organization_scheduler import Identity, Organizations, OrganizationScheduler
from app.round2.pipeline import (
    analyze_result, extractive_comparison, integrate, normalize_renderer_payload,
    resolve_times, validate_payload,
)
from tests.test_organization_scheduler import registry, success


def test_round2_rotation_preserves_round1_cursor(tmp_path):
    ledger = tmp_path / 'quota.sqlite'
    first = OrganizationScheduler(ledger, registry())
    assert success(first, 'first-1') == 1
    slots = (6, 7, 8, 9, 10)
    identities = [Identity(slot=slot, organization=f'org-{slot}', project=f'project-{slot}',
        credential_id=f'inventory-{slot}', credential_sha256=sha256(f'test-{slot}'.encode()).hexdigest(),
        verified_by='fixture', ownership_evidence='synthetic test', verified_at=0.0,
        expires_at=None) for slot in slots]
    second = OrganizationScheduler(ledger, Organizations(
        identities, {slot: f'test-{slot}' for slot in slots}, slots), rotation_slots=slots)
    assert [success(second, f'second-{index}') for index in range(6)] == [6, 7, 8, 9, 10, 6]
    assert success(first, 'first-2') == 2
    assert second.status()['cursor'] == 7


def test_disjoint_intervals_and_insert_only_after_render():
    source = {'G1': {'text': 'Alpha. Skip. Beta.', 'provenance': {
        'original_segments': [{'id': 1, 'start': 2, 'end': 3}, {'id': 2, 'start': 8, 'end': 9}],
        'segment_character_spans': [{'segment_id': 1, 'start': 0, 'end': 6},
                                    {'segment_id': 2, 'start': 13, 'end': 18}]}}}
    evidence = [{'source_id': 'G1', 'start_char': 0, 'end_char': 6, 'quote': 'Alpha.'},
                {'source_id': 'G1', 'start_char': 13, 'end_char': 18, 'quote': 'Beta.'}]
    spans = resolve_times(evidence, source, ['G1'])
    assert [(span['start'], span['end']) for span in spans] == [(2, 3), (8, 9)]
    visual = dict(anchor_note_id='FCT_0001', spans=spans, source_segment_ids=['FCT_0001'],
        payload={'title': 'Example'}, needs_timestamp_alignment=False, image='visuals/example.png')
    assert integrate('before\nafter', {'FCT_0001': {'anchor': 6}}, [visual]) == 'before\nafter'
    visual['render_status'] = 'rendered'
    result = integrate('before\nafter', {'FCT_0001': {'anchor': 6}}, [visual])
    assert result.startswith('before\n\n![Example]') and result.endswith('\nafter')
    assert '2.00–3.00s, 8.00–9.00s' in result


def test_reject_reversed_values_and_unsupported_edge():
    with pytest.raises(ValueError):
        validate_payload(dict(type='data_structure', title='Array', subtype='array', values=[2, 1]),
                         ['The array contains 1, 2.'])
    with pytest.raises(ValueError):
        validate_payload(dict(type='architecture', title='Connection', direction='RIGHT',
            components=[dict(id='A', label='App'), dict(id='B', label='Store')],
            connections=[dict({'from': 'A', 'to': 'B'}, label='calls')]),
            ['App never calls Store.'])


def test_saved_comparison_can_recover_without_invented_examples():
    payload = dict(type='table', title='Java naming', headers=['Element', 'Example'],
                   rows=[['Class name', 'MyMainClass'], ['Method name', 'calculateTotal']])
    quotes = ['Java class names use PascalCase.', 'Java method names use camelCase.']
    recovered = extractive_comparison(payload, quotes)
    validate_payload(recovered, quotes)
    assert recovered['rows'] == [['class names', quotes[0]], ['method names', quotes[1]]]
    assert extractive_comparison(payload, quotes[:1]) is None
    assert normalize_renderer_payload({'type': 'flowchart', 'direction': 'top-down'})['direction'] == 'DOWN'


def test_context_cannot_own_visual_and_invalid_visual_preserves_unit():
    ids = ['FCT_0001', 'FCT_0002']
    notes = {identifier: dict(position=index, unresolved=False, text='Example')
             for index, identifier in enumerate(ids)}
    unit = dict(mode='text_and_visual', source_segment_ids=ids[1:], remaining_text='',
        visuals=[dict(source_segment_ids=ids, needs_review=False, missing_information=[])])
    visuals, issues = analyze_result(dict(units=[unit]), dict(primary=ids[1:], context=ids[:1]), notes)
    assert not visuals and 'context-owned' in issues[0]['reason']


@pytest.mark.parametrize('kind', ['concept_tree', 'mind_map'])
def test_hierarchy_replaces_complete_notes_only_after_render(kind):
    from app.round2.visual_cards import visual_card

    labels = ['Exchange rates can use the opposite quotation convention.',
              'An exchange rate is the price of one currency relative to another.']
    topic = 'Exchange rates and monetary policy'
    ids = ['CON_0001', 'CON_0002']
    payload = dict(type=kind, title=topic, nodes=[
        dict(id='root', label=topic),
        *(dict(id=f'branch{i}', label=label, parent='root') for i, label in enumerate(labels)),
    ])
    markdown = '\n\n'.join(f'{label}\n\nAnchor {i}' for i, label in enumerate(labels))
    notes = {}
    for i, (key, label) in enumerate(zip(ids, labels)):
        body_start = markdown.index(label)
        notes[key] = dict(text=label, topic=topic, position=i, unresolved=False, body_start=body_start,
            body_end=body_start + len(label), anchor=markdown.index(f'Anchor {i}') + len(f'Anchor {i}'),
            timing=[dict(start=i, end=i + 1, resolution='speech_segment')])
    candidate = dict(source_segment_ids=ids, needs_review=False, missing_information=[], payload=payload,
                     evidence=[dict(note_id=key, quote=label) for key, label in zip(ids, labels)])
    unit = dict(mode='visual_only', source_segment_ids=ids, remaining_text=None, visuals=[candidate])
    visuals, issues = analyze_result(dict(units=[unit]), dict(primary=ids, context=[]), notes)
    assert not issues
    assert integrate(markdown, notes, visuals) == markdown
    assert all(label in visual_card(payload) for label in labels)
    visuals[0].update(render_status='rendered', image='visuals/tree.png')
    refined = integrate(markdown, notes, visuals)
    assert all(label not in refined for label in labels)
    assert 'visuals/tree.png' in refined
    assert '0.00–1.00s, 1.00–2.00s' in refined


def test_chart_rejects_unsupported_values_and_timeline_keeps_dates():
    from app.round2.visual_cards import visual_card

    chart = dict(type='chart', title='Temperature', unit='degrees', points=[
        dict(label='Monday', value='-12'), dict(label='Tuesday', value='7')])
    quotes = ['Monday was -12 degrees.', 'Tuesday was 7 degrees.']
    validate_payload(chart, quotes)
    assert '-12 degrees' in visual_card(chart)
    chart['points'][0]['value'] = '12'
    with pytest.raises(ValueError, match='quantitative evidence'):
        validate_payload(chart, quotes)
    timeline = dict(type='timeline', title='Events', events=[
        dict(time='1900', label='First event'), dict(time='1910', label='Second event')])
    validate_payload(timeline, ['First event in 1900.', 'Second event in 1910.'])
    rendered = visual_card(timeline)
    assert rendered.index('1900') < rendered.index('1910')


def test_connection_can_use_two_ordered_excerpts():
    payload = dict(type='architecture', title='Connection', direction='RIGHT',
        components=[dict(id='A', label='App'), dict(id='B', label='Store')],
        connections=[{'from': 'A', 'to': 'B', 'label': 'sends requests'}])
    validate_payload(payload, ['App sends requests.', 'It sends requests to Store.'])
    with pytest.raises(ValueError):
        validate_payload(payload, ['App sends requests.', 'It never sends requests to Store.'])
