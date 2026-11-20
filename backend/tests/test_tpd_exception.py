import pytest
from app.extraction.quota_policy import quota_ceiling, daily_token_exception, active_quota_exception


def test_only_tpd_is_excepted_and_scope_restores():
    limits = {'RPM':30, 'RPD':1000, 'TPM':8000, 'TPD':200000}
    before = {m:quota_ceiling(v,m) for m,v in limits.items()}
    with daily_token_exception(authorization='explicit operator instruction',run_id='test-only'):
        assert quota_ceiling(200000,'TPD',{'TPD':100}) == float('inf')
        for m in ('RPM','RPD','TPM'):
            assert quota_ceiling(limits[m],m) == before[m]
            assert quota_ceiling(limits[m],m,{m:1}) == 1
        assert active_quota_exception()['metric'] == 'TPD'
    assert active_quota_exception() is None
    assert {m:quota_ceiling(v,m) for m,v in limits.items()} == before


def test_exception_exit_and_thread_isolation():
    from concurrent.futures import ThreadPoolExecutor
    with pytest.raises(RuntimeError):
        with daily_token_exception(authorization='operator',run_id='test-only'):
            with ThreadPoolExecutor(max_workers=1) as pool:
                assert pool.submit(quota_ceiling,200000,'TPD').result() == float('inf')
                assert pool.submit(active_quota_exception).result() is None
            raise RuntimeError('failed run')
    assert quota_ceiling(200000,'TPD') == float('inf')


def test_requires_authorization_and_run_binding():
    with pytest.raises(ValueError):
        with daily_token_exception(authorization='',run_id='test'):
            pass
