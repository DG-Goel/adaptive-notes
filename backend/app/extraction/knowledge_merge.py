"""Auditable knowledge-ID normalization and explicitly reviewed recovery merging.

Pure operations: callers own file I/O, evidence review, and downstream regeneration.
No extraction, provider calls, semantic inference, or historical artifact mutation.
"""
from collections import Counter
from hashlib import sha256
import json
import re
from typing import Literal

from pydantic import BaseModel, Field

from app.models.knowledge import KnowledgeDocument
from app.models.source import SourceDocument

CATEGORIES = (
    "concepts", "definitions", "explanations", "examples",
    "facts", "formulas", "procedures", "relationships",
)
PREFIXES = dict(zip(CATEGORIES, ("CON", "DEF", "EXP", "EXM", "FCT", "FRM", "PRC", "REL")))


def _canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def _digest(value):
    return sha256(_canonical(value).encode("utf-8")).hexdigest()


def _payload(item):
    return item.model_dump(mode="json", exclude={"knowledge_id"})


def _entries(document):
    for category in CATEGORIES:
        for index, item in enumerate(getattr(document, category)):
            yield category, index, item


class IdMapping(BaseModel):
    artifact_id: str
    category: str
    item_index: int
    old_id: str
    new_id: str
    content_fingerprint: str
    reason: Literal["preserved", "collision_reassigned", "recovery_added", "exact_duplicate"]


class ProvenanceValidationReport(BaseModel):
    valid: bool
    items_checked: int
    errors: list[str] = Field(default_factory=list)


class PreservationComparison(BaseModel):
    passed: bool
    before_count: int
    after_count: int
    before_unique_ids: int
    after_unique_ids: int
    reassigned_count: int
    duplicate_occurrences: int
    document_metadata_unchanged: bool
    before_non_id_digest: str
    after_non_id_digest: str
    item_comparisons: list[dict] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class MergeDecision(BaseModel):
    category: str
    item_index: int
    action: Literal["include", "consolidate", "exclude", "pending"]
    reason: str = Field(min_length=1)
    target_id: str | None = None


class KnowledgeMergeResult(BaseModel):
    document: KnowledgeDocument
    mappings: list[IdMapping]
    decisions: list[MergeDecision] = Field(default_factory=list)
    preservation: PreservationComparison | None = None
    provenance: ProvenanceValidationReport | None = None


def validate_provenance(knowledge_doc, source_doc, *, required_source_id=None):
    """Check reference integrity, never semantic support."""
    errors = []
    source_ids = [unit.source_id for unit in source_doc.source_units]
    duplicate_sources = {sid for sid, count in Counter(source_ids).items() if count > 1}
    if duplicate_sources:
        errors.append("Ambiguous source IDs: " + ", ".join(sorted(duplicate_sources)))
    if knowledge_doc.document_id != source_doc.document_id:
        errors.append("Knowledge/source document ID mismatch")
    if knowledge_doc.source_filename != source_doc.filename:
        errors.append("Knowledge/source filename mismatch")
    if any(unit.document_id != source_doc.document_id for unit in source_doc.source_units):
        errors.append("Source unit document ID mismatch")
    if required_source_id is not None and required_source_id not in source_ids:
        errors.append("Required source ID is absent")
    valid_ids = set(source_ids) - duplicate_sources
    entries = list(_entries(knowledge_doc))
    for category, index, item in entries:
        label = f"{category}[{index}]"
        if item.document_id != source_doc.document_id:
            errors.append(f"{label}: document ID mismatch")
        if not item.source_unit_ids:
            errors.append(f"{label}: empty source references")
        if any(sid not in valid_ids for sid in item.source_unit_ids):
            errors.append(f"{label}: invalid or ambiguous source references")
        if required_source_id is not None and required_source_id not in item.source_unit_ids:
            errors.append(f"{label}: missing canonical {required_source_id} reference")
    return ProvenanceValidationReport(valid=not errors, items_checked=len(entries), errors=errors)


def _allocator(document):
    reserved = {item.knowledge_id for _, _, item in _entries(document)}
    suffixes = []
    for category, _, item in _entries(document):
        match = re.fullmatch(r"([A-Z]+)_(\d+)", item.knowledge_id)
        if not match or match.group(1) != PREFIXES[category]:
            raise ValueError(f"Invalid knowledge ID/type prefix: {item.knowledge_id}")
        suffixes.append(int(match.group(2)))
    next_number = max(suffixes, default=0) + 1

    def allocate(category):
        nonlocal next_number
        while True:
            candidate = f"{PREFIXES[category]}_{next_number:04d}"
            next_number += 1
            if candidate not in reserved:
                reserved.add(candidate)
                return candidate
    return allocate


def compare_preservation(before, after, mappings):
    """Independently compare all fields, allowing only mapped duplicate-ID changes."""
    old_entries, new_entries = list(_entries(before)), list(_entries(after))
    old_ids = [item.knowledge_id for _, _, item in old_entries]
    new_ids = [item.knowledge_id for _, _, item in new_entries]
    duplicates = len(old_ids) - len(set(old_ids))
    errors, comparisons, seen = [], [], set()
    changed = 0
    metadata_before = before.model_dump(mode="json", exclude=set(CATEGORIES))
    metadata_after = after.model_dump(mode="json", exclude=set(CATEGORIES))
    metadata_equal = metadata_before == metadata_after
    if not metadata_equal:
        errors.append("Document metadata changed")
    if len(old_entries) != len(new_entries):
        errors.append("Item count changed")
    if len(new_ids) != len(set(new_ids)):
        errors.append("Output knowledge IDs are not unique")
    mapping_lookup = {}
    for mapping in mappings:
        key = (mapping.category, mapping.item_index)
        if key in mapping_lookup:
            errors.append("Duplicate mapping locator")
        mapping_lookup[key] = mapping
    expected_keys = {(category, index) for category, index, _ in old_entries}
    if set(mapping_lookup) != expected_keys:
        errors.append("Mapping locators do not cover exactly the input items")
    for old_entry, new_entry in zip(old_entries, new_entries):
        category, index, old = old_entry
        new_category, new_index, new = new_entry
        same_payload = _payload(old) == _payload(new)
        id_changed = old.knowledge_id != new.knowledge_id
        is_duplicate = old.knowledge_id in seen
        seen.add(old.knowledge_id)
        mapping = mapping_lookup.get((category, index))
        valid_mapping = (
            mapping is not None
            and mapping.old_id == old.knowledge_id
            and mapping.new_id == new.knowledge_id
            and mapping.content_fingerprint == _digest(_payload(old))
            and mapping.reason == ("collision_reassigned" if is_duplicate else "preserved")
        )
        passed = (
            category == new_category and index == new_index and same_payload
            and id_changed == is_duplicate and valid_mapping
            and re.fullmatch(PREFIXES[category] + r"_\d+", new.knowledge_id) is not None
        )
        changed += int(id_changed)
        if not passed:
            errors.append(f"{category}[{index}]: preservation or mapping failure")
        comparisons.append({
            "category": category, "item_index": index,
            "old_id": old.knowledge_id, "new_id": new.knowledge_id,
            "before_non_id_digest": _digest(_payload(old)),
            "after_non_id_digest": _digest(_payload(new)),
            "non_id_fields_equal": same_payload, "passed": passed,
        })
    if changed != duplicates:
        errors.append("Reassigned count does not equal duplicate occurrences")
    return PreservationComparison(
        passed=not errors, before_count=len(old_entries), after_count=len(new_entries),
        before_unique_ids=len(set(old_ids)), after_unique_ids=len(set(new_ids)),
        reassigned_count=changed, duplicate_occurrences=duplicates,
        document_metadata_unchanged=metadata_equal,
        before_non_id_digest=_digest([_payload(item) for _, _, item in old_entries]),
        after_non_id_digest=_digest([_payload(item) for _, _, item in new_entries]),
        item_comparisons=comparisons, errors=errors,
    )


def normalize_knowledge_ids(knowledge_doc: KnowledgeDocument, *, artifact_id: str):
    """Preserve every item; reassign only second/later occurrences of existing IDs."""
    if not artifact_id:
        raise ValueError("artifact_id is required")
    original = knowledge_doc.model_dump(mode="json")
    document = knowledge_doc.model_copy(deep=True)
    allocate = _allocator(document)
    seen, mappings = set(), []
    for category, index, item in _entries(document):
        old_id = item.knowledge_id
        collision = old_id in seen
        seen.add(old_id)
        if collision:
            item.knowledge_id = allocate(category)
        mappings.append(IdMapping(
            artifact_id=artifact_id, category=category, item_index=index,
            old_id=old_id, new_id=item.knowledge_id,
            content_fingerprint=_digest(_payload(item)),
            reason="collision_reassigned" if collision else "preserved",
        ))
    preservation = compare_preservation(knowledge_doc, document, mappings)
    if knowledge_doc.model_dump(mode="json") != original:
        raise ValueError("Normalization mutated its input")
    if not preservation.passed:
        raise ValueError("Preservation failed: " + "; ".join(preservation.errors))
    return KnowledgeMergeResult(document=document, mappings=mappings, preservation=preservation)


def resolve_knowledge_reference(mappings, *, artifact_id, old_id, category=None, item_index=None):
    candidates = [
        mapping for mapping in mappings
        if mapping.artifact_id == artifact_id and mapping.old_id == old_id
        and (category is None or mapping.category == category)
        and (item_index is None or mapping.item_index == item_index)
    ]
    if len(candidates) != 1:
        raise ValueError("Missing or ambiguous knowledge reference; provide an item locator")
    return candidates[0].new_id


def merge_recovered_knowledge(
    base_doc, recovered_doc, source_doc, *, artifact_id, decisions, required_source_id=None,
):
    """Apply exhaustive, explicit review decisions; never infer semantic duplicates."""
    if not artifact_id:
        raise ValueError("artifact_id is required")
    base_report = validate_provenance(base_doc, source_doc)
    if not base_report.valid:
        raise ValueError("Invalid base provenance: " + "; ".join(base_report.errors))
    if len({item.knowledge_id for _, _, item in _entries(base_doc)}) != len(base_doc.get_all_items()):
        raise ValueError("Normalize base IDs before merging")
    if (recovered_doc.document_id, recovered_doc.source_filename) != (
        source_doc.document_id, source_doc.filename,
    ):
        raise ValueError("Recovery document provenance mismatch")
    candidates = list(_entries(recovered_doc))
    expected = {(category, index) for category, index, _ in candidates}
    decision_map = {(decision.category, decision.item_index): decision for decision in decisions}
    if len(decision_map) != len(decisions) or set(decision_map) != expected:
        raise ValueError("Exactly one review decision is required for every recovery item")
    document = base_doc.model_copy(deep=True)
    allocate = _allocator(document)
    mappings = []
    for category, index, item in candidates:
        decision = decision_map[(category, index)]
        if decision.action in {"exclude", "pending"}:
            if decision.target_id is not None:
                raise ValueError("Excluded/pending items cannot have a target ID")
            continue
        single = recovered_doc.model_copy(deep=True)
        for name in CATEGORIES:
            setattr(single, name, [item.model_copy(deep=True)] if name == category else [])
        report = validate_provenance(single, source_doc, required_source_id=required_source_id)
        if not report.valid:
            raise ValueError("Invalid accepted recovery provenance: " + "; ".join(report.errors))
        if decision.action == "include":
            if decision.target_id is not None:
                raise ValueError("Included items cannot specify a consolidation target")
            copied = item.model_copy(deep=True)
            copied.knowledge_id = allocate(category)
            getattr(document, category).append(copied)
            new_id = copied.knowledge_id
            reason = "recovery_added"
        else:
            targets = [target for target in getattr(document, category)
                       if target.knowledge_id == decision.target_id]
            if len(targets) != 1:
                raise ValueError("Consolidation target must identify one item of the same type")
            target = targets[0]
            expected_payload = _payload(item)
            actual_payload = _payload(target)
            expected_payload.pop("source_unit_ids")
            actual_payload.pop("source_unit_ids")
            if expected_payload != actual_payload:
                raise ValueError("Consolidation requires exact non-ID, non-source equality")
            target.source_unit_ids = list(dict.fromkeys(target.source_unit_ids + item.source_unit_ids))
            new_id, reason = target.knowledge_id, "exact_duplicate"
        mappings.append(IdMapping(
            artifact_id=artifact_id, category=category, item_index=index,
            old_id=item.knowledge_id, new_id=new_id,
            content_fingerprint=_digest(_payload(item)), reason=reason,
        ))
    document.update_statistics()
    provenance = validate_provenance(document, source_doc)
    if not provenance.valid:
        raise ValueError("Merged provenance validation failed")
    return KnowledgeMergeResult(
        document=document, mappings=mappings,
        decisions=[decision.model_copy(deep=True) for decision in decisions],
        provenance=provenance,
    )
