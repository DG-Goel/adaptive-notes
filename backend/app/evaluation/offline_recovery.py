"""Explicit, source-bound offline review, separate from provider completion.

This module has no provider, credential, authorization or quota dependencies.
Review decisions are supplied by a reviewer; quote matching is not entailment.
"""
from copy import deepcopy
from collections import defaultdict

from app.models.knowledge import Fact
from app.models.educational_review import EducationalReview, FieldReview, ReviewQuote
from app.evaluation.field_faithfulness import leaves, audit_fields
from app.evaluation.citation_repair import revise_reviewed_text


def apply_offline_plan(knowledge, source, plan):
    result = knowledge.model_copy(deep=True)
    units = {u.source_id: u for u in source.source_units}
    items = {i.knowledge_id: i for i in result.get_all_items()}
    if len(units) != len(source.source_units) or len(items) != len(result.get_all_items()):
        raise ValueError('Canonical source and knowledge IDs must be unique')
    changes = []

    def evidence(record):
        refs = [ReviewQuote.model_validate(e) for e in record['evidence']]
        if not refs or not record['reviewer'].strip() or not record['rationale'].strip():
            raise ValueError('Explicit reviewer, rationale and evidence required')
        for q in refs:
            if q.source_id not in units or q.quote not in (units[q.source_id].text or ''):
                raise ValueError('Exact canonical source quotation required')
            if units[q.source_id].educational_assessment.excluded:
                raise ValueError('Excluded source cannot support offline recovery')
        return refs

    for recovery in plan.get('recoveries', []):
        refs = evidence(recovery)
        raw = deepcopy(recovery['item'])
        required = {'knowledge_id', 'knowledge_type', 'document_id', 'source_unit_ids', 'content', 'fact_text'}
        if not required <= raw.keys() or raw['knowledge_type'] != 'fact':
            raise ValueError('Complete raw fact required before constructor defaults')
        if raw['knowledge_id'] in items or raw['document_id'] != source.document_id:
            raise ValueError('Duplicate ID or incorrect document identity')
        if set(raw['source_unit_ids']) != {q.source_id for q in refs}:
            raise ValueError('Primary identity must match recovery evidence')
        if not raw['content'].strip() or raw['content'] != raw['fact_text']:
            raise ValueError('Common and category fields must agree')
        item = Fact.model_validate(raw, strict=True)
        item.extraction_metadata = dict(origin='offline_source_review', provider_generated=False,
            primary_source_ids=list(item.source_unit_ids), context_source_ids=[],
            source_grounding={'evidence': [dict(source_id=q.source_id, quote=q.quote,
                fields=['/content', '/fact_text']) for q in refs],
                'semantic_entailment_verified': False})
        item.educational_review = EducationalReview(reviewer=recovery['reviewer'],
            rationale=recovery['rationale'], status='SUPPORTED', unresolved=False,
            field_reviews=[FieldReview(path=p, mode='faithful_paraphrase', status='SUPPORTED',
                evidence=refs, reviewer=recovery['reviewer'], rationale=recovery['rationale'])
                for p in ('/content', '/fact_text')])
        result.facts.append(item)
        items[item.knowledge_id] = item
        changes.append(dict(kind='offline_recovery', item_id=item.knowledge_id,
            provider_completion_changed=False))

    for review in plan.get('field_reviews', []):
        refs = evidence(review)
        item = items[review['item_id']]
        values = dict(leaves(item.model_dump(mode='json')))
        if values.get(review['path']) != review['expected_text']:
            raise ValueError('Review no longer matches the exact field value')
        if not {q.source_id for q in refs} <= set(item.source_unit_ids):
            raise ValueError('Review cannot silently introduce contextual sources')
        if 'replacement' in review:
            if review['status'] != 'SUPPORTED':
                raise ValueError('Replacement requires affirmative source review')
            changes.append(revise_reviewed_text(item, review['path'], review['replacement'],
                source, refs[0].source_id, refs[0].quote,
                reviewer=review['reviewer'], rationale=review['rationale']))
        er = item.educational_review or EducationalReview()
        previous = [r.model_dump(mode='json') for r in er.field_reviews if r.path == review['path']]
        if previous:
            item.extraction_metadata = item.extraction_metadata or {}
            item.extraction_metadata.setdefault('offline_field_review_history', []).extend(previous)
        er.field_reviews = [r for r in er.field_reviews if r.path != review['path']]
        er.field_reviews.append(FieldReview(path=review['path'], mode=review['mode'],
            status=review['status'], evidence=refs, reviewer=review['reviewer'], rationale=review['rationale']))
        item.educational_review = er
        changes.append(dict(kind='field_review', item_id=item.knowledge_id,
            path=review['path'], status=review['status'], reviewer=review['reviewer'],
            rationale=review['rationale'], previous_reviews=previous))
    result.update_statistics()
    return result, changes


def reviewed_student_preview(knowledge, source, duplicate_decisions, *, section_titles=None, version=7):
    """Only affirmatively reviewed fields enter prose; retain all items in audit.

    Equivalence is a field-level presentation link, never a destructive merge.
    """
    rows = audit_fields(knowledge, source)
    by_item = defaultdict(list)
    for row in rows:
        by_item[row['knowledge_id']].append(row)
    items = {i.knowledge_id: i for i in knowledge.get_all_items()}
    aliases = {}
    for decision in duplicate_decisions:
        if decision['classification'] != 'MEANINGFULLY_EQUIVALENT':
            continue
        left, right = decision['left'], decision['right']
        if left == right or left not in items or right not in items:
            raise ValueError('Invalid equivalence target')
        # Equivalent content does not authorize suppressing distinct auxiliary fields.
        if not decision.get('rationale') or not decision.get('reviewer'):
            raise ValueError('Reviewed equivalence required')
        if all(any(r['path'] == '/content' and r['status'] == 'SUPPORTED'
                   for r in by_item[k]) for k in (left, right)):
            aliases[right] = left
    positions = {u.source_id: u.position for u in source.source_units}
    def primary(item):
        return (item.extraction_metadata or {}).get('primary_source_ids', item.source_unit_ids)
    roles = {'deliberately_incorrect_demonstration': 0, 'identified_mistake': 1,
             'explanation_of_mistake': 2, 'corrected_approach': 3, 'alternative_valid_approach': 4}
    def order(item):
        return (min(positions[s] for s in primary(item)),
                roles.get(item.educational_review.role if item.educational_review else '', 5), item.knowledge_id)
    blocks, mapping, withheld = [], [], []
    for item in sorted(items.values(), key=order):
        candidates = [r for r in by_item[item.knowledge_id] if r['status'] == 'SUPPORTED'
                      and not (r['literal_code_form'] and not r['literal_substring'])]
        selected, seen = [], set()
        for row in sorted(candidates, key=lambda r: (r['path'] != '/content', r['path'])):
            if row['original_output'] in seen:
                continue
            seen.add(row['original_output'])
            if item.knowledge_id in aliases and row['path'] in ('/content', '/fact_text'):
                continue
            selected.append(row)
        if selected or item.knowledge_id in aliases:
            first_source = min(primary(item), key=lambda s: positions[s])
            heading = (section_titles or {}).get(first_source) or item.section or ('Source ' + ', '.join(primary(item)))
            blocks.append((heading, item, selected))
        for row in by_item[item.knowledge_id]:
            if row not in candidates:
                withheld.append(dict(item_id=item.knowledge_id, path=row['path'], status=row['status']))
        mapping.append(dict(item_id=item.knowledge_id, displayed_paths=[r['path'] for r in selected],
            equivalent_content_of=aliases.get(item.knowledge_id), source_ids=item.source_unit_ids,
            primary_source_ids=primary(item)))
    lines = ['# Reviewed student notes — version '+str(version), '',
        'Source-backed review subset. This is an incomplete preview, not a fully verified course.', '',
        'Only fields with affirmative source-comparison review are shown. Original items, withheld fields, and evidence remain in the companion audit.', '']
    previous = None
    for heading, item, selected in blocks:
        if heading != previous:
            lines.extend(['## ' + heading, ''])
            previous = heading
        lines.extend(['### ' + item.knowledge_id, ''])
        if item.knowledge_type == 'formula' and (not item.educational_review or item.educational_review.formula_status != 'COMPLETE'):
            lines.extend(['**Incomplete formula / visual-context warning.** Only individually reviewed components are shown; no complete equation is approved.', ''])
        if item.educational_review and item.educational_review.role != 'unresolved':
            lines.extend(['Instructional role: **' + item.educational_review.role.replace('_', ' ') + '**.', ''])
        if item.knowledge_id in aliases:
            lines.extend(['Equivalent statement: see **' + aliases[item.knowledge_id] + '**. Sources: '
                          + ', '.join(item.source_unit_ids) + '.', ''])
        for row in selected:
            label = '' if row['path'] == '/content' else '**' + row['path'].strip('/').replace('/', ' / ') + ':** '
            if row['path'].startswith('/steps/'):
                label = '**Step ' + str(int(row['path'].split('/')[-1]) + 1) + ':** '
            text = row['original_output']
            if item.knowledge_type == 'formula' and row['path'] in ('/content', '/formula_text'):
                fence = '`' * max(3, max((len(s) for s in text.split() if set(s) == {'`'}), default=0) + 1)
                text = fence + 'text\n' + text + '\n' + fence
            lines.extend([label + text, '',
                'Source: ' + ', '.join(dict.fromkeys(q['source_id'] for q in row['evidence']))
                + ' · Field: `' + row['path'] + '` · Exact quotations: companion `field_review_queue.json`.', ''])
    return dict(markdown='\n'.join(lines), mapping=mapping, withheld=withheld, field_review_queue=rows,
        aliases=aliases, displayed_items=len(blocks), publication_eligible=False)
