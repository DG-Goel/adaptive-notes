"""Multiple-choice quiz output with the grounded answer as the correct choice."""
import json

from app.extraction import quiz_optional
from app.extraction.organization_scheduler import digest

VERSION = 'compact_field_rows_quiz_v4'


def system():
    return quiz_optional.system().replace('short-answer', 'multiple-choice') + """
Use a concise answer that can serve directly as the correct option. Add
distractors: exactly three distinct, plausible incorrect options of similar
length. Each question must have one unambiguously correct choice given the
cited excerpt. Distractors are alternatives for assessment, never note facts.
Return fewer questions if you cannot write three meaningful distractors.
"""


def response_format():
    result = quiz_optional.response_format()
    result['json_schema']['name'] = VERSION
    fields = result['json_schema']['schema']['properties']['quiz']['items']
    fields['properties']['distractors'] = {'type': 'array', 'items': {'type': 'string'}}
    fields['required'].append('distractors')
    return result


resolve_response = quiz_optional.resolve_response


def questions(content, chunk):
    data = json.loads(content)
    candidates = data.get('quiz')
    if not isinstance(candidates, list):
        return []
    results = []
    seen = set()
    for row in candidates:
        if not isinstance(row, dict) or not isinstance(row.get('question'), str):
            continue
        distractors = row.get('distractors')
        if not isinstance(distractors, list) or len(distractors) != 3:
            continue
        options = [row.get('answer'), *distractors]
        if any(not isinstance(value, str) or not value.strip() for value in options):
            continue
        if len({' '.join(value.split()).casefold() for value in options}) != 4:
            continue
        parsed = quiz_optional.questions(json.dumps({'quiz': [row]}), chunk)
        if not parsed:
            continue
        row = parsed[0]
        title = ' '.join(row['question'].split()).casefold()
        if title in seen:
            continue
        seen.add(title)
        options = sorted((value.strip() for value in options),
                         key=lambda option: digest([row['question'], option]))
        results.append({**row, 'options': options, 'correct_option_index': options.index(row['answer'])})
        if len(results) == 4:
            break
    return results
