import json
import pytest
from app.extraction.typed_claim_wire import decode,resolve_response
from app.extraction.canonical_grounding import response_format
from app.models.knowledge import ExtractionChunk


def fixture():
    d={c:[] for c in response_format()['json_schema']['schema']['properties']}
    d.update(claims=[dict(id='C1',text='Java is a programming language.',refs=['Q0000'],basis='explicit',availability='SOURCE_SUPPORTED',literal_kind='verbal',instructional_role=None,related_refs=[])],abstentions=[])
    d['facts']=[dict(fact_text=['C1'],fact_type={'is_null':True,'value':[]})]
    return d


def test_lossless_native_validation():
    d=fixture(); decoded,unused=decode(json.dumps(d)); assert unused==[]
    c=ExtractionChunk(chunk_id='t',source_units=['S1'],text_content='[S1] Java is a programming language.',token_count=10)
    from app.extraction.canonical_grounding import resolve_response as native
    assert json.loads(resolve_response(json.dumps(d),c)[0])==json.loads(native(json.dumps(decoded),c)[0])


@pytest.mark.parametrize('defect',['missing_field','unknown_claim','duplicate_claim','duplicate_ref','unknown_evidence'])
def test_fail_closed(defect):
    d=fixture()
    if defect=='missing_field': del d['facts'][0]['fact_text']
    elif defect=='unknown_claim': d['facts'][0]['fact_text']=['missing']
    elif defect=='duplicate_claim': d['claims'].append(dict(d['claims'][0]))
    elif defect=='duplicate_ref': d['claims'][0]['refs']=['Q0000','Q0000']
    elif defect=='unknown_evidence': d['claims'][0]['refs']=['S1']
    c=ExtractionChunk(chunk_id='t',source_units=['S1'],text_content='[S1] Java is a programming language.',token_count=10)
    with pytest.raises(Exception): resolve_response(json.dumps(d),c)


def test_unassigned_claim_is_review_only_never_silently_lost():
    d=fixture(); d['facts']=[]
    decoded,review=decode(json.dumps(d))
    assert decoded['facts']==[]
    assert review[0]['text']==d['claims'][0]['text']
