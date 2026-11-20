"""Experimental offline contract exercise. Inputs are recorded mock responses."""
import json
from dataclasses import dataclass
from types import MappingProxyType

from pydantic import BaseModel, ConfigDict, Field

from app.extraction.extractor import KnowledgeExtractor
from app.extraction.llm_provider import MockLLMProvider
from app.extraction.prompts import CATEGORY_FIELDS
from app.models.knowledge import ExtractionChunk


class Link(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    relation: str = Field(min_length=1)
    target_id: str = Field(min_length=1)


class AtomicFact(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    fact_id: str = Field(pattern=r"^f[0-9]{3,}$")
    source_id: str = Field(min_length=1)
    claim: str = Field(min_length=1)
    quote: str = Field(min_length=1)
    scope: str = Field(min_length=1)
    relationships: tuple[Link, ...] = ()


class FactResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    facts: list[AtomicFact]


@dataclass(frozen=True)
class MockResponse:
    body: str
    finish_reason: str = "stop"


@dataclass(frozen=True)
class Outcome:
    status: str
    stage: str
    items: tuple = ()
    error: str = ""


class Incomplete(ValueError):
    pass


def completed(response):
    if response.finish_reason != "stop":
        raise Incomplete(f"Finish reason {response.finish_reason}")
    return response.body


def stage_a(response, sources, review_fact, expected_ids):
    rows = FactResponse.model_validate_json(completed(response)).facts
    facts = {}
    for fact in rows:
        if fact.fact_id in facts:
            raise ValueError("Duplicate fact ID")
        if any(not value.strip() for value in (fact.claim, fact.quote, fact.scope)):
            raise ValueError("Blank fact field")
        if fact.source_id not in sources or fact.quote not in sources[fact.source_id]:
            raise ValueError("Invalid canonical ID or noncontiguous quotation")
        if not review_fact(fact):
            raise ValueError(f"Unapproved atomic claim or scope {fact.fact_id}")
        facts[fact.fact_id] = fact
    for fact in facts.values():
        if any(link.target_id == fact.fact_id or link.target_id not in facts
               for link in fact.relationships):
            raise ValueError("Invalid relationship target")
    if not facts or expected_ids - facts.keys():
        raise Incomplete("Stage A missing expected facts")
    return MappingProxyType(facts)


def reconstruct(refs, facts, sources):
    grouped = {}
    for path, ids in refs.items():
        if (not isinstance(ids, list) or not ids
                or any(not isinstance(fid, str) or fid not in facts for fid in ids)
                or len(ids) != len(set(ids))):
            raise ValueError(f"Invalid fact references at {path}")
        for fid in ids:
            fact = facts[fid]
            if fact.source_id not in sources or fact.quote not in sources[fact.source_id]:
                raise ValueError("Invalid fact provenance")
            grouped.setdefault((fact.source_id, fact.quote), set()).add(path)
    return [{"source_id": sid, "quote": quote, "fields": sorted(paths)}
            for (sid, quote), paths in grouped.items()]


def parser_for(sources, scheduling_id):
    if scheduling_id in sources:
        raise ValueError("Scheduling ID cannot be source provenance")
    parser = KnowledgeExtractor(MockLLMProvider(), strict_evidence=True, verbose=False)
    parser.valid_source_ids = set(sources)
    parser._evidence_sources = dict(sources)
    chunk = ExtractionChunk(chunk_id=scheduling_id, source_units=list(sources),
                            text_content="\n".join(f"[{sid}] {text}" for sid, text in sources.items()))
    return parser, chunk


def field_values(item, paths):
    data = item.model_dump(mode="json")
    for path in paths:
        value = data
        for segment in path[1:].split("/"):
            key = segment.replace("~1", "/").replace("~0", "~")
            value = value[int(key)] if isinstance(value, list) else value[key]
        yield path, value


def stage_b(response, facts, sources, scheduling_id, review_field):
    data = json.loads(completed(response))
    if not isinstance(data, dict) or set(data) != CATEGORY_FIELDS.keys():
        raise ValueError("Expected all eight category arrays")
    parser, chunk = parser_for(sources, scheduling_id)
    pending = []
    covered = set()
    seen = set()
    for category, rows in data.items():
        if not isinstance(rows, list):
            raise ValueError("Expected category array")
        contract = CATEGORY_FIELDS[category]
        allowed = set(contract["required"] + contract["optional"]) | {"content", "evidence_refs"}
        for row in rows:
            if not isinstance(row, dict) or row.keys() - allowed:
                raise ValueError("Invalid item fields")
            refs = row.get("evidence_refs")
            if not isinstance(refs, dict) or not refs:
                raise ValueError("Missing field-level evidence references")
            evidence = reconstruct(refs, facts, sources)
            expanded = {key: value for key, value in row.items() if key != "evidence_refs"}
            expanded["source_evidence"] = evidence
            expanded["source_unit_ids"] = sorted({entry["source_id"] for entry in evidence})
            item, = parser._parse_response(json.dumps({category: [expanded]}), chunk, "JAVA")
            paths = parser._substantive_fields(item)
            if "/content" not in paths or any(
                not review_field(category, path, value, tuple(facts[fid] for fid in refs[path]))
                for path, value in field_values(item, paths)
            ):
                raise ValueError("Unapproved field claim, scope or evidence")
            content = " ".join(item.content.casefold().split())
            if content in seen:
                raise ValueError("Duplicate item content")
            seen.add(content)
            covered.update(refs["/content"])
            pending.append(item)
    if not pending or facts.keys() - covered:
        raise Incomplete("Stage B lost atomic fact coverage")
    return tuple(pending)


def run_offline(sources, scheduling_id, mock_a, mock_b, review_fact, review_field, expected_ids):
    """Call local mocks only. The return value is the sole publication boundary."""
    stage = "A"
    try:
        if scheduling_id in sources:
            raise ValueError("Scheduling ID cannot be source provenance")
        facts = stage_a(mock_a(sources), sources, review_fact, expected_ids)
        stage = "B"
        items = stage_b(mock_b(facts), facts, sources, scheduling_id, review_field)
    except Incomplete as exc:
        return Outcome("incomplete", stage, error=str(exc))
    except (ValueError, TypeError, KeyError) as exc:
        return Outcome("failed", stage, error=str(exc))
    return Outcome("complete", stage, items)
