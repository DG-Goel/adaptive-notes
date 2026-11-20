from jsonschema import Draft202012Validator
from app.extraction.organization_extraction import groq_wire_schema


def test_transport_keyword_removed_but_local_uniqueness_preserved():
    original={'type':'array','items':{'type':'string'},'uniqueItems':True}
    wire=groq_wire_schema(original)
    assert 'uniqueItems' not in wire
    assert original['uniqueItems'] is True
    assert not Draft202012Validator(original).is_valid(['Q1','Q1'])
    assert Draft202012Validator(original).is_valid(['Q1','Q2'])


def test_atomic_claim_transport_is_subset_of_original_union():
    legacy={'type':'object','properties':{'text':{'type':'string'}},'required':['text'],'additionalProperties':False}
    atomic={'type':'object','properties':{'text':{'type':'string'},'claims':{'type':'array'}},'required':['text','claims'],'additionalProperties':False}
    original={'anyOf':[legacy,atomic]}
    wire=groq_wire_schema(original)
    assert wire==atomic
    assert Draft202012Validator(original).is_valid({'text':'x','claims':[]})
    assert not Draft202012Validator(wire).is_valid({'text':'x'})


def test_budget_counts_repeated_references_without_modifying_wire():
    import json
    from app.extraction.organization_extraction import schema_budget_text
    from app.extraction.organization_scheduler import ExtractionConfiguration
    value={'type':'object','properties':{'long_claim_field':{'type':'string'}},'required':['long_claim_field'],'additionalProperties':False}
    schema={'type':'object','properties':{str(i):{'$ref':'#/$defs/value'} for i in range(5)},'$defs':{'value':value}}
    response={'type':'json_schema','json_schema':{'name':'test','schema':schema}}
    before=json.dumps(response)
    text=schema_budget_text(ExtractionConfiguration(response_format='json_schema'),response)
    assert text.count('long_claim_field')==10
    assert '$ref' not in text
    assert json.dumps(response)==before


def test_budget_rejects_recursive_schema():
    import pytest
    from app.extraction.organization_extraction import schema_budget_text
    from app.extraction.organization_scheduler import ExtractionConfiguration,SchedulerHold
    response={'type':'json_schema','json_schema':{'schema':{'$ref':'#/$defs/value','$defs':{'value':{'$ref':'#/$defs/value'}}}}}
    with pytest.raises(SchedulerHold): schema_budget_text(ExtractionConfiguration(response_format='json_schema'),response)
