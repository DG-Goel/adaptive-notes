"""Opt-in composition root. No jobs, stage runner, prompts or storage writes."""
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping

from .clients import RoleClient
from .config import EngineConfig, load_config


@dataclass(frozen=True)
class Engine:
    config: EngineConfig
    clients: Mapping[str, RoleClient] = field(repr=False)
    renderer_id: str = 'antv-infographic'
    templates: tuple = ()  # Fifteen slots planned; no invented AntV template IDs.

    def verify_models(self):
        return {role: client.verify_model() for role, client in self.clients.items()}

    def close(self):
        failure = None
        for client in self.clients.values():
            try:
                client.close()
            except Exception as error:
                failure = error
        if failure:
            raise failure


def build_engine(env, *, transport_factory=None):
    config = load_config(env)
    if transport_factory is None:
        from .gemini import GeminiTransport
        transport_factory = GeminiTransport
    clients = {}
    try:
        for role, settings in config.clients.items():
            clients[role] = RoleClient(settings, transport_factory(settings))
    except Exception:
        for client in clients.values():
            try:
                client.close()
            except Exception:
                pass
        raise
    return Engine(config, MappingProxyType(clients))
