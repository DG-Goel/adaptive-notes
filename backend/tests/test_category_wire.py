import json
import pytest
from jsonschema import Draft202012Validator
from app.extraction.category_wire import response_format,resolve_response
from app.models.knowledge import ExtractionChunk


def value(text,refs=None):
    refs=refs or ['Q0000']
    return dict(text=text,refs=refs,claims=[dict(text=text,refs=refs,basis='explicit',availability='SOURCE_SUPPORTED',literal_kind='verbal',instructional_role=None,related_refs=[])])


def test_original_task12a_validation_and_no_claim_ids():
    c=ExtractionChunk(chunk_id='t',source_units=['S1'],text_content='[S1] Java is a programming language.',token_count=10)
    data=dict(items=[dict(fact_text=value('Java is a programming language.'),fact_type=None)],abstentions=[],excluded=[])
    result,audit=resolve_response(json.dumps(data),c,'facts')
    assert json.loads(result)['facts'][0]['fact_text']=='Java is a programming language.'
    assert any(a.get('policy')=='evidence_first_12a_v1' for a in audit)


def test_unknown_evidence_and_missing_required_fields_rejected():
    c=ExtractionChunk(chunk_id='t',source_units=['S1'],text_content='[S1] Java is a programming language.',token_count=10)
    data=dict(items=[dict(fact_text=value('Invented',['Q9999']),fact_type=None)],abstentions=[],excluded=[])
    with pytest.raises(Exception): resolve_response(json.dumps(data),c,'facts')
    del data['items'][0]['fact_text']
    with pytest.raises(Exception): resolve_response(json.dumps(data),c,'facts')


@pytest.mark.parametrize('category',['concepts','definitions','explanations','examples','facts','formulas','procedures','relationships'])
def test_every_category_retains_original_evidence_schema(category):
    schema=response_format(category)['json_schema']['schema']
    Draft202012Validator.check_schema(schema)
    assert set(schema['properties'])=={'items','abstentions','excluded'}
    assert 'claims' in schema['$defs']['value']['anyOf'][1]['properties']
