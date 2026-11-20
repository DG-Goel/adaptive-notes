"""Synthetic derived-source fixtures test policy, not PDF/PPTX/OCR parser quality."""
import hashlib
import json
from pathlib import Path
import pytest
from app.models.source import SourceUnit
from app.models.knowledge import ExtractionChunk
from app.ingestion.educational_policy import EducationalAssessment, validate_exclusions
from app.extraction.chunker import ContentChunker
from app.extraction.source_context import select_context
from app.extraction.grounded_fields import resolve_response
from app.extraction.prompts import CATEGORY_FIELDS


@pytest.mark.parametrize('text,kind,status,provenance',[
 ('Subscribe today. A variable stores a value.','paragraph','mixed',{'segment':1}),
 ('Area = pi r², for a circle.','formula','educational',{}),
 ('Mitosis divides a cell into daughter cells.','paragraph','educational',{}),
 ('In 1914 war began; in 1918 it ended.','paragraph','educational',{}),
 ('Under dry conditions, the sample showed increased resistance.','paragraph','incomplete_educational',{}),
 ('Table 1: observations\nTime | Value\n1 | 2','table','educational',{'page':2}),
 ('Slide 3: evaporation follows heating.','paragraph','educational',{'slide':3,'element':'shape7'}),
 ('l0 mg? concentration may be 10 mg.','paragraph','noisy_educational',{'ocr':True}),
 ('Thank you and subscribe.','paragraph','noneducational',{}),
 ('A previously unclassified theorem.','paragraph','uncertain',{}),
])
def test_policy_retains_content_and_available_provenance(text,kind,status,provenance):
    u=SourceUnit(source_id='S1',document_id='D',type=kind,position=0,text=text,
        content_role='noise',provenance=provenance,educational_assessment=EducationalAssessment(status=status))
    chunks=ContentChunker().chunk([u],'D')
    assert chunks[0].source_units==['S1'] and text in chunks[0].text_content
    assert SourceUnit.model_validate_json(u.model_dump_json()).provenance==provenance
    if status in {'uncertain','noisy_educational','incomplete_educational'}:
        assert chunks[0].review_source_ids==['S1']


def test_whole_exclusion_requires_review_and_cannot_conflict_with_citations():
    u=SourceUnit(source_id='S',document_id='D',type='paragraph',position=0,text='Subscribe',
        educational_assessment=EducationalAssessment(status='noneducational',reason='Only promotion',whole_unit_reviewed=True))
    assert validate_exclusions([u],['S'])=={'S'}
    assert ContentChunker().chunk([u],'D')==[]
    for exclusions,cited in [(['S','S'],[]),(['unknown'],[]),(['S'],['S'])]:
        with pytest.raises(ValueError): validate_exclusions([u],exclusions,cited)


def test_bounded_context_and_primary_coverage():
    units=[SourceUnit(source_id=f'S{i}',document_id='D',type='paragraph',position=i,text=t)
           for i,t in enumerate(['Definition begins','continues here','conditions apply'])]
    chunks=ContentChunker(max_tokens_per_chunk=5).chunk(units,'D')
    assert [s for c in chunks for s in c.source_units]==[u.source_id for u in units]
    context=select_context(chunks[1],units,100)
    assert context['primary_ids']==['S1'] and context['context_ids']==['S0','S2']
    assert context==select_context(chunks[1],units,100)
    assert select_context(chunks[1],units,0)['limitations']
    assert chunks[1].source_units==['S1']


def test_uninterpreted_visual_is_visible_as_limitation():
    u=SourceUnit(source_id='V',document_id='D',type='picture',position=0)
    assert ContentChunker().chunk([u],'D')[0].uninterpreted_source_ids==['V']


def test_historical_contradiction_remains_rejected_unchanged():
    root=Path(__file__).resolve().parents[1]/'data/output'
    manifest=json.loads((root/'java_authorization_20261107_021447_950425/manifest.json').read_text())
    response=next((root/'java_live_java-20261107_021447_950425').glob('*.response.json'))
    before=hashlib.sha256(response.read_bytes()).hexdigest()
    content=json.loads(response.read_text())['choices'][0]['message']['content']
    with pytest.raises(ValueError,match='contradictory exclusion'):
        resolve_response(content,ExtractionChunk.model_validate(manifest['requests'][0]['chunk']))
    assert hashlib.sha256(response.read_bytes()).hexdigest()==before


def test_exclusion_unknown_duplicate_and_cited_rejected():
    chunk=ExtractionChunk(chunk_id='C',source_units=['S'],text_content='[S] A cell divides.')
    for refs in [['Q9999'],['Q0000','Q0000']]:
        raw={**{c:[] for c in CATEGORY_FIELDS},'excluded':[dict(ref=r,reason='noneducational') for r in refs]}
        with pytest.raises(ValueError): resolve_response(json.dumps(raw),chunk)


def test_real_transcript_parser_preserves_timestamp(tmp_path):
    from app.ingestion.transcript_parser import parse_transcript
    path=tmp_path/'lecture.txt';path.write_text('00:00:12 A cell divides into two daughter cells.\n',encoding='utf-8')
    doc=parse_transcript(path,min_segment_words=1,max_segment_words=100)
    assert doc.source_units and doc.source_units[0].provenance['timestamp']=='00:00:12'
