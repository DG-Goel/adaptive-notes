import json
import pytest
from app.extraction.field_row_wire import decode,resolve_response
from app.models.knowledge import ExtractionChunk


def fixture():
    return dict(rows=[dict(item='I1',category='facts',field='fact_text',element=0,part='value',text='Java is a programming language.',refs=['Q0000'],basis='explicit',availability='SOURCE_SUPPORTED',literal_kind='verbal',instructional_role=None,related_refs=[])],abstentions=[],excluded=[])


def test_original_resolver_and_literal_preservation():
    d=fixture(); decoded=decode(json.dumps(d)); assert decoded['facts'][0]['fact_text']['text']==d['rows'][0]['text']
    from app.extraction.canonical_grounding import resolve_response as native
    chunk=ExtractionChunk(chunk_id='test',source_units=['S1'],text_content='[S1] Java is a programming language.',token_count=10)
    assert json.loads(resolve_response(json.dumps(d),chunk)[0])==json.loads(native(json.dumps(decoded),chunk)[0])


@pytest.mark.parametrize('defect',['field','part','refs','variable'])
def test_strict_failures(defect):
    d=fixture(); row=d['rows'][0]
    if defect=='field': row['field']='formula_text'
    elif defect=='part': row['part']='symbol'
    elif defect=='refs': row['refs']=['Q0000','Q0000']
    elif defect=='variable': row.update(category='formulas',field='variables',part='symbol')
    with pytest.raises(Exception): decode(json.dumps(d))


def test_scalar_labels_preserve_claim_order_without_dropping_rows():
    d=fixture(); d['rows'][0]['element']=8
    assert decode(json.dumps(d))['facts'][0]['fact_text']['text']==d['rows'][0]['text']


def test_unknown_source_evidence_rejected():
    d=fixture(); d['rows'][0]['refs']=['S1']
    c=ExtractionChunk(chunk_id='t',source_units=['S1'],text_content='[S1] Java is a programming language.',token_count=10)
    with pytest.raises(Exception): resolve_response(json.dumps(d),c)
