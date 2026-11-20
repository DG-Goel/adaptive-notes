from app.extraction.output_splitting import smaller_chunks
from app.models.knowledge import ExtractionChunk
from app.models.source import SourceUnit


def test_exact_spans_preserve_text_and_stop_at_bound():
    text=('Java words.\n\t'*100)+'END'
    source=SourceUnit(source_id='S1',document_id='D',type='paragraph',position=0,text=text)
    chunk=ExtractionChunk(chunk_id='C',source_units=['S1'],text_content='[S1] '+text)
    children=smaller_chunks(chunk,[source])
    assert len(children)==2
    spans=[c.source_spans['S1'] for c in children]
    assert spans[0][0]==0 and spans[0][1]==spans[1][0] and spans[1][1]==len(text)
    assert ''.join(text[a:b] for a,b in spans)==text
    assert all(c.source_units==['S1'] for c in children)
    assert smaller_chunks(chunk.model_copy(update={'split_depth':8}),[source])==[]


def test_no_silent_character_cut_when_no_boundary():
    source=SourceUnit(source_id='S1',document_id='D',type='paragraph',position=0,text='X'*1000)
    chunk=ExtractionChunk(chunk_id='C',source_units=['S1'],text_content='[S1] '+source.text)
    assert smaller_chunks(chunk,[source])==[]
