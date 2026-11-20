"""Materialize the user's approved Java request inventory without network calls."""
import json
from pathlib import Path
from datetime import datetime, timezone
from app.extraction.document_authorization import document_plan, DocumentStageARecord
from app.extraction.stage_a_bridge import LocalCredentialApproval
from app.extraction.organization_scheduler import ExtractionConfiguration, digest, configuration_fingerprint


def main(split_depth=0, rotate_five=False):
    root = Path(__file__).resolve().parent
    stamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S_%f')
    run = 'java-' + stamp
    config = ExtractionConfiguration(max_retries=0,prompt_policy="canonical_grounded_v4",response_format="json_schema",reasoning_effort="low",preferred_output_tokens=3000)
    manifest = document_plan(root.parent/'java.txt', config, run,split_depth,'reserve_preferred_v1')
    inventory = json.loads((root/'data/output/organization_inventory_20261106/inventory.json').read_text())
    from app.extraction.document_authorization import request_slots
    selected=[1,2,3,4,5] if rotate_five else [1]
    assignments=request_slots(manifest,selected)
    authorization = 'Current chat: approved complete real java.txt testing and explicitly requested rotating the five friends separately owned credentials when --rotate-five is selected; explicitly reaffirmed 85 percent of configured total quota with existing ledger accounting, without external available-capacity verification.'
    records=[]
    for entry in manifest['requests']:
        identity=next(r for r in inventory if r['slot']==assignments[entry['request_id']])
        common={k:identity[k] for k in ('organization','project','credential_id','credential_sha256')}
        common.update(provider='Groq',model=config.model,stage='A',operator='requesting operator',
            authorization=authorization,run_id=entry['request_id'],request_sha256=entry['request_sha256'])
        record=DocumentStageARecord(**common,decision='PASS',source_id='DOCUMENT',limits=tuple(
            dict(scope='organization',metric=m,limit=n) for m,n in identity['configured_provider_limits'].items()))
        approval=LocalCredentialApproval(**common,evidence_kind=identity['verification_method'],
            ownership_evidence=identity['ownership_evidence'],verified_by=identity['verified_by'],
            verified_at=identity['verified_at'],expires_at=identity['expires_at'],authorization_evidence=authorization)
        records.append(dict(request_id=entry['request_id'],record=record.model_dump(mode='json'),
            credential_approval=approval.model_dump(mode='json')))
    out=root/'data/output'/('java_authorization_'+stamp)
    out.mkdir()
    for name,value in [('manifest.json',manifest),('approvals.json',records),('authorization.json',dict(
            approved_manifest_sha256=digest(manifest),authorization=authorization,selected_slot=1,
            selected_slots=selected,request_slots=assignments,
            quota_policy='85_percent_configured_totals_local_shared_ledger',
            configuration_review={'target_sha256':configuration_fingerprint(config),'evidence':'Current chat: full test using current canonical_grounded_v4 production policy; low reasoning, full 3000-token output reserve, schema-inclusive budgeting. Explicit correction: do not require external available-capacity evidence. Preserve all earlier ledger usage and reservations.'},
            source_sha256=manifest['source_sha256'],request_count=len(records),live_calls=0))]:
        (out/name).write_text(json.dumps(value,indent=2),encoding='utf-8')
    roots=sum(not e.get('parent_request_id') for e in manifest['requests'])
    print(json.dumps(dict(output=str(out),initial_requests=roots,contingent_recovery_requests=len(records)-roots,requests=len(records),live_calls=0)))


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('--split-depth',type=int,default=0,choices=(0,1,2))
    parser.add_argument('--rotate-five',action='store_true')
    args=parser.parse_args()
    main(args.split_depth,args.rotate_five)
