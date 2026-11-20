import pytest
from app.extraction.quota_policy import quota_ceiling,HARD_CEILINGS
from app.extraction.token_budget import TokenBudgetManager
from app.extraction.organization_scheduler import SchedulerHold
from tests.test_organization_scheduler import make,approvals


@pytest.mark.parametrize('metric,limit,cap',[('RPM',30,25),('RPD',1000,850),('TPM',8000,6800),('ITPM',8000,6800)])
def test_hard_percent(metric,limit,cap):
    assert quota_ceiling(limit,metric)==cap
    assert quota_ceiling(limit,metric,{metric:limit})==cap


def test_old_configuration_cannot_raise_active_ceiling(tmp_path):
    s=make(tmp_path,scheduler_ceilings=(30,1000,8000,200000))
    with pytest.raises(SchedulerHold): s.claim('r','a'*64,2801,4000,approvals(s))


def test_exact_boundary(tmp_path):
    s=make(tmp_path)
    s.claim('r','a'*64,2800,4000,approvals(s))


def test_request_margin_cannot_raise_limit():
    b=TokenBudgetManager(safety_margin=.99)
    assert b.safety_margin==.85
    assert b.calculate_budget('short',system_text='',preferred_output_tokens=3000).tpm_limit==6800
    assert TokenBudgetManager(safety_margin=.4).safety_margin==.4


def test_historical_fixed_stage_a_allocation_fits_current_ceiling():
    from app.extraction.stage_a_bridge import frozen_harness
    h=frozen_harness()
    _,budget,_=h.request_plan()
    assert budget.total_tokens<=6800
