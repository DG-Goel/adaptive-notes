"""Network-denied full applicable regression launcher."""
import os
import socket
import pytest

for key in list(os.environ):
    if 'API_KEY' in key or 'GROQ' in key or 'GEMINI' in key:
        os.environ.pop(key, None)

def denied(*args, **kwargs):
    raise RuntimeError('Task 7 offline regressions: network connections disabled')

socket.socket.connect = denied
socket.socket.connect_ex = denied
if __name__ == '__main__':
    raise SystemExit(pytest.main(['tests', '-q',
        '--ignore=tests/test_extraction_integration.py',
        '--ignore=tests/test_ingestion.py', '--ignore=tests/test_ingestion_fast.py',
        '--basetemp=data/output/task7_full_offline_temp3',
        '--junitxml=data/output/task7_educational_completeness_20261109/regression_results_final.xml']))
