"""Opt-in Round 1 quiz sidecar; the existing note resolver stays unchanged."""
import json
from jsonschema import Draft202012Validator
from app.extraction import field_row_wire as base
from app.extraction.quote_catalog import catalog
from app.extraction.source_context import evidence_view

VERSION = 'compact_field_rows_quiz_v1'
LEVELS = ['Remember', 'Understand', 'Apply', 'Analyze', 'Evaluate', 'Create']
PROMPT = '''
QUIZ EXTENSION: In addition to rows, abstentions and excluded, return quiz with
exactly FOUR distinct short-answer questions about this PRIMARY chunk. This adds
one top-level field to the note wire; all note extraction rules remain unchanged.
Each question has question, answer, explanation, bloom_level and refs (excerpt IDs).
Choose any appropriate Bloom level: Remember, Understand, Apply, Analyze, Evaluate,
Create. Levels may repeat; do not force advanced levels unsupported by the source.
Use four different learning targets or cognitive tasks, not paraphrases of one
question. Keep questions concise and answers and explanations brief but complete.
All answer facts and explanations must be supported by cited excerpts, including
at least one primary excerpt per question. Never use outside knowledge, invent
code/results, or present uncertain OCR or incomplete formulas as established facts.
Application/evaluation/creation questions must stay within explicitly taught
examples, criteria or methods; give a source-supported expected answer/rubric.
Use lower levels when necessary. Do not omit notes to make room for questions.
If the source cannot support four honest questions, fail explicitly rather than
fabricating teaching material to fill the count.
'''


def system():
    return base.system() + PROMPT


def response_format():
    result = base.response_format()
    result['json_schema']['name'] = VERSION
    schema = result['json_schema']['schema']
    fields = {key: {'type': 'string', 'minLength': 1} for key in
              ('question', 'answer', 'explanation')}
    fields['bloom_level'] = {'type': 'string', 'enum': LEVELS}
    fields['refs'] = {'type': 'array', 'minItems': 1, 'items': {'type': 'string'}}
    schema['properties']['quiz'] = {'type': 'array', 'minItems': 4, 'maxItems': 4,
        'items': {'type': 'object', 'properties': fields, 'required': list(fields),
                  'additionalProperties': False}}
    schema['required'].append('quiz')
    return result


def questions(content, chunk):
    data = json.loads(content)
    shape = response_format()['json_schema']['schema']['properties']['quiz']
    Draft202012Validator(shape).validate(data.get('quiz'))
    entries = catalog(evidence_view(chunk))
    seen = set()
    result = []
    for row in data['quiz']:
        title = ' '.join(row['question'].split()).casefold()
        if not title or title in seen or any(not row[key].strip() for key in ('answer', 'explanation')):
            raise ValueError('Quiz contains empty or duplicate questions')
        seen.add(title)
        if any(ref not in entries for ref in row['refs']):
            raise ValueError('Quiz references an unknown excerpt')
        evidence = [entries[ref] for ref in dict.fromkeys(row['refs'])]
        if not any(e['source_id'] in chunk.source_units for e in evidence):
            raise ValueError('Quiz requires primary chunk evidence')
        result.append({**row, 'evidence': evidence, 'semantic_verified': False})
    return result


def resolve_response(content, chunk):
    questions(content, chunk)
    data = json.loads(content)
    data.pop('quiz')
    return base.resolve_response(json.dumps(data, ensure_ascii=False), chunk)
