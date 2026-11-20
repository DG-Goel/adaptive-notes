"""Topic labels and transcript timing for Round 1 quiz questions."""
import json

from app.extraction import quiz_wire
from app.extraction.organization_scheduler import SchedulerHold

VERSION = 'compact_field_rows_quiz_v2'


def system():
    return quiz_wire.system() + """
Each quiz question also requires topic: a short, specific keyword phrase naming
the concept being tested. Use the same label for questions testing the same
concept. Put the excerpt that directly teaches that topic first in refs and cite
the tightest relevant excerpts. Do not generate timestamps.
"""


def response_format():
    result = quiz_wire.response_format()
    result['json_schema']['name'] = VERSION
    item = result['json_schema']['schema']['properties']['quiz']['items']
    item['properties']['topic'] = {'type': 'string', 'minLength': 1, 'maxLength': 80}
    item['required'].append('topic')
    return result


def split_topics(content):
    data = json.loads(content)
    topics = []
    for question in data.get('quiz', []):
        topic = question.pop('topic', None)
        if not isinstance(topic, str) or not topic.strip() or len(topic) > 80:
            raise SchedulerHold('Quiz question requires a short topic label')
        topics.append(' '.join(topic.split()))
    return json.dumps(data, ensure_ascii=False), topics


def resolve_response(content, chunk):
    notes_and_quiz, _ = split_topics(content)
    return quiz_wire.resolve_response(notes_and_quiz, chunk)


def review_timestamps(evidence, sources, source_spans):
    timestamps = {}
    for excerpt in evidence:
        source = sources[excerpt['source_id']]
        quote = excerpt['quote']
        text = source.text or ''
        lower, upper = (source_spans or {}).get(source.source_id, (0, len(text)))
        start = text.find(quote, lower, upper)
        if start < 0 or text.find(quote, start + 1, upper) >= 0:
            continue
        segments = {s['id']: s for s in source.provenance.get('original_segments', [])}
        for span in source.provenance.get('segment_character_spans', []):
            segment = segments.get(span['segment_id'])
            if segment and start < span['end'] and start + len(quote) > span['start']:
                timestamps[(source.source_id, segment['id'])] = {
                    'source_id': source.source_id, 'segment_id': segment['id'],
                    'start': segment['start'], 'end': segment['end'],
                }
    return list(timestamps.values())
