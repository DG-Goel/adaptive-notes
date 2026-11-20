import pytest
from app.models.knowledge import KnowledgeDocument
from app.models.source import SourceDocument, SourceUnit
from app.evaluation.offline_recovery import apply_offline_plan, reviewed_student_preview


def fixture(text):
    source = SourceDocument(document_id='D', filename='fixture', page_count=0, source_units=[
        SourceUnit(source_id='S1', document_id='D', type='paragraph', position=1, text=text)])
    knowledge = KnowledgeDocument(document_id='D', source_filename='fixture', extraction_timestamp='offline')
    recovery = dict(item=dict(knowledge_id='FCT_0001', knowledge_type='fact', document_id='D',
        source_unit_ids=['S1'], content=text, fact_text=text), evidence=[dict(source_id='S1', quote=text)],
        reviewer='fixture source reviewer', rationale='Preserves the source assertion and its qualifications.')
    return source, knowledge, dict(recoveries=[recovery])


@pytest.mark.parametrize('text', [
    'For a circle, area equals pi times radius squared.',
    'The sample may react under dry conditions.',
    'The treaty was signed in 1919.',
    'The study reports correlation, without establishing causation.',
    'Cool the device before opening the cover.',
    'The speaker is uncertain about the date.'])
def test_cross_domain_reviewed_recovery_preserves_source_and_original(text):
    source, original, plan = fixture(text)
    knowledge, changes = apply_offline_plan(original, source, plan)
    assert not original.get_all_items()
    assert knowledge.total_items == 1 and changes[0]['provider_completion_changed'] is False
    preview = reviewed_student_preview(knowledge, source, [])
    assert text in preview['markdown']
    assert knowledge.facts[0].extraction_metadata['provider_generated'] is False
    assert not preview['publication_eligible']


@pytest.mark.parametrize('mutation', ['quote', 'identity', 'missing', 'inconsistent', 'excluded'])
def test_recovery_rejects_invalid_raw_contract(mutation):
    source, knowledge, plan = fixture('The sample may react.')
    recovery = plan['recoveries'][0]
    if mutation == 'quote': recovery['evidence'][0]['quote'] = 'Invented evidence'
    if mutation == 'identity': recovery['item']['source_unit_ids'] = ['S2']
    if mutation == 'missing': del recovery['item']['fact_text']
    if mutation == 'inconsistent': recovery['item']['fact_text'] = 'The sample always reacts.'
    if mutation == 'excluded':
        from app.ingestion.educational_policy import EducationalAssessment
        source.source_units[0].educational_assessment = EducationalAssessment(status='noneducational', reason='fixture exclusion', whole_unit_reviewed=True)
    with pytest.raises(ValueError): apply_offline_plan(knowledge, source, plan)


def test_stale_review_rejected_and_unreviewed_auxiliary_field_withheld():
    source, original, plan = fixture('The sample may react.')
    knowledge, _ = apply_offline_plan(original, source, plan)
    item = knowledge.facts[0]
    item.fact_type = 'Invented experiment'
    preview = reviewed_student_preview(knowledge, source, [])
    assert 'Invented experiment' not in preview['markdown']
    assert any(w['path'] == '/fact_type' for w in preview['withheld'])
    plan = dict(field_reviews=[dict(item_id=item.knowledge_id, path='/content', expected_text='stale',
        evidence=[dict(source_id='S1', quote=source.source_units[0].text)], reviewer='reviewer', rationale='rationale')])
    with pytest.raises(ValueError, match='exact field'): apply_offline_plan(knowledge, source, plan)


def test_equivalence_keeps_unique_supported_detail_and_all_evidence():
    source, original, plan = fixture('A device may cool. An observation.')
    first = plan['recoveries'][0]
    import copy
    second = copy.deepcopy(first)
    second['item']['knowledge_id'] = 'FCT_0002'
    plan['recoveries'].append(second)
    knowledge, _ = apply_offline_plan(original, source, plan)
    knowledge.facts[1].fact_type = 'An observation.'
    from app.models.educational_review import FieldReview
    knowledge.facts[1].educational_review.field_reviews.append(FieldReview(path='/fact_type',
        mode='literal', status='SUPPORTED', evidence=second['evidence'], reviewer='reviewer', rationale='Exact source label'))
    decision = dict(left='FCT_0001', right='FCT_0002', classification='MEANINGFULLY_EQUIVALENT', rationale='Same scoped assertion', reviewer='reviewer')
    preview = reviewed_student_preview(knowledge, source, [decision])
    assert len(knowledge.get_all_items()) == 2
    assert preview['aliases'] == {'FCT_0002':'FCT_0001'}
    assert 'An observation.' in preview['markdown'] and 'Equivalent statement' in preview['markdown']


def test_unsupported_and_contradicted_fields_never_enter_preview():
    source, original, plan = fixture('A qualified observation.')
    knowledge, _ = apply_offline_plan(original, source, plan)
    for row in knowledge.facts[0].educational_review.field_reviews:
        row.status = 'CONTRADICTED'
        row.mode = 'contradicted'
    preview = reviewed_student_preview(knowledge, source, [])
    assert preview['displayed_items'] == 0
    assert len(preview['withheld']) == 2


def test_context_cannot_move_item_before_its_primary_source():
    source, original, plan = fixture('A qualified observation.')
    source.source_units.append(SourceUnit(source_id='CONTEXT', document_id='D', position=0,
        type='paragraph', text='Earlier context.'))
    knowledge, _ = apply_offline_plan(original, source, plan)
    item = knowledge.facts[0]
    item.source_unit_ids.append('CONTEXT')
    item.extraction_metadata['context_source_ids'] = ['CONTEXT']
    preview = reviewed_student_preview(knowledge, source, [], section_titles={'S1':'Primary topic', 'CONTEXT':'Earlier topic'})
    assert '## Primary topic' in preview['markdown'] and '## Earlier topic' not in preview['markdown']
    assert preview['mapping'][0]['primary_source_ids'] == ['S1']
