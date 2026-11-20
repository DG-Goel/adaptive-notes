"""Explicit feature-gated, offline Phase 2 entry point. No API clients or jobs."""


def prepare_reading(reader,source_id,limits,*,environment=None,context=None,counter=None,parts=None):
    import os
    env = os.environ if environment is None else environment
    flag = env.get('NOETRA_INFOGRAPHIC_ENGINE_ENABLED','false').strip().lower()
    if flag == 'false':
        return None
    if flag != 'true':
        raise ValueError('NOETRA_INFOGRAPHIC_ENGINE_ENABLED must be true or false')
    from .source_index import build_index
    from .token_budget import TokenBudgetManager
    from .reading_windows import ReadingSession
    return ReadingSession(build_index(reader.snapshot(source_id)),
                          TokenBudgetManager(limits,context,counter),parts)
