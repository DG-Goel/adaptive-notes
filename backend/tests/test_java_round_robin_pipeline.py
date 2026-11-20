"""Offline integration using the unmodified project transcript and mock HTTP."""
import json
import time
from pathlib import Path

import httpx

from tests.test_organization_scheduler import make, approvals
from tests.test_organization_extraction import envelope
from app.ingestion.transcript_parser import parse_transcript
from app.extraction.chunker import ContentChunker
from app.extraction.organization_extraction import extract_chunk, prepare_request
from app.extraction.organization_scheduler import digest
from app.models.knowledge import KnowledgeDocument
from app.analysis.analyzer import ContentAnalyzer
from app.representation.selector import RepresentationSelector
from app.assembly.assembler import NoteAssembler
from app.rendering.renderer import MarkdownRenderer


def test_actual_java_round_robin_pipeline(tmp_path, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Live transport forbidden")
    monkeypatch.setattr(httpx, "HTTPTransport", forbidden)
    path = Path(__file__).resolve().parents[2] / "java.txt"
    document = parse_transcript(path, min_segment_words=50, max_segment_words=500, detect_timestamps=True)
    chunks = ContentChunker().chunk(document.source_units, document.document_id)
    scheduler = make(tmp_path)
    clock = [time.time()]
    monkeypatch.setattr("app.extraction.organization_scheduler.time.time", lambda: clock[0])
    sources = {unit.source_id: unit for unit in document.source_units}
    items, assignments, responses = [], [], []
    for index, chunk in enumerate(chunks):
        if index and index % 5 == 0:
            clock[0] += 61
        request_id = f"java-{index:04d}"
        payload, budget = prepare_request(chunk, scheduler.configuration)
        def respond(request):
            assert json.loads(request.content) == payload
            expected_slot = index % 5 + 1
            assert request.headers["authorization"] == f"Bearer test-secret-{expected_slot}"
            concepts = []
            for source_id in chunk.source_units:
                text = sources[source_id].text
                concepts.append({"concept_name": text.split()[0], "content": text,
                    "source_unit_ids": [source_id], "source_evidence": [
                        {"source_id": source_id, "quote": text, "fields": ["/concept_name", "/content"]}]})
            reply = envelope(json.dumps({"concepts": concepts}))
            reply["usage"] = {"prompt_tokens": budget.input_tokens,
                              "completion_tokens": budget.max_output_tokens,
                              "total_tokens": budget.total_tokens}
            responses.append(reply)
            return httpx.Response(200, json=reply)
        extracted = extract_chunk(scheduler, request_id, chunk, document.source_units,
            document.document_id, approvals(scheduler, request_id, digest(payload)),
            transport=httpx.MockTransport(respond))
        for item in extracted:
            item.knowledge_id = f"K{len(items):05d}"
            items.append(item)
        assignments.append({"chunk_index": index, "chunk_id": chunk.chunk_id,
            "credential": f"NOTES {index % 5 + 1}", "source_ids": chunk.source_units,
            "mock_reserved_tokens": budget.total_tokens})
    assert [sid for chunk in chunks for sid in chunk.source_units] == [u.source_id for u in document.source_units]
    assert [sid for item in items for sid in item.source_unit_ids] == [u.source_id for u in document.source_units]
    knowledge = KnowledgeDocument(document_id=document.document_id, source_filename=document.filename,
        extraction_timestamp="offline-simulated", concepts=items, source_units_processed=len(sources))
    knowledge.update_statistics()
    KnowledgeDocument.model_validate(knowledge.model_dump())
    analyzed = ContentAnalyzer().analyze(knowledge)
    represented = RepresentationSelector().select(analyzed)
    assembled = NoteAssembler().assemble(represented)
    rendered = MarkdownRenderer().render(assembled)
    assert [entry.source_unit_ids[0] for entry in rendered.manifest.items] == list(sources)
    def save(name, value):
        (tmp_path / name).write_text(json.dumps(value, indent=2, default=str), encoding="utf-8")
    save("source_document.json", document.model_dump())
    save("chunks.json", [chunk.model_dump() for chunk in chunks])
    save("assignments.json", assignments)
    save("mock_responses.json", responses)
    save("knowledge.json", knowledge.model_dump())
    save("assembled.json", assembled.model_dump())
    save("render_manifest.json", rendered.manifest.model_dump())
    save("scheduler_status.json", scheduler.status())
    (tmp_path / "notes.md").write_text(rendered.content, encoding="utf-8")
    save("summary.json", {"input": str(path), "chunks": len(chunks), "source_units": len(sources),
        "items": len(items), "mock_calls": len(responses), "live_calls": 0, "live_tokens": 0,
        "note": "Mock responses quote source units verbatim. Semantic extraction quality is unevaluated."})
