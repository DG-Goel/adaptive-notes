"""Read-only characterization of the existing harness using fixture evidence."""
from pathlib import Path
import sys

import httpx
import pytest

HARNESS = Path(__file__).resolve().parents[1] / "t0022_live_stage_a_harness_20261104_074428"
sys.path.insert(0, str(HARNESS))
from test_live_stage_a import admission, KEY
from admission import Admission, Hold, QuotaLedger
from live_stage_a import execute, request_plan


@pytest.fixture(autouse=True)
def block_real_transport(monkeypatch):
    def fail(*args, **kwargs):
        pytest.fail("Network transport must not be constructed")
    monkeypatch.setattr(httpx, "HTTPTransport", fail)


def claim(tmp_path, values):
    record = Admission.model_validate(values)
    QuotaLedger(tmp_path / "quota.sqlite").claim(record, request_plan()[1], 0.85)


@pytest.mark.parametrize("missing", ["all", "RPD", "TPD"])
def test_missing_windows(tmp_path, missing):
    values = admission()
    values["windows"] = [
        w for w in values["windows"] if missing not in ("all", w["metric"])
    ]
    with pytest.raises(Hold, match="Missing or duplicate"):
        claim(tmp_path, values)


def test_duplicate_window(tmp_path):
    values = admission()
    values["windows"].append(dict(values["windows"][0]))
    with pytest.raises(Hold, match="duplicate"):
        claim(tmp_path, values)


@pytest.mark.parametrize("field", ["evidence", "used", "outstanding"])
def test_incomplete_window(tmp_path, field):
    values = admission()
    values["windows"][-1].pop(field)
    with pytest.raises(ValueError, match=field):
        claim(tmp_path, values)


def test_empty_evidence(tmp_path):
    values = admission()
    values["windows"][-1]["evidence"] = ""
    with pytest.raises(ValueError, match="evidence"):
        claim(tmp_path, values)


def test_stale_evidence(tmp_path):
    values = admission()
    values["data_as_of"] -= 16
    with pytest.raises(Hold, match="Stale"):
        claim(tmp_path, values)


def test_wrong_request_hash(tmp_path):
    record = Admission.model_validate(admission(request_sha256="0" * 64))
    with pytest.raises(Hold, match="exact payload"):
        execute(record, KEY, tmp_path)
    assert not list(tmp_path.iterdir())


@pytest.mark.xfail(strict=True, reason="Gate does not require complete applicable project windows")
def test_incomplete_applicable_project_limits(tmp_path):
    values = admission()
    values["windows"].append(dict(values["windows"][2], scope="project"))
    try:
        claim(tmp_path, values)
    except Hold:
        return
    pytest.fail("Project TPM was supplied but RPM, RPD and TPD were omitted")
