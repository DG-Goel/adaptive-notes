"""Local total-limit accounting; all credentials and approvals are fixtures."""
import json
import time

import pytest

from app.extraction.organization_scheduler import LocalQuotaAdmission, QuotaLimit, SchedulerHold
from app.extraction.stage_a_bridge import StageAAuthorization
from tests.test_organization_scheduler import make


def local(scheduler, request='r', limits=None):
    identity = scheduler.organizations.identities[0]
    return LocalQuotaAdmission(**{f: getattr(identity, f) for f in
        ('organization', 'project', 'credential_id', 'credential_sha256')},
        request_id=request, request_sha256='a' * 64,
        configuration_sha256=scheduler.config_hash, authorization='offline-fixture-only',
        windows=tuple(QuotaLimit(scope='organization', metric=m, limit=n) for m, n in
            (limits or dict(RPM=30, RPD=1000, TPM=8000, TPD=200000)).items()))


def claim(s, request='r', inp=2800, out=4000, **kwargs):
    a = local(s, request, **kwargs)
    return s.claim(request, 'a' * 64, inp, out, {a.organization: a})


def test_local_boundary_reservations_and_reset(tmp_path, monkeypatch):
    clock = [time.time()]
    monkeypatch.setattr('app.extraction.organization_scheduler.time.time', lambda: clock[0])
    s = make(tmp_path, (1,))
    identity, admission = claim(s)
    assert s.status({identity.organization: local(s, 'next')}, 1, 1)['slots'][0]['quota_state'] == 'quota_exhausted'
    s.check_dispatch('r', identity, admission)
    s.record_attempt('r', usage={'prompt_tokens': 2800, 'completion_tokens': 4000, 'total_tokens': 6800})
    s.finish('r', 'success')
    with pytest.raises(SchedulerHold):
        claim(s, 'next', 1, 1)
    clock[0] += 61
    claim(s, 'next', 1, 1)


@pytest.mark.parametrize('limits,inp,out', [
    (dict(RPM=30, RPD=1000, TPM=8000, TPD=200000), 2801, 4000),
    (dict(RPM=30, RPD=1000, TPM=1000, TPD=200000), 451, 400),
    (dict(RPM=10000, RPD=10000, TPM=100000, TPD=1000000), 2801, 4000),
])
def test_stricter_total_or_configured_ceiling(tmp_path, limits, inp, out):
    with pytest.raises(SchedulerHold):
        claim(make(tmp_path, (1,)), inp=inp, out=out, limits=limits)


def test_missing_limits_and_request_binding(tmp_path):
    s = make(tmp_path, (1,))
    a = local(s)
    for invalid in (a.model_copy(update={'windows': a.windows[:-1]}),
                    a.model_copy(update={'request_sha256': 'b' * 64})):
        with pytest.raises(SchedulerHold):
            s.claim('r', 'a' * 64, 1, 1, {invalid.organization: invalid})


def test_uncertain_usage_survives_reset_and_restart(tmp_path, monkeypatch):
    clock = [time.time()]
    monkeypatch.setattr('app.extraction.organization_scheduler.time.time', lambda: clock[0])
    s = make(tmp_path, (1,))
    claim(s)
    s.record_attempt('r', uncertain=True, category='transient_network')
    s.finish('r', 'uncertain')
    clock[0] += 86401
    with pytest.raises(SchedulerHold):
        claim(make(tmp_path, (1,)), 'next', 1, 1)


def test_audit_does_not_claim_verified_external_capacity(tmp_path):
    s = make(tmp_path, (1,))
    claim(s)
    with s.transaction() as db:
        event = json.loads(db.execute("SELECT details FROM audit_events WHERE event='claimed'").fetchone()[0])
    assert event['quota_before'] == 'local_tracked'
    assert 'used' not in local(s).windows[0].model_dump()


def test_local_mode_still_requires_stage_a_authorization(tmp_path):
    from pydantic import ValidationError
    s = make(tmp_path, (1,))
    with pytest.raises(ValidationError):
        StageAAuthorization({}, {}).claim(s, s.organizations.identities[0], local(s), 'r', {}, None)


def test_identity_without_expiry_and_explicit_disable(tmp_path):
    from app.extraction.organization_scheduler import Organizations, OrganizationScheduler, load_organizations
    from tests.test_organization_scheduler import registry
    from pydantic import ValidationError
    r = registry((1,))
    identities = [i.model_copy(update={'expires_at':None}) for i in r.identities]
    s = OrganizationScheduler(tmp_path/'infinite.sqlite',
        Organizations(identities, {1:'test-secret-1'}, (1,)))
    claim(s, inp=100, out=200)
    assert s.status()['slots'][0]['identity_verified'] is True
    assert identities[0].valid_at(41024448000.0)
    assert not identities[0].model_copy(update={'verified_at':100.0}).valid_at(99.0)
    data = identities[0].model_dump()
    del data['expires_at']
    with pytest.raises(ValidationError):
        type(identities[0])(**data)
    with pytest.raises(SchedulerHold, match='enabled'):
        load_organizations(identities, {})
