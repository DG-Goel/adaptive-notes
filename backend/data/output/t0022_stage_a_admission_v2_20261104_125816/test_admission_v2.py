from copy import deepcopy
import time

import pytest

from admission import Admission, CredentialApproval, Hold
from test_live_stage_a import admission, block_live_transport, credential_approval, dispatch


def project_record():
    values = admission(project_limits_apply=True)
    values["windows"] += [dict(row, scope="project") for row in values["windows"]]
    values["limits"] += [dict(row, scope="project") for row in values["limits"]]
    return values


@pytest.mark.parametrize("metric", ["RPM", "RPD", "TPD"])
def test_missing_applicable_project_window(tmp_path, metric):
    values = project_record()
    # Even omitting the metric from both declarations cannot bypass completeness.
    for name in ("limits", "windows"):
        values[name] = [row for row in values[name]
                        if (row["scope"], row["metric"]) != ("project", metric)]
    calls, run = dispatch(tmp_path, values)
    with pytest.raises(Hold, match="inventory|daily"):
        run()
    assert not calls


@pytest.mark.parametrize("metric", ["ITPM", "OTPM"])
def test_configured_split_limit_missing(tmp_path, metric):
    values = admission(organization_split_metrics=[metric])
    values["limits"].append(dict(scope="organization", metric=metric, limit=8000))
    calls, run = dispatch(tmp_path, values)
    with pytest.raises(Hold, match="inventory|daily"):
        run()
    assert not calls


@pytest.mark.parametrize("field", ["limits", "project_limits_apply", "organization_split_metrics",
                                   "inventory_evidence", "complete_limit_inventory"])
def test_missing_inventory_declaration(field):
    values = admission()
    del values[field]
    with pytest.raises(ValueError, match=field):
        Admission.model_validate(values)


@pytest.mark.parametrize("kind", ["mismatched_ceiling", "duplicate_limit", "project_above_org",
                                   "unexpected_project", "duplicate_usage", "duplicate_split"])
def test_inconsistent_inventory(tmp_path, kind):
    values = project_record()
    if kind == "mismatched_ceiling":
        values["windows"][0]["limit"] -= 1
    elif kind == "duplicate_limit":
        values["limits"].append(deepcopy(values["limits"][0]))
    elif kind == "project_above_org":
        values["limits"][4]["limit"] += 1
        values["windows"][4]["limit"] += 1
    elif kind == "unexpected_project":
        values["project_limits_apply"] = False
    elif kind == "duplicate_usage":
        values["windows"].append(deepcopy(values["windows"][0]))
    else:
        values["organization_split_metrics"] = ["ITPM", "ITPM"]
    calls, run = dispatch(tmp_path, values)
    with pytest.raises(Hold, match="contradict|inventory|Duplicate"):
        run()
    assert not calls


@pytest.mark.parametrize("offset", [-16, 30])
def test_row_timestamp_is_checked_independently(tmp_path, offset):
    values = admission()
    values["windows"][-1]["data_as_of"] += offset
    calls, run = dispatch(tmp_path, values)
    with pytest.raises(Hold, match="quota row"):
        run()
    assert not calls


@pytest.mark.parametrize("field,value", [("evidence", " \t"), ("data_as_of", None)])
def test_missing_or_blank_row_evidence(field, value):
    values = admission()
    if value is None:
        del values["windows"][-1][field]
    else:
        values["windows"][-1][field] = value
    with pytest.raises(ValueError, match=field):
        Admission.model_validate(values)


@pytest.mark.parametrize("field,value", [
    ("credential_id", "another-key"), ("credential_sha256", "0"*64),
    ("organization", "another-org"), ("project", "another-project"),
    ("operator", "another-operator"), ("authorization", "unrelated authorization"),
    ("run_id", "another-run"), ("request_sha256", "0"*64),
    ("expires_at", 1),
])
def test_independent_approval_binding(tmp_path, field, value):
    values = admission()
    approval = credential_approval(Admission.model_validate(values), **{field: value})
    calls, run = dispatch(tmp_path, values, approval=approval)
    with pytest.raises(Hold, match="binding|inventory|expired"):
        run()
    assert not calls and not list(tmp_path.iterdir())


@pytest.mark.parametrize("field", ["authorization_evidence", "ownership_evidence", "verified_by"])
def test_blank_approval_evidence(field):
    approved = credential_approval(Admission.model_validate(admission())).model_dump()
    approved[field] = " \t"
    with pytest.raises(ValueError, match=field):
        CredentialApproval.model_validate(approved)


def test_complete_project_and_split_inventory_passes_offline(tmp_path):
    values = project_record()
    values["organization_split_metrics"] = ["ITPM", "OTPM"]
    for metric in ("ITPM", "OTPM"):
        row = dict(scope="organization", metric=metric, limit=8000)
        values["limits"].append(row)
        values["windows"].append(dict(row, used=0, outstanding=0,
                                     data_as_of=values["data_as_of"], evidence="fixture"))
    calls, run = dispatch(tmp_path, values)
    assert run()["status"] == "awaiting_manual_review"
    assert len(calls) == 1
