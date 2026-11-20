"""Lazy Google SDK adapter. No existing NOETRA provider is imported or altered."""
from .clients import ProviderError
from .contracts import Completion, ModelInfo


def _safe_call(operation):
    failure = None
    try:
        return operation()
    except Exception as error:
        code = getattr(error, 'code', None)
        if code == 429:
            # Provider quota exhaustion is a hold, never an automatic retry.
            failure = ProviderError('quota_hold')
        elif code in (401, 403):
            failure = ProviderError('credential_rejected')
        elif code == 404:
            failure = ProviderError('model_unavailable')
        elif isinstance(code, int) and 500 <= code < 600:
            failure = ProviderError('server_unavailable', retryable=True)
        elif isinstance(error, (ConnectionError, TimeoutError)):
            failure = ProviderError('network_unavailable', retryable=True)
        else:
            failure = ProviderError('request_failed')
    raise failure from None


class GeminiTransport:
    def __init__(self, config):
        # SDK retries are disabled so every network attempt is accounted by RoleClient.
        def create():
            from google import genai
            from google.genai import types
            return genai.Client(api_key=config.api_key, http_options=types.HttpOptions(
                timeout=config.timeout_seconds * 1000,
                retry_options=types.HttpRetryOptions(attempts=1)))
        self._client = _safe_call(create)

    def model_info(self, model):
        info = _safe_call(lambda: self._client.models.get(model=model))
        return ModelInfo(info.name, info.input_token_limit or 0, info.output_token_limit or 0,
                         tuple(info.supported_actions or ()))

    def complete(self, model, content, max_output_tokens):
        response = _safe_call(lambda: self._client.models.generate_content(
            model=model, contents=content,
            config={'temperature': 0, 'max_output_tokens': max_output_tokens}))
        usage = response.usage_metadata
        text = _safe_call(lambda: response.text)
        if not text:
            raise ProviderError('empty_or_blocked_response')
        input_tokens = getattr(usage, 'prompt_token_count', None)
        total_tokens = getattr(usage, 'total_token_count', None)
        output_tokens = getattr(usage, 'candidates_token_count', None)
        if total_tokens is not None and input_tokens is not None:
            output_tokens = max(0, total_tokens - input_tokens)
        elif output_tokens is not None:
            output_tokens += getattr(usage, 'thoughts_token_count', None) or 0
        return Completion(text, input_tokens, output_tokens)

    def close(self):
        _safe_call(self._client.close)
