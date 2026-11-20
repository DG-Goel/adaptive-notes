import pytest
from app.models.knowledge import Fact,Procedure,Formula,KnowledgeDocument
from app.models.source import SourceDocument,SourceUnit
from app.models.educational_review import EducationalReview,FieldReview,ReviewQuote
from app.evaluation.field_faithfulness import audit_fields
from app.evaluation.citation_repair import add_reviewed_evidence
from app.evaluation.notes_pipeline import build_preview


def fixture(text='Under dry conditions the sample may react.'):
    s=SourceDocument(document_id='D',filename='fixture',page_count=0,source_units=[SourceUnit(source_id='S0',document_id='D',position=0,type='paragraph',text=text),SourceUnit(source_id='S1',document_id='D',position=1,type='paragraph',text='Check the combined condition first.')])
    f=Fact(knowledge_id='FCT_0001',document_id='D',source_unit_ids=['S0'],content='The sample always reacts in 2027.',fact_text='The sample always reacts in 2027.')
    k=KnowledgeDocument(document_id='D',source_filename='fixture',extraction_timestamp='offline',facts=[f])
    return s,k,f


@pytest.mark.parametrize('text',['Cells may divide.','Under dry conditions samples may react.','The evidence dates to 1918.','The experiment rejected the hypothesis.','The manual requires cooling first.'])
def test_unreviewed_claims_never_become_supported(text):
    s,k,f=fixture(text);rows=audit_fields(k,s)
    assert {r['path'] for r in rows}=={'/content','/fact_text'}
    assert all(r['status']=='NOT_REVIEWED' and not r['confirmed_defect'] for r in rows)


def test_faithful_paraphrase_does_not_require_verbatim():
    s,k,f=fixture('The sample may react under dry conditions.')
    f.content=f.fact_text='Under dry conditions, a reaction is possible.'
    f.educational_review=EducationalReview(field_reviews=[FieldReview(path='/content',mode='faithful_paraphrase',status='SUPPORTED',evidence=[ReviewQuote(source_id='S0',quote=s.source_units[0].text)],reviewer='fixture reviewer',rationale='Same qualified claim')])
    row=next(r for r in audit_fields(k,s) if r['path']=='/content')
    assert row['status']=='SUPPORTED' and not row['literal_substring']
    f.educational_review.field_reviews[0].mode='literal'
    assert next(r for r in audit_fields(k,s) if r['path']=='/content')['status']=='NOT_REVIEWED'


def test_code_in_procedure_and_citation_permissions():
    s,k,_=fixture('Read input from the terminal.')
    proc=Procedure(knowledge_id='PRC_0001',document_id='D',source_unit_ids=['S0'],content='Read input.',procedure_name='Input',steps=['var x = inventedCall();','Check the combined condition first.'])
    k.procedures=[proc]
    record=add_reviewed_evidence(proc,'/steps/1',s,'S1',s.source_units[1].text,reviewer='fixture',rationale='Exact correction passage')
    assert proc.extraction_metadata['primary_source_ids']==['S0'] and record['primary_coverage_unchanged']
    assert any(r['path']=='/steps/0' and r['code_like'] for r in audit_fields(k,s))
    result=build_preview(k,s,required_chunks=['C'],completed_chunks=['C'])
    assert 'inventedCall' not in result['markdown']
    assert 'Check the combined condition first.' in result['markdown']
    for path,quote in [('/missing','Check the combined condition first.'),('/steps/1','invented evidence')]:
        with pytest.raises(ValueError):add_reviewed_evidence(proc,path,s,'S1',quote,reviewer='fixture',rationale='test')


def test_supported_spoken_arithmetic_not_false_fragment():
    s,k,_=fixture('Ten plus three times two gives sixteen.')
    f=Formula(knowledge_id='FRM_0001',document_id='D',source_unit_ids=['S0'],content='10 + 3 * 2 = 16',formula_text='10 + 3 * 2 = 16')
    f.educational_review=EducationalReview(formula_status='COMPLETE',status='SUPPORTED',reviewer='fixture',rationale='Complete expression/result explicitly spoken',evidence=[ReviewQuote(source_id='S0',quote=s.source_units[0].text)])
    k.facts=[];k.formulas=[f]
    assert 'Formula fragment:' not in build_preview(k,s,required_chunks=['C'],completed_chunks=['C'])['markdown']


def test_exact_merge_keeps_each_sources_field_evidence():
    from app.extraction.consolidation import consolidate
    s,k,f=fixture('A fact.')
    f.content=f.fact_text='A fact.'
    f.extraction_metadata={'source_grounding':{'mechanically_valid':True,'evidence':[dict(source_id='S0',quote='A fact.',fields=['/content','/fact_text'])]}}
    other=f.model_copy(deep=True);other.knowledge_id='FCT_0002';other.source_unit_ids=['S1']
    other.extraction_metadata['source_grounding']['evidence'][0]['source_id']='S1'
    k.facts.append(other)
    result,_=consolidate(k)
    assert len(result.facts)==1
    assert {e['source_id'] for e in result.facts[0].extraction_metadata['source_grounding']['evidence']}=={'S0','S1'}


def test_recovery_plans_differ_from_parent_and_preserve_failed_source_spans():
    import json
    from pathlib import Path
    root=Path(__file__).resolve().parents[1]
    plan=json.loads((root/'data/output/task6_source_faithfulness_20261109/targeted_recovery_plan.json').read_text())
    assert plan['authorization']=='NONE' and plan['live_calls']==0
    assert len(plan['requests'])==4
    for parent in {r['failed_parent'] for r in plan['requests']}:
        rows=[r for r in plan['requests'] if r['failed_parent']==parent]
        assert len(rows)==2
        spans=[next(iter(r['chunk']['source_spans'].values())) for r in rows]
        assert spans[0][0]==0 and spans[0][1]==spans[1][0]
        assert all(r['status']=='PENDING_SEPARATE_AUTHORIZATION' for r in rows)


def test_actual_saved_repair_preserves_failures_and_restores_citations(tmp_path):
    import json
    from pathlib import Path
    from repair_saved_knowledge import repair
    root=Path(__file__).resolve().parents[1]
    result=repair(root/'data/output/java_live_java-20261109_022409_842270',
        root/'data/output/task6_source_faithfulness_20261109/repair_plan.json',tmp_path/'rebuild')
    assert result['report']['after']==458
    assert result['report']['gates']['extraction_completion']['outcome']=='FAIL'
    proc=next(i for i in result['knowledge'].procedures if i.knowledge_id=='PRC_0397')
    assert {'T0041','T0042','T0029'}<=set(proc.source_unit_ids)
    assert proc.extraction_metadata['primary_source_ids']==['T0041']
    assert any(e['source_id']=='T0042' and '/steps/3' in e['fields'] for e in proc.extraction_metadata['source_grounding']['evidence'])
    reps={r.knowledge_id:r for r in result['representations'].representations}
    assert reps['FRM_0014'].primary_format=='formula_display'
    assert reps['FRM_0015'].primary_format=='formula_display'
    assert reps['FRM_0007'].primary_format=='standard_text'
    assert 'mortgage = P * R' in result['markdown']
