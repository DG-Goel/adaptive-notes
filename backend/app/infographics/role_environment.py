"""Fixed numbered credentials; canonical names always win over legacy aliases."""
CANONICAL={'planner':'GEMINI_API_KEY_1','generator':'GEMINI_API_KEY_2','verifier':'GEMINI_API_KEY_3'}


def role_key(environment,role):
    name=CANONICAL[role]
    value=environment.get(name,None)
    if value is None: value=environment.get('GEMINI_'+role.upper()+'_API_KEY','')
    return value


def initialize_role(role,environment=None,*,transport_factory=None,config=None,verify=True):
    import os
    env=os.environ if environment is None else environment
    flag=env.get('NOETRA_INFOGRAPHIC_ENGINE_ENABLED','false').strip().lower()
    if flag=='false': return None
    if flag!='true': raise ValueError('NOETRA_INFOGRAPHIC_ENGINE_ENABLED must be true or false')
    from .config import ClientConfig
    from .clients import RoleClient
    if config is None:
        key=role_key(env,role)
        if not key: raise ValueError(CANONICAL[role]+' is required when enabled')
        values={}
        for name,field in ClientConfig.__dataclass_fields__.items():
            if name in {'role','api_key'}: continue
            default=(8000 if name=='max_output_tokens' else 32000 if name=='context_tokens' else field.default) if role=='generator' else field.default
            raw=env.get('NOETRA_INFOGRAPHIC_'+role.upper()+'_'+name.upper(),default)
            try: values[name]=str(raw) if name=='model' else int(raw)
            except (ValueError,TypeError): raise ValueError('Invalid '+role+' setting: '+name) from None
        config=ClientConfig(role,key,**values)
    if config.role!=role: raise ValueError(role+' configuration required')
    if transport_factory is None:
        from .gemini import GeminiTransport
        transport_factory=GeminiTransport
    client=RoleClient(config,transport_factory(config))
    try: metadata=client.verify_model() if verify else None
    except Exception:
        client.close(); raise
    return client,metadata
