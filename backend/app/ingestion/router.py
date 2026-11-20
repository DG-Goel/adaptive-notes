"""Document-agnostic canonical ingestion; TXT segmentation remains unchanged."""
from hashlib import sha256
from pathlib import Path
from app.ingestion.transcript_parser import parse_transcript

ROUTER_VERSION='structured_ingestion_v2'


def ingest_document(path, *, document_id='DOC001', parser_options=None):
    path=Path(path)
    options=dict(parser_options or {})
    extension=path.suffix.lower()
    if extension=='.json' and options=={'multimodal_stage4':True}:
        from app.ingestion.multimodal_adapter import parse_multimodal
        doc=parse_multimodal(path,document_id=document_id)
    elif extension=='.txt':
        if options:
            raise ValueError('Docling parser options do not apply to TXT')
        doc=parse_transcript(path,min_segment_words=50,max_segment_words=500,detect_timestamps=True)
        parser_path=Path(__file__).with_name('transcript_parser.py')
        doc.ingestion={'version':ROUTER_VERSION,'parser':{'name':'TranscriptParser',
            'implementation_sha256':sha256(parser_path.read_bytes()).hexdigest()},'status':'success'}
    elif extension in {'.pdf','.docx','.pptx','.png','.jpg','.jpeg','.tif','.tiff','.bmp'}:
        from app.ingestion.docling_parser import DoclingParser
        doc=DoclingParser(verbose=False,**options).parse(path,document_id=document_id)
    else:
        raise ValueError(f'Unsupported ingestion format: {extension}')
    doc.ingestion['router_version']=ROUTER_VERSION
    doc.ingestion['router_sha256']=sha256(Path(__file__).read_bytes()).hexdigest()
    return doc
