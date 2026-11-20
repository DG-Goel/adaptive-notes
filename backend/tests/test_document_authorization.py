from pathlib import Path
import copy
import pytest
from app.extraction.document_authorization import document_plan, DocumentStageAAuthorization
from app.extraction.organization_scheduler import ExtractionConfiguration, digest, SchedulerHold


def test_actual_java_manifest_and_mutation(tmp_path):
    source = tmp_path/'java.txt'
    source.write_bytes((Path(__file__).resolve().parents[2]/'java.txt').read_bytes())
    config = ExtractionConfiguration(max_retries=0)
    plan = document_plan(source, config, 'java-test')
    assert len(plan['requests']) > 1
    split=document_plan(source,config,'split-test',1)
    assert len(split['requests'])>len(plan['requests'])
    assert [sid for e in split['requests'] for sid in e['source_ids']] == [sid for e in plan['requests'] for sid in e['source_ids']]
    protected=document_plan(source,config,'protected',output_policy='reserve_preferred_v1')
    roots=[e for e in protected['requests'] if e['parent_request_id'] is None]
    assert list(dict.fromkeys(sid for e in roots for sid in e['source_ids']))==[sid for e in plan['requests'] for sid in e['source_ids']]
    from app.ingestion.transcript_parser import parse_transcript
    doc=parse_transcript(source,min_segment_words=50,max_segment_words=500,detect_timestamps=True)
    for u in doc.source_units:
        spans=[(e['chunk']['source_spans'] or {}).get(u.source_id,(0,len(u.text))) for e in roots if u.source_id in e['source_ids']]
        assert ''.join(u.text[a:b] for a,b in spans)==u.text
    assert all(e['payload']['max_tokens']==4000 for e in protected['requests'])
    gate = object.__new__(DocumentStageAAuthorization)
    gate.manifest = copy.deepcopy(plan)
    gate.approved_manifest_sha256 = digest(plan)
    gate.configuration = config
    for entry in plan['requests']:
        assert gate.expected_payload(entry['request_id']) == entry['payload']
    with pytest.raises(SchedulerHold):
        gate.expected_payload('unapproved')
    gate.manifest['requests'][0]['payload']['temperature'] = 1
    with pytest.raises(SchedulerHold):
        gate.expected_payload(plan['requests'][0]['request_id'])
    gate.manifest = copy.deepcopy(plan)
    source.write_text('changed',encoding='utf-8')
    with pytest.raises(SchedulerHold):
        gate.expected_payload(plan['requests'][0]['request_id'])
