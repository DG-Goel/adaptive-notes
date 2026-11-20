"""Configuration belongs exclusively to the new engine; no dotenv side effects."""
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import Mapping

ROLES = ('planner', 'generator', 'verifier')
DEFAULT_MODEL = 'gemma-4-31b-it'


@dataclass(frozen=True)
class ClientConfig:
    role: str
    api_key: str = field(repr=False)
    model: str = DEFAULT_MODEL
    requests_per_minute: int = 5
    tokens_per_minute: int = 32000
    context_tokens: int = 16000
    max_output_tokens: int = 2000
    concurrency: int = 1
    max_attempts: int = 2
    retry_seconds: int = 2
    timeout_seconds: int = 60

    def __post_init__(self):
        if self.role not in ROLES:
            raise ValueError('Unknown infographic client role')
        if not self.api_key.strip():
            raise ValueError(f'GEMINI_{self.role.upper()}_API_KEY is required when enabled')
        if not self.model or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-._' for c in self.model):
            raise ValueError('Invalid infographic model identifier')
        for name in ('requests_per_minute', 'tokens_per_minute', 'context_tokens',
                     'max_output_tokens', 'concurrency', 'max_attempts',
                     'retry_seconds', 'timeout_seconds'):
            value = getattr(self, name)
            if type(value) is not int or value <= 0:
                raise ValueError(f'{self.role}: {name} must be a positive integer')
        if self.max_output_tokens >= self.context_tokens:
            raise ValueError(f'{self.role}: output budget must be smaller than context budget')


@dataclass(frozen=True)
class EngineConfig:
    clients: Mapping[str, ClientConfig] = field(repr=False)
    artifact_namespace: Path = Path(__file__).resolve().parents[2] / 'data' / 'infographics'
    template_capacity: int = 15
    category_capacity: int = 3


def load_config(env):
    clients = {}
    for role in ROLES:
        prefix = f'NOETRA_INFOGRAPHIC_{role.upper()}_'
        defaults = ClientConfig.__dataclass_fields__
        values = {}
        for name in ('requests_per_minute', 'tokens_per_minute', 'context_tokens',
                     'max_output_tokens', 'concurrency', 'max_attempts',
                     'retry_seconds', 'timeout_seconds'):
            try:
                values[name] = int(env.get(prefix + name.upper(), defaults[name].default))
            except (TypeError, ValueError):
                raise ValueError(f'{prefix}{name.upper()} must be a positive integer') from None
        from .role_environment import role_key
        clients[role] = ClientConfig(role, role_key(env, role),
                                    env.get(prefix + 'MODEL', DEFAULT_MODEL), **values)
    if len({c.api_key for c in clients.values()}) != len(ROLES):
        raise ValueError('Infographic roles require three distinct dedicated credentials')
    return EngineConfig(MappingProxyType(clients))
