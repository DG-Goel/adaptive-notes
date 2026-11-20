import httpx
import pytest
from tests.test_organization_scheduler import make
from tests.test_organization_extraction import setup
from app.extraction.organization_extraction import extract_chunk


def test_full_error_body_saved_without_headers_or_usage_release(tmp_path):
    s=make(tmp_path); chunk,sources,payload,records=setup(s); saved=[]
    body={'error':{'code':'json_validate_failed','message':'fixture rejection','failed_generation':'x'*5000}}
    with pytest.raises(Exception):
        extract_chunk(s,'r',chunk,sources,'JAVA',records,
            transport=httpx.MockTransport(lambda request:httpx.Response(400,json=body)),response_sink=saved.append)
    assert saved[0]['provider_error_response']['body']==body
    assert 'headers' not in saved[0]
    with s.transaction() as db:
        row=db.execute('select * from attempts').fetchone()
        assert row['http_status']==400 and row['charged']>0
