"""Controlled recovery using the existing extractor; no network calls at import time."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys

from app.extraction.extractor import KnowledgeExtractor
from app.extraction.knowledge_merge import (
    CATEGORIES, MergeDecision, merge_recovered_knowledge, normalize_knowledge_ids,
    validate_provenance,
)
from app.extraction.llm_provider import GroqProvider
from app.models.knowledge import KnowledgeDocument
from app.models.source import SourceDocument

MODEL = "openai/gpt-oss-120b"
ACTIONS = {"INCLUDE": "include", "EXACT_DUPLICATE": "consolidate",
           "EXCLUDE_WITH_JUSTIFICATION": "exclude", "PENDING_REVIEW": "pending"}


def fingerprint(value):
    return sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save(directory, name, value):
    with (directory / name).open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False)


def entries(document):
    for category in CATEGORIES:
        for index, item in enumerate(getattr(document, category)):
            yield category, index, item


def review_items(document, source, base, review=None, *, canonical_id):
    """Every item is accounted for. Source membership is not semantic approval."""
    provenance = validate_provenance(document, source, required_source_id=canonical_id)
    if not provenance.valid:
        raise ValueError("Invalid recovery provenance: " + "; ".join(provenance.errors))
    items = list(entries(document))
    if document.total_items != len(items):
        raise ValueError("Recovery total_items disagrees with item count")
    review = review or {"items": []}
    supplied = review.get("items", [])
    indexed = {(row["category"], row["item_index"]): row for row in supplied}
    expected = {(category, index) for category, index, _ in items}
    if supplied and (len(indexed) != len(supplied) or set(indexed) != expected):
        raise ValueError("Review must account for every item exactly once")
    sources = {unit.source_id: unit.text or "" for unit in source.source_units}
    decisions, rows = [], []
    for category, index, item in items:
        payload = item.model_dump(mode="json")
        key = (category, index)
        row = indexed.get(key, {
            "disposition": "PENDING_REVIEW", "reason": "Source support not yet reviewed",
        })
        action = row["disposition"]
        if action not in ACTIONS:
            raise ValueError("Unknown item disposition")
        if supplied and row.get("item_fingerprint") != fingerprint(payload):
            raise ValueError("Stale item review fingerprint")
        evidence = row.get("source_evidence", [])
        for quote in evidence:
            if quote["source_id"] not in item.source_unit_ids:
                raise ValueError("Review cites evidence outside item provenance")
            if not quote["quote"] or quote["quote"] not in sources[quote["source_id"]]:
                raise ValueError("Review evidence is not an exact source passage")
        if action in {"INCLUDE", "EXACT_DUPLICATE"}:
            if not evidence or not row.get("reviewer") or not row.get("full_item_reviewed"):
                raise ValueError("Accepted items require full-item manual review and source evidence")
        identical = []
        candidate = {k: v for k, v in payload.items() if k not in {"knowledge_id", "source_unit_ids"}}
        for _, _, existing in entries(base):
            other = existing.model_dump(mode="json", exclude={"knowledge_id", "source_unit_ids"})
            if candidate == other:
                identical.append(existing.knowledge_id)
        if action == "INCLUDE" and identical:
            raise ValueError("Exact duplicate requires an explicit consolidation decision")
        decisions.append(MergeDecision(
            category=category, item_index=index, action=ACTIONS[action],
            reason=row["reason"], target_id=row.get("target_id"),
        ))
        rows.append({
            **row, "category": category, "item_index": index, "old_id": item.knowledge_id,
            "item_fingerprint": fingerprint(payload), "original_item": payload,
            "exact_duplicate_targets": identical,
        })
    return decisions, {"canonical_source_id": canonical_id, "items_checked": len(items),
                       "provenance": provenance.model_dump(), "items": rows}


def require_smoke(path, source):
    """Validate supplied real-call evidence; never infer success from historical percentages."""
    if path is None:
        raise ValueError("BLOCKED: real Groq smoke-test evidence is required before extraction")
    return validate_smoke(load(path), source)


def validate_smoke(report, source):
    metadata = report.get("response_metadata", {})
    if (report.get("provider") != "Groq" or report.get("model") != MODEL
            or metadata.get("model") != MODEL or report.get("real_request") is not True
            or report.get("status") != "PASSED" or metadata.get("finish_reason") != "stop"):
        raise ValueError("BLOCKED: smoke provider/model/status/finish reason is not acceptable")
    if report.get("source_fingerprint") != fingerprint(source.model_dump(mode="json")):
        raise ValueError("BLOCKED: smoke evidence does not match these source units")
    usage = metadata.get("usage", {})
    if any(type(usage.get(key)) is not int or usage[key] < 0
           for key in ("prompt_tokens", "completion_tokens", "total_tokens")):
        raise ValueError("BLOCKED: smoke token usage missing")
    if not report.get("command") or not report.get("timestamp"):
        raise ValueError("BLOCKED: smoke execution evidence missing")
    knowledge = KnowledgeDocument.model_validate(report["knowledge"])
    if not knowledge.get_all_items() or not validate_provenance(knowledge, source).valid:
        raise ValueError("BLOCKED: smoke knowledge/schema/provenance invalid")
    manual = report.get("manual_review", {})
    if not (manual.get("approved") is True and manual.get("reviewer") and manual.get("reason")):
        raise ValueError("BLOCKED: smoke extraction quality has not been manually approved")
    return report


def segments_for(unit, manifest=None):
    """Use the whole source by default; optional boundaries require an explicit source review."""
    text = unit.text or ""
    if not manifest:
        return [{"start": 0, "end": len(text), "text": text, "reason": "Whole canonical source"}]
    if (manifest.get("source_fingerprint") != fingerprint(unit.model_dump(mode="json"))
            or manifest.get("reviewed") is not True or not manifest.get("reviewer")):
        raise ValueError("Segmentation requires review bound to the canonical source")
    segments, position = [], 0
    for row in manifest.get("segments", []):
        start, end = row["start"], row["end"]
        if type(start) is not int or type(end) is not int or start != position or not start < end <= len(text):
            raise ValueError("Segment boundaries must cover source contiguously without overlap")
        if not row.get("reason") or not row.get("context_preserved"):
            raise ValueError("Sentence/example context review is required")
        if start and text[start - 1:start].isalnum() and text[start:start + 1].isalnum():
            raise ValueError("Cannot split within a word")
        if end < len(text) and text[end - 1:end].isalnum() and text[end:end + 1].isalnum():
            raise ValueError("Cannot split within a word")
        segments.append({**row, "text": text[start:end]})
        position = end
    if not segments or position != len(text):
        raise ValueError("Segmentation omits source content")
    return segments


def extract_t0018(source, provider, *, smoke_evidence, manifest=None):
    """Each segment uses SourceDocument -> existing chunker/extractor/accounting."""
    validate_smoke(smoke_evidence, source)
    if type(provider) is not GroqProvider or provider.model != MODEL:
        raise ValueError("Recovery requires Groq and exactly " + MODEL)
    unit = next(unit for unit in source.source_units if unit.source_id == "T0018")
    records, documents = [], []
    for index, segment in enumerate(segments_for(unit, manifest)):
        view = source.model_copy(deep=True)
        view.source_units = [unit.model_copy(update={"text": segment["text"]}, deep=True)]
        extractor = KnowledgeExtractor(provider, verbose=False, max_retries=2)
        try:
            result = extractor.extract(view)
        except Exception as error:
            # Never lose already completed segments or print unsanitized provider exceptions.
            records.append({"segment_index": index, **segment, "outcome": "FAILED",
                            "error_type": type(error).__name__})
            for remaining_index, remaining in enumerate(segments_for(unit, manifest)[index + 1:], index + 1):
                records.append({"segment_index": remaining_index, **remaining,
                                "outcome": "NOT_ATTEMPTED", "reason": "Extraction could not complete"})
            break
        report = validate_provenance(result, source, required_source_id="T0018")
        accounting = result.extraction_metadata
        resolved = (accounting.get("extraction_successful") is True
                    and accounting.get("scheduled_roots", 0) > 0
                    and accounting.get("failed_roots", 1) == 0
                    and accounting.get("skipped_roots", 1) == 0
                    and bool(result.get_all_items()) and report.valid)
        records.append({
            "segment_index": index, **segment, "outcome": "SUCCESS" if resolved else "FAILED",
            "accounting": accounting, "provenance": report.model_dump(),
            "knowledge": result.model_dump(mode="json"),
        })
        documents.append(result)
        # A permanent failure ends dependent API work; retain prior partial results.
        error = getattr(provider, "last_error_metadata", None)
        if isinstance(error, dict) and error.get("retryable") is False and not resolved:
            for remaining_index, remaining in enumerate(segments_for(unit, manifest)[index + 1:], index + 1):
                records.append({"segment_index": remaining_index, **remaining,
                                "outcome": "NOT_ATTEMPTED", "reason": "Permanent provider failure"})
            break
    candidate = KnowledgeDocument(
        document_id=source.document_id, source_filename=source.filename,
        extraction_timestamp=documents[0].extraction_timestamp if documents else "",
    )
    for document in documents:
        for category in CATEGORIES:
            getattr(candidate, category).extend(getattr(document, category))
    candidate.update_statistics()
    normalized = normalize_knowledge_ids(candidate, artifact_id="T0018-segments")
    candidate = normalized.document
    candidate.extraction_metadata = {
        "segment_id_mappings": [row.model_dump() for row in normalized.mappings],
        "segment_outcomes": [{"segment_index": row["segment_index"], "outcome": row["outcome"]}
                             for row in records],
    }
    return candidate, records



def validate_candidate(candidate, records, source):
    """Bind replayed segment evidence to canonical text and the final candidate items."""
    unit = next(unit for unit in source.source_units if unit.source_id == "T0018")
    position, recovered = 0, {category: [] for category in CATEGORIES}
    for index, record in enumerate(records):
        start, end = record.get("start"), record.get("end")
        if (record.get("segment_index") != index or start != position
                or type(end) is not int or not start < end <= len(unit.text or "")
                or record.get("text") != unit.text[start:end]):
            raise ValueError("Candidate segment evidence does not preserve canonical source")
        position = end
        if "knowledge" in record:
            document = KnowledgeDocument.model_validate(record["knowledge"])
            provenance = validate_provenance(document, source, required_source_id="T0018")
            accounting = record.get("accounting", {})
            if record["outcome"] == "SUCCESS" and not (
                    provenance.valid and document.get_all_items()
                    and accounting.get("extraction_successful") is True
                    and accounting.get("failed_roots") == 0
                    and accounting.get("skipped_roots") == 0
                    and accounting.get("scheduled_roots", 0) > 0):
                raise ValueError("Candidate success lacks valid extraction evidence")
            for category in CATEGORIES:
                recovered[category].extend(
                    item.model_dump(mode="json", exclude={"knowledge_id"})
                    for item in getattr(document, category))
        elif record["outcome"] == "SUCCESS":
            raise ValueError("Successful segment has no extracted knowledge")
    if not records or position != len(unit.text or ""):
        raise ValueError("Candidate segment evidence omits source content")
    for category in CATEGORIES:
        actual = [item.model_dump(mode="json", exclude={"knowledge_id"})
                  for item in getattr(candidate, category)]
        if actual != recovered[category]:
            raise ValueError("Candidate items differ from preserved segment results")
    if len({item.knowledge_id for item in candidate.get_all_items()}) != len(candidate.get_all_items()):
        raise ValueError("Candidate knowledge IDs collide")


def finalize_status(candidate, records, review_report, topic_review, source):
    """Manual source/topic review is mandatory even after all API segments succeed."""
    if not candidate.get_all_items():
        return "FAILED"
    if not records or any(row["outcome"] != "SUCCESS" for row in records):
        return "PARTIAL"
    reviewed = review_report["items"]
    expected_items = {fingerprint(item.model_dump(mode="json")) for _, _, item in entries(candidate)}
    if len(reviewed) != len(candidate.get_all_items()) or {row.get("item_fingerprint") for row in reviewed} != expected_items:
        return "PENDING_REVIEW"
    if any(row["disposition"] == "PENDING_REVIEW" for row in reviewed):
        return "PENDING_REVIEW"
    if not any(row["disposition"] in {"INCLUDE", "EXACT_DUPLICATE"} for row in review_report["items"]):
        return "FAILED"
    if not topic_review:
        return "PENDING_REVIEW"
    expected = fingerprint({"candidate": candidate.model_dump(mode="json"),
                            "source": source.model_dump(mode="json")})
    if (topic_review.get("review_fingerprint") != expected or not topic_review.get("reviewer")
            or topic_review.get("complete") is not True or topic_review.get("unresolved_gaps") != []
            or not topic_review.get("topics") or topic_review.get("source_reviewed_in_full") is not True):
        return "PENDING_REVIEW"
    sources = {unit.source_id: unit.text or "" for unit in source.source_units}
    accepted = {row["old_id"] for row in review_report["items"]
                if row["disposition"] in {"INCLUDE", "EXACT_DUPLICATE"}}
    for topic in topic_review["topics"]:
        if (not topic.get("reason") or not topic.get("knowledge_ids")
                or not set(topic["knowledge_ids"]) <= accepted
                or topic.get("source_id") != "T0018" or not topic.get("source_quote")
                or topic["source_quote"] not in sources[topic["source_id"]]):
            return "PENDING_REVIEW"
    return "RECOVERED"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for flag in ("sources", "base", "t0017", "output"):
        parser.add_argument("--" + flag, type=Path, required=True)
    parser.add_argument("--model", default=MODEL, choices=[MODEL])
    parser.add_argument("--provider", default="Groq", choices=["Groq"])
    parser.add_argument("--t0017-review", type=Path)
    parser.add_argument("--execute-t0018", action="store_true")
    parser.add_argument("--smoke-report", type=Path)
    parser.add_argument("--boundaries", type=Path)
    parser.add_argument("--candidate", type=Path)
    parser.add_argument("--t0018-review", type=Path)
    parser.add_argument("--topic-review", type=Path)
    args = parser.parse_args(argv)
    if args.execute_t0018 and args.candidate:
        parser.error("--execute-t0018 and --candidate are mutually exclusive")
    if args.output.exists():
        raise ValueError("Refusing to overwrite existing output directory")
    source = SourceDocument.model_validate(load(args.sources))
    if len([unit for unit in source.source_units if unit.source_id == "T0018"]) != 1:
        raise ValueError("Expected one canonical T0018 source")
    base = KnowledgeDocument.model_validate(load(args.base))
    t17 = KnowledgeDocument.model_validate(load(args.t0017))
    normalized = normalize_knowledge_ids(base, artifact_id=str(args.base.resolve()))
    decisions, review17 = review_items(
        t17, source, normalized.document,
        load(args.t0017_review) if args.t0017_review else None, canonical_id="T0017",
    )
    merged = merge_recovered_knowledge(
        normalized.document, t17, source, artifact_id=str(args.t0017.resolve()),
        decisions=decisions, required_source_id="T0017",
    )
    # Gate before provider construction, credential loading, or any extraction request.
    smoke = require_smoke(args.smoke_report, source) if args.execute_t0018 else None
    args.output.mkdir(parents=True, exist_ok=False)
    save(args.output, "base_preservation.json", normalized.preservation.model_dump())
    save(args.output, "base_id_mappings.json", [row.model_dump() for row in normalized.mappings])
    save(args.output, "t0017_review.json", review17)
    save(args.output, "t0017_merge.json", merged.model_dump(mode="json"))
    report = {"release": "NO-GO", "t0017_status": "REVIEWED_PARTIAL_MERGE",
              "t0018_status": "NOT_EXECUTED", "provider": "Groq", "model": MODEL,
              "input_sha256": {str(path.resolve()): sha256(path.read_bytes()).hexdigest()
                               for path in (args.sources, args.base, args.t0017)}}
    if args.execute_t0018:
        from dotenv import load_dotenv
        load_dotenv(Path(__file__).parent / ".env", override=False)
        provider = GroqProvider(model=MODEL)
        candidate, records = extract_t0018(
            source, provider, smoke_evidence=smoke, manifest=load(args.boundaries) if args.boundaries else None,
        )
        envelope = {"source_fingerprint": fingerprint(source.model_dump(mode="json")),
                    "smoke_evidence": smoke, "knowledge": candidate.model_dump(mode="json"),
                    "segments": records}
        save(args.output, "recovery_candidate.json", envelope)
    elif args.candidate:
        envelope = load(args.candidate)
        if envelope["source_fingerprint"] != fingerprint(source.model_dump(mode="json")):
            raise ValueError("Candidate source mismatch")
        # Persisted candidates must retain the same validated real smoke evidence.
        smoke_path = args.output / "candidate_smoke_evidence.json"
        save(args.output, smoke_path.name, envelope["smoke_evidence"])
        require_smoke(smoke_path, source)
        candidate = KnowledgeDocument.model_validate(envelope["knowledge"])
        records = envelope["segments"]
    else:
        save(args.output, "recovery_report.json", report)
        return 2  # Offline inspection/partial merging is not completed recovery.
    validate_candidate(candidate, records, source)
    decisions18, review18 = review_items(
        candidate, source, merged.document,
        load(args.t0018_review) if args.t0018_review else None, canonical_id="T0018",
    )
    merged18 = merge_recovered_knowledge(
        merged.document, candidate, source, artifact_id="T0018-candidate",
        decisions=decisions18, required_source_id="T0018",
    )
    report["t0018_status"] = finalize_status(
        candidate, records, review18, load(args.topic_review) if args.topic_review else None, source,
    )
    report["segments"] = records
    save(args.output, "t0018_review.json", review18)
    save(args.output, "merged_knowledge.json", merged18.document.model_dump(mode="json"))
    save(args.output, "recovery_id_mappings.json", [row.model_dump() for row in merged18.mappings])
    save(args.output, "recovery_report.json", report)
    return 0 if report["t0018_status"] == "RECOVERED" else 2


if __name__ == "__main__":
    sys.exit(main())
