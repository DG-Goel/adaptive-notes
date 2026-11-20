from run_full_multimodal_categories import must_stop


def test_quota_hold_stops_even_when_every_primary_was_attempted():
    assert must_stop({'errors':[{'error':'quota_exhausted: recovery child blocked'}]}, {'r1'},{'r1'})


def test_429_and_unattempted_work_stop():
    assert must_stop({'http_429':1},set(),set())
    assert must_stop({}, {'r1','r2'},{'r1'})


def test_completed_primary_work_with_validation_failures_is_independent():
    assert not must_stop({'errors':[{'error':'Invalid evidence reference'}]}, {'r1'},{'r1'})
