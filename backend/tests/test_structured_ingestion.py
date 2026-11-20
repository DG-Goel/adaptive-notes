"""Task 11: saved real Docling replay, actual model-free conversions, mock LLM.

These fixtures establish transport/structure fidelity, never semantic approval.
"""
import copy
from hashlib import sha256
import json
from pathlib import Path
from types import SimpleNamespace
import pytest

from app.ingestion.docling_parser import DoclingParser
from app.models.source import SourceDocument, SourceUnit
from app.extraction.chunker import ContentChunker
from app.extraction.source_context import bind_context
from app.extraction.context_grounding import chunk_prompt
from app.extraction.quote_catalog import catalog

ROOT=Path(__file__).resolve().parents[1]


def controlled_structure():
    def item(ref,label,text=None,**extra):
        return {'self_ref':ref,'label':label,'text':text,**extra}
    cells=[dict(text=t,row_span=1,col_span=1,start_row_offset_idx=r,end_row_offset_idx=r+1,
                start_col_offset_idx=c,end_col_offset_idx=c+1,column_header=r==0,row_header=c==0)
           for r,row in enumerate([['Condition','Mass (mg)'],['Dry','10']]) for c,t in enumerate(row)]
    return {'name':'controlled','origin':{'filename':'controlled.pdf'},'pages':{'1':{}},
        'body':{'children':[{'$ref':'#/texts/0'},{'$ref':'#/groups/0'},{'$ref':'#/tables/0'},
                             {'$ref':'#/pictures/0'},{'$ref':'#/texts/3'},{'$ref':'#/texts/4'},
                             {'$ref':'#/texts/5'},{'$ref':'#/pictures/1'}]},
        'texts':[item('#/texts/0','section_header','Measurements',level=1),
                 item('#/texts/1','list_item','Keep the sample dry.',parent={'$ref':'#/groups/0'}),
                 item('#/texts/2','caption','Sample apparatus',parent={'$ref':'#/pictures/0'}),
                 item('#/texts/3','code','    if ready:\n        measure()\n',code_language='Python'),
                 item('#/texts/4','formula','v = d / t',prov=[{'page_no':1,'charspan':[0,9],
                    'bbox':{'l':1,'t':20,'r':40,'b':1,'coord_origin':'BOTTOMLEFT'}}]),
                 item('#/texts/5','text','2',formatting={'script':'sub'})],
        'groups':[item('#/groups/0','list',children=[{'$ref':'#/texts/1'},{'$ref':'#/texts/1'}])],
        'tables':[item('#/tables/0','table',data={'num_rows':2,'num_cols':2,'table_cells':cells})],
        'pictures':[item('#/pictures/0','picture',children=[{'$ref':'#/texts/2'}],captions=[{'$ref':'#/texts/2'}]),
                    item('#/pictures/1','picture',meta={'tabular_chart':{'chart_data':{'num_rows':2,'num_cols':2,'table_cells':cells}}})]}


def create_documents(directory):
    """Controlled educational source files; no model or network required."""
    from docx import Document
    from docx.oxml import OxmlElement
    from docx.enum.style import WD_STYLE_TYPE
    from pptx import Presentation
    from pptx.chart.data import CategoryChartData
    from pptx.enum.chart import XL_CHART_TYPE
    from pptx.util import Inches
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    txt=directory/'controlled.txt'
    txt.write_text('Under dry conditions, the sample mass is 10 mg.\n\nKeep the sample dry.',encoding='utf-8')
    word=Document();word.add_heading('Measurements',0);word.add_heading('Conditions',1)
    word.add_paragraph('Under dry conditions, the sample mass is 10 mg.')
    word.add_paragraph('Keep the sample dry.',style='List Bullet')
    table=word.add_table(rows=2,cols=2)
    for row,values in zip(table.rows,[['Condition','Mass (mg)'],['Dry','10']]):
        for cell,text in zip(row.cells,values):cell.text=text
    p=word.add_paragraph('Carbon dioxide: CO');p.add_run('2').font.subscript=True
    p=word.add_paragraph();math=OxmlElement('m:oMath');run=OxmlElement('m:r');t=OxmlElement('m:t')
    t.text='v = d / t';run.append(t);math.append(run);p._p.append(math)
    word.styles.add_style('Code',WD_STYLE_TYPE.PARAGRAPH)
    word.add_paragraph('    if ready:\n        measure()',style='Code')
    docx=directory/'controlled.docx';word.save(docx)
    deck=Presentation();slide=deck.slides.add_slide(deck.slide_layouts[1])
    slide.shapes.title.text='Measurements'
    slide.placeholders[1].text='Under dry conditions, the sample mass is 10 mg.\nKeep the sample dry.'
    slide=deck.slides.add_slide(deck.slide_layouts[5]);slide.shapes.title.text='Recorded values'
    data=CategoryChartData();data.categories=['Dry'];data.add_series('Mass (mg)',[10])
    slide.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED,Inches(1),Inches(2),Inches(6),Inches(3),data)
    pptx=directory/'controlled.pptx';deck.save(pptx)
    # A native PDF text object exercises the installed model-free Docling pipeline.
    stream=b'BT /F1 12 Tf 40 700 Td (Under dry conditions the sample mass is 10 mg.) Tj ET'
    objects=[b'<< /Type /Catalog /Pages 2 0 R >>',b'<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
        b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 600 800] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>',
        b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>',
        b'<< /Length '+str(len(stream)).encode()+b' >>\nstream\n'+stream+b'\nendstream']
    content=b'%PDF-1.4\n';offsets=[]
    for i,obj in enumerate(objects,1):
        offsets.append(len(content));content+=f'{i} 0 obj\n'.encode()+obj+b'\nendobj\n'
    start=len(content);content+=b'xref\n0 6\n0000000000 65535 f \n'
    content+=b''.join(f'{n:010d} 00000 n \n'.encode() for n in offsets)
    content+=f'trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n{start}\n%%EOF\n'.encode()
    pdf_path=directory/'controlled.pdf';pdf_path.write_bytes(content)
    return [txt,docx,pptx,pdf_path]


def mock_notes(source):
    """Current canonical wire validation -> mocked strict extraction -> actual notes."""
    from app.extraction.canonical_grounding import resolve_response
    from app.extraction.prompts import CATEGORY_FIELDS
    from app.extraction.extractor import KnowledgeExtractor
    from app.extraction.llm_provider import MockLLMProvider
    from app.models.knowledge import KnowledgeDocument
    from app.evaluation.notes_pipeline import build_preview
    chunks=ContentChunker().chunk(source.source_units,source.document_id)
    facts=[];serialized=[];done=[]
    for chunk in chunks:
        chunk=bind_context(chunk,source.source_units)
        body=json.loads(chunk_prompt(chunk));serialized.append(body)
        candidates=[e for e in body['excerpts'] if e['role']=='primary']
        if not candidates:
            continue
        unit_map={u.source_id:u for u in source.source_units}
        substantive=[e for e in candidates if unit_map[e['source_id']].type!='heading'
                     and unit_map[e['source_id']].content_role not in ('furniture','noise','structural')]
        e=(substantive or candidates)[0]
        value={'text':e['quote'],'refs':[e['ref']]}
        response={**{c:[] for c in CATEGORY_FIELDS},'excluded':[],
            'facts':[{'fact_text':value,'fact_type':None}]}
        resolved,_=resolve_response(json.dumps(response),chunk)
        extractor=KnowledgeExtractor(MockLLMProvider(responses={},default_response=resolved),strict_evidence=True,verbose=False)
        extractor.valid_source_ids={u.source_id for u in source.source_units}
        extractor._evidence_sources={u.source_id:u.text or '' for u in source.source_units}
        items=extractor._extract_from_chunk(chunk,source.document_id)
        for item in items:
            item.extraction_metadata.update(primary_source_ids=[s for s in item.source_unit_ids if s in chunk.source_units])
            item.knowledge_id=f'FCT_{len(facts)+1:04d}'
            facts.append(item)
        done.append(chunk.chunk_id)
    knowledge=KnowledgeDocument(document_id=source.document_id,source_filename=source.filename,
        extraction_timestamp='offline-mock',facts=facts)
    preview=build_preview(knowledge,source,required_chunks=[c.chunk_id for c in chunks],completed_chunks=done)
    return preview,serialized


def test_saved_pdf_all_42_recovered_and_historical_ids_unchanged():
    path=ROOT/'data/output/docling_structure.json';oldpath=ROOT/'data/output/source_units.json'
    hashes=[sha256(p.read_bytes()).hexdigest() for p in (path,oldpath)]
    raw=json.loads(path.read_text(encoding='utf-8'));old=json.loads(oldpath.read_text(encoding='utf-8'))
    source=DoclingParser.project_document(raw)
    mapping={u.docling_ref:u for u in source.source_units}
    missing=[t for t in raw['texts'] if t['self_ref'] not in {u['docling_ref'] for u in old['source_units']}]
    assert len(missing)==42 and all(mapping[t['self_ref']].text==t['text'] for t in missing)
    assert len(source.source_units)==154 and len(mapping)==154
    assert all(mapping[u['docling_ref']].source_id==u['source_id'] for u in old['source_units'])
    assert len(source.ingestion['unresolved_source_ids'])==15
    for doc in [source,SourceDocument.model_validate(old)]:
        for chunk in ContentChunker().chunk(doc.source_units,doc.document_id):
            body=json.loads(chunk_prompt(bind_context(chunk,doc.source_units)))
            assert not ({e['source_id'] for e in body['excerpts']} & set(chunk.uninterpreted_source_ids))
    assert hashes==[sha256(p.read_bytes()).hexdigest() for p in (path,oldpath)]


def test_structures_identity_relationships_scripts_and_literal_code(tmp_path):
    raw=controlled_structure();source=DoclingParser.project_document(raw)
    units={u.docling_ref:u for u in source.source_units}
    assert len(units)==10
    assert units['#/texts/1'].parent_id==units['#/groups/0'].source_id
    assert units['#/texts/2'].parent_id==units['#/pictures/0'].source_id
    assert units['#/texts/3'].text=='    if ready:\n        measure()\n'
    assert units['#/texts/4'].provenance['docling_provenance'][0]['bbox']['coord_origin']=='BOTTOMLEFT'
    assert json.loads(units['#/tables/0'].text)['table']['table_cells'][2]['text']=='Dry'
    assert json.loads(units['#/texts/5'].text)=={'text':'2','script':'sub'}
    assert 'native_chart' in units['#/pictures/1'].text
    for chunk in ContentChunker().chunk(source.source_units,source.document_id):
        entries=catalog(bind_context(chunk,source.source_units))
        for e in entries.values():
            if e['source_id']==units['#/texts/3'].source_id:
                assert e['quote'].startswith('    ')
    one=DoclingParser.save_sidecar(raw,source,tmp_path)
    # Repeat from the same projection, without recursively embedding its sidecar pointer.
    fresh=DoclingParser.project_document(raw)
    assert DoclingParser.save_sidecar(raw,fresh,tmp_path)==one


@pytest.mark.parametrize('mutation',['missing','duplicate','fake_pending','pending_quote','state_conflict'])
def test_marker_guards_stay_strict(mutation):
    source=DoclingParser.project_document(controlled_structure())
    chunk=ContentChunker().chunk(source.source_units,source.document_id)[0]
    if mutation=='missing':chunk.text_content=''
    elif mutation=='duplicate':chunk.text_content+='\n'+chunk.text_content
    elif mutation=='fake_pending':chunk.uninterpreted_source_ids.append(chunk.source_units[0])
    elif mutation=='pending_quote':chunk.text_content+='\n['+chunk.uninterpreted_source_ids[0]+'] invented diagram'
    else:chunk.source_states[chunk.source_units[0]]='failed'
    with pytest.raises(ValueError):catalog(chunk)


def test_partial_and_broken_reference_are_retained(tmp_path):
    raw=controlled_structure();raw['body']['children'].append({'$ref':'#/texts/missing'})
    source=DoclingParser.project_document(raw,conversion_status='partial_success',conversion_errors=['page 2 OCR failed'])
    assert source.ingestion['status']=='incomplete'
    assert any(e.get('kind')=='item_resolution_failed' for e in source.ingestion['errors'] if isinstance(e,dict))
    assert any(u.representation_status=='failed' for u in source.source_units)
    parser=DoclingParser(sidecar_dir=tmp_path/'sidecars')
    path=tmp_path/'test.docx';path.write_bytes(b'fixture')
    parser.converter=SimpleNamespace(convert=lambda _:SimpleNamespace(status='partial_success',errors=['OCR failed'],
        document=SimpleNamespace(model_dump=lambda **_:raw)))
    parsed=parser.parse(path)
    assert parsed.ingestion['status']=='incomplete' and Path(parsed.ingestion['sidecar']['path']).exists()


def test_metadata_context_does_not_expand_coverage():
    source=DoclingParser.project_document(controlled_structure())
    units=source.source_units;table=next(u for u in units if u.type=='table')
    chunk=ContentChunker()._create_chunk('table',[table],None)
    contextual=bind_context(chunk,units)
    assert contextual.source_units==[table.source_id]
    assert units[0].source_id in contextual.context_source_ids
    assert sum(len(e['quote']) for e in json.loads(chunk_prompt(contextual))['excerpts'] if e['role']=='context')<=1000


@pytest.fixture(scope='module')
def actual_documents(tmp_path_factory):
    return create_documents(tmp_path_factory.mktemp('real_formats'))


@pytest.mark.parametrize('extension',['.txt','.docx','.pptx','.pdf'])
def test_real_conversion_to_request_mock_extraction_and_notes(actual_documents,tmp_path,monkeypatch,extension):
    import socket
    def no_network(*a,**kw):raise AssertionError('Network forbidden in offline conversion')
    monkeypatch.setattr(socket.socket,'connect',no_network)
    from app.ingestion.router import ingest_document
    from app.extraction.document_authorization import document_plan
    from app.extraction.organization_scheduler import ExtractionConfiguration,digest
    path=next(p for p in actual_documents if p.suffix==extension)
    options={} if extension=='.txt' else {'sidecar_dir':str(tmp_path/'sidecars')}
    if extension=='.pdf':options['pdf_mode']='native'
    source=ingest_document(path,parser_options=options)
    assert source.source_units and any('10' in (u.text or '') for u in source.source_units)
    if extension=='.docx':
        assert any(u.type=='table' and u.text for u in source.source_units)
        assert any(u.type=='formula' for u in source.source_units)
        assert any(u.type=='code' and u.text.startswith('    if ready:') for u in source.source_units)
    if extension=='.pptx':
        assert any('native_chart' in (u.text or '') for u in source.source_units)
        assert any(u.page==2 for u in source.source_units)
    config=ExtractionConfiguration(prompt_policy='canonical_grounded_v4',response_format='json_schema')
    plan=document_plan(path,config,'offline',parser_options=options)
    assert plan==document_plan(path,config,'offline',parser_options=options)
    assert all(e['request_sha256']==digest(e['payload']) for e in plan['requests'])
    preview,payloads=mock_notes(source)
    assert preview['report']['after']>0 and 'UNVERIFIED PREVIEW' in preview['markdown']
    assert preview['report']['publication_eligible'] is False
    assert preview['report']['gates']['semantic_faithfulness']['outcome']!='PASS'
    assert payloads


def test_formula_and_code_reach_actual_payload_without_enrichment():
    from app.extraction.organization_extraction import prepare_request
    from app.extraction.organization_scheduler import ExtractionConfiguration
    source=DoclingParser.project_document(controlled_structure())
    chunks=ContentChunker().chunk(source.source_units,source.document_id)
    config=ExtractionConfiguration(prompt_policy='canonical_grounded_v4',response_format='json_schema')
    texts='\n'.join(prepare_request(bind_context(c,source.source_units),config)[0]['messages'][1]['content'] for c in chunks)
    assert 'v = d / t' in texts and '    if ready:' in texts


def test_nontext_only_chunk_stays_in_pending_manifest(tmp_path,monkeypatch):
    from app.extraction import document_authorization as auth
    from app.extraction.organization_scheduler import ExtractionConfiguration
    path=tmp_path/'figure.pdf';path.write_bytes(b'fixture')
    raw={'body':{'children':[{'$ref':'#/pictures/0'}]},'pictures':[{'self_ref':'#/pictures/0','label':'picture'}]}
    source=DoclingParser.project_document(raw)
    monkeypatch.setattr(auth,'ingest_document',lambda *a,**kw:source)
    plan=auth.document_plan(path,ExtractionConfiguration(prompt_policy='canonical_grounded_v4',response_format='json_schema'),'pending')
    assert plan['requests']==[] and len(plan['pending_chunks'])==1
    assert plan['source_inventory'][0]['state']=='awaiting_interpretation'


def test_parser_version_changes_request_hash(tmp_path,monkeypatch):
    from app.extraction import document_authorization as auth
    from app.extraction.organization_scheduler import ExtractionConfiguration,digest
    path=tmp_path/'source.txt';path.write_text('Samples may react under dry conditions.',encoding='utf-8')
    config=ExtractionConfiguration(prompt_policy='canonical_grounded_v4',response_format='json_schema')
    original=auth.document_plan(path,config,'binding')
    ingest=auth.ingest_document
    def changed(*a,**kw):
        source=ingest(*a,**kw);source.ingestion['version']='different-parser';return source
    monkeypatch.setattr(auth,'ingest_document',changed)
    revised=auth.document_plan(path,config,'binding')
    assert digest(original)!=digest(revised)
    assert original['requests'][0]['request_sha256']!=revised['requests'][0]['request_sha256']


def test_empty_page_is_unresolved_without_blank_evidence():
    source=DoclingParser.project_document({'pages':{'1':{}},'body':{'children':[]}})
    assert source.ingestion['status']=='incomplete'
    assert source.source_units[0].representation_status=='awaiting_interpretation'
    assert source.source_units[0].docling_ref=='#/pages/1'


def test_large_structured_elements_are_not_fragmented_without_headers():
    from app.extraction.output_splitting import smaller_chunks
    source=DoclingParser.project_document(controlled_structure())
    for unit in source.source_units:
        if unit.type in ('table','formula','code'):
            chunk=ContentChunker()._create_chunk('indivisible',[unit],None)
            assert smaller_chunks(chunk,source.source_units)==[]
