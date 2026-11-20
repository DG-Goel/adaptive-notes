"""Guarded live Stage A entry point. Import and --show-request are offline."""
import argparse
from dataclasses import dataclass
import json
import os
from pathlib import Path
import sys
import time

import httpx

from admission import Admission, CredentialApproval, Hold, QuotaLedger, fresh, verify_credential

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
from app.extraction.token_budget import TokenBudgetManager
sys.path.insert(0, str(HERE.parent / "t0022_safety_infrastructure_20261104_003405"))
from control import Ledger, encode, digest
from stage_a import SOURCE_SHA256, source_units
from prototype import stage_a

MODEL = "openai/gpt-oss-120b"
URL = "https://api.groq.com/openai/v1/chat/completions"
MESSAGE_HASH = "a45de9f9dafbc5e768d18d71ec579f038b9611f9cfd33c0b167cf9c9c9d2dba7"
# Retain the original shared reservation database across harness versions.
LIVE_STATE = HERE.parent / "t0022_live_stage_a_harness_20261104_074428" / "runs"
CREDENTIAL_APPROVAL = HERE / "credential_approval.json"
PREFLIGHT = HERE.parent / "t0022_stage_a_preflight_20261104_073749" / "PREFLIGHT.md"


@dataclass(frozen=True)
class Completion:
    body: str
    finish_reason: str


def request_plan():
    text = PREFLIGHT.read_text(encoding="utf-8")
    config = json.loads(text.split("```json\n", 1)[1].split("\n```", 1)[0])
    sources = source_units()
    messages = config["messages"]
    if (config["provider"], config["model"], config["source_id"]) != ("Groq", MODEL, "T0022"):
        raise Hold("Provider, model or canonical source mismatch")
    if config["max_tokens_planned"] != 4000:
        raise Hold("Output cap differs from reviewed configuration")
    if (digest(encode(messages)) != MESSAGE_HASH or
            messages["user"] != "[T0022] " + sources["T0022"]):
        raise Hold("Reviewed message or source mismatch")
    budget = TokenBudgetManager().calculate_budget(messages["user"], system_text=messages["system"])
    if not budget.is_safe or (budget.input_tokens, budget.max_output_tokens) != (1007, 4000):
        raise Hold("Reviewed allocation changed")
    payload = {
        "model": MODEL,
        "messages": [{"role": role, "content": messages[role]} for role in ("system", "user")],
        "temperature": 0,
        "max_completion_tokens": 4000,
        "response_format": {"type": "json_object"},
        "stream": False,
        "service_tier": "on_demand",
    }
    return payload, budget, sources


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key")
        result[key] = value
    return result


def reject_constant(value):
    raise ValueError("Non-JSON numeric constant")


def execute(record, api_key, state_root, margin=0.85, *, approval, transport=None):
    record = Admission.model_validate(record.model_dump())
    payload, budget, sources = request_plan()
    request_hash = digest(encode(payload))
    if record.request_sha256 != request_hash:
        raise Hold("Authorization does not match the exact payload")
    verify_credential(record, approval, api_key, time.time())
    admission = record.model_dump(exclude={"credential_sha256"})
    artifact = encode({
        "record": admission,
        "credential_approval": approval.model_dump(exclude={"credential_sha256"}),
        "token_margin": margin,
    })
    if api_key.encode() in artifact:
        raise Hold("Admission metadata contains credential material")
    state_root = Path(state_root)
    run_dir = state_root / record.run_id
    if run_dir.exists():
        raise Hold("Run artifact directory already exists")
    state_root.mkdir(parents=True, exist_ok=True)
    quota = QuotaLedger(state_root / "quota.sqlite")
    quota.claim(record, budget, margin)
    run_dir.mkdir()
    ledger = Ledger(run_dir, record.run_id)
    ledger.claim("A", {"authorization": record.authorization, "request_sha256": request_hash})
    ledger.artifact("A_request.json", encode(payload))
    ledger.artifact("A_admission.json", artifact)
    # A dedicated synchronous client sends only the fixed URL. The CLI never injects transport.
    with httpx.Client(transport=transport or httpx.HTTPTransport(retries=0, trust_env=False),
                      timeout=90, trust_env=False, follow_redirects=False) as client:
        fresh(record, time.time())
        verify_credential(record, approval, api_key, time.time())
        quota.mark(record.run_id, "dispatch_attempt")
        ledger.event("A", "dispatch_attempt", {"url": URL})
        try:
            response = client.post(URL, json=payload, headers={"Authorization": f"Bearer {api_key}"})
        except httpx.HTTPError as exc:
            quota.mark(record.run_id, "uncertain")
            ledger.event("A", "uncertain_outcome", {"error_type": type(exc).__name__})
            raise Hold("Dispatch uncertain. Claim remains consumed.") from None
    usage = {}
    try:
        raw = response.content
        if api_key.encode() in raw:
            raise Hold("Response contained credential material")
        ledger.artifact("A_response.json", raw)
        request_id = response.headers.get("x-request-id") or response.headers.get("x-groq-request-id")
        if request_id and api_key in request_id:
            request_id = None
        ledger.event("A", "confirmed_response", {"status_code": response.status_code,
                                                "request_id": request_id})
        if response.status_code != 200:
            raise Hold(f"HTTP {response.status_code}. Attempt stopped.")
        envelope = json.loads(raw, object_pairs_hook=unique_object, parse_constant=reject_constant)
        usage = envelope.get("usage") or {}
        if not isinstance(usage, dict):
            usage = {}
            raise Hold("Invalid response usage")
        choices = envelope["choices"]
        if envelope["model"] != MODEL or not isinstance(choices, list) or len(choices) != 1:
            raise Hold("Unexpected response model or choice count")
        choice = choices[0]
        content = choice["message"]["content"]
        json.loads(content, object_pairs_hook=unique_object, parse_constant=reject_constant)
        facts = stage_a(Completion(content, choice["finish_reason"]), sources, lambda _: True, set())
        snapshot = encode({"run": record.run_id, "source_sha256": SOURCE_SHA256,
                           "facts": [fact.model_dump(mode="json") for fact in facts.values()]})
        ledger.artifact("A_facts.json", snapshot)
        ledger.event("A", "awaiting_manual_review", {"artifact_hash": digest(snapshot)})
    except (ValueError, TypeError, KeyError, AttributeError) as exc:
        ledger.event("A", "validation_failed", {"error_type": type(exc).__name__})
        if isinstance(exc, Hold):
            raise
        raise Hold("Response incomplete or invalid. Review the preserved artifacts.") from None
    finally:
        quota.mark(record.run_id, "response_received", completed=True, usage=usage)
    return {"status": "awaiting_manual_review", "checkpoint": str(run_dir / "A_facts.json"),
            "sha256": digest(snapshot), "publishable_items": 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--show-request", action="store_true")
    action.add_argument("--execute-live", action="store_true")
    parser.add_argument("--admission", type=Path)
    parser.add_argument("--token-margin", type=float, default=0.85)
    args = parser.parse_args()
    try:
        if args.show_request:
            payload, budget, _ = request_plan()
            print(json.dumps({"payload": payload, "sha256": digest(encode(payload)),
                              "estimated_allocation": budget.total_tokens}, indent=2))
            return 0
        if args.admission is None:
            raise Hold("Fresh explicit admission record required")
        record = Admission.model_validate_json(args.admission.read_bytes())
        approval = CredentialApproval.model_validate_json(CREDENTIAL_APPROVAL.read_bytes())
        result = execute(record, os.environ.get("GROQ_STAGE_A_API_KEY"), LIVE_STATE,
                         args.token_margin, approval=approval)
        print(json.dumps(result, indent=2))
        return 0
    except (ValueError, OSError) as exc:
        print("HOLD:", str(exc) if isinstance(exc, Hold) else type(exc).__name__, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
