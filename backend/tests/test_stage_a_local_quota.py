"""Exercise live-path admission offline, without constructing a provider client."""
import time

import pytest

from app.extraction import stage_a_bridge as bridge
from app.extraction.organization_scheduler import LocalQuotaAdmission, QuotaLimit, digest, SchedulerHold
from tests.test_organization_scheduler import make


def setup(tmp_path, monkeypatch, request='r'):
    harness = bridge.frozen_harness()
    monkeypatch.setattr(harness, 'LIVE_STATE', tmp_path / 'stage_a')
    monkeypatch.setattr(bridge, 'frozen_harness', lambda: harness)
    s = make(tmp_path, (1,), max_retries=0)
    identity = s.organizations.identities[0]
    # Synthetic reviewed allocation below the current cap; the historical frozen
    # 1007+4000 allocation is intentionally no longer admissible.
    from app.extraction.token_budget import TokenBudget
    payload={'model':'openai/gpt-oss-120b','messages':[{'role':'user','content':'offline fixture'}],'max_tokens':200}
    budget=TokenBudget(100,200,300,4000,True)
    monkeypatch.setattr(harness,'request_plan',lambda:(payload,budget,None))
    limits = tuple(QuotaLimit(scope='organization', metric=m, limit=n) for m,n in
        dict(RPM=30, RPD=1000, TPM=8000, TPD=200000).items())
    binding = {f: getattr(identity, f) for f in ('organization','project','credential_id','credential_sha256')}
    admission = LocalQuotaAdmission(**binding, request_id=request, request_sha256=digest(payload),
        configuration_sha256=s.config_hash, authorization='offline-fixture', windows=limits)
    record = dict(**binding, decision='PASS', provider='Groq', model='openai/gpt-oss-120b', stage='A',
        source_id='T0022', run_id=request, operator='fixture', authorization='offline-fixture',
        request_sha256=digest(payload), limits=tuple(w.model_dump() for w in limits))
    approval = {k:v for k,v in record.items() if k not in ('decision','source_id','limits')}
    approval.update(evidence_kind='operator_reviewed_console_inventory', ownership_evidence='fixture-only',
        verified_by='fixture', verified_at=time.time()-1, expires_at=time.time()+300,
        authorization_evidence='fixture-only')
    stage = bridge.StageAAuthorization(record, approval)
    s.claim(request, digest(payload), budget.input_tokens, budget.max_output_tokens, {identity.organization:admission})
    return harness, s, identity, admission, payload, budget, stage


def test_no_available_quota_records_needed_and_confirmed_reset(tmp_path, monkeypatch):
    h,s,i,a,p,b,stage = setup(tmp_path, monkeypatch)
    stage.claim(s,i,a,'r',p,b)
    s.record_attempt('r', usage={'prompt_tokens':100, 'completion_tokens':100, 'total_tokens':200})
    s.finish('r', 'success')
    stage.reconcile_local(s,'r')
    with h.QuotaLedger(h.LIVE_STATE/'quota.sqlite').transaction() as db:
        row = db.execute('SELECT * FROM live_a_claims WHERE run_id=?',('r',)).fetchone()
    assert row[4] is not None  # completed: eligible to age out of rolling windows
    assert row[7] == 'confirmed'
    assert row[5:7] == (100,100)
    with pytest.raises(SchedulerHold, match='reservation'):
        stage.claim(s,i,a,'r',p,b)


def test_uncertainty_remains_reserved(tmp_path, monkeypatch):
    h,s,i,a,p,b,stage = setup(tmp_path, monkeypatch)
    stage.claim(s,i,a,'r',p,b)
    s.record_attempt('r', uncertain=True, category='transient_network')
    s.finish('r','uncertain')
    stage.reconcile_local(s,'r')
    with h.QuotaLedger(h.LIVE_STATE/'quota.sqlite').transaction() as db:
        assert db.execute('SELECT completed FROM live_a_claims').fetchone()[0] is None


def test_explicit_nonexpiring_approval_is_accepted(tmp_path, monkeypatch):
    h,s,i,a,p,b,stage = setup(tmp_path, monkeypatch)
    stage.approval['expires_at'] = None
    stage.claim(s,i,a,'r',p,b)


@pytest.mark.parametrize('expiry', [0.0, 'missing'])
def test_expired_or_missing_approval_is_not_infinite(tmp_path, monkeypatch, expiry):
    from pydantic import ValidationError
    h,s,i,a,p,b,stage = setup(tmp_path, monkeypatch)
    if expiry == 'missing':
        del stage.approval['expires_at']
    else:
        stage.approval['expires_at'] = expiry
    with pytest.raises((SchedulerHold, ValidationError)):
        stage.claim(s,i,a,'r',p,b)


@pytest.mark.parametrize('change', ['payload','approval','limits','authorization'])
def test_nonquota_controls_preserved(tmp_path, monkeypatch, change):
    h,s,i,a,p,b,stage = setup(tmp_path, monkeypatch)
    if change == 'payload':
        p = {**p, 'max_tokens':1}
    elif change == 'approval':
        stage.approval['credential_sha256'] = 'b'*64
    elif change == 'limits':
        stage.record['limits'] = tuple({**w, 'limit':w['limit']+1} for w in stage.record['limits'])
    else:
        a = a.model_copy(update={'authorization':'wrong'})
    with pytest.raises((SchedulerHold, h.Hold)):
        stage.claim(s,i,a,'r',p,b)


def test_previous_shared_claim_blocks_85_percent_budget(tmp_path, monkeypatch):
    h,s,i,a,p,b,stage = setup(tmp_path, monkeypatch)
    h.LIVE_STATE.mkdir()
    ledger = h.QuotaLedger(h.LIVE_STATE/'quota.sqlite')
    with ledger.transaction() as db:
        db.execute("INSERT INTO live_a_claims VALUES (?,?,?,?,NULL,?,?,'uncertain',?,?)",
            ('previous',i.organization,i.project,time.time(),6800,0,'b'*64,'fixture'))
    with pytest.raises(SchedulerHold, match='85%'):
        stage.claim(s,i,a,'r',p,b)
