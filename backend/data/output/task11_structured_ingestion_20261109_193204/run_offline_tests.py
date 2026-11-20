"""Reproducible Task 11 regression invocation; Windows spawn needs a real file."""
import os
from pathlib import Path
import socket
import sys

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
os.environ['HF_HUB_OFFLINE']='1'
os.environ['TRANSFORMERS_OFFLINE']='1'


def blocked(*args,**kwargs):
    raise AssertionError('Task 11 offline suite forbids network connections')


socket.socket.connect=blocked
socket.create_connection=blocked


if __name__=='__main__':
    import pytest
    class Offline:
        def pytest_collection_modifyitems(self,items):
            for item in items:
                if item.name=='test_extraction_with_real_openai':
                    item.add_marker(pytest.mark.skip(reason='Task 11 forbids live API calls'))
    os.chdir(ROOT)
    raise SystemExit(pytest.main(['tests','-q','--disable-warnings','--tb=short',
        '--basetemp=data/output/task11_test_tmp_full_04',
        '--junitxml='+str(Path(__file__).with_name('regression_final_pass.xml'))],plugins=[Offline()]))
