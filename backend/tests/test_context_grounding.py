"""Synthetic cross-domain fixtures; no provider calls."""
import json
import pytest
from app.models.source import SourceUnit
from app.models.knowledge import ExtractionChunk
from app.extraction.source_context import bind_context
from app.extraction.organization_extraction import prepare_request
from app.extraction.organization_scheduler import ExtractionConfiguration,digest
from app.extraction.context_grounding import resolve_response
from app.extraction.prompts import CATEGORY_FIELDS
from app.extraction.claim_review import review_claim


def setup(text='Area equals pi times radius squared.'):
    units=[SourceUnit(source_id='P',document_id='D',type='paragraph',position=0,text=text),
           SourceUnit(source_id='C',document_id='D',type='paragraph',position=1,text='This applies only to circles.')]
    chunk=bind_context(ExtractionChunk(chunk_id='X',source_units=['P'],text_content='[P] '+text),units)
    config=ExtractionConfiguration(prompt_policy='context_grounded_v3',response_format='json_schema')
    return chunk,config


@pytest.mark.parametrize('text',['Area equals pi times radius squared.','Cells may divide under these conditions.',
 'The treaty was signed in 1918.','The experiment applies only under dry conditions.',
 'Call the method after opening the connection.','A Java variable stores a value.'])
def test_actual_payload_context_hash_and_valid_multiple_evidence(text):
    chunk,config=setup(text)
    payload,budget=prepare_request(chunk,config)
    body=json.loads(payload['messages'][1]['content'])
    assert body['primary_source_ids']==['P'] and body['context_source_ids']==['C']
    assert any(e['source_id']=='C' and e['role']=='context' for e in body['excerpts'])
    assert prepare_request(chunk,config)==(payload,budget)
    changed=chunk.model_copy(update={'context_text':'[C] Changed context.'})
    assert digest(prepare_request(changed,config)[0])!=digest(payload)
    v={'text':text,'refs':['Q0000','Q0001']}
    raw={**{c:[] for c in CATEGORY_FIELDS},'excluded':[],'facts':[dict(content=v,fact_text=v,fact_type=None)]}
    resolved,audit=resolve_response(json.dumps(raw),chunk)
    assert json.loads(resolved)['facts'][0]['source_unit_ids']==['P','C']
    assert chunk.source_units==['P'] and audit[0]['context_counts_as_completed'] is False
    assert audit[0]['claim_reviews'][0]['semantic_verified'] is False


@pytest.mark.parametrize('problem',['context_item','context_exclusion','mismatch','missing_field'])
def test_permissions_and_raw_consistency(problem):
    chunk,_=setup();v={'text':'A claim','refs':['Q0000']}
    raw={**{c:[] for c in CATEGORY_FIELDS},'excluded':[],'facts':[dict(content=v,fact_text=v,fact_type=None)]}
    if problem=='context_item': v['refs']=['Q0001']
    if problem=='context_exclusion': raw['excluded']=[dict(ref='Q0001',reason='noneducational')]
    if problem=='mismatch': raw['facts'][0]['content']={'text':'Different','refs':['Q0000']}
    if problem=='missing_field': del raw['facts'][0]['content']
    with pytest.raises(ValueError): resolve_response(json.dumps(raw),chunk)


def test_semantics_never_promoted_by_matching_context():
    report=review_claim('The sample always weighs 20 mg.',['The sample may weigh 10 mg under dry conditions.'])
    assert report['signals']['unsupported_numbers']==['20']
    assert report['signals']['possibly_lost_qualifiers']
    assert not report['semantic_verified']
    assert review_claim('The sample reacts.',['The sample does not react.'])['signals']['possible_contradiction']
