"""Gate A entry point. Returns a review checkpoint only."""
import json
from pathlib import Path
import sys

from control import Refused, digest, dispatch_once, encode

ROOT = Path(__file__).resolve().parent.parent
PROTOTYPE = ROOT / "t0022_offline_prototype_20261103_225328"
sys.path.insert(0, str(PROTOTYPE))
from prototype import MockResponse, stage_a

SOURCE = ROOT / "groq_strict_t0022_20261103_8daaab0610db4f2f" / "source_units.json"
SOURCE_SHA256 = "4edcc092ab609aed3809184feeb3dd8485836199ccaad239bb4954d91dadf7aa"
REQUIRED_TOPICS = frozenset({
    "final_pi_error", "division_type_mismatch", "declaration_repair",
    "pi_to_PI", "float_double_alternatives", "increment_1_to_2",
})


def source_units():
    raw = SOURCE.read_bytes()
    if digest(raw) != SOURCE_SHA256:
        raise Refused("Unexpected T0022 source hash")
    units = json.loads(raw)["source_units"]
    if [row["source_id"] for row in units] != ["T0022"]:
        raise Refused("Unexpected source IDs")
    return {"T0022": units[0]["text"]}


def execute_a(ledger, scenario, organization, authorization):
    if not isinstance(authorization, str) or not authorization.strip():
        raise Refused("Explicit offline Stage A authorization required")
    sources = source_units()
    messages = {
        "system": (
            "Return a JSON facts array with fact_id, source_id, claim, quote, scope and optional "
            "relationships with relation and target_id. Cite only T0022 and contiguous exact text. "
            "Keep the final pi error distinct from the division type mismatch and declaration repair. "
            "Preserve explicit pi-to-PI naming, scoped float or double alternatives and increment 1 to 2 "
            "when supported. Omit inference, reconstructed code, decrement behavior and universal claims."
        ),
        "user": "[T0022] " + sources["T0022"],
    }
    reply = dispatch_once(ledger, "A", scenario, organization, messages,
                          {"authorization": authorization, "source_sha256": SOURCE_SHA256})
    try:
        if reply.status_code != 200:
            raise Refused(f"HTTP {reply.status_code}. Attempt stopped.")
        # Mechanical validation only. Approval must separately attest semantic review.
        facts = stage_a(MockResponse(reply.body, reply.finish_reason), sources, lambda _: True, set())
        snapshot = encode({"run": ledger.run_id, "source_sha256": SOURCE_SHA256,
                           "facts": [f.model_dump(mode="json") for f in facts.values()]})
        ledger.artifact("A_facts.json", snapshot)
        ledger.event("A", "awaiting_manual_review", {"artifact_hash": digest(snapshot)})
    except (ValueError, TypeError, KeyError) as exc:
        ledger.event("A", "validation_failed", {"reason": str(exc)})
        raise
    return {"status": "awaiting_manual_review", "publishable_items": ()}
