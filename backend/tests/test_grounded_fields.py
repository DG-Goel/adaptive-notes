import json
import pytest
from app.extraction.grounded_fields import resolve_response, response_format
from app.extraction.prompts import CATEGORY_FIELDS
from app.models.knowledge import ExtractionChunk
from app.extraction.extractor import KnowledgeExtractor


def body():
    return {**{c:[] for c in CATEGORY_FIELDS},'excluded':[]}


def chunk():
    return ExtractionChunk(chunk_id='C',source_units=['T1'],text_content='[T1] Open the editor. Save the file.')


def value(text,refs=None):
    return dict(text=text,refs=['Q0000'] if refs is None else refs)


def test_procedure_fields_have_individual_evidence():
    raw=body()
    raw['procedures']=[dict(content=value('Open the editor.'),procedure_name=value('Open the editor'),
        steps=[value('Open the editor.'),value('Save the file.',['Q0001'])],prerequisites=None,outcomes=None)]
    resolved,audit=resolve_response(json.dumps(raw),chunk())
    item=json.loads(resolved)['procedures'][0]
    assert {p for e in item['source_evidence'] for p in e['fields']}=={'/content','/procedure_name','/steps/0','/steps/1'}
    parser=KnowledgeExtractor(None,verbose=False,strict_evidence=True)
    parser.valid_source_ids={'T1'}
    parser._evidence_sources={'T1':'Open the editor. Save the file.'}
    assert len(parser._parse_response(resolved,chunk(),'D'))==1
    assert audit[0]['unaccounted_refs']==[]


@pytest.mark.parametrize('fault',['missing_content','empty_refs','unknown_ref','extra_field'])
def test_missing_or_invalid_evidence_never_repaired(fault):
    raw=body(); item=dict(content=value('Open the editor.'),fact_text=value('Open the editor.'),fact_type=None)
    raw['facts']=[item]
    if fault=='missing_content': del item['content']
    if fault=='empty_refs': item['content']['refs']=[]
    if fault=='unknown_ref': item['content']['refs']=['Q9999']
    if fault=='extra_field': item['invented']='no'
    with pytest.raises(ValueError): resolve_response(json.dumps(raw),chunk())


def test_empty_response_preserves_unresolved_excerpts():
    raw=body()
    _,audit=resolve_response(json.dumps(raw),chunk())
    assert audit[0]['review_required'] and len(audit[0]['unaccounted_refs'])==2
    raw['excluded']=[dict(ref=k,reason='promotion') for k in ['Q0000','Q0001']]
    resolved,audit=resolve_response(json.dumps(raw),chunk())
    assert not any(json.loads(resolved).values())
    assert len(audit[0]['excluded'])==2
