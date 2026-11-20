import pytest
from tests.test_organization_scheduler import make,approvals
from app.extraction.organization_scheduler import SchedulerHold


def test_pre_dispatch_failure_closes_but_preserves_charge(tmp_path):
    s=make(tmp_path); s.claim('r','a'*64,100,200,approvals(s)); s.finish('r','validation_failed')
    with s.transaction() as db: row=db.execute('select * from attempts').fetchone()
    assert row['completed'] is not None and row['category']=='not_dispatched'
    assert row['charged']==300 and row['input_reserved']==100 and row['output_reserved']==200


def test_legacy_reconciliation_is_guarded_and_preserves_charge(tmp_path):
    s=make(tmp_path); s.claim('r','a'*64,100,200,approvals(s)); s.finish('r','validation_failed')
    with s.transaction() as db: db.execute('update attempts set completed=NULL,category=NULL,input_actual=NULL,output_actual=NULL')
    s.close_undispatched('r','fixture: authorization failed before dispatch')
    with s.transaction() as db: row=db.execute('select * from attempts').fetchone()
    assert row['charged']==300 and row['dispatched'] is None
    with pytest.raises(SchedulerHold): s.close_undispatched('r','no double reconciliation')


def test_dispatched_uncertainty_cannot_be_reconciled(tmp_path):
    s=make(tmp_path); i,a=s.claim('r','a'*64,100,200,approvals(s)); s.check_dispatch('r',i,a)
    s.record_attempt('r',uncertain=True,category='transient_network'); s.finish('r','uncertain')
    with pytest.raises(SchedulerHold): s.close_undispatched('r','must refuse')
    with s.transaction() as db: row=db.execute('select * from attempts').fetchone()
    assert row['completed'] is None and row['charged']==300
