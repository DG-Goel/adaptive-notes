"""Offline foundation tests: no real credentials, requests or lecture writes."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
import os
from pathlib import Path
import subprocess
import sys
from threading import Event, Lock

import pytest

from app.infographics import initialize
from app.infographics.clients import LocalLimitError, ProviderError, RoleClient, WORKLOADS
from app.infographics.config import ClientConfig, DEFAULT_MODEL
from app.infographics.contracts import Completion, ModelInfo


def environment(**extra):
    return dict(NOETRA_INFOGRAPHIC_ENGINE_ENABLED='true',
                GEMINI_PLANNER_API_KEY='planner-test-secret',
                GEMINI_GENERATOR_API_KEY='generator-test-secret',
                GEMINI_VERIFIER_API_KEY='verifier-test-secret', **extra)


class Transport:
    def __init__(self, config):
        self.config = config
        self.calls = []
        self.closed = False

    def model_info(self, model):
        self.calls.append(('model', model))
        return ModelInfo('models/' + model, 32000, 4000, ('generateContent',))

    def complete(self, model, content, max_output_tokens):
        self.calls.append(('complete', model, max_output_tokens))
        return Completion('test response', 10, 4)

    def close(self):
        self.closed = True


@pytest.mark.parametrize('env', [{}, {'NOETRA_INFOGRAPHIC_ENGINE_ENABLED': 'false'},
    {'NOETRA_INFOGRAPHIC_ENGINE_ENABLED': ' FALSE ', 'NOETRA_INFOGRAPHIC_PLANNER_CONCURRENCY': 'bad'}])
def test_disabled_returns_before_any_configuration_or_transport(env):
    def forbidden(_):
        pytest.fail('Disabled engine constructed a transport')
    assert initialize(env, transport_factory=forbidden) is None


def test_disabled_import_is_lazy_and_has_no_side_effects(tmp_path):
    code = '''
import os, socket, sys
def forbidden(*args, **kwargs):
    raise AssertionError('Unexpected network or directory access')
socket.socket = forbidden
os.mkdir = forbidden
from app.infographics import initialize
assert initialize({'NOETRA_INFOGRAPHIC_ENGINE_ENABLED':'false'}) is None
assert 'app.infographics.runtime' not in sys.modules
assert 'app.infographics.gemini' not in sys.modules
assert 'google.genai' not in sys.modules
'''
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1',
               PYTHONPATH=str(Path(__file__).resolve().parents[1]))
    result = subprocess.run([sys.executable, '-c', code], cwd=tmp_path, env=env,
                            capture_output=True, text=True, timeout=20)
    assert result.returncode == 0, result.stderr
    assert list(tmp_path.iterdir()) == []


def test_enabled_constructs_three_independent_clients_without_requests():
    engine = initialize(environment(), transport_factory=Transport)
    assert set(engine.clients) == {'planner', 'generator', 'verifier'}
    assert len({id(c._transport) for c in engine.clients.values()}) == 3
    assert not engine.templates
    assert engine.config.template_capacity == 15 and engine.config.category_capacity == 3
    assert engine.renderer_id == 'antv-infographic'
    for role, client in engine.clients.items():
        assert client.config.api_key == f'{role}-test-secret'
        assert client._transport.calls == []
        assert client.accounting.attempts == 0
        assert 'test-secret' not in repr(client.config)
    engine.close()
    assert all(c._transport.closed for c in engine.clients.values())


def test_independent_limits_and_no_legacy_key_fallback():
    env = environment(NOETRA_INFOGRAPHIC_PLANNER_CONCURRENCY='3',
                      NOETRA_INFOGRAPHIC_GENERATOR_CONTEXT_TOKENS='9000',
                      GEMINI_API_KEY='legacy-do-not-use')
    engine = initialize(env, transport_factory=Transport)
    assert engine.clients['planner'].config.concurrency == 3
    assert engine.clients['generator'].config.context_tokens == 9000
    assert engine.clients['verifier'].config.context_tokens == 16000
    del env['GEMINI_GENERATOR_API_KEY']
    with pytest.raises(ValueError, match='GEMINI_GENERATOR_API_KEY'):
        initialize(env, transport_factory=Transport)


@pytest.mark.parametrize('name,value', [
    ('NOETRA_INFOGRAPHIC_ENGINE_ENABLED', 'yes'),
    ('NOETRA_INFOGRAPHIC_PLANNER_CONCURRENCY', '0'),
    ('NOETRA_INFOGRAPHIC_VERIFIER_MAX_ATTEMPTS', 'garbage'),
    ('NOETRA_INFOGRAPHIC_GENERATOR_MODEL', '../invalid'),
    ('NOETRA_INFOGRAPHIC_PLANNER_MAX_OUTPUT_TOKENS', '16000'),
    ('GEMINI_VERIFIER_API_KEY', 'planner-test-secret'),
])
def test_invalid_configuration_never_constructs_clients(name, value):
    env = environment()
    env[name] = value
    with pytest.raises(ValueError):
        initialize(env, transport_factory=lambda _: pytest.fail('Configuration must validate first'))


def test_explicit_model_verification_and_role_scoping():
    engine = initialize(environment(), transport_factory=Transport)
    planner = engine.clients['planner']
    with pytest.raises(RuntimeError, match='verify'):
        planner.complete('adaptive_segmentation', 'test')
    with pytest.raises(ValueError, match='not authorized'):
        planner.complete('targeted_repair', 'test')
    models = engine.verify_models()
    assert all(m.name == 'models/' + DEFAULT_MODEL for m in models.values())
    result = planner.complete('adaptive_segmentation', 'test')
    assert result.text == 'test response'
    assert planner.accounting.attempts == 2
    assert planner.accounting.reported_input_tokens == 10
    assert planner.accounting.reported_output_tokens == 4
    assert planner.accounting.completions == 1
    assert planner.accounting.reserved_tokens == 260 + 2000
    assert engine.clients['generator'].accounting.attempts == 1


@pytest.mark.parametrize('role', ['planner', 'generator', 'verifier'])
def test_every_workload_is_exclusively_assigned(role):
    engine = initialize(environment(), transport_factory=Transport)
    client = engine.clients[role]
    client.verify_model()
    for workload in set().union(*WORKLOADS.values()):
        if workload not in WORKLOADS[role]:
            with pytest.raises(ValueError, match='not authorized'):
                client.complete(workload, 'test')
    assert client.accounting.attempts == 1


def test_failed_reverification_revokes_generation_admission():
    client, transport, _ = client_with_clock()
    transport.model_info = lambda _: ModelInfo('models/other', 32000, 4000, ('generateContent',))
    with pytest.raises(ProviderError):
        client.verify_model()
    with pytest.raises(RuntimeError, match='verify'):
        client.complete('adaptive_segmentation', 'test')


@pytest.mark.parametrize('info', [ModelInfo('models/other', 32000, 4000, ('generateContent',)),
    ModelInfo('models/' + DEFAULT_MODEL, 32000, 4000, ()),
    ModelInfo('models/' + DEFAULT_MODEL, 0, 0, ('generateContent',))])
def test_unavailable_model_does_not_allow_generation(info):
    settings = ClientConfig('planner', 'secret')
    transport = Transport(settings)
    transport.model_info = lambda _: info
    client = RoleClient(settings, transport)
    with pytest.raises(ProviderError):
        client.verify_model()
    with pytest.raises(RuntimeError):
        client.complete('adaptive_segmentation', 'test')


def client_with_clock(**changes):
    settings = replace(ClientConfig('planner', 'secret'), **changes)
    now = [0.0]
    transport = Transport(settings)
    client = RoleClient(settings, transport, clock=lambda: now[0], sleep=lambda _: None)
    client.verify_model()
    return client, transport, now


def test_request_limit_includes_model_checks_and_expires():
    client, transport, now = client_with_clock(requests_per_minute=1)
    with pytest.raises(LocalLimitError):
        client.complete('adaptive_segmentation', 'test')
    assert len(transport.calls) == 1
    now[0] = 60
    client.complete('adaptive_segmentation', 'test')
    assert client.accounting.attempts == 2


def test_token_limit_and_context_fail_before_provider_request():
    client, transport, _ = client_with_clock(tokens_per_minute=100)
    with pytest.raises(LocalLimitError):
        client.complete('adaptive_segmentation', 'test')
    with pytest.raises(LocalLimitError):
        client.complete('adaptive_segmentation', 'x' * 16000)
    with pytest.raises(ValueError):
        client.complete('adaptive_segmentation', 'test', max_output_tokens=4001)
    assert len(transport.calls) == 1


def test_retry_accounting_is_bound_to_original_role():
    client, transport, _ = client_with_clock()
    attempts = []
    def complete(*_):
        attempts.append(transport.config.api_key)
        if len(attempts) == 1:
            raise ProviderError('server_unavailable', retryable=True)
        return Completion('ok', None, None)
    transport.complete = complete
    client.complete('adaptive_segmentation', 'test')
    assert attempts == ['secret', 'secret']
    assert client.accounting.attempts == 3
    assert client.accounting.failures == 1
    assert client.accounting.unreported_completions == 1


def test_quota_hold_does_not_retry_or_switch_keys():
    client, transport, _ = client_with_clock()
    def complete(*_):
        raise ProviderError('quota_hold')
    transport.complete = complete
    with pytest.raises(ProviderError, match='quota_hold'):
        client.complete('adaptive_segmentation', 'test')
    assert client.accounting.attempts == 2


def test_raw_transport_errors_are_not_in_displayed_tracebacks():
    import traceback
    client, transport, _ = client_with_clock()
    def complete(*_):
        raise RuntimeError('secret credential and prompt contents')
    transport.complete = complete
    with pytest.raises(ProviderError) as caught:
        client.complete('adaptive_segmentation', 'test')
    assert 'secret credential' not in ''.join(traceback.format_exception(caught.value))
    assert client.accounting.failures == 1


def test_concurrency_is_bounded_per_role():
    client, transport, _ = client_with_clock(requests_per_minute=10)
    entered, release = Event(), Event()
    lock = Lock()
    counts = [0, 0]
    def complete(*_):
        with lock:
            counts[0] += 1
            counts[1] = max(counts)
        entered.set()
        assert release.wait(5)
        with lock:
            counts[0] -= 1
        return Completion('ok', 1, 1)
    transport.complete = complete
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(client.complete, 'adaptive_segmentation', 'test') for _ in range(3)]
        assert entered.wait(5)
        release.set()
        assert all(f.result(timeout=5).text == 'ok' for f in futures)
    assert counts[1] == 1


def test_partial_initialization_closes_created_clients():
    transports = []
    def factory(config):
        if config.role == 'generator':
            raise RuntimeError('factory failed')
        transports.append(Transport(config))
        return transports[-1]
    with pytest.raises(RuntimeError):
        initialize(environment(), transport_factory=factory)
    assert transports[0].closed


def test_close_is_idempotent_and_prevents_further_requests():
    client, transport, _ = client_with_clock()
    client.close()
    client.close()
    with pytest.raises(RuntimeError, match='closed'):
        client.complete('adaptive_segmentation', 'test')
    assert transport.closed


def test_google_sdk_adapter_without_network(monkeypatch):
    from types import SimpleNamespace
    from google import genai
    from app.infographics.gemini import GeminiTransport
    seen = {}
    def factory(**kwargs):
        seen.update(kwargs)
        return SimpleNamespace(models=SimpleNamespace(
            get=lambda **_: SimpleNamespace(name='models/' + DEFAULT_MODEL,
                input_token_limit=32000, output_token_limit=4000,
                supported_actions=['generateContent']),
            generate_content=lambda **_: SimpleNamespace(text='ok', usage_metadata=SimpleNamespace(
                prompt_token_count=3, candidates_token_count=2))), close=lambda: None)
    monkeypatch.setattr(genai, 'Client', factory)
    settings = ClientConfig('planner', 'private-test-key')
    transport = GeminiTransport(settings)
    assert seen['api_key'] == settings.api_key
    assert seen['http_options'].retry_options.attempts == 1
    assert seen['http_options'].timeout == 60000
    assert transport.model_info(DEFAULT_MODEL).input_tokens == 32000
    assert transport.complete(DEFAULT_MODEL, 'test', 100).output_tokens == 2
    transport.close()


@pytest.mark.parametrize('code,category,retryable', [(401,'credential_rejected',False),
    (403,'credential_rejected',False),(404,'model_unavailable',False),
    (429,'quota_hold',False),(503,'server_unavailable',True)])
def test_sdk_errors_are_safe(code, category, retryable):
    from app.infographics.gemini import _safe_call
    import traceback
    def operation():
        error = RuntimeError('NEVER_PRINT_THIS_API_KEY')
        error.code = code
        raise error
    with pytest.raises(ProviderError) as caught:
        _safe_call(operation)
    assert caught.value.category == category
    assert caught.value.retryable == retryable
    assert 'NEVER_PRINT_THIS_API_KEY' not in ''.join(traceback.format_exception(caught.value))
