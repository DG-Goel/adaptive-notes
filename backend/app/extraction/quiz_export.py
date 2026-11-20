"""Deterministic, atomic quiz exports from successful Round 1 work items."""
import json


def export_quiz(folder, records, sources, missing, *, allow_fewer=False):
    positions = {source.source_id: i for i, source in enumerate(sources)}
    records = sorted(records, key=lambda r: (r['chunk_serial'],
        min(positions[sid] for sid in r['source_ids']),
        min((span[0] for span in (r.get('source_spans') or {}).values()), default=0),
        r['request_id']))
    questions = [q for record in records for q in record['questions']]
    if not allow_fewer and any(len(record['questions']) != 4 for record in records):
        raise ValueError('Every successful quiz work item must contain four questions')
    if len({q['id'] for q in questions}) != len(questions):
        raise ValueError('Duplicate quiz question IDs')
    result = dict(status='incomplete' if missing else 'complete',
        missing_chunk_serials=missing, successful_work_items=len(records),
        question_count=len(questions), questions=questions,
        counting_policy='Four per successful leaf chunk; retries add none. Split recovery children are separate chunks.',
        semantic_verified=False)
    if allow_fewer:
        result['counting_policy'] = 'Up to four supported questions per successful chunk.'
        result['work_items_with_fewer_than_four_questions'] = sum(len(r['questions']) < 4 for r in records)
    def write(name, text):
        target = folder/name
        if target.exists() and target.read_text(encoding='utf-8') == text:
            return
        temp = target.with_suffix(target.suffix+'.tmp')
        temp.write_text(text, encoding='utf-8')
        temp.replace(target)
    write('quiz.json', json.dumps(result, ensure_ascii=False, indent=2))
    lines = ['# Lecture quiz', '', f"Status: {result['status']}. {len(questions)} questions.",
             '', 'Answers are generated source-linked candidates, not independently verified.', '']
    for number, q in enumerate(questions, 1):
        timing = ', '.join(f"{span['start']:.2f}–{span['end']:.2f}s"
                           for span in q.get('review_timestamps', []))
        lines.extend([f"## {number}. {q['question']}", '',
            *([f"Topic: {q['topic']}", ''] if q.get('topic') else []),
            *([f"Review timestamps: {timing}", ''] if timing else []),
            f"Bloom level: {q['bloom_level']} · Chunk {q['chunk_serial']}", '',
            *([f"{i}. {option}" for i, option in enumerate(q.get('options', []), 1)] + ['']
              if q.get('options') else []),
            f"**Answer:** {q['answer']}", '', f"**Explanation:** {q['explanation']}", '',
            'Sources: ' + ', '.join(dict.fromkeys(e['source_id'] for e in q['evidence'])), ''])
    write('quiz.md', '\n'.join(lines))
    return result
