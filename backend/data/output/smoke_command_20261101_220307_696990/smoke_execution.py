"""One-request real Groq smoke test; no recovery or retries."""
import json
import logging
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from hashlib import sha256

sys.path.insert(0, str(Path.cwd().resolve()))

import httpx
import groq
from dotenv import load_dotenv
from app.extraction.llm_provider import GroqProvider
from app.extraction.extractor import KnowledgeExtractor
from app.extraction.knowledge_merge import validate_provenance
from app.models.source import SourceDocument
from app.models.knowledge import KnowledgeDocument
from recover_t0018_exhaustive import fingerprint

root = Path.cwd().resolve()
assert Path(sys.prefix).resolve() == root / ".venv", "Wrong virtual environment"
logging.disable(logging.CRITICAL)
load_dotenv(root / ".env", override=False)
model = "openai/gpt-oss-120b"
if os.getenv("GROQ_MODEL") != model:
    raise SystemExit("Configured GROQ_MODEL does not match the required model")
keys = [os.getenv(f"GROQ_API_KEY_{index}") for index in range(1, 6)]
keys = [value for value in keys if value] or [os.getenv("GROQ_API_KEY")]
assert keys and keys[0], "No configured Groq credential"
source_path = root / "data/output/complete_e2e_validation/validation_20261101_174430/source_units.json"
source_bytes = source_path.read_bytes()
full_source = SourceDocument.model_validate_json(source_bytes)
unit = next(unit for unit in full_source.source_units if unit.source_id == "T0022")
source = full_source.model_copy(deep=True)
source.source_units = [unit.model_copy(deep=True)]
stamp = datetime.now(timezone(timedelta(hours=5, minutes=30))).strftime("%Y%m%d_%H%M%S_%f")
out = root / "data/output" / ("groq_real_smoke_" + stamp)
out.mkdir(exist_ok=False)
def save(name, value):
    with (out / name).open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False)
save("source_units.json", source.model_dump(mode="json"))
save("request_metadata.json", {
    "provider": "Groq", "model": model, "source_id": unit.source_id,
    "input_characters": len(unit.text or ""), "input_words": len((unit.text or "").split()),
    "credential_selection": "one configured credential; no rotation",
    "provider_retries": 0, "sdk_retries": 0, "extractor_retries": 0,
    "split_depth": 0, "python_executable": sys.executable, "python_version": sys.version,
    "groq_sdk_version": groq.__version__, "source_artifact_sha256": sha256(source_bytes).hexdigest(),
})
provider = GroqProvider(model=model, api_key=keys[0], use_multi_key=False, max_retries=1)
network = {"requests": 0, "status_codes": []}
def requested(request):
    network["requests"] += 1
def responded(response):
    network["status_codes"].append(response.status_code)
client = httpx.Client(event_hooks={"request": [requested], "response": [responded]})
provider.client = provider.client.with_options(max_retries=0, timeout=90.0, http_client=client)
original_extract = provider._extract_response_content
captured = {}
def capture(response):
    captured["content"] = response.choices[0].message.content
    return original_extract(response)
provider._extract_response_content = capture
extractor = KnowledgeExtractor(provider, verbose=False, max_retries=0, max_split_depth=0)
def failed_response(response, chunk_id, error_msg):
    save("failed_response_diagnostic.json", {
        "chunk_id": chunk_id, "error": provider._sanitize_error(error_msg),
        "response_saved_separately": False,
    })
extractor._save_failed_response = failed_response
result = None
unexpected = None
try:
    result = extractor.extract(source)
except Exception as error:
    unexpected = {"type": type(error).__name__, "message": provider._sanitize_error(str(error))}
finally:
    client.close()
raw = captured.get("content")
secrets = keys + [value for name, value in os.environ.items()
                  if any(word in name.upper() for word in ("API_KEY", "TOKEN", "SECRET", "PASSWORD")) and value]
safe_raw = isinstance(raw, str) and not any(secret in raw for secret in secrets if len(secret) >= 8)
raw_saved = False
if safe_raw:
    with (out / "response_content.json.txt").open("x", encoding="utf-8") as stream:
        stream.write(raw)
    raw_saved = True
parsed = False
if raw is not None:
    try:
        json.loads(raw)
        parsed = True
    except (ValueError, TypeError):
        pass
provenance = validate_provenance(result, full_source) if result else None
schema_valid = False
if result:
    result = KnowledgeDocument.model_validate_json(result.model_dump_json())
    schema_valid = True
    save("knowledge.json", result.model_dump(mode="json"))
metadata = getattr(provider, "last_response_metadata", {})
technical = (
    network["requests"] == 1 and network["status_codes"] == [200]
    and metadata.get("model") == model and metadata.get("finish_reason") == "stop"
    and parsed and schema_valid and provenance and provenance.valid
    and result.total_items > 0 and result.extraction_metadata.get("extraction_successful") is True
)
report = {
    "provider": "Groq", "model": model, "real_request": True,
    "status": "PENDING_MANUAL_REVIEW" if technical else "FAILED",
    "timestamp": stamp, "command": ".\\.venv\\Scripts\\python.exe -B " + str(Path(sys.argv[0]).resolve()),
    "source_id": unit.source_id, "source_fingerprint": fingerprint(full_source.model_dump(mode="json")),
    "response_metadata": metadata, "network": network, "json_valid": parsed,
    "schema_valid": schema_valid, "provenance": provenance.model_dump() if provenance else None,
    "extracted_items": result.total_items if result else 0,
    "knowledge": result.model_dump(mode="json") if result else None,
    "error": getattr(provider, "last_error_metadata", None) or unexpected,
    "raw_content_saved": raw_saved, "release": "NO-GO",
    "manual_review": {"approved": False, "reason": "Awaiting inspection of every item"},
}
save("technical_validation.json", report)
assert source_path.read_bytes() == source_bytes
print(json.dumps({"artifact_directory": str(out), "status": report["status"],
                  "network": network, "response_metadata": metadata,
                  "items": report["extracted_items"], "error": report["error"]}, ensure_ascii=True))
