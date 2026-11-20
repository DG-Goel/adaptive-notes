"""Keep source-supported questions without making quiz quality a notes gate."""
import json

from app.extraction import field_row_wire, quiz_topics, quiz_wire
from app.extraction.quote_catalog import catalog
from app.extraction.source_context import evidence_view

VERSION = 'compact_field_rows_quiz_v3'


def system():
    return field_row_wire.system() + """
Alongside the notes return a quiz array. Aim for FOUR distinct short-answer
questions about teaching in the primary excerpts. Return fewer, including [],
when the excerpts cannot support four. Empty note and quiz arrays are valid
for non-teaching dialogue. Always return the JSON object, including when empty.
Each question has question, answer, explanation, topic, bloom_level and refs.
Use a short specific topic and cite the closest supporting excerpt first.
Each question requires primary evidence. Never invent answers or timestamps.
Use Remember, Understand, Apply, Analyze, Evaluate or Create as bloom_level.
"""


def response_format():
    result = quiz_topics.response_format()
    result['json_schema']['name'] = VERSION
    quiz = result['json_schema']['schema']['properties']['quiz']
    quiz.pop('minItems')
    quiz.pop('maxItems')
    for field in quiz['items']['properties'].values():
        for constraint in ('minLength', 'maxLength', 'minItems', 'enum'):
            field.pop(constraint, None)
    return result


def resolve_response(content, chunk):
    notes = json.loads(content)
    notes.pop('quiz', None)
    return field_row_wire.resolve_response(json.dumps(notes, ensure_ascii=False), chunk)


def questions(content, chunk):
    candidates = json.loads(content).get('quiz')
    if not isinstance(candidates, list):
        return []
    entries = catalog(evidence_view(chunk))
    accepted = []
    seen = set()
    for row in candidates:
        if not isinstance(row, dict):
            continue
        keys = ('question', 'answer', 'explanation', 'topic', 'bloom_level')
        if any(not isinstance(row.get(key), str) or not row[key].strip() for key in keys):
            continue
        title = ' '.join(row['question'].split()).casefold()
        refs = row.get('refs')
        if (title in seen or len(row['topic']) > 80 or row['bloom_level'] not in quiz_wire.LEVELS
                or not isinstance(refs, list) or any(not isinstance(ref, str) or ref not in entries for ref in refs)):
            continue
        evidence = [entries[ref] for ref in dict.fromkeys(refs)]
        if not any(item['source_id'] in chunk.source_units for item in evidence):
            continue
        seen.add(title)
        accepted.append({**{key: row[key].strip() for key in keys}, 'refs': refs,
                         'evidence': evidence, 'semantic_verified': False})
        if len(accepted) == 4:
            break
    return accepted
