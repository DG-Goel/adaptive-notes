"""Lossless indexing fixtures for existing NOETRA notes formats."""
from dataclasses import replace
import json

import pytest

from app.infographics.contracts import SourceSnapshot
from app.infographics.source_index import (FileSourceReader, StructuralSourceIndexer,
    build_index, digest, subdivide)


def snapshot(text,media='text/markdown',source_id='lecture-1'):
    data=text.encode('utf-8')
    return SourceSnapshot(source_id,digest(data),data,media)


def assert_lossless(index):
    index.validate()
    assert index.reconstruct() == index.text
    assert index.reconstruct().encode('utf-8') == index.snapshot.content
    for b in index.units:
        assert b.text == index.text[b.source_start:b.source_end]
        assert b.content_hash == digest(b.text.encode('utf-8'))
        assert b.token_count == len(b.text.encode('utf-8'))
        assert b.token_count_kind == 'estimated'


@pytest.mark.parametrize('text',['','\n','\r\n\r\n','Hello.','Hello.\n\nWorld.\n',
    '# T\r\n\r\nSome text.\r\n','中文讲义。\n\nहिंदी नोट्स।\n\nالعربية 😀 e\u0301',
    '\ufeff# UTF-8 BOM is preserved\n'])
def test_lossless_offsets_unicode_and_empty(text):
    index=build_index(snapshot(text))
    assert_lossless(index)
    assert tuple(b.position for b in index.blocks)==tuple(range(len(index.blocks)))


def test_nested_headings_and_parent_links():
    index=build_index(snapshot('# Chapter\n\nIntro.\n\n## Section\n\n### Subsection\n\nBody.\n\n## Next\n\nEnd.'))
    body=next(b for b in index.blocks if b.text.startswith('Body'))
    sub=next(b for b in index.blocks if b.text.startswith('###'))
    assert body.section_path==('Chapter','Section','Subsection')
    assert body.parent_id==sub.id
    assert index.blocks[-1].section_path==('Chapter','Next')
    assert_lossless(index)


@pytest.mark.parametrize('text,kind',[
    ('```python\nprint("# Not a heading")\n\nprint("x")\n```\n','code'),
    ('~~~~js\nlet x=1;\n~~~\n~~~~\n','code'),
    ('```mermaid\ngraph TD\n A-->B\n```\n','diagram'),
    ('$$\nx^2+y^2=z^2\n$$\n','math'),
    ('$$ E=mc^2 $$\n','math'),
    ('\\[\nx=1\n\\]\n','math'),
    ('| Term | Meaning |\n| --- | --- |\n| a | b |\n','table'),
    ('- First\n  - Nested\n    continued\n- Second\n','bullet_list'),
    ('1. First\n   1. Nested\n2. Second\n','numbered_list'),
    ('Definition: A queue is FIFO.\n','definition'),
    ('**Example**: A FIFO queue.\n','example'),
    ('![A diagram](visuals/image.png)\n','diagram'),
    ('A | B\n--- | ---\na | b\n','table'),
    ('<table>\n<tr><th>A</th></tr>\n\n<tr><td>B</td></tr>\n</table>\n','table'),
    ('<svg>\n<path d="x"/>\n\n</svg>\n','diagram'),
    ('\\begin{align}\nx&=1\\\\\n\ny&=2\n\\end{align}\n','math'),
])
def test_atomic_structures(text,kind):
    index=build_index(snapshot(text))
    assert len(index.blocks)==1
    assert index.blocks[0].type==kind
    assert_lossless(index)


def test_unterminated_fences_and_equations_retain_rest_of_document():
    for prefix in ('```python\n','$$\n'):
        text=prefix+'Unclosed content\n\n# Still retained\n'
        index=build_index(snapshot(text))
        assert_lossless(index)
        assert len(index.blocks)==1


def test_equations_code_qualifications_and_examples_have_structural_cohesion():
    text='## Formula\n\nEnergy is:\n\n$$\nE=mc^2\n$$\n\nWhere m is mass.\n\nExample: m=1.\n\nUnless otherwise stated, c is fixed.\n'
    index=build_index(snapshot(text))
    assert len({b.cohesion_id for b in index.blocks})==1
    assert_lossless(index)
    code=build_index(snapshot('Run this:\n\n```py\nprint(1)\n```\n\nThis prints one.\n'))
    assert len({b.cohesion_id for b in code.blocks})==1


def test_existing_knowledge_anchor_and_literal_timestamps():
    text='A fact at 01:23–01:27.\n\n*[Knowledge ID: FCT_0042 | Sources: G00001, G00002]*\n\n*Source: G00001 · 2.00–3.00s*\n'
    index=build_index(snapshot(text))
    anchors=[b for b in index.blocks if b.type=='source_reference']
    assert anchors[0].references==('FCT_0042','G00001','G00002')
    assert '01:23–01:27' in index.blocks[0].timestamps
    assert 'FCT_0042' in index.blocks[0].references
    assert anchors[-1].timestamps==('2.00–3.00s',)
    assert len({b.cohesion_id for b in index.blocks})==1


def test_stable_ids_bind_artifact_hash_and_offsets():
    value=snapshot('# Heading\n\nSame.\n\nSame.\n')
    a,b=build_index(value),build_index(value)
    assert a==b and a.fingerprint==b.fingerprint
    assert len({x.id for x in a.blocks})==len(a.blocks)
    assert a.blocks[0].id!=build_index(snapshot(a.text,source_id='other')).blocks[0].id
    assert a.blocks[0].id!=build_index(snapshot(a.text+'change')).blocks[0].id


def test_safe_list_subdivision_preserves_nested_items_and_parent_traceability():
    text=''.join(f'- Item {i}\n  - Nested item {i}\n' for i in range(20))
    index=build_index(snapshot(text))
    assert len(index.blocks)==1
    fitted=subdivide(index,100)
    assert fitted.subdivisions[0][0]==index.blocks[0].id
    assert len(fitted.units)>1 and not fitted.oversized
    assert all(b.parent_id==index.blocks[0].id for b in fitted.units)
    assert all(b.text.startswith('- Item') and '  - Nested' in b.text for b in fitted.units)
    assert fitted==subdivide(index,100)
    assert_lossless(fitted)


def test_setext_headings_and_list_lazy_continuations():
    text='Chapter\n=======\n\nSection\n-------\n\n- An item\ncontinued on next line\n- Second item\n'
    index=build_index(snapshot(text))
    assert [b.type for b in index.blocks]==['heading','heading','bullet_list']
    assert index.blocks[-1].section_path==('Chapter','Section')
    assert_lossless(index)


def test_subdivision_keeps_heading_with_first_child():
    index=build_index(snapshot('# Heading\n\n'+''.join('- Item '+str(i)+' '+'x'*40+'\n' for i in range(20))))
    fitted=subdivide(index,150)
    assert fitted.units[0].type=='heading'
    assert fitted.units[1].cohesion_id==fitted.units[0].cohesion_id
    assert_lossless(fitted)


@pytest.mark.parametrize('text',['x'*1000,'```\n'+'x'*1000+'\n```',
    '$$\n'+'x'*1000+'\n$$','| A | B |\n|---|---|\n| '+'x'*1000+' | B |',
    '- Parent\n  - '+'x'*1000+'\n'])
def test_oversized_atoms_are_reported_without_damage(text):
    index=subdivide(build_index(snapshot(text)),100)
    assert index.oversized
    assert all(b.status=='unsupported_atomic_block' for b in index.oversized)
    assert_lossless(index)


def test_json_ordered_notes_exact_slices_and_all_metadata():
    values=[dict(note_id='CON_0001',text='First\n\n中文',timing=[dict(source_id='G1',start=1.2,end=3.4)],
                 source_gaps=[],visuals=[dict(payload=dict(type='table',rows=[['a','b']]))]),
            dict(note_id='EXA_0002',text='Example',unknown=dict(retain='ALL'))]
    text=json.dumps(values,ensure_ascii=False,indent=2)+'\r\n'
    index=build_index(snapshot(text,'application/json'))
    rows=[b for b in index.blocks if b.type=='ordered_note']
    assert len(rows)==2
    assert rows[0].locator=='/0' and 'CON_0001' in rows[0].references
    assert 'G1' in rows[0].timestamps[0]
    assert json.loads(rows[0].text)==values[0]
    assert 'unknown' in rows[1].text
    assert_lossless(index)


def test_frontend_note_document_sections_blocks_and_unknown_metadata():
    value=dict(id='lecture',title='Title',meta=dict(unknown=True),sections=[
        dict(id='s1',title='Chapter',level=1,startSeconds=1,blocks=[dict(id='b1',type='paragraph',content='原文')]),
        dict(id='s2',title='Subsection',level=2,blocks=[dict(id='b2',type='math',latex='x^2'),
            dict(id='b3',type='list',items=[dict(id='item',content='nested',items=[])])])],
        unplacedArtifacts=[dict(id='visual',payload='must remain')])
    index=build_index(snapshot(json.dumps(value,ensure_ascii=False),'application/json'))
    content=[b for b in index.blocks if b.type not in {'json_structure'}]
    assert [b.type for b in content]==['paragraph','math','list']
    assert content[1].section_path==('Chapter','Subsection')
    assert content[0].timestamps==('{"startSeconds": 1}',)
    assert 'must remain' in index.reconstruct()
    assert_lossless(index)


@pytest.mark.parametrize('text',['{"not":"notes"}','[1,2]','{"sections":[{}]}',
    '[{"note_id":"x","text":"a","text":"b"}]','[','[] trailing','[1,]'])
def test_unsupported_or_invalid_json_fails_explicitly(text):
    with pytest.raises((ValueError,TypeError)):
        build_index(snapshot(text,'application/json'))


def test_file_reader_is_read_only_and_hash_detects_mutation(tmp_path):
    path=tmp_path/'generated_notes.md'
    path.write_bytes(b'# Chapter\r\n\r\nOriginal.\r\n')
    reader=FileSourceReader({'lecture':path})
    before=path.read_bytes()
    source=reader.snapshot('lecture')
    assert build_index(source).reconstruct().encode()==before
    assert path.read_bytes()==before
    assert not hasattr(reader,'write')
    with pytest.raises(KeyError): reader.snapshot('unknown')
    path.write_bytes(before+b'Edited')
    assert reader.snapshot('lecture').sha256!=source.sha256


def test_phase1_source_indexer_adapter():
    source=snapshot('One.\n\nTwo.\n')
    items=StructuralSourceIndexer().index((source,))
    assert len(items)==2
    for item in items:
        evidence=item.evidence[0]
        assert item.text==source.content.decode()[evidence.start:evidence.end]
        assert evidence.source_sha256==source.sha256


def test_invalid_snapshot_hash_encoding_and_index_coverage():
    with pytest.raises(ValueError,match='hash'):
        build_index(replace(snapshot('Hello'),sha256='invalid'))
    raw=b'\xff'
    with pytest.raises(ValueError,match='UTF-8'):
        build_index(SourceSnapshot('bad',digest(raw),raw,'text/markdown'))
    with pytest.raises(ValueError,match='media'):
        build_index(replace(snapshot('x'),media_type='application/pdf'))
    index=build_index(snapshot('Hello'))
    with pytest.raises(ValueError,match='order|coverage'):
        replace(index,units=(replace(index.units[0],position=1),)).validate()


def test_large_lecture_complete_reconstruction():
    text=''.join(f'## Topic {i}\n\nOriginal paragraph {i}: 数据 and Unicode.\n\n' for i in range(1000))
    index=build_index(snapshot(text))
    assert len(index.blocks)==2000
    assert_lossless(index)
