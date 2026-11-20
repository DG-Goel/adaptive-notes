"""One operator-authorized attempt; no persistent quota policy changes or retries."""
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from types import MethodType
from dotenv import dotenv_values
from run_authorized_java import save
from app.extraction.document_authorization import DocumentStageAAuthorization, request_slots
from app.extraction.organization_scheduler import (
    Identity, load_organizations, OrganizationScheduler, ExtractionConfiguration,
    LocalQuotaAdmission, digest, SchedulerHold,
)
from app.extraction.organization_extraction import extract_chunk, prepare_request
from app.models.knowledge import ExtractionChunk, KnowledgeDocument
from app.extraction.knowledge_merge import CATEGORIES
from app.ingestion.router import ingest_document
import app.extraction.stage_a_bridge as bridge

ROOT = Path(__file__).resolve().parent
FOLDER = ROOT/'data/output/multimodal_notes_full_multimodal-20261110_135722_143719'
REQUEST = 'multimodal-20261110_135722_143719-0224'
CONSENT = 'Current user: i told you to try run it once ignore the local gurard for once'


def main():
    manifest = json.loads((FOLDER/'manifest.json').read_bytes())
    authority = json.loads((FOLDER/'authorization.json').read_bytes())
    approved = next(a for a in json.loads((FOLDER/'approvals.json').read_bytes()) if a['request_id'] == REQUEST)
    entry = next(e for e in manifest['requests'] if e['request_id'] == REQUEST)
    config = ExtractionConfiguration.model_validate_json(json.dumps(manifest['configuration']))
    assert config.max_retries == 0
    assert digest(manifest) == authority['approved_manifest_sha256']
    slots = authority['selected_slots']
    assignments = request_slots(manifest, slots)
    assert assignments == authority['request_slots']
    rows = json.loads((ROOT/'data/output/organization_inventory_20261106/inventory.json').read_bytes())
    identities = [Identity(**{k: r[k] for k in Identity.model_fields}) for r in rows if r['slot'] in slots]
    orgs = load_organizations(identities, dotenv_values(ROOT/'.env'))
    identity = next(i for i in identities if i.slot == assignments[REQUEST])
    scheduler = OrganizationScheduler(ROOT/'data/live_state/organization.sqlite', orgs, config,
                                      configuration_review=authority['configuration_review'])
    with scheduler.transaction() as db:
        if db.execute('SELECT 1 FROM operations WHERE id=?', (REQUEST,)).fetchone():
            raise SchedulerHold('One-time request already claimed; no second attempt permitted')
    gate = DocumentStageAAuthorization(approved['record'], approved['credential_approval'], manifest,
        authority['approved_manifest_sha256'], config, rotation_slots=slots)
    chunk = ExtractionChunk.model_validate(entry['chunk'])
    payload, budget = prepare_request(chunk, config)
    assert payload == entry['payload'] and digest(payload) == entry['request_sha256']
    # Verify the current source/payload before enabling the process-local exception.
    assert gate.expected_payload(REQUEST) == payload
    document = ingest_document(Path(manifest['source_path']), parser_options=manifest.get('parser_options'))
    admission = LocalQuotaAdmission(**{k: getattr(identity,k) for k in
        ('organization','project','credential_id','credential_sha256')}, request_id=REQUEST,
        request_sha256=digest(payload), configuration_sha256=scheduler.config_hash,
        authorization=approved['record']['authorization'], windows=gate.record.limits)
    report = dict(request_id=REQUEST, slot=identity.slot, operator_instruction=CONSENT,
                  started_at=datetime.now(timezone.utc).isoformat(), max_physical_attempts=1,
                  persistent_policy_changed=False, previous_charges_preserved=True)
    report_path = FOLDER/(REQUEST+'.one_time_override.json')
    save(report_path, report)
    def capacity_once(self, db, candidate, evidence, inp, out, now):
        if (candidate != identity or evidence.request_id != REQUEST or inp != budget.input_tokens
                or out != budget.max_output_tokens):
            raise SchedulerHold('Quota exception is bound to one exact request')
        self._event(db, REQUEST, identity.organization, 'operator_one_time_quota_override', report)
    scheduler._capacity = MethodType(capacity_once, scheduler)
    original_ceiling = bridge.quota_ceiling
    # Shared Stage A still performs identity, exact payload and durable claim checks.
    # Only its numeric local quota comparison is excepted, in this single-call process.
    bridge.quota_ceiling = lambda *args, **kwargs: 2**62
    started = time.monotonic()
    try:
        print('Sending exactly one approved request on NOTES '+str(identity.slot), flush=True)
        items = extract_chunk(scheduler, REQUEST, chunk, document.source_units, document.document_id,
            {identity.organization: admission}, stage_a=gate,
            response_sink=lambda body: save(FOLDER/(REQUEST+'.response.json'), body))
        groups = {c: [] for c in CATEGORIES}
        for item in items:
            category = next(c for c in CATEGORIES if c.rstrip('s') == item.knowledge_type
                            or (c == 'procedures' and item.knowledge_type == 'procedure'))
            groups[category].append(item)
        part = KnowledgeDocument(document_id=document.document_id, source_filename=document.filename,
            extraction_timestamp=datetime.now(timezone.utc).isoformat(),
            source_units_processed=len(chunk.source_units)-len(chunk.uninterpreted_source_ids), **groups)
        part.update_statistics()
        save(FOLDER/(REQUEST+'.json'), part.model_dump(mode='json'))
        report.update(result='locally_validated', extracted_items=len(items))
    except Exception as exc:
        orgs.check_metadata(str(exc))
        report.update(result='failed_or_unresolved', error_type=type(exc).__name__, error=str(exc))
    finally:
        bridge.quota_ceiling = original_ceiling
        report['elapsed_seconds'] = time.monotonic()-started
        with scheduler.transaction() as db:
            report['attempts'] = [dict(r) for r in db.execute('SELECT * FROM attempts WHERE request_id=?', (REQUEST,))]
            report['operation'] = [dict(r) for r in db.execute('SELECT id,state,slot FROM operations WHERE id=?', (REQUEST,))]
        assert len(report['attempts']) <= 1
        report['physical_dispatches'] = sum(a['dispatched'] is not None for a in report['attempts'])
        save(report_path, report)
        print(json.dumps(report), flush=True)


if __name__ == '__main__':
    main()
