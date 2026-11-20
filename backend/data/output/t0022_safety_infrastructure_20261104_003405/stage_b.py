"""Separate Gate B entry point and explicit human approval record."""
import json
import time

from control import Refused, digest, dispatch_once, encode
from stage_a import REQUIRED_TOPICS, SOURCE_SHA256, source_units
from prototype import MockResponse, stage_a, stage_b
from app.extraction.prompts import CATEGORY_FIELDS


def checkpoint(ledger):
    try:
        raw = (ledger.directory / "A_facts.json").read_bytes()
    except FileNotFoundError as exc:
        raise Refused("Stage A checkpoint missing") from exc
    events = dict(ledger.events("A"))
    if ("validation_failed" in events or
            events.get("awaiting_manual_review", {}).get("artifact_hash") != digest(raw)):
        raise Refused("Stage A checkpoint incomplete or modified")
    payload = json.loads(raw)
    if payload["run"] != ledger.run_id or payload["source_sha256"] != SOURCE_SHA256:
        raise Refused("Checkpoint run or source mismatch")
    return raw, payload


def approve_b(ledger, reviewer, artifact_hash, reviewed_fact_ids, coverage):
    """Explicit operator attestation that every claim and scope was reviewed."""
    raw, payload = checkpoint(ledger)
    ids = {fact["fact_id"] for fact in payload["facts"]}
    if not reviewer.strip() or artifact_hash != digest(raw) or set(reviewed_fact_ids) != ids:
        raise Refused("Reviewer, artifact hash or review coverage mismatch")
    if set(coverage) != REQUIRED_TOPICS or any(fid not in ids for fid in coverage.values()):
        raise Refused("Required T0022 teaching facts not attested")
    if coverage["final_pi_error"] == coverage["division_type_mismatch"]:
        raise Refused("Distinct compiler errors require distinct facts")
    with ledger.connect() as db:
        db.execute("INSERT INTO approvals VALUES (?, 'B', ?, ?, ?, ?)",
                   (ledger.run_id, reviewer, artifact_hash, time.time(),
                    encode({"reviewed_fact_ids": sorted(ids), "coverage": coverage}).decode()))


def execute_b(ledger, scenario, organization, review_field):
    with ledger.connect() as db:
        approval = db.execute(
            "SELECT reviewer,artifact_hash,approved_at FROM approvals WHERE run=? AND stage='B'",
            (ledger.run_id,)).fetchone()
    if approval is None:
        raise Refused("Separate Stage B approval required")
    raw, payload = checkpoint(ledger)
    if digest(raw) != approval[1]:
        raise Refused("Stage A artifact hash differs from approval")
    sources = source_units()
    facts = stage_a(MockResponse(encode({"facts": payload["facts"]}).decode()),
                    sources, lambda _: True, set())
    # Use the verified bytes already read. Never reread an unverified prompt input.
    reply = dispatch_once(ledger, "B", scenario, organization, {
        "system": (
            "Structure only the reviewed facts into the eight category arrays. Every populated "
            "field needs evidence_refs mapping its JSON Pointer to supporting fact IDs. Preserve "
            "scope, distinct compiler errors and explicit naming correction. Category contracts: "
            + encode(CATEGORY_FIELDS).decode()
        ),
        "user": encode({"facts": payload["facts"]}).decode(),
    }, {"reviewer": approval[0], "artifact_hash": approval[1], "approved_at": approval[2]})
    try:
        if reply.status_code != 200:
            raise Refused(f"HTTP {reply.status_code}. Attempt stopped.")
        items = stage_b(MockResponse(reply.body, reply.finish_reason), facts, sources,
                        "JAVA_CHUNK_000", review_field)
        ledger.artifact("B_review_result.json", encode([item.model_dump(mode="json") for item in items]))
        ledger.event("B", "isolated_result", {"items": len(items)})
    except (ValueError, TypeError, KeyError) as exc:
        ledger.event("B", "validation_failed", {"reason": str(exc)})
        raise
    return {"status": "isolated_result", "items": items, "publishable_items": ()}
