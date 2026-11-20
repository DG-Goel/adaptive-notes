"""Lossless bounded splitting; retain canonical IDs and exact source offsets."""
import re
from app.extraction.chunk_splitter import ChunkSplitter
from app.models.knowledge import ExtractionChunk


def smaller_chunks(chunk, sources):
    if chunk.split_depth >= 8:
        return []
    if len(chunk.source_units)>1:
        return ChunkSplitter(max_split_depth=8).split_chunk(chunk,sources)
    source_id=chunk.source_units[0]
    source=next(u for u in sources if u.source_id==source_id)
    if source.type in ('table','formula','code') or source.representation_status=='structured':
        # A text fragment could detach values from headings or break literal syntax.
        # Hold an oversized indivisible element instead of silently changing its meaning.
        return []
    start,end=(chunk.source_spans or {}).get(source_id,(0,len(source.text or '')))
    text=(source.text or '')[start:end]
    if len(text)<400:
        return []
    # Choose a whitespace boundary near the midpoint; both slices retain all bytes.
    boundaries=[m.end() for m in re.finditer(r'\s+',text) if len(text)//3<=m.end()<=2*len(text)//3]
    if not boundaries:
        return []
    middle=start+min(boundaries,key=lambda n:abs(n-len(text)//2))
    result=[]
    for index,(a,b) in enumerate(((start,middle),(middle,end))):
        result.append(ExtractionChunk(chunk_id=f'{chunk.chunk_id}_FRAG{index}',source_units=[source_id],
            text_content=f'[{source_id}] '+source.text[a:b],section=chunk.section,page_range=chunk.page_range,
            split_depth=chunk.split_depth+1,parent_chunk_id=chunk.chunk_id,source_spans={source_id:(a,b)},
            source_states={source_id:source.representation_status or 'text'},
            literal_source_texts={source_id:source.text[a:b]} if source.type=='code' else {}))
    return result
