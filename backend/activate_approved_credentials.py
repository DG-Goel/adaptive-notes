"""Record current operator approval and activate existing slots. No network calls."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import re
import time

from dotenv import dotenv_values
from app.extraction.organization_scheduler import Identity, load_organizations


def main():
    root = Path(__file__).resolve().parent
    inventory_path = root / 'data/output/organization_inventory_20261106/inventory.json'
    env_path = root / '.env'
    rows = json.loads(inventory_path.read_text(encoding='utf-8'))
    before = json.loads(json.dumps(rows))
    env = dotenv_values(env_path)
    now = datetime.now(timezone.utc)
    evidence = ('Current chat: user explicitly approved the first credential setup issue '
                'for all five existing slots. Local key fingerprints checked. '
                'No new console or live model-access verification was performed.')
    fields = ('slot','organization','project','credential_id','credential_sha256',
              'verified_by','ownership_evidence','verified_at','expires_at')
    for row in rows:
        prefix = f"GROQ_ORG_{row['slot']}_"
        key = env.get(prefix + 'API_KEY')
        if not key or sha256(key.encode()).hexdigest() != row['credential_sha256']:
            raise ValueError('Stored key fingerprint does not match inventory')
        if env.get(prefix + 'ID') != row['organization']:
            raise ValueError('Configured organization differs from inventory')
        row.update(verified_at=now.timestamp(), expires_at=None, enabled=True,
                   verified_by='requesting operator; explicit current-chat approval',
                   current_operator_confirmation_reviewed_at=now.isoformat(),
                   current_operator_confirmation_evidence=evidence,
                   verification_validity_status='operator-approved until explicitly revoked; provider expiry unknown',
                   review_window_policy='no expiration; explicitly requested by operator in current chat',
                   live_credential_acceptance='not_tested')
    identities = [Identity(**{k:r[k] for k in fields}) for r in rows]
    original = env_path.read_bytes()
    updated = original
    for row in rows:
        name = f"GROQ_ORG_{row['slot']}_ENABLED"
        pattern = rb'(?m)^' + name.encode() + rb'=[^\r\n]*'
        updated, count = re.subn(pattern, name.encode() + b'=true', updated)
        if count != 1:
            raise ValueError('Missing or duplicate enabled flag')
    proposed = dict(env)
    proposed.update({f"GROQ_ORG_{r['slot']}_ENABLED": 'true' for r in rows})
    registry = load_organizations(identities, proposed)
    assert registry.enabled == (1,2,3,4,5)
    assert all(i.valid_at(time.time()) and i.expires_at is None for i in identities)
    out = root / 'data/output' / ('credential_activation_' + now.strftime('%Y%m%d_%H%M%S_%f'))
    out.mkdir()
    (out/'inventory_before.json').write_text(json.dumps(before,indent=2),encoding='utf-8')
    (out/'identity_records.json').write_text(json.dumps([i.model_dump() for i in identities],indent=2),encoding='utf-8')
    inventory_path.write_text(json.dumps(rows,indent=2),encoding='utf-8')
    env_path.write_bytes(updated)
    actual = load_organizations(identities, dotenv_values(env_path))
    assert actual.enabled == registry.enabled
    # Check every .env line other than the five enabled flags remains byte-identical.
    def without_flags(data):
        return re.sub(rb'(?m)^GROQ_ORG_[1-5]_ENABLED=[^\r\n]*',b'<enabled flag>',data)
    assert without_flags(original) == without_flags(env_path.read_bytes())
    report = {'status':'credential_identity_setup_completed', 'enabled_slots':list(actual.enabled),
        'reviewed_at':now.isoformat(),'review_valid_until':None,
        'validity_meaning':'operator approval remains valid until explicitly revoked; provider expiry unknown',
        'key_fingerprints_match':True,'organization_mappings_unchanged':True,
        'key_material_unchanged':True,'live_calls':0,
        'request_bound_stage_a_approval':'not_created; Java payload authorization remains separate',
        'live_constraint':'The live bridge requires selection of one organization; enabling five is not approval for cross-organization live rotation.',
        'evidence':evidence}
    (out/'activation_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({'output':str(out),**report},indent=2))


if __name__ == '__main__':
    main()
