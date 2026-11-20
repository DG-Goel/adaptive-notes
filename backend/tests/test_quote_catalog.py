import json
import pytest
from app.extraction.quote_catalog import catalog,resolve_response
from app.models.knowledge import ExtractionChunk


def fixture():
    return ExtractionChunk(chunk_id='C',source_units=['T1'],text_content="[T1] you'll write Java.\nWe can see Java se.\n")


def test_explicit_reference_resolves_original_text_and_preserves_raw():
    chunk=fixture()
    entry=catalog(chunk)['Q0000']
    raw=json.dumps({'facts':[{'content':'You will write Java.','source_unit_ids':['T1'],
        'source_evidence':[{'source_id':'T1','quote_id':'Q0000','quote':'you will write Java','fields':['/content']}]}]})
    resolved,audit=resolve_response(raw,chunk)
    assert json.loads(resolved)['facts'][0]['source_evidence'][0]['quote']==entry['quote']
    assert audit[0]['original_quote']=='you will write Java'
    assert json.loads(raw)['facts'][0]['source_evidence'][0]['quote']=='you will write Java'


@pytest.mark.parametrize('changes',[{'quote_id':'invented'},{'source_id':'T2'},{'quote':None},{'quote':''}])
def test_reject_bad_reference_or_missing_required_quote(changes):
    evidence=dict(source_id='T1',quote_id='Q0000',quote='Java',fields=['/content'])
    evidence.update(changes)
    with pytest.raises(ValueError):
        resolve_response(json.dumps({'facts':[dict(source_unit_ids=['T1'],source_evidence=[evidence])]}),fixture())


def test_no_reference_does_not_fuzzy_repair_quote():
    raw=json.dumps({'facts':[{'source_evidence':[dict(source_id='T1',quote='wrong',fields=['/content'])]}]})
    resolved,audit=resolve_response(raw,fixture())
    assert json.loads(resolved)==json.loads(raw) and audit==[]


def test_existing_array_reference_expands_without_inventing_fields():
    raw=json.dumps({'procedures':[{'steps':['one','two'],'source_unit_ids':['T1'],
        'source_evidence':[dict(source_id='T1',quote_id='Q0000',quote='Java',fields=['/steps','/unknown'])]}]})
    resolved,audit=resolve_response(raw,fixture())
    assert json.loads(resolved)['procedures'][0]['source_evidence'][0]['fields']==['/steps/0','/steps/1','/unknown']
    assert audit[0]['original_fields']==['/steps','/unknown']
