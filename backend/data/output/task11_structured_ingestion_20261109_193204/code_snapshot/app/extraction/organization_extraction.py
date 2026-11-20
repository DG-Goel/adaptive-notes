"""Opt-in chunk operation; deliberately not installed in production or Stage A/B.

Reuses the existing prompt, budget, response guard, strict parser and classifier.
An operation ID is durable. All attempts stay on the claimed organization.
"""
from types import SimpleNamespace
import json
import time

from app.extraction.extractor import KnowledgeExtractor
from app.extraction.llm_provider import GroqProvider, GroqProviderError, LLMProvider
from app.extraction.prompts import EXTRACTION_SYSTEM_PROMPT, build_extraction_prompt
from app.extraction.token_budget import TokenBudgetManager
from app.extraction.organization_scheduler import MODEL, SchedulerHold, digest
from app.extraction.quote_catalog import chunk_prompt, resolve_response


def extraction_policy(configuration):
    if configuration.prompt_policy == 'canonical_grounded_v4':
        from app.extraction import canonical_grounding as wire
        if configuration.response_format != 'json_schema':
            raise SchedulerHold('Canonical grounding requires strict schema')
        return wire.SYSTEM,wire.chunk_prompt,wire.resolve_response,wire.response_format()
    if configuration.prompt_policy == 'context_grounded_v3':
        from app.extraction import context_grounding as wire
        if configuration.response_format != 'json_schema':
            raise SchedulerHold('Context grounding requires strict schema')
        return wire.SYSTEM,wire.chunk_prompt,wire.resolve_response,wire.response_format()
    if configuration.prompt_policy == 'grounded_fields_v2':
        from app.extraction import grounded_fields as wire
        if configuration.response_format != 'json_schema':
            raise SchedulerHold('Grounded fields require strict schema mode')
        return wire.SYSTEM, wire.chunk_prompt, wire.resolve_response, wire.response_format()
    if configuration.response_format != 'json_object':
        raise SchedulerHold('Legacy policy requires JSON object mode')
    return EXTRACTION_SYSTEM_PROMPT, chunk_prompt, resolve_response, {'type':'json_object'}


def schema_budget_text(configuration, response_format):
    return json.dumps(response_format,ensure_ascii=False,separators=(',',':')) if configuration.response_format=='json_schema' else ''


def request_prompt(chunk,builder):
    prompt = builder(chunk)
    if chunk.ingestion_binding:
        if prompt.startswith('{'):
            body=json.loads(prompt)
            body['ingestion_binding']=chunk.ingestion_binding
            prompt=json.dumps(body,ensure_ascii=False,separators=(',',':'))
        else:
            prompt += '\nINGESTION VERSION SHA256 (metadata, not source evidence): '+chunk.ingestion_binding
    return prompt


def prepare_request(chunk, configuration):
    system, builder, _, response_format = extraction_policy(configuration)
    prompt=request_prompt(chunk,builder)
    budget = TokenBudgetManager(tokens_per_minute=configuration.tokens_per_minute).calculate_budget(
        prompt, system_text=system+schema_budget_text(configuration,response_format),
        min_output_tokens=configuration.min_output_tokens,
        preferred_output_tokens=configuration.preferred_output_tokens)
    if not budget.is_safe:
        raise SchedulerHold("Existing extraction budget rejects this chunk")
    payload = {"model": configuration.model,
               "messages": [{"role": "system", "content": system},
                            {"role": "user", "content": prompt}],
               "temperature": configuration.temperature, "max_tokens": budget.max_output_tokens,
               "response_format": response_format}
    if configuration.reasoning_effort is not None:
        payload['reasoning_effort']=configuration.reasoning_effort
    return payload, budget


class _BoundProvider(LLMProvider):
    def __init__(self, scheduler, identity, admission, request_id, payload, budget, transport, response_sink=None):
        self.response_sink = response_sink
        self.scheduler, self.identity, self.admission = scheduler, identity, admission
        self.request_id, self.payload, self.budget = request_id, payload, budget
        self.transport = transport
        self.tokens_per_minute = scheduler.configuration.tokens_per_minute
        self.called = False
        # Reuse classification and response validation without constructing legacy clients/pools.
        self.guard = GroqProvider.__new__(GroqProvider)
        self.guard.api_key = scheduler.organizations.key(identity)
        self.guard.key_pool = SimpleNamespace(credentials=[SimpleNamespace(api_key=scheduler.organizations.key(i))
                for i in scheduler.organizations.identities if i.slot in scheduler.organizations.enabled])

    def generate(self, prompt, system=None, temperature=0.0, max_tokens=4000):
        actual = {"model": MODEL, "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}],
                  "temperature": temperature, "max_tokens": max_tokens, "response_format": self.payload["response_format"]}
        if "reasoning_effort" in self.payload:
            actual["reasoning_effort"]=self.payload["reasoning_effort"]
        if self.called or actual != self.payload:
            raise SchedulerHold("Bound operation already used or request settings changed")
        self.called = True
        from groq import Groq
        import httpx
        # No SDK retries, environment proxies, credential pools or automatic redirects.
        client = Groq(api_key=self.guard.api_key, max_retries=0,
                      http_client=httpx.Client(transport=self.transport or httpx.HTTPTransport(retries=0, trust_env=False),
                                              timeout=90, trust_env=False, follow_redirects=False))
        try:
            for attempt in range(self.scheduler.configuration.max_retries + 1):
                if attempt:
                    self.scheduler.retry(self.request_id, self.identity, self.admission,
                                         self.budget.input_tokens, self.budget.max_output_tokens)
                # Revalidate immediately before every physical dispatch, including retries.
                self.scheduler.check_dispatch(self.request_id, self.identity, self.admission)
                start = time.monotonic()
                try:
                    raw_response = client.chat.completions.with_raw_response.create(**self.payload)
                    response = raw_response.parse()
                except Exception as exc:
                    failure = self.guard._classify_error(exc)
                    uncertain = failure.category in ("transient_network", "transient_server", "unknown")
                    self.scheduler.record_attempt(self.request_id, http_status=failure.status_code,
                                                  duration=time.monotonic() - start, category=failure.category,
                                                  uncertain=uncertain, diagnostics=failure.diagnostics())
                    can_retry = failure.category in ("transient_network", "transient_server", "transient_request")
                    if failure.status_code in (400, 401, 403, 429):
                        can_retry = False
                    if can_retry and attempt < self.scheduler.configuration.max_retries:
                        time.sleep(2 ** attempt)
                        continue
                    self.scheduler.finish(self.request_id, "uncertain" if uncertain else "failed",
                                          status=failure.status_code, retry_after=failure.retry_after)
                    # No outer retry can reinterpret the same operation as a new selection.
                    raise GroqProviderError(str(failure), category=failure.category, retryable=False,
                                            status_code=failure.status_code, error_code=failure.error_code,
                                            retry_after=failure.retry_after, retry_after_header=failure.retry_after_header) from None
                usage = response.usage.model_dump() if response.usage else {}
                finish = response.choices[0].finish_reason if response.choices else None
                # Avoid arbitrary model-generated diagnostic strings in the audit ledger.
                safe_finish = finish if finish in ("stop", "length", "end_turn", "tool_calls", "content_filter") else "unexpected"
                self.scheduler.record_attempt(self.request_id, usage=usage, http_status=raw_response.status_code, finish=safe_finish,
                                              duration=time.monotonic() - start)
                if self.response_sink is not None:
                    evidence = response.model_dump(mode='json')
                    self.scheduler.organizations.check_metadata(evidence)
                    self.response_sink(evidence)
                    with self.scheduler.transaction() as db:
                        self.scheduler._event(db,self.request_id,self.identity.organization,'response_saved',{'sha256':digest(evidence)})
                if response.model != MODEL or len(response.choices) != 1:
                    raise SchedulerHold("Unexpected model or response choice count")
                content = self.guard._extract_response_content(response)
                self.scheduler.organizations.check_metadata(content)
                # Fail malformed JSON before the legacy parser's diagnostic file writer.
                def unique(pairs):
                    result = {}
                    for key, value in pairs:
                        if key in result:
                            raise SchedulerHold("Duplicate JSON field")
                        result[key] = value
                    return result
                def invalid_constant(value):
                    raise SchedulerHold("Invalid JSON numeric constant")
                json.loads(content, object_pairs_hook=unique, parse_constant=invalid_constant)
                return content
        finally:
            client.close()


def extract_chunk(scheduler, request_id, chunk, source_units, document_id, admissions, *, transport=None, stage_a=None, response_sink=None):
    """Explicitly invoked operation. No document loop, recovery, publication or stage hooks.

    transport exists for offline HTTP tests. Production callers must separately authorize
    execution and provide verified per-organization admissions for this exact request.
    Returned items pass mechanical evidence only; semantic verification remains downstream.
    """
    # The frozen Stage A harness authorizes a fixed T0022 request. Until a reviewed
    # bridge can bind arbitrary chunks to that mechanism, this adapter is offline.
    import httpx
    from app.extraction.stage_a_bridge import StageAAuthorization
    from app.extraction.document_authorization import DocumentStageAAuthorization
    from app.extraction.single_request_authorization import SingleRequestStageAAuthorization
    live = type(transport) is not httpx.MockTransport
    if live and (transport is not None or type(stage_a) not in (StageAAuthorization, DocumentStageAAuthorization, SingleRequestStageAAuthorization)):
        raise SchedulerHold("Live dispatch requires the frozen Stage A integration and provider authorization")
    sources = {}
    for unit in source_units:
        if unit.source_id in sources:
            raise SchedulerHold("Ambiguous canonical source ID")
        sources[unit.source_id] = unit.text or ""
    if not chunk.source_units or any(sid not in sources for sid in chunk.source_units):
        raise SchedulerHold("Chunk references unknown canonical sources")
    if scheduler.configuration.prompt_policy in ('context_grounded_v3','canonical_grounded_v4'):
        from app.extraction.source_context import bind_context
        chunk=bind_context(chunk,source_units)
    payload, budget = prepare_request(chunk, scheduler.configuration)
    identity, admission = scheduler.claim(request_id, digest(payload), budget.input_tokens, budget.max_output_tokens, admissions)
    stage_claimed = False
    try:
        if live or stage_a is not None:
            stage_a.claim(scheduler, identity, admission, request_id, payload, budget)
            stage_claimed = True
        provider = _BoundProvider(scheduler, identity, admission, request_id, payload, budget, transport, response_sink)
        extractor = KnowledgeExtractor(provider, verbose=False, strict_evidence=True,
                                       min_output_tokens=scheduler.configuration.min_output_tokens,
                                       preferred_output_tokens=scheduler.configuration.preferred_output_tokens)
        extractor.valid_source_ids = set(sources)
        extractor._evidence_sources = sources
        system,builder,resolver,format_spec=extraction_policy(scheduler.configuration)
        extractor.prompt_builder = lambda _:request_prompt(chunk,builder)
        extractor.system_prompt = system
        extractor.budget_schema_text = schema_budget_text(scheduler.configuration,format_spec)
        def resolve(content):
            resolved,corrections=resolver(content,chunk)
            scheduler.organizations.check_metadata(corrections)
            with scheduler.transaction() as db:
                scheduler._event(db,request_id,identity.organization,'quote_resolution',{'resolutions':corrections})
            return resolved
        extractor.response_transform = resolve
        # Existing method performs exact prompt assembly, budget and strict validation.
        from app.extraction.source_context import evidence_view
        validation_chunk=evidence_view(chunk) if scheduler.configuration.prompt_policy in ('context_grounded_v3','canonical_grounded_v4') else chunk
        items = extractor._extract_from_chunk(validation_chunk, document_id)
        if not items and scheduler.configuration.prompt_policy not in ("grounded_fields_v2","context_grounded_v3","canonical_grounded_v4"):
            raise SchedulerHold("No validated extraction items; not a successful extraction")
    except Exception as exc:
        diagnostic={'type':type(exc).__name__,'message':str(exc)}
        scheduler.organizations.check_metadata(diagnostic)
        with scheduler.transaction() as db:
            scheduler._event(db,request_id,identity.organization,'operation_error',diagnostic)
            op = db.execute("SELECT state FROM operations WHERE id=?", (request_id,)).fetchone()
            unresolved = db.execute("SELECT 1 FROM attempts WHERE request_id=? AND completed IS NULL AND category IS NOT NULL", (request_id,)).fetchone()
        if op["state"] == "claimed":
            scheduler.finish(request_id, "uncertain" if unresolved else "validation_failed")
        if stage_claimed:
            stage_a.reconcile_local(scheduler, request_id)
        if isinstance(exc, GroqProviderError):
            raise
        # Never expose source/model text, credentials or nested SDK exceptions.
        raise SchedulerHold("Operation failed validation or admission; inspect secret-free audit") from None
    if scheduler.configuration.prompt_policy in ('context_grounded_v3','canonical_grounded_v4'):
        for item in items:
            from app.extraction.quote_catalog import evidence_source_ids
            item.extraction_metadata['primary_source_ids']=[s for s in item.source_unit_ids if s in evidence_source_ids(chunk)]
            item.extraction_metadata['context_source_ids']=list(chunk.context_source_ids)
            item.extraction_metadata['semantic_verified']=False
    scheduler.finish(request_id, "success")
    if stage_claimed:
        stage_a.reconcile_local(scheduler, request_id)
    return items
