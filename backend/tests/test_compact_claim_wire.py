import copy
import json
import pytest
from app.extraction.compact_claim_wire import decode,response_format,resolve_response
from app.extraction.organization_extraction import extraction_policy,schema_budget_text
from app.extraction.organization_scheduler import ExtractionConfiguration
from app.models.knowledge import ExtractionChunk


def fixture():
    return dict(claims=[dict(id='C1',text='Java is a programming language.',refs=['Q0000'],basis='explicit',availability='SOURCE_SUPPORTED',literal_kind='verbal',instructional_role=None,related_refs=[])],
        items=[dict(category='facts',fields=[dict(name='fact_text',is_null=False,groups=[['C1']],variables=[])])],abstentions=[],excluded=[])


def test_lossless_decode_and_unchanged_resolver():
    d=fixture(); decoded=decode(json.dumps(d))
    assert decoded['facts'][0]['fact_text']['claims'][0]['text']==d['claims'][0]['text']
    assert decoded['facts'][0]['fact_type'] is None
    chunk=ExtractionChunk(chunk_id='test',source_units=['S1'],text_content='[S1] Java is a programming language.',token_count=10)
    from app.extraction.canonical_grounding import resolve_response as native
    expected=native(json.dumps(decoded),chunk)[0]
    actual=resolve_response(json.dumps(d),chunk)[0]
    assert json.loads(actual)==json.loads(expected)


@pytest.mark.parametrize('defect',['unknown','duplicate','unused','missing','invented_field','bad_refs','hidden_null'])
def test_fail_closed(defect):
    d=fixture()
    if defect=='unknown': d['items'][0]['fields'][0]['groups']=[['missing']]
    elif defect=='duplicate': d['claims'].append(copy.deepcopy(d['claims'][0]))
    elif defect=='unused': d['items']=[]
    elif defect=='missing': d['items'][0]['fields']=[]
    elif defect=='invented_field': d['items'][0]['fields'][0]['name']='imaginary'
    elif defect=='bad_refs': d['claims'][0]['refs']=['Q0000','Q0000']
    elif defect=='hidden_null': d['items'][0]['fields'][0]['is_null']=True
    with pytest.raises(Exception): decode(json.dumps(d))


def test_unsupported_evidence_still_rejected_by_task12a():
    d=fixture(); d['claims'][0]['refs']=['Q9999']
    chunk=ExtractionChunk(chunk_id='test',source_units=['S1'],text_content='[S1] Java is a programming language.',token_count=10)
    with pytest.raises(Exception): resolve_response(json.dumps(d),chunk)


def test_schema_overhead_reduced_without_dispositions_removed():
    cfg=ExtractionConfiguration(prompt_policy='canonical_grounded_v4',response_format='json_schema',wire_format='compact_claim_table_v1')
    _,_,_,wire=extraction_policy(cfg)
    text=schema_budget_text(cfg,wire)
    assert len(text)<6000
    for name in ('availability','literal_kind','instructional_role','related_refs'): assert name in text
