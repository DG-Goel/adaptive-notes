"""Independent, disabled-first generator composition using numbered key 2."""
def initialize_generator(environment=None,*,transport_factory=None,config=None,verify=True):
    from .role_environment import initialize_role
    return initialize_role('generator',environment,transport_factory=transport_factory,config=config,verify=verify)
