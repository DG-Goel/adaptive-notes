"""OCR failure/restart tests use fake engines; no models are initialized."""
import json
from pathlib import Path
from types import SimpleNamespace
import numpy as np
from PIL import Image
import pytest
from pdf_ocr_pipeline import PDFOCRPipeline,PageResult


def pipeline():
    obj=PDFOCRPipeline.__new__(PDFOCRPipeline)
    obj.dpi=150;obj.backend='fixture';obj.gpu_enabled=False
    obj.ocr_engine=lambda _:SimpleNamespace(txts=['10 mg'],boxes=np.array([[[0,0],[2,0],[2,2],[0,2]]]),scores=[0.91])
    return obj


@pytest.mark.parametrize('native,mode,expected,blank',[
    ('source text','exception','partial',False),('', 'exception','failed',False),
    ('','empty_white','success',True),('', 'empty_dark','partial',False),
    ('source text','empty_white','partial',False),('', 'recognized','success',False)])
def test_failure_blank_and_confidence(native,mode,expected,blank):
    obj=pipeline()
    obj._extract_native_text=lambda _:native
    obj._render_page=lambda *a:Image.new('RGB',(16,16),'black' if mode=='empty_dark' else 'white')
    if mode=='exception':
        def error(_):raise RuntimeError('controlled OCR failure')
        obj.ocr_engine=error
    elif mode.startswith('empty'):
        obj.ocr_engine=lambda _:None
    page=SimpleNamespace(close=lambda:None)
    result=obj._process_page([page],0,1,1,Path('.'))
    assert result.status==expected and result.blank_verified is blank
    assert result.native_text==native
    if mode=='exception':assert 'controlled OCR failure' in result.error
    if mode=='recognized':assert result.ocr_confidence==[0.91] and result.ocr_boxes


def test_partial_page_retried_and_old_attempt_preserved(tmp_path,monkeypatch):
    import pdf_ocr_pipeline as module
    obj=pipeline();source=tmp_path/'fixture.pdf';source.write_bytes(b'controlled')
    out=tmp_path/'output';(out/'pages').mkdir(parents=True)
    obj._setup_output_directory=lambda _:out
    pdf=SimpleNamespace(__len__=lambda:1,close=lambda:None)
    class FakePDF:
        def __len__(self):return 1
        def close(self):pass
    monkeypatch.setattr(module.pdfium,'PdfDocument',lambda _:FakePDF())
    calls=[]
    def process(**kw):
        calls.append(kw['page_number'])
        return PageResult(1,'retained source','',0,0,'partial',error='OCR failed') if len(calls)==1 else PageResult(1,'retained source','OCR source',10,0,'success')
    obj._process_page=process
    first=obj.process_pdf(source)
    assert first.completed_pages==[] and first.partial_pages==[1]
    second=obj.process_pdf(source)
    assert calls==[1,1] and second.completed_pages==[1] and second.partial_pages==[]
    obj.process_pdf(source)
    assert calls==[1,1]
    assert list((out/'pages/history').glob('*.json'))


def test_persistence_failure_never_keeps_completion_or_discards_text(tmp_path,monkeypatch):
    import pdf_ocr_pipeline as module
    obj=pipeline();source=tmp_path/'fixture.pdf';source.write_bytes(b'controlled')
    out=tmp_path/'output';(out/'pages').mkdir(parents=True)
    obj._setup_output_directory=lambda _:out
    class FakePDF:
        def __len__(self):return 1
        def close(self):pass
    monkeypatch.setattr(module.pdfium,'PdfDocument',lambda _:FakePDF())
    obj._process_page=lambda **kw:PageResult(1,'native evidence','OCR evidence',12,0,'success')
    original=obj._save_page_result
    calls=[]
    def once(result,directory):
        calls.append(1)
        if len(calls)==1:raise OSError('Controlled persistence failure')
        original(result,directory)
    obj._save_page_result=once
    manifest=obj.process_pdf(source)
    assert manifest.completed_pages==[] and manifest.failed_pages==[1]
    saved=json.loads((out/'pages/page_0001.json').read_text(encoding='utf-8'))
    assert saved['native_text']=='native evidence' and saved['ocr_text']=='OCR evidence'
    assert saved['status']=='failed'
