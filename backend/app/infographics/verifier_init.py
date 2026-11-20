"""Verifier-only, disabled-first composition through the canonical role adapter."""
def initialize_verifier(environment=None,*,transport_factory=None,config=None,verify=True):
    import os
    env=os.environ if environment is None else environment
    flag=env.get('NOETRA_INFOGRAPHIC_ENGINE_ENABLED','false').strip().lower()
    if flag=='false':return None
    if flag!='true':raise ValueError('NOETRA_INFOGRAPHIC_ENGINE_ENABLED must be true or false')
    from .role_environment import initialize_role
    class Settings:
        def get(self,key,default=None):
            defaults={'NOETRA_INFOGRAPHIC_VERIFIER_CONTEXT_TOKENS':64000,'NOETRA_INFOGRAPHIC_VERIFIER_MAX_OUTPUT_TOKENS':8000}
            return env.get(key,defaults.get(key,default))
    return initialize_role('verifier',Settings(),transport_factory=transport_factory,config=config,verify=verify)
