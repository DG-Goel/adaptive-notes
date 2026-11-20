"""Independent Phase 1 foundation. Importing this package has no side effects."""


def initialize(environment=None, *, transport_factory=None):
    """Return None when disabled, without importing provider or runtime modules."""
    import os

    env = os.environ if environment is None else environment
    flag = env.get('NOETRA_INFOGRAPHIC_ENGINE_ENABLED', 'false').strip().lower()
    if flag == 'false':
        return None
    if flag != 'true':
        raise ValueError('NOETRA_INFOGRAPHIC_ENGINE_ENABLED must be true or false')
    from .runtime import build_engine

    return build_engine(env, transport_factory=transport_factory)
