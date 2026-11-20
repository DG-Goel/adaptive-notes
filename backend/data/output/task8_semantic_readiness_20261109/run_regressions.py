"""Full applicable offline suite. Main guard also protects Windows worker imports."""
import os
import socket
import pytest

for name in list(os.environ):
    if 'API_KEY' in name or 'GROQ' in name or 'GEMINI' in name:os.environ.pop(name,None)
def denied(*args,**kwargs):raise RuntimeError('Task 8 offline regression: network disabled')
socket.socket.connect=denied
socket.socket.connect_ex=denied
if __name__=='__main__':
    raise SystemExit(pytest.main(['tests','-q','--ignore=tests/test_extraction_integration.py',
        '--ignore=tests/test_ingestion.py','--ignore=tests/test_ingestion_fast.py',
        '--basetemp=data/output/task8_full_regression_verified_temp',
        '--junitxml=data/output/task8_semantic_readiness_20261109/full_regressions_verified.xml']))
