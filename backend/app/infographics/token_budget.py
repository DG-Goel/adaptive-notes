"""Offline, provider-independent request budgeting with final serialized checks."""
from dataclasses import asdict, dataclass
import json
import math
from typing import Protocol

from .contracts import ModelInfo


@dataclass(frozen=True)
class TokenCount:
    value: int
    kind: str = 'estimated'
    method: str = 'utf8-bytes-upper-bound-v1'

    def __post_init__(self):
        if type(self.value) is not int or self.value < 0 or self.kind not in {'estimated','measured'}:
            raise ValueError('Invalid token count')


class TokenCounter(Protocol):
    def count(self, text: str) -> TokenCount: ...


class ConservativeCounter:
    def count(self, text):
        return TokenCount(len(text.encode('utf-8')))


@dataclass(frozen=True)
class ContextConfig:
    target_source_tokens: int = 10000
    max_source_tokens: int = 16000
    lookahead_tokens: int = 1500
    previous_context_tokens: int = 500
    reserved_output_tokens: int = 3000
    thinking_tokens: int = 0
    safety_margin_ratio: float = 0.10
    framing_tokens: int = 256
    max_no_progress: int = 3
    expansion_factor: float = 1.5

    def __post_init__(self):
        for key in ('target_source_tokens','max_source_tokens','reserved_output_tokens','max_no_progress'):
            if type(getattr(self,key)) is not int or getattr(self,key) <= 0:
                raise ValueError(f'{key} must be positive')
        for key in ('lookahead_tokens','previous_context_tokens','thinking_tokens','framing_tokens'):
            if type(getattr(self,key)) is not int or getattr(self,key) < 0:
                raise ValueError(f'{key} must be nonnegative')
        if not math.isfinite(self.safety_margin_ratio) or not 0 <= self.safety_margin_ratio < 1:
            raise ValueError('Invalid token safety margin')
        if not math.isfinite(self.expansion_factor) or self.expansion_factor <= 1:
            raise ValueError('Window expansion factor must exceed one')
        if self.target_source_tokens > self.max_source_tokens:
            raise ValueError('Initial source target exceeds maximum source target')


@dataclass(frozen=True)
class ModelLimits:
    input_tokens: int
    output_tokens: int
    shared_context_tokens: int | None = None
    metadata_verified: bool = False
    model_name: str = ''
    # Phase 1 complete() always uses its conservative byte-bound admission.
    phase1_byte_guard: bool = False

    def __post_init__(self):
        for value in (self.input_tokens,self.output_tokens):
            if type(value) is not int or value <= 0:
                raise ValueError('Explicit positive input/output limits are required')
        if self.shared_context_tokens is not None and (type(self.shared_context_tokens) is not int or self.shared_context_tokens <= 0):
            raise ValueError('Shared context limit must be positive or absent')

    @classmethod
    def from_client(cls, config, metadata: ModelInfo | None = None):
        if metadata is not None and (metadata.name != 'models/' + config.model or 'generateContent' not in metadata.methods):
            raise ValueError('Metadata does not match configured model or capability')
        return cls(min(metadata.input_tokens,config.context_tokens) if metadata else config.context_tokens,
                   min(metadata.output_tokens,config.max_output_tokens) if metadata else config.max_output_tokens,
                   config.context_tokens, metadata is not None,
                   metadata.name if metadata else config.model, True)


@dataclass(frozen=True)
class RequestParts:
    system_instructions: str = ''
    segmentation_prompt: str = ''  # Supplied by future callers; no prompt authored here.
    request_metadata: str = ''
    previous_summary: str = ''


def block_payload(block):
    return dict(id=block.id,position=block.position,type=block.type,
                section_path=block.section_path,parent_id=block.parent_id,
                source_start=block.source_start,source_end=block.source_end,
                references=block.references,timestamps=block.timestamps,text=block.text)


def serialize_request(index, parts, previous, source, lookahead):
    """Explicit region ownership is data, not an LLM instruction/prompt."""
    body = dict(source_artifact_id=index.snapshot.source_id,source_sha256=index.snapshot.sha256,
                index_version=index.version,system_instructions=parts.system_instructions,
                segmentation_prompt=parts.segmentation_prompt,request_metadata=parts.request_metadata,
                regions=dict(
                    A=dict(ownership='read_only',summary=parts.previous_summary,
                           blocks=[block_payload(b) for b in previous]),
                    B=dict(ownership='commit_eligible',blocks=[block_payload(b) for b in source]),
                    C=dict(ownership='lookahead_only',blocks=[block_payload(b) for b in lookahead])))
    return json.dumps(body,ensure_ascii=False,separators=(',',':'))


@dataclass(frozen=True)
class BudgetReport:
    fits: bool
    reason: str
    input_count: TokenCount
    input_with_framing: int
    output_tokens: int
    thinking_tokens: int
    input_limit: int
    output_limit: int
    shared_context_limit: int | None
    safety_margin_tokens: int
    components: tuple[tuple[str, TokenCount], ...]
    metadata_verified: bool
    phase1_guard_tokens: int
    input_safety_margin_tokens: int
    shared_safety_margin_tokens: int


class TokenBudgetManager:
    def __init__(self, limits: ModelLimits, config: ContextConfig | None = None,
                 counter: TokenCounter | None = None):
        self.limits = limits
        self.config = config or ContextConfig()
        self.counter = counter or ConservativeCounter()
        # Hosted output ceiling may reduce the adjustable response target.
        self.response_tokens = min(self.config.reserved_output_tokens,
                                   limits.output_tokens - self.config.thinking_tokens)
        if self.response_tokens <= 0:
            raise ValueError('Thinking allowance leaves no response budget')

    def count(self, text):
        return self.counter.count(text)

    @property
    def framing_tokens(self):
        return max(256 if self.limits.phase1_byte_guard else 0,self.config.framing_tokens)

    @property
    def input_capacity(self):
        limit = self.limits.input_tokens
        capacity = limit - math.ceil(limit*self.config.safety_margin_ratio)
        if self.limits.shared_context_tokens is not None:
            shared = self.limits.shared_context_tokens
            capacity = min(capacity, shared - math.ceil(shared*self.config.safety_margin_ratio)
                           - self.response_tokens - self.config.thinking_tokens)
        return max(0,capacity-self.framing_tokens)

    def check(self,index,parts,previous=(),source=(),lookahead=(),*,payload=None):
        body = serialize_request(index,parts,previous,source,lookahead) if payload is None else payload
        count = self.count(body)
        guard = len(body.encode('utf-8')) if self.limits.phase1_byte_guard else 0
        input_tokens = max(count.value,guard) + self.framing_tokens
        components = [(key,self.count(value)) for key,value in (
            ('system_instructions',parts.system_instructions),
            ('segmentation_prompt',parts.segmentation_prompt),
            ('request_metadata',parts.request_metadata),
            ('previous_context',parts.previous_summary + ''.join(b.text for b in previous)),
            ('current_source_window',''.join(b.text for b in source)),
            ('forward_lookahead',''.join(b.text for b in lookahead)))]
        components.append(('serialized_request',count))
        # Tokenizers are not necessarily additive. Full serialized count is authoritative.
        fits = max(count.value,guard) <= self.input_capacity
        reason = 'within_budget' if fits else 'input_or_shared_context_limit'
        return BudgetReport(fits,reason,count,input_tokens,self.response_tokens,
            self.config.thinking_tokens,self.limits.input_tokens,self.limits.output_tokens,
            self.limits.shared_context_tokens,
            math.ceil((self.limits.shared_context_tokens or self.limits.input_tokens)*self.config.safety_margin_ratio),
            tuple(components),self.limits.metadata_verified,guard,
            math.ceil(self.limits.input_tokens*self.config.safety_margin_ratio),
            math.ceil(self.limits.shared_context_tokens*self.config.safety_margin_ratio) if self.limits.shared_context_tokens else 0)

    def source_capacity(self,index,parts):
        report = self.check(index,parts)
        overhead = max(report.input_count.value,report.phase1_guard_tokens)
        return max(0,min(self.config.max_source_tokens,self.input_capacity-overhead))

    def public_config(self):
        sample = self.count('counter identity')
        return dict(limits=asdict(self.limits),context=asdict(self.config),
                    counter=dict(kind=sample.kind,method=sample.method))

    def preflight(self,index,parts,previous,source,lookahead,*,final_payload=None,
                  provider_metadata: ModelInfo | None = None):
        """Recheck the final request; no API call is made. Missing metadata stays explicit."""
        manager = self
        if provider_metadata is not None:
            if self.limits.model_name and provider_metadata.name not in {self.limits.model_name,'models/'+self.limits.model_name}:
                raise ValueError('Preflight model mismatch')
            if 'generateContent' not in provider_metadata.methods:
                raise ValueError('Preflight model cannot generate content')
            limits = ModelLimits(min(self.limits.input_tokens,provider_metadata.input_tokens),
                min(self.limits.output_tokens,provider_metadata.output_tokens),
                self.limits.shared_context_tokens,True,provider_metadata.name,self.limits.phase1_byte_guard)
            manager = TokenBudgetManager(limits,self.config,self.counter)
        return manager.check(index,parts,previous,source,lookahead,payload=final_payload)
