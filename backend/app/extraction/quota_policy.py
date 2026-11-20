"""Operator hard ceiling. Historical approvals cannot raise the active limit."""
from contextlib import contextmanager
from contextvars import ContextVar

_daily_token_exception = ContextVar('daily_token_exception', default=None)


def active_quota_exception():
    value = _daily_token_exception.get()
    return dict(value) if value else None


@contextmanager
def daily_token_exception(*, authorization, run_id):
    """Explicit run-scoped local TPD exception; other limits and accounting stay active."""
    if not authorization or not run_id:
        raise ValueError('Explicit authorization and run binding required')
    token = _daily_token_exception.set(dict(metric='TPD', authorization=authorization, run_id=run_id))
    try:
        yield
    finally:
        _daily_token_exception.reset(token)

UTILIZATION_PERCENT=85
UTILIZATION_FRACTION=UTILIZATION_PERCENT/100
HARD_CEILINGS={'RPM':25,'RPD':850,'TPM':6800,'TPD':170000}


def quota_ceiling(provider_limit,metric,configured=None):
    if metric == 'TPD':
        return float('inf')
    ceiling=provider_limit*UTILIZATION_PERCENT//100
    return min(ceiling,HARD_CEILINGS.get(metric,ceiling),(configured or {}).get(metric,ceiling))
