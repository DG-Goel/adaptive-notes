from copy import deepcopy
from datetime import datetime,timezone
import json
import pytest
from app.models.source import SourceDocument,SourceUnit
from app.models.knowledge import KnowledgeDocument,Fact,Procedure,Formula
from app.evaluation.semantic_review import (build_review_inventory,append_decision,resolve_reviews,
    fingerprint,plan_sample,verify_history)
from app.evaluation.review_outputs import evidence_desk_html,materialize_reviews,comprehensive_draft,coverage_report


def fixture(text='Under dry conditions, the sample may react.',kind='paragraph'):
    s=SourceDocument(document_id='D',filename='fixture',page_count=1,source_units=[
        SourceUnit(source_id='BEFORE',document_id='D',type='paragraph',text='An earlier qualification.',position=0),
        SourceUnit(source_id='S1',document_id='D',type=kind,text=text,position=1,section='Lesson'),
        SourceUnit(source_id='AFTER',document_id='D',type='paragraph',text='An exception follows.',position=2)])
    i=Fact(knowledge_id='FCT_0001',document_id='D',source_unit_ids=['S1'],content=text,fact_text=text,
        extraction_metadata=dict(primary_source_ids=['S1'],context_source_ids=[],source_grounding=dict(
            mechanically_valid=True,evidence=[dict(source_id='S1',quote=text,fields=['/content','/fact_text'])])))
    k=KnowledgeDocument(document_id='D',source_filename='fixture',extraction_timestamp='offline',facts=[i])
    return k,s


def decision(w,**updates):
    p=w['packets'][0]
    return dict(packet_id=p['packet_id'],binding=p['binding'],source_version=p['source_version'],members=p['members'],
        status='SUPPORTED',reviewer='synthetic fixture reviewer',reviewer_kind='assistant',
        reviewed_at=datetime.now(timezone.utc).isoformat(),rationale='Synthetic test: same explicitly qualified assertion.',
        qualifications_checked=True,evidence_checked=True,**updates)


@pytest.mark.parametrize('text,kind',[
    ('For a circle, area equals pi times the radius squared.','formula'),
    ('The while condition is checked before the body.','paragraph'),
    ('Mitosis produces daughter cells.','paragraph'),
    ('For constant mass, force equals mass times acceleration.','formula'),
    ('The treaty was signed in 1919.','paragraph'),
    ('The study found correlation without establishing causation.','table'),
    ('Cool the device before opening its cover.','paragraph'),
    ('The lecturer is uncertain whether the date was 1918.','paragraph')])
def test_eight_domains_require_explicit_review(text,kind):
    k,s=fixture(text,kind);w=build_review_inventory(k,s)
    assert w['counts']['fields']==2 and w['counts']['exact_evidence_bundles']==1
    assert w['counts']['atomic_factual_claim_count'] is None
    assert all(r['semantic_status']=='NOT_REVIEWED' for r in w['inventory'])
    history=append_decision(w,[],decision(w))
    resolved=resolve_reviews(w,history)
    assert all(r['semantic_status']=='SUPPORTED' for r in resolved['inventory'])
    assert all(r['review_provenance']['reviewer_kind']=='assistant' for r in resolved['inventory'])


@pytest.mark.parametrize('mutation',['text','citation','source','neighbor','qualification','permission','role'])
def test_approval_invalidated_by_material_change(mutation):
    k,s=fixture();w=build_review_inventory(k,s);h=append_decision(w,[],decision(w))
    if mutation=='text':k.facts[0].content='The sample always reacts.'
    if mutation=='citation':k.facts[0].extraction_metadata['source_grounding']['evidence'][0]['quote']='the sample'
    if mutation=='source':s.source_units[1].text+=' Only below freezing.'
    if mutation=='neighbor':s.source_units[2].text+=' The previous claim is retracted.'
    if mutation=='qualification':k.facts[0].fact_type='Only if the sample is heated.'
    if mutation=='permission':k.facts[0].extraction_metadata['context_source_ids']=['S1']
    if mutation=='role':
        from app.models.educational_review import EducationalReview
        k.facts[0].educational_review=EducationalReview(role='deliberately_incorrect_demonstration')
    current=build_review_inventory(k,s);r=resolve_reviews(current,h)
    assert r['invalidated_decisions'] and all(x['semantic_status']=='NOT_REVIEWED' for x in r['inventory'])
    with pytest.raises(ValueError,match='Stale'):append_decision(current,h,decision(w))


def test_similar_claim_and_distinct_evidence_never_reuse():
    k,s=fixture();w=build_review_inventory(k,s);h=append_decision(w,[],decision(w))
    other=k.facts[0].model_copy(deep=True);other.knowledge_id='FCT_0002';other.content=other.fact_text='The sample always reacts.'
    k.facts.append(other);current=build_review_inventory(k,s);r=resolve_reviews(current,h)
    assert all(x['semantic_status']=='NOT_REVIEWED' for x in r['inventory'] if x['item_id']=='FCT_0002')
    k.facts[0].extraction_metadata['source_grounding']['evidence'].append(dict(source_id='S1',quote='the sample',fields=['/content']))
    assert build_review_inventory(k,s)['counts']['exact_evidence_bundles']>1


@pytest.mark.parametrize('status',['SUPPORTED','PARTIALLY_SUPPORTED','UNSUPPORTED','CONTRADICTED','INCONCLUSIVE','NOT_REVIEWED'])
def test_all_decisions_preserve_history_without_certification(status):
    k,s=fixture();w=build_review_inventory(k,s)
    d=decision(w);d['status']=status
    h=append_decision(w,[],d);d['status']='INCONCLUSIVE'
    d['rationale']='Synthetic follow-up review; distinct from replaying the same exported decision.'
    h=append_decision(w,h,d)
    assert len(h)==2 and h[0]['decision']['status']==status
    assert resolve_reviews(w,h)['inventory'][0]['semantic_status']=='INCONCLUSIVE'
    broken=deepcopy(h);broken[0]['decision']['rationale']='Modified history'
    with pytest.raises(ValueError,match='integrity'):verify_history(broken)


@pytest.mark.parametrize('field,value',[('rationale',' '),('reviewer',''),('reviewed_at','2026-01-01T00:00:00'),('qualifications_checked',False),('evidence_checked',False)])
def test_incomplete_affirmative_review_rejected(field,value):
    k,s=fixture();w=build_review_inventory(k,s);d=decision(w);d[field]=value
    with pytest.raises(ValueError):append_decision(w,[],d)


def test_incomplete_source_and_incorrect_demonstration_stay_honest():
    k,s=fixture('This demonstration is wrong: 2 + 2 = 5. The correct value is 4.')
    from app.models.educational_review import EducationalReview
    k.facts[0].educational_review=EducationalReview(role='deliberately_incorrect_demonstration')
    s.source_units[1].interpretation_limitations=['Missing figure']
    w=build_review_inventory(k,s)
    assert any('Incorrect demonstration' in x for x in w['inventory'][0]['risk_reasons'])
    assert any('missing_visuals' in x for x in w['inventory'][0]['suggested_defect_categories'])
    assert w['inventory'][0]['semantic_status']=='NOT_REVIEWED'


def test_no_literal_code_approval_and_no_draft_loss():
    k,s=fixture('Read a value and print it.')
    k.facts[0].content=k.facts[0].fact_text='int invented = 42;'
    w=build_review_inventory(k,s)
    with pytest.raises(ValueError,match='Nonliteral'):append_decision(w,[],decision(w))
    r=resolve_reviews(w,[]);draft=comprehensive_draft(k,s,r)
    assert len(draft['retention'])==2 and 'int invented = 42;' not in draft['markdown']
    assert 'WITHHELD' in draft['markdown'] and 'UNVERIFIED' in draft['markdown']


def test_context_is_bounded_and_does_not_authorize_evidence():
    k,s=fixture();w=build_review_inventory(k,s,neighbor_chars=7)
    assert all(len(x['text'])<=7 and x['evidence_permission']=='NOT_AUTHORIZED_BY_THIS_PACKET'
        for x in w['packets'][0]['neighbor_context'])
    assert any(x['truncated'] for x in w['packets'][0]['neighbor_context'])


def test_partial_review_does_not_certify_coverage_or_unrelated_fields():
    k,s=fixture();k.facts[0].fact_type='An extra unreviewed qualification'
    w=build_review_inventory(k,s)
    p=next(p for p in w['packets'] if '/content' in p['members'][0])
    d=decision(w);d.update(packet_id=p['packet_id'],binding=p['binding'],members=p['members'],status='PARTIALLY_SUPPORTED')
    r=resolve_reviews(w,append_decision(w,[],d));draft=comprehensive_draft(k,s,r)
    coverage=coverage_report(k,s,r,accepted_primary_ids=[],topic_inventory=[dict(source_id='S1',quote=s.source_units[1].text,
        represented_by=['FCT_0001:/content'])],retention=draft['retention'])
    assert coverage['accepted_extraction_units']==0 and coverage['primary_units_with_knowledge']==1
    assert not coverage['topic_inventory_exhaustive'] and not coverage['whole_document_verified']
    projected=materialize_reviews(k,r)
    assert not any(x.status=='SUPPORTED' for x in projected.facts[0].educational_review.field_reviews)


def test_packet_ui_escapes_source_and_export_stays_draft():
    k,s=fixture('</script><script>alert(1)</script>');w=build_review_inventory(k,s)
    html=evidence_desk_html(resolve_reviews(w,[]))
    assert '</script><script>alert(1)' not in html
    assert 'textContent' in html and 'Not accepted until version validation' in html
    assert 'new Date().toISOString()' in html


def test_sampling_is_deterministic_and_does_not_assign_scores():
    k,s=fixture();w=build_review_inventory(k,s);a=plan_sample(w,risk_count=0,random_count=1)
    assert a==plan_sample(w,risk_count=0,random_count=1)
    assert not set(a['random_sample'])&set(a['risk_sample'])
    assert a['overall_quality_score'] is None and a['findings_status']=='NOT_REVIEWED'


def test_incomplete_formula_cannot_be_approved_as_complete_equation():
    k,s=fixture('The expression continues in the missing figure.')
    k.facts=[]
    k.formulas=[Formula(knowledge_id='FRM_0001',document_id='D',source_unit_ids=['S1'],
        content='M = P * R',formula_text='M = P * R',extraction_metadata=dict(source_grounding=dict(evidence=[
            dict(source_id='S1',quote=s.source_units[1].text,fields=['/content','/formula_text'])])))]
    w=build_review_inventory(k,s)
    with pytest.raises(ValueError,match='completeness'):append_decision(w,[],decision(w))


def test_legacy_pin_does_not_survive_changed_claim_or_qualifications():
    k,s=fixture()
    from app.models.educational_review import EducationalReview,FieldReview
    k.facts[0].educational_review=EducationalReview(field_reviews=[FieldReview(path='/content',
        mode='faithful_paraphrase',status='SUPPORTED',reviewer='recorded fixture reviewer',rationale='Synthetic original decision',
        evidence=[dict(source_id='S1',quote=s.source_units[1].text)])])
    w=build_review_inventory(k,s)
    pin=dict(source_version=w['source_version'],field_bindings={r['key']:r['binding'] for r in w['inventory']},
        baseline_artifact='synthetic fixture',baseline_sha256='fixture',imported_at=datetime.now(timezone.utc).isoformat())
    assert resolve_reviews(w,[],legacy_pin=pin)['inventory'][0]['semantic_status']=='SUPPORTED'
    k.facts[0].content='The sample always reacts without exceptions.'
    r=resolve_reviews(build_review_inventory(k,s),[],legacy_pin=pin)
    assert all(x['semantic_status']=='NOT_REVIEWED' for x in r['inventory'])


def test_neighbor_reference_without_association_is_not_evidence_permission():
    k,s=fixture();k.facts[0].extraction_metadata['source_grounding']['evidence'][0].update(
        source_id='AFTER',quote=s.source_units[2].text)
    w=build_review_inventory(k,s)
    assert all(not r['mechanical_validation']['active_field_evidence_valid'] for r in w['inventory'])
    with pytest.raises(ValueError,match='valid evidence'):append_decision(w,[],decision(w))


def test_composite_field_is_not_counted_as_one_atomic_fact():
    k,s=fixture('The sample may react. It must remain dry. A wet sample is excluded.')
    w=build_review_inventory(k,s)
    assert len(w['packets'])==1 and w['packets'][0]['atomic_claim_count'] is None
    assert w['packets'][0]['claim_unit_kind']=='UNSPLIT_FIELD_BUNDLE'


def test_all_adaptive_formats_still_exist_and_prior_review_record_is_preserved():
    from app.representation.formats import RepresentationFormat
    assert len(list(RepresentationFormat))==9
    k,s=fixture();w=build_review_inventory(k,s)
    r=resolve_reviews(w,append_decision(w,[],decision(w)))
    projected=materialize_reviews(k,r)
    assert 'semantic_review_prior_record' in projected.facts[0].extraction_metadata
    assert not k.facts[0].educational_review


def test_import_is_validated_before_any_new_output_is_written(tmp_path):
    from import_semantic_reviews import import_reviews
    k,s=fixture();w=build_review_inventory(k,s)
    kp=tmp_path/'knowledge.json';sp=tmp_path/'source.json';dp=tmp_path/'decisions.json'
    kp.write_text(k.model_dump_json(),encoding='utf-8');sp.write_text(s.model_dump_json(),encoding='utf-8')
    bad=decision(w);bad['binding']='stale'
    dp.write_text(json.dumps([bad]),encoding='utf-8')
    output=tmp_path/'bad'
    with pytest.raises(ValueError,match='Stale'):import_reviews(kp,sp,dp,output)
    assert not output.exists()
    dp.write_text(json.dumps([decision(w)]),encoding='utf-8')
    result=import_reviews(kp,sp,dp,tmp_path/'valid')
    assert all(r['semantic_status']=='SUPPORTED' for r in result['inventory'])
    assert (tmp_path/'valid'/'decision_history.json').exists()


def test_invalid_legacy_citation_scope_is_not_grandfathered_as_supported():
    k,s=fixture()
    from app.models.educational_review import EducationalReview,FieldReview
    k.facts[0].educational_review=EducationalReview(field_reviews=[FieldReview(path='/content',mode='faithful_paraphrase',
        status='SUPPORTED',reviewer='synthetic reviewer',rationale='Invalid old permission fixture',
        evidence=[dict(source_id='AFTER',quote=s.source_units[2].text)])])
    w=build_review_inventory(k,s)
    pin=dict(source_version=w['source_version'],field_bindings={r['key']:r['binding'] for r in w['inventory']},
        baseline_artifact='synthetic fixture',baseline_sha256='fixture',imported_at=datetime.now(timezone.utc).isoformat())
    r=resolve_reviews(w,[],legacy_pin=pin)
    row=next(r for r in r['inventory'] if r['path']=='/content')
    assert row['semantic_status']=='INCONCLUSIVE' and row['legacy_review']['status']=='SUPPORTED'


def test_source_reference_does_not_prove_topic_completeness():
    k,s=fixture();w=build_review_inventory(k,s);r=resolve_reviews(w,append_decision(w,[],decision(w)))
    report=coverage_report(k,s,r,topic_inventory=[dict(source_id='S1',quote=s.source_units[1].text,
        represented_by=['FCT_0001:/content'])])
    topic=report['sections']['Lesson'][0]['topics'][0]
    assert topic['represented_field_status']=='SUPPORTED' and topic['topic_coverage_status']=='NEEDS_REVIEW'
    with pytest.raises(ValueError,match='unknown canonical'):
        coverage_report(k,s,r,accepted_primary_ids=['invented'])
    with pytest.raises(ValueError,match='authorized source'):
        coverage_report(k,s,r,topic_inventory=[dict(source_id='AFTER',quote=s.source_units[2].text,
            represented_by=['FCT_0001:/content'])])


def test_reviewed_formula_component_does_not_hide_visual_warning():
    from app.evaluation.offline_recovery import reviewed_student_preview
    from app.models.educational_review import EducationalReview,FieldReview
    k,s=fixture('P means principal; the full equation is shown in a missing figure.')
    k.facts=[]
    k.formulas=[Formula(knowledge_id='FRM_0001',document_id='D',source_unit_ids=['S1'],
        content='M = P * R',formula_text='M = P * R',variables={'P':'principal'},
        educational_review=EducationalReview(formula_status='VISUAL_CONTEXT_REQUIRED',field_reviews=[
            FieldReview(path='/variables/P',mode='faithful_paraphrase',status='SUPPORTED',reviewer='synthetic reviewer',
                rationale='Explicit component definition, not a complete formula.',evidence=[dict(source_id='S1',quote=s.source_units[1].text)])]))]
    notes=reviewed_student_preview(k,s,[],version=8)['markdown']
    assert 'visual-context warning' in notes and 'principal' in notes and 'M = P * R' not in notes


def test_embedded_nonliteral_code_does_not_leak_through_uncertain_prose():
    k,s=fixture('Declare a variable and read its value.')
    k.facts[0].content=k.facts[0].fact_text='Declare a variable, e.g., int invented = 42; then read its value.'
    w=build_review_inventory(k,s);r=resolve_reviews(w,[]);draft=comprehensive_draft(k,s,r)
    assert 'int invented = 42;' not in draft['markdown']
    assert 'then read its value' in draft['markdown'] and 'literal fragment withheld' in draft['markdown']
    assert all(x['semantic_status']=='NOT_REVIEWED' for x in r['inventory'])
    assert any(x['disposition']=='PARTIALLY_WITHHELD_MARKER' for x in draft['retention'])
    assert 'int invented = 42;' in k.facts[0].content
