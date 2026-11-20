"""Controlled fixtures validate engineering, never live model performance."""
import json
import pytest
from app.models.knowledge import Fact,KnowledgeDocument,Formula,Procedure
from app.models.source import SourceUnit,SourceDocument
from app.extraction.consolidation import consolidate
from app.evaluation.notes_pipeline import build_preview


def fixture(text='Cells divide.'):
    source=SourceDocument(document_id='D',filename='synthetic.txt',page_count=1,
        source_units=[SourceUnit(source_id=s,document_id='D',type='paragraph',position=i,text=text)
                      for i,s in enumerate(['S','C'])])
    fact=Fact(knowledge_id='FCT_0001',document_id='D',source_unit_ids=['S','C'],content=text,fact_text=text,
              extraction_metadata={'primary_source_ids':['S'],'context_source_ids':['C']})
    doc=KnowledgeDocument(document_id='D',source_filename='synthetic.txt',extraction_timestamp='offline',facts=[fact])
    return source,doc


@pytest.mark.parametrize('texts',[
 ['A cell divides.','A cell divides.'],['A cell divides.','A cell splits.'],
 ['Samples may react.','Samples never react.'],['Speed is distance/time.','Speed is time/distance.'],
 ['Growth increases under dry conditions.','Growth increases under wet conditions.'],
 ['The treaty began in 1918.','The treaty ended in 1918.']])
def test_only_exact_claims_merge(texts):
    _,doc=fixture(texts[0]);copy=doc.facts[0].model_copy(deep=True)
    copy.knowledge_id='FCT_0001';copy.content=copy.fact_text=texts[1];doc.facts.append(copy)
    result,audit=consolidate(doc)
    assert len(result.facts)==(1 if texts[0]==texts[1] else 2)
    assert sum(len(ids) for ids in audit['original_ids'].values())==2
    assert len({i.knowledge_id for i in result.facts})==len(result.facts)


@pytest.mark.parametrize('text',['int x = 1;','Area = πr².','Cells divide.','The treaty began in 1918.',
 'Under dry conditions samples may react.','Open valve, then inspect gauge.','Slide 2: organisms have cells.',
 'OCR: l0 mg? uncertain.'])
def test_cross_domain_gates_and_coverage(text):
    source,doc=fixture(text)
    result=build_preview(doc,source,required_chunks=['one','two'],completed_chunks=['one'])
    report=result['report']
    assert report['gates']['extraction_completion']['outcome']=='FAIL'
    assert report['gates']['semantic_faithfulness']['outcome']!='PASS'
    assert report['source_coverage']['S'] and not report['source_coverage']['C']
    assert 'UNVERIFIED PREVIEW' in result['markdown']
    assert report['before']==report['after']==1
    assert report['original_knowledge'][0]['fields']['content']==text


def test_no_silent_loss_of_procedure_details_and_injection():
    source,doc=fixture()
    doc.procedures=[Procedure(knowledge_id='PRC_0001',document_id='D',source_unit_ids=['S'],
        content='Inspect safely',procedure_name='Inspect',steps=['Open','Check'],
        prerequisites=['Disconnect power'],outcomes='Recorded result')]
    # This test concerns preservation/rendering, so supply actual field evidence.
    # The former fixture had no procedure teaching in its source at all.
    source.source_units[0].text='Inspect safely. Inspect. Open. Check. Disconnect power. Recorded result.'
    from app.evaluation.field_faithfulness import leaves
    doc.procedures[0].extraction_metadata={'source_grounding':{'mechanically_valid':True,'evidence':[
        {'source_id':'S','quote':source.source_units[0].text,
         'fields':[p for p,_ in leaves(doc.procedures[0].model_dump(mode='json'))]}]}}
    result=build_preview(doc,source,required_chunks=['one'],completed_chunks=['one'])
    assert 'Disconnect power' in result['markdown'] and 'Recorded result' in result['markdown']
    assert result['report']['gates']['structural_validity']['outcome']=='PASS'
    from app.rendering.renderer import MarkdownRenderer
    assert '<script>' not in MarkdownRenderer()._escape_markdown('<script>bad</script>',True)
    assert '...' not in MarkdownRenderer()._clean_for_mermaid('a'*90)


def test_real_parser_mocked_strict_extraction_to_notes(tmp_path):
    from app.ingestion.transcript_parser import parse_transcript
    from app.extraction.chunker import ContentChunker
    from app.extraction.extractor import KnowledgeExtractor
    from app.extraction.llm_provider import MockLLMProvider
    path=tmp_path/'lecture.txt';path.write_text('A cell divides into daughter cells.',encoding='utf-8')
    source=parse_transcript(path,min_segment_words=1,max_segment_words=100)
    chunk=ContentChunker().chunk(source.source_units,source.document_id)[0]
    sid=chunk.source_units[0];text=source.source_units[0].text
    raw={'facts':[dict(content=text,fact_text=text,source_unit_ids=[sid],
        source_evidence=[dict(source_id=sid,quote=text,fields=['/content','/fact_text'])])]}
    parser=KnowledgeExtractor(MockLLMProvider(responses={},default_response=json.dumps(raw)),strict_evidence=True,verbose=False)
    parser.valid_source_ids={sid};parser._evidence_sources={sid:text}
    items=parser._extract_from_chunk(chunk,source.document_id)
    doc=KnowledgeDocument(document_id=source.document_id,source_filename=source.filename,
        extraction_timestamp='offline',facts=items)
    result=build_preview(doc,source,required_chunks=[chunk.chunk_id],completed_chunks=[chunk.chunk_id])
    assert result['report']['after']==1
    assert result['report']['gates']['extraction_completion']['outcome']=='PASS'


@pytest.mark.parametrize('format_name,payload',[
 ('standard_text',{'content':'Text with a condition.'}),
 ('definition_box',{'term':'Cell','definition':'A basic biological unit.'}),
 ('comparison_table',{'items':['A','B'],'dimensions':['Mass'],'values':{'A':{'Mass':'1'},'B':{'Mass':'2'}}}),
 ('flowchart',{'steps':['Open','Inspect'],'procedure_name':'Check'}),
 ('timeline',{'events':[{'time':'1918','event':'Treaty signed'}]}),
 ('cause_effect_diagram',{'cause':'Heating','effect':'Expansion','mechanism':'Observed expansion'}),
 ('hierarchy_tree',{'root':'Organism','children':[{'name':'Cell','children':[]}]}),
 ('example_callout',{'exemplifies':'Assignment','example_text':'int x = 1;'}),
 ('formula_display',{'formula':'E = mc²','conditions':'In the stated model'})])
def test_nine_rendering_contracts(format_name,payload):
    from app.assembly.models import AssembledItem
    from app.rendering.renderer import MarkdownRenderer
    item=AssembledItem(knowledge_id='FCT_0001',document_id='D',knowledge_type='fact',
        primary_format=format_name,format_content=payload,selection_confidence=1,
        confidence_label='high',selection_reasoning='Synthetic explicit payload',source_unit_ids=['S'],
        position_in_section=0,ordering_rationale='Source order')
    lines,status,reason=MarkdownRenderer()._render_item(item)
    assert status=='complete' and 'S' in '\n'.join(lines)
    broken=item.model_copy(update={'format_content':{}})
    lines,status,reason=MarkdownRenderer()._render_item(broken)
    assert status!='complete' and reason
