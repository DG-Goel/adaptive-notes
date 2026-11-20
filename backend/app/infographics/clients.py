"""Role-scoped clients; retries never switch keys or providers."""
from collections import deque
from dataclasses import dataclass, replace
from threading import BoundedSemaphore, Lock
import time

from .contracts import Completion, LLMTransport, ModelInfo

WORKLOADS = {
    'planner': frozenset({'adaptive_segmentation', 'master_category_routing', 'global_consolidation'}),
    'generator': frozenset({'template_selection', 'content_compression', 'structured_generation'}),
    'verifier': frozenset({'coverage_verification', 'factual_grounding', 'hallucination_detection',
                           'targeted_repair', 'reverification'}),
}


class ProviderError(RuntimeError):
    """Safe error: raw provider payloads and exception strings are never retained."""
    def __init__(self, category, *, retryable=False, retry_after=0):
        super().__init__(f'Infographic provider error: {category}')
        self.category = category
        self.retryable = retryable
        self.retry_after = retry_after


class LocalLimitError(RuntimeError):
    pass


@dataclass
class Accounting:
    attempts: int = 0
    failures: int = 0
    completions: int = 0
    reserved_tokens: int = 0
    reported_input_tokens: int = 0
    reported_output_tokens: int = 0
    unreported_completions: int = 0


class RoleClient:
    def __init__(self, config, transport: LLMTransport, *, clock=time.monotonic, sleep=time.sleep):
        self.config = config
        self._transport = transport
        self._clock, self._sleep = clock, sleep
        self._lock = Lock()
        self._slots = BoundedSemaphore(config.concurrency)
        self._requests = deque()
        self._usage = Accounting()
        self._model = None
        self._closed = False

    @property
    def accounting(self):
        with self._lock:
            return replace(self._usage)

    def _reserve(self, tokens):
        with self._lock:
            if self._closed:
                raise RuntimeError('Infographic client is closed')
            now = self._clock()
            while self._requests and self._requests[0][0] <= now - 60:
                self._requests.popleft()
            if len(self._requests) >= self.config.requests_per_minute:
                raise LocalLimitError('Role request limit reached; retry after the window expires')
            if sum(t for _, t in self._requests) + tokens > self.config.tokens_per_minute:
                raise LocalLimitError('Role token limit reached; retry after the window expires')
            self._requests.append((now, tokens))
            self._usage.attempts += 1
            self._usage.reserved_tokens += tokens

    def _call(self, operation, tokens=0):
        with self._slots:
            for attempt in range(self.config.max_attempts):
                self._reserve(tokens)
                failure = None
                try:
                    return operation()
                except ProviderError as error:
                    # Construct a new safe exception, without keeping provider traceback/context.
                    failure = ProviderError(error.category, retryable=error.retryable,
                                            retry_after=error.retry_after)
                except Exception:
                    failure = ProviderError('unexpected_transport_failure')
                with self._lock:
                    self._usage.failures += 1
                if not failure.retryable or attempt + 1 == self.config.max_attempts:
                    raise failure from None
                self._sleep(max(self.config.retry_seconds * 2 ** attempt, failure.retry_after))

    def verify_model(self) -> ModelInfo:
        """Explicit metadata request with this role's credential; never a fallback."""
        with self._lock:
            self._model = None
        model = self._call(lambda: self._transport.model_info(self.config.model))
        if model.name != 'models/' + self.config.model or 'generateContent' not in model.methods:
            raise ProviderError('model_unavailable')
        if model.input_tokens <= 0 or model.output_tokens <= 0:
            raise ProviderError('model_limits_unavailable')
        with self._lock:
            self._model = model
        return model

    def complete(self, workload: str, content: str, *, max_output_tokens=None) -> Completion:
        if workload not in WORKLOADS[self.config.role]:
            raise ValueError('Workload is not authorized for this infographic role')
        with self._lock:
            model = self._model
        if model is None:
            raise RuntimeError('Explicitly verify this role model before generation')
        output = self.config.max_output_tokens if max_output_tokens is None else max_output_tokens
        if type(output) is not int or not 0 < output <= min(self.config.max_output_tokens, model.output_tokens):
            raise ValueError('Output token budget exceeds configured or provider limits')
        # UTF-8 byte count plus framing is a deliberately conservative admission
        # bound, not a reported tokenizer count. Never claim estimates are usage.
        input_bound = len(content.encode('utf-8')) + 256
        if input_bound > model.input_tokens or input_bound + output > self.config.context_tokens:
            raise LocalLimitError('Request exceeds context budget; future context manager must segment it')
        result = self._call(lambda: self._transport.complete(self.config.model, content, output),
                            input_bound + output)
        with self._lock:
            self._usage.completions += 1
            self._usage.reported_input_tokens += result.input_tokens or 0
            self._usage.reported_output_tokens += result.output_tokens or 0
            self._usage.unreported_completions += int(result.input_tokens is None or result.output_tokens is None)
        return result

    def close(self):
        with self._lock:
            if self._closed:
                return
            self._closed = True
        self._transport.close()
