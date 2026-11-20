"""Planner-only composition; disabled flag checked before any credential read."""
def initialize_planner(environment=None,*,transport_factory=None,config=None,verify=True):
    import os
    env=os.environ if environment is None else environment
    flag=env.get('NOETRA_INFOGRAPHIC_ENGINE_ENABLED','false').strip().lower()
    if flag=='false': return None
    if flag!='true': raise ValueError('NOETRA_INFOGRAPHIC_ENGINE_ENABLED must be true or false')
    from .config import ClientConfig
    from .clients import RoleClient
    if config is None:
        values={}
        for name,field in ClientConfig.__dataclass_fields__.items():
            if name in {'role','api_key'}: continue
            raw=env.get('NOETRA_INFOGRAPHIC_PLANNER_'+name.upper(),field.default)
            try: values[name]=str(raw) if name=='model' else int(raw)
            except (ValueError,TypeError): raise ValueError('Invalid planner setting: '+name) from None
        from .role_environment import role_key
        config=ClientConfig('planner',role_key(env,'planner'),**values)
    if config.role!='planner': raise ValueError('Planner configuration required')
    if transport_factory is None:
        from .gemini import GeminiTransport
        transport_factory=GeminiTransport
    client=RoleClient(config,transport_factory(config))
    try:
        metadata=client.verify_model() if verify else None
    except Exception:
        client.close(); raise
    return client,metadata
