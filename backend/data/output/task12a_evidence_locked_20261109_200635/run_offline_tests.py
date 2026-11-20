"""Task 12A release regression runner; no physical network connections."""
import os,socket,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
os.environ['HF_HUB_OFFLINE']='1';os.environ['TRANSFORMERS_OFFLINE']='1'
def blocked(*a,**kw):raise AssertionError('Task 12A forbids network connections')
socket.socket.connect=blocked;socket.create_connection=blocked
if __name__=='__main__':
    import pytest
    class Offline:
        def pytest_collection_modifyitems(self,items):
            for item in items:
                if item.name=='test_extraction_with_real_openai':
                    item.add_marker(pytest.mark.skip(reason='Task 12A forbids live calls'))
    os.chdir(ROOT)
    raise SystemExit(pytest.main(['tests','-q','--disable-warnings','--tb=short',
        '--basetemp=data/output/task12a_tmp_full_03',
        '--junitxml='+str(Path(__file__).with_name('regression_release.xml'))],plugins=[Offline()]))
