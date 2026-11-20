import copy,json
from pathlib import Path
import pytest
from pydantic import ValidationError
from app.extraction.single_request_authorization import SingleRequestStageAAuthorization
from app.extraction.organization_scheduler import digest,SchedulerHold


def package():
    root=Path(__file__).resolve().parents[1]/'data/output/task4_controlled_benchmark'
    m=json.loads((root/'manifest.json').read_text())
    from app.extraction.organization_scheduler import ExtractionConfiguration,configuration_fingerprint
    config=ExtractionConfiguration.model_validate_json(json.dumps(m['configuration']))
    m['configuration_sha256']=configuration_fingerprint(config)
    # Prepare a fresh offline fixture; never rewrite the archived unapproved package.
    from app.models.source import SourceDocument
    from app.models.knowledge import ExtractionChunk
    from app.extraction.source_context import bind_context
    from app.extraction.organization_extraction import prepare_request
    source=SourceDocument.model_validate(m['source_document'])
    m['payload'],_=prepare_request(bind_context(ExtractionChunk.model_validate(m['primary_chunk']),source.source_units),config)
    m['request_sha256']=digest(m['payload'])
    return root,m


def test_prepared_exact_payload_without_authorization():
    _,m=package()
    # Read-only contract inspection, deliberately not an authorization object.
    gate=object.__new__(SingleRequestStageAAuthorization)
    gate.manifest=m;gate.approved_manifest_sha256=digest(m)
    assert gate.expected_payload(m['request_id'])==m['payload']
    with pytest.raises(SchedulerHold):gate.expected_payload('another-request')


@pytest.mark.parametrize('field',['payload','source','configuration','boundary'])
def test_changed_request_cannot_reuse_binding(field):
    _,m=package();m=copy.deepcopy(m)
    if field=='payload':m['payload']['max_tokens']+=1
    if field=='source':m['source_document']['source_units'][0]['text']='Changed source'
    if field=='configuration':m['configuration']['max_retries']=1
    if field=='boundary':m['execution_boundary']['max_requests']=2
    gate=object.__new__(SingleRequestStageAAuthorization)
    gate.manifest=m;gate.approved_manifest_sha256=digest(m)
    with pytest.raises(SchedulerHold):gate.expected_payload(m['request_id'])


def test_pending_records_cannot_authorize_dispatch():
    root,m=package()
    record=json.loads((root/'stage_a.pending.json').read_text())
    approval=json.loads((root/'credential_approval.pending.json').read_text())
    with pytest.raises(ValidationError):
        SingleRequestStageAAuthorization(record,approval,m,digest(m))
