"""Applicable offline suite; deny all network and guard Windows worker imports."""
import os,socket,pytest
for key in list(os.environ):
    if 'API_KEY' in key or 'GROQ' in key or 'GEMINI' in key:os.environ.pop(key,None)
def denied(*args,**kwargs):raise RuntimeError('Task 9 offline regressions: network denied')
socket.socket.connect=denied;socket.socket.connect_ex=denied
if __name__=='__main__':
    raise SystemExit(pytest.main(['tests','-q','--ignore=tests/test_extraction_integration.py',
        '--ignore=tests/test_ingestion.py','--ignore=tests/test_ingestion_fast.py',
        '--basetemp=data/output/task9_full_regression_final_temp',
        '--junitxml=data/output/task9_review_pilot_20261109/full_regressions_final.xml']))
