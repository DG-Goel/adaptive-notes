import pytest
from app.models.knowledge import KnowledgeDocument,Procedure,Fact,Formula,Example
from app.models.source import SourceDocument,SourceUnit
from app.models.educational_review import EducationalReview,ReviewQuote,InstructionLink
from app.evaluation.notes_pipeline import build_preview


def run(items,texts,**kwargs):
    source=SourceDocument(document_id='D',filename='fixture',page_count=0,source_units=[SourceUnit(source_id=f'S{i}',document_id='D',position=i,type='paragraph',text=t) for i,t in enumerate(texts)])
    groups=dict(facts=[],procedures=[],examples=[],formulas=[])
    for item in items:groups[{'fact':'facts','procedure':'procedures','example':'examples','formula':'formulas'}[item.knowledge_type]].append(item)
    k=KnowledgeDocument(document_id='D',source_filename='fixture',extraction_timestamp='offline',**groups)
    return build_preview(k,source,required_chunks=['C'],completed_chunks=['C'],**kwargs)


@pytest.mark.parametrize('wrong,right',[
 ('Check multiples of 5 before multiples of 15.','Check multiples of 15 first.'),
 ('2 + 2 = 5.','2 + 2 = 4.'),('Plants do not respire.','Plants respire.'),
 ('All reactions release heat.','Some reactions absorb heat.'),
 ('The initial date was accepted.','Later evidence revises the initial date.'),
 ('The hypothesis was supported.','The experiment rejected the hypothesis.'),
 ('Replace the pump first.','Check the power supply before replacing the pump.')])
def test_instructional_roles_and_correction_links_across_domains(wrong,right):
    a=Procedure(knowledge_id='PRC_0001',document_id='D',source_unit_ids=['S0'],content=wrong,procedure_name='Demonstration',steps=[wrong])
    b=Fact(knowledge_id='FCT_0001',document_id='D',source_unit_ids=['S1'],content=right,fact_text=right)
    a.educational_review=EducationalReview(role='deliberately_incorrect_demonstration',reviewer='fixture reviewer',rationale='Source correction',evidence=[ReviewQuote(source_id='S0',quote=wrong)],links=[InstructionLink(kind='corrected_by',target_id=b.knowledge_id,evidence=[ReviewQuote(source_id='S1',quote=right)])])
    result=run([a,b],[wrong,right])
    assert 'INCORRECT DEMONSTRATION' in result['markdown'] and 'corrected by: FCT' in result['markdown']
    assert result['report']['after']==2 and not result['report']['publication_eligible']
    a.educational_review.links=[]
    assert 'Correction not available' in run([a],[wrong])['markdown']


@pytest.mark.parametrize('status',['COMPLETE','INCOMPLETE','AMBIGUOUS','VISUAL_CONTEXT_REQUIRED','NEEDS_REVIEW'])
def test_formula_status_preserved(status):
    f=Formula(knowledge_id='FRM_0001',document_id='D',source_unit_ids=['S0'],content='F = m*a',formula_text='F = m*a')
    f.educational_review=EducationalReview(formula_status=status,reviewer='fixture',rationale='Available expression',evidence=[ReviewQuote(source_id='S0',quote='F = m*a')])
    r=run([f],['F = m*a'])
    assert ('Formula fragment:' in r['markdown'])==(status!='COMPLETE')


@pytest.mark.parametrize('snippet',['print("hello")','const x = 1;','x = 2;'])
def test_literal_vs_reconstructed_code(snippet):
    example=Example(knowledge_id='EXM_0001',document_id='D',source_unit_ids=['S0'],content=snippet,example_text=snippet,exemplifies='Output')
    example.educational_review=EducationalReview(code_kind='literal',reviewer='fixture',rationale='Exact code',evidence=[ReviewQuote(source_id='S0',quote=snippet)])
    assert 'Source fidelity: literal substring' in run([example],[snippet])['markdown']
    example.educational_review=None
    r=run([example],['The source verbally describes output.'])
    if True:
        assert 'Literal source code unavailable' in r['markdown'] and snippet not in r['markdown']
        assert r['report']['original_knowledge'][0]['fields']['example_text']==snippet


def test_missing_topic_and_invalid_review_block_publication():
    f=Fact(knowledge_id='FCT_0001',document_id='D',source_unit_ids=['S0'],content='A fact',fact_text='A fact')
    f.educational_review=EducationalReview(status='SUPPORTED',reviewer='fixture',rationale='Wrong evidence',evidence=[ReviewQuote(source_id='S0',quote='fabricated')])
    r=run([f],['A fact. Important condition.'],topic_expectations=[dict(label='Condition',source_id='S0',quote='Important condition.',represented_by=[])])
    assert r['report']['gates']['educational_completeness']['outcome']=='FAIL'
    assert r['report']['gates']['semantic_faithfulness']['outcome']=='FAIL'
    assert r['report']['educational_review']['claim_reviews'][0]['status']=='NOT_REVIEWED'


def test_source_heading_order_and_heading_free_grouping():
    from app.representation.models import SelectedRepresentation
    from app.assembly.assembler import NoteAssembler
    reps=[SelectedRepresentation(knowledge_id=f'FCT_{i:04}',document_id='D',knowledge_type='fact',source_unit_ids=[f'S{i}'],primary_format='standard_text',format_content={'content':'Fact'},selection_confidence=1,confidence_label='high',selection_reasoning='fixture',section=label,source_position=i) for i,label in enumerate(['Z first section','A later section'])]
    assembler=NoteAssembler();groups,order=assembler._group_by_section(reps)
    assert [s.section_name for s in assembler._create_sections(groups,order)]==['Z first section','A later section']
    f=Fact(knowledge_id='FCT_0001',document_id='D',source_unit_ids=['S0'],content='A fact',fact_text='A fact')
    assert run([f],['A fact'])['assembled'].sections[0].section_name=='Source S0'


def test_a_lost_rendered_item_fails_retention_gate(monkeypatch):
    from app.rendering.renderer import MarkdownRenderer
    original=MarkdownRenderer.render
    def losing(self,doc):
        result=original(self,doc);result.manifest.items=[];return result
    monkeypatch.setattr(MarkdownRenderer,'render',losing)
    f=Fact(knowledge_id='FCT_0001',document_id='D',source_unit_ids=['S0'],content='A fact',fact_text='A fact')
    assert run([f],['A fact'])['report']['gates']['structural_validity']['outcome']=='FAIL'


def test_historical_benchmark_rebuild_is_safe_and_preserves_all_items(tmp_path):
    import json
    from pathlib import Path
    from rebuild_educational_preview import rebuild
    root=Path(__file__).resolve().parents[1]
    base=root/'data/output/java_live_java-20261107_152814_899964'
    result=rebuild(base/'cross_run_preview/knowledge.json',base/'source_document.json',
        root/'data/output/task5_educational_quality_20261107/review_annotations.json',tmp_path/'preview')
    assert result['report']['after']==376
    assert 'INCORRECT DEMONSTRATION' in result['markdown']
    assert 'VISUAL_CONTEXT_REQUIRED' in result['markdown'].replace('\\','')
    assert 'double result = (double)10 / 3' not in result['markdown']
    assert '```json' not in result['markdown']
    assert len(result['assembled'].sections)>1
    for section in result['assembled'].sections:
        ids=[item.knowledge_id for item in section.items]
        if 'PRC_0332' in ids:
            assert ids.index('PRC_0332')<ids.index('EXP_0094')<ids.index('EXM_0131')
