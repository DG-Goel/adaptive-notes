import json
import pytest
from app.extraction.canonical_grounding import resolve_response
from app.extraction.prompts import CATEGORY_FIELDS
from app.models.knowledge import ExtractionChunk


def test_projection_is_exact_and_evidenced():
    chunk=ExtractionChunk(chunk_id='C',source_units=['S'],text_content='[S] Cells divide.')
    data={**{c:[] for c in CATEGORY_FIELDS},'excluded':[]}
    data['facts']=[dict(fact_text={'text':'Cells divide.','refs':['Q0000']},fact_type=None)]
    result,audit=resolve_response(json.dumps(data),chunk)
    item=json.loads(result)['facts'][0]
    assert item['content']==item['fact_text']=='Cells divide.'
    assert {p for e in item['source_evidence'] for p in e['fields']}=={'/content','/fact_text'}
    del data['facts'][0]['fact_text']
    with pytest.raises(ValueError):resolve_response(json.dumps(data),chunk)


def test_empty_evidence_forbidden_by_wire_schema():
    from jsonschema import Draft202012Validator
    from app.extraction.canonical_grounding import response_format
    data={**{c:[] for c in CATEGORY_FIELDS},'excluded':[]}
    data['facts']=[dict(fact_text={'text':'A claim','refs':[]},fact_type=None)]
    assert not Draft202012Validator(response_format()['json_schema']['schema']).is_valid(data)
