import json
from types import SimpleNamespace
import pytest
from jsonschema import ValidationError
from app.extraction import quiz_wire
from app.extraction import quiz_topics
from app.extraction import quiz_optional
from app.extraction import quiz_mcq
from app.extraction.quiz_export import export_quiz
from app.extraction.organization_extraction import extraction_policy, prepare_request
from app.extraction.organization_scheduler import ExtractionConfiguration
from app.models.knowledge import ExtractionChunk


def fixture():
    chunk = ExtractionChunk(chunk_id='chunk1', source_units=['S1'],
        text_content='[S1] A queue is first in first out.')
    rows = [dict(question=f'Question {i}?', answer='First in first out.',
                 explanation='The source describes queue ordering.', bloom_level=level,
                 refs=['Q0000']) for i, level in enumerate(quiz_wire.LEVELS[:4])]
    return chunk, dict(rows=[], abstentions=[], excluded=[], quiz=rows)


def test_quiz_wire_and_existing_note_resolver():
    chunk, body = fixture()
    config = ExtractionConfiguration(prompt_policy='canonical_grounded_v4',
        wire_format=quiz_wire.VERSION, response_format='json_schema', preferred_output_tokens=3000)
    system, _, resolver, schema = extraction_policy(config)
    assert 'exactly FOUR' in system
    assert schema['json_schema']['schema']['properties']['quiz']['minItems'] == 4
    payload, budget = prepare_request(chunk, config)
    assert budget.is_safe and payload['max_tokens'] >= 3000
    resolved, _ = resolver(json.dumps(body), chunk)
    assert 'quiz' not in json.loads(resolved)
    assert len(quiz_wire.questions(json.dumps(body), chunk)) == 4


def test_quiz_topics_and_timestamp_provenance():
    chunk, body = fixture()
    for row in body['quiz']:
        row['topic'] = 'Queue ordering'
    content = json.dumps(body)
    quiz_topics.resolve_response(content, chunk)
    original, topics = quiz_topics.split_topics(content)
    assert topics == ['Queue ordering'] * 4
    evidence = quiz_wire.questions(original, chunk)[0]['evidence']
    quote = evidence[0]['quote']
    text = f'Intro\n{quote}\n{quote}'
    first = len('Intro\n')
    source = SimpleNamespace(source_id='S1', text=text, provenance={
        'original_segments': [{'id': 'intro', 'start': 0, 'end': 2},
                              {'id': 'topic', 'start': 7.5, 'end': 10}],
        'segment_character_spans': [{'segment_id': 'intro', 'start': 0, 'end': 5},
                                    {'segment_id': 'topic', 'start': first, 'end': first + len(quote)}],
    })
    assert quiz_topics.review_timestamps(evidence, {'S1': source}, None) == []
    assert quiz_topics.review_timestamps(evidence, {'S1': source},
        {'S1': (first, first + len(quote))}) == [
            {'source_id': 'S1', 'segment_id': 'topic', 'start': 7.5, 'end': 10}]
    del body['quiz'][0]['topic']
    with pytest.raises(RuntimeError, match='topic label'):
        quiz_topics.resolve_response(json.dumps(body), chunk)


def test_optional_quiz_never_blocks_note_resolution():
    chunk, body = fixture()
    for row in body['quiz']:
        row['topic'] = 'Queue ordering'
    body['quiz'][0]['explanation'] = ''
    body['quiz'][1]['refs'] = ['Q9999']
    body['quiz'][3]['question'] = body['quiz'][2]['question']
    content = json.dumps(body)
    resolved, _ = quiz_optional.resolve_response(content, chunk)
    assert 'quiz' not in json.loads(resolved)
    assert len(quiz_optional.questions(content, chunk)) == 1
    body['quiz'] = []
    empty = json.dumps(body)
    quiz_optional.resolve_response(empty, chunk)
    assert quiz_optional.questions(empty, chunk) == []


def test_multiple_choice_rejects_duplicate_options_and_keeps_correct_index():
    chunk, body = fixture()
    for row in body['quiz']:
        row.update(topic='Queue ordering', distractors=['Last in first out', 'Random order', 'Priority order'])
    body['quiz'][0]['distractors'][0] = ' FIRST  IN FIRST OUT. '
    config = ExtractionConfiguration(prompt_policy='canonical_grounded_v4',
        wire_format=quiz_mcq.VERSION, response_format='json_schema', preferred_output_tokens=3000)
    payload, _ = prepare_request(chunk, config)
    assert payload['response_format']['json_schema']['name'] == quiz_mcq.VERSION
    content = json.dumps(body)
    quiz_mcq.resolve_response(content, chunk)
    questions = quiz_mcq.questions(content, chunk)
    assert len(questions) == 3
    for row in questions:
        assert len(row['options']) == 4
        assert row['options'][row['correct_option_index']] == row['answer']


@pytest.mark.parametrize('fault', ['missing', 'extra', 'duplicate', 'unknown_ref', 'level', 'context_only'])
def test_invalid_quizzes_rejected(fault):
    chunk, body = fixture()
    if fault == 'missing': body['quiz'].pop()
    if fault == 'extra': body['quiz'].append(body['quiz'][0])
    if fault == 'duplicate': body['quiz'][1]['question'] = body['quiz'][0]['question']
    if fault == 'unknown_ref': body['quiz'][0]['refs'] = ['Q9999']
    if fault == 'level': body['quiz'][0]['bloom_level'] = 'Guess'
    if fault == 'context_only':
        chunk = chunk.model_copy(update=dict(context_source_ids=['S2'], context_text='[S2] Context.'))
        body['quiz'][0]['refs'] = ['Q0001']
    with pytest.raises((ValueError, ValidationError)):
        quiz_wire.questions(json.dumps(body), chunk)


def test_order_resume_and_incomplete_export(tmp_path):
    chunk, body = fixture()
    def record(serial):
        rows = quiz_wire.questions(json.dumps(body), chunk)
        for i, row in enumerate(rows):
            row.update(id=f'{serial}-{i}', chunk_serial=serial)
        return dict(chunk_serial=serial, request_id=f'r{serial}', source_ids=['S1'], questions=rows)
    sources = [SimpleNamespace(source_id='S1')]
    records = [record(2), record(1)]
    result = export_quiz(tmp_path, records, sources, [])
    assert result['question_count'] == 8
    assert [q['chunk_serial'] for q in result['questions']] == [1]*4 + [2]*4
    stamp = (tmp_path/'quiz.json').stat().st_mtime_ns
    export_quiz(tmp_path, reversed(records), sources, [])
    assert (tmp_path/'quiz.json').stat().st_mtime_ns == stamp
    assert export_quiz(tmp_path, records, sources, [3])['status'] == 'incomplete'
