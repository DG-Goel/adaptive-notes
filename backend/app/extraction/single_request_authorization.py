"""Exact one-request boundary; preparation never grants authorization."""
from app.extraction.document_authorization import DocumentStageARecord
from app.extraction.stage_a_bridge import StageAAuthorization
from app.extraction.organization_scheduler import digest, SchedulerHold, ExtractionConfiguration, configuration_fingerprint
from app.extraction.organization_extraction import prepare_request
from app.extraction.source_context import bind_context
from app.models.source import SourceDocument
from app.models.knowledge import ExtractionChunk


class SingleRequestStageAAuthorization(StageAAuthorization):
    def __init__(self,record,approval,manifest,approved_manifest_sha256):
        import copy,json
        self.manifest=copy.deepcopy(manifest)
        self.approved_manifest_sha256=approved_manifest_sha256
        super().__init__(DocumentStageARecord.model_validate_json(json.dumps(record)),approval)

    def local_record_type(self):
        return DocumentStageARecord

    def expected_payload(self,request_id):
        import json
        m=self.manifest
        if digest(m)!=self.approved_manifest_sha256 or request_id!=m['request_id'] or m['execution_boundary']!={'max_requests':1,'automatic_retries':0,'continuation':False,'rotation':False}:
            raise SchedulerHold('Single-request manifest binding changed')
        config=ExtractionConfiguration.model_validate_json(json.dumps(m['configuration']))
        if config.max_retries!=0 or configuration_fingerprint(config)!=m['configuration_sha256']:
            raise SchedulerHold('Configuration changed or retries enabled')
        source=SourceDocument.model_validate(m['source_document'])
        chunk=ExtractionChunk.model_validate(m['primary_chunk'])
        # Hash the exact approved snapshot, not newly introduced constructor defaults.
        # Schema validation above and exact regenerated payload comparison below remain mandatory.
        if digest(m['source_document'])!=m['source_sha256']:
            raise SchedulerHold('Source snapshot changed')
        canonical={u.source_id:u.text for u in source.source_units}
        if chunk.text_content!='\n'.join(f'[{sid}] {canonical[sid]}' for sid in chunk.source_units):
            raise SchedulerHold('Primary source serialization mismatch')
        payload,_=prepare_request(bind_context(chunk,source.source_units),config)
        if payload!=m['payload'] or digest(payload)!=m['request_sha256']:
            raise SchedulerHold('Exact request changed')
        return payload
