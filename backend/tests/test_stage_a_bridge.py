import pytest

from app.extraction.stage_a_bridge import frozen_harness, StageAAuthorization


def test_bridge_loads_actual_frozen_checks():
    harness = frozen_harness()
    assert harness.verify_credential.__module__ == "admission"
    payload, budget, sources = harness.request_plan()
    assert payload and budget and sources


def test_bridge_rejects_missing_genuine_records_before_claim():
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        StageAAuthorization({}, {}).claim(None, None, None, "unapproved", {}, None)
