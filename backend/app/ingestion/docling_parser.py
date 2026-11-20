"""Versioned, lossless projection of the installed Docling reference graph.

Replay does not construct a converter. Model conversion requires local artifacts;
this adapter never opts into remote enrichment or automatic model downloads.
"""
from hashlib import sha256
from importlib.metadata import version
import json
import math
from pathlib import Path
from app.ingestion.content_classifier import ContentRoleClassifier
from app.models.source import BoundingBox, SourceDocument, SourceUnit

PARSER_VERSION = 'docling_source_v2'


def canonical_json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'),allow_nan=False)


def finite_metadata(value):
    """Docling reports unavailable confidence as NaN; retain it as JSON null."""
    if isinstance(value,float) and not math.isfinite(value):
        return None
    if isinstance(value,dict):
        return {k:finite_metadata(v) for k,v in value.items()}
    if isinstance(value,list):
        return [finite_metadata(v) for v in value]
    return value


def fingerprint():
    return {'adapter':PARSER_VERSION, 'implementation_sha256':sha256(Path(__file__).read_bytes()).hexdigest(),
            'docling':version('docling'), 'docling_core':version('docling-core')}


def ref(value):
    return value.get('$ref', value.get('cref')) if isinstance(value, dict) else None


class DoclingParser:
    def __init__(self, verbose=True, enable_ocr=True, *, pdf_mode='standard',
                 model_artifacts_path=None, sidecar_dir=None):
        if pdf_mode not in ('standard', 'native'):
            raise ValueError('Unknown PDF mode')
        self.verbose, self.enable_ocr, self.pdf_mode = verbose, enable_ocr, pdf_mode
        self.model_artifacts_path = Path(model_artifacts_path) if model_artifacts_path else None
        self.sidecar_dir = Path(sidecar_dir) if sidecar_dir else Path(__file__).resolve().parents[2]/'data/output/structured_ingestion_v2'
        self.converter = None

    def _converter(self, path):
        if self.converter is not None:
            return self.converter
        from docling.datamodel.base_models import InputFormat
        from docling.document_converter import DocumentConverter, PdfFormatOption, NativePdfFormatOption, ImageFormatOption
        from docling.datamodel.pipeline_options import PdfPipelineOptions, NativePdfPipelineOptions, RapidOcrOptions
        from docling.datamodel.backend_options import PdfBackendOptions
        options = {}
        if path.suffix.lower() in ('.pdf','.png','.jpg','.jpeg','.tif','.tiff','.bmp'):
            if self.pdf_mode=='native':
                if path.suffix.lower()!='.pdf':
                    raise ValueError('Native PDF mode cannot perform image OCR')
                options[InputFormat.PDF] = NativePdfFormatOption(
                    pipeline_options=NativePdfPipelineOptions(generate_page_images=False),
                    backend_options=PdfBackendOptions(include_bitmap_images=True))
            else:
                if not self.model_artifacts_path or not self.model_artifacts_path.is_dir():
                    raise RuntimeError('Offline conversion requires an existing model_artifacts_path; no models downloaded')
                pipeline = PdfPipelineOptions(artifacts_path=self.model_artifacts_path,
                    do_ocr=self.enable_ocr, ocr_options=RapidOcrOptions(), enable_remote_services=False)
                options[InputFormat.PDF] = PdfFormatOption(pipeline_options=pipeline)
                options[InputFormat.IMAGE] = ImageFormatOption(pipeline_options=pipeline)
        allowed = [InputFormat.PDF,InputFormat.IMAGE] if options else [InputFormat.DOCX,InputFormat.PPTX]
        self.converter = DocumentConverter(allowed_formats=allowed,format_options=options)
        return self.converter

    def parse(self, file_path, document_id='DOC001'):
        path=Path(file_path)
        if not path.is_file():
            raise FileNotFoundError(path)
        source_hash=sha256(path.read_bytes()).hexdigest()
        result=self._converter(path).convert(str(path))
        status=str(getattr(result.status,'value',result.status))
        errors=[e.model_dump(mode='json') if hasattr(e,'model_dump') else str(e) for e in getattr(result,'errors',[])]
        if status not in ('success','partial_success'):
            raise ValueError(f'Docling conversion failed: {status}: {errors}')
        raw=result.document.model_dump(mode='json')
        if sha256(path.read_bytes()).hexdigest()!=source_hash:
            raise ValueError('Source changed during conversion')
        document=self.project_document(raw,document_id=document_id,filename=path.name,
            conversion_status=status,conversion_errors=errors,source_sha256=source_hash)
        document.ingestion['conversion_mode']=self.pdf_mode if path.suffix.lower()=='.pdf' else 'native_office_or_image'
        if path.suffix.lower()=='.pdf' and self.pdf_mode=='native':
            limitation='Native PDF conversion has no OCR, layout, heading or table reconstruction'
            document.ingestion['limitations']=[limitation]
            for unit in document.source_units:
                unit.interpretation_limitations.append(limitation)
        confidence=getattr(result,'confidence',None)
        if confidence is not None:
            document.ingestion['confidence']=finite_metadata(confidence.model_dump(mode='json'))
        self.save_sidecar(raw,document,self.sidecar_dir)
        return document

    @staticmethod
    def project_document(raw, *, document_id='DOC001',filename=None,conversion_status='replayed',
                         conversion_errors=None,source_sha256=None):
        """DFS includes picture children, groups, furniture and captions, once per ref.

        Top-level historical S IDs retain their element associations. Additional
        refs receive deterministic N IDs; reading-order position is independent.
        """
        if hasattr(raw,'model_dump'):
            raw=raw.model_dump(mode='json')
        nodes={}
        for value in raw.values():
            if isinstance(value,list):
                for node in value:
                    if isinstance(node,dict) and node.get('self_ref'):
                        key=node['self_ref']
                        if key in nodes:
                            raise ValueError(f'Duplicate Docling reference: {key}')
                        nodes[key]=node
        roots=raw.get('body',{}).get('children',[])
        identities={ref(r):f'S{i:04d}' for i,r in enumerate(roots,1)}
        errors=list(conversion_errors or [])
        ordered,seen,active=[],set(),set()
        relationships=[]

        def walk(key,relationship='children',owner=None):
            if not key:
                errors.append({'kind':'invalid_reference','owner':owner})
                return
            if owner:
                relationships.append({'from':owner,'to':key,'relationship':relationship})
            if key in active:
                errors.append({'kind':'cyclic_reference','ref':key})
                return
            if key in seen:
                return
            seen.add(key)
            node=nodes.get(key)
            if node is None:
                errors.append({'kind':'item_resolution_failed','ref':key,'owner':owner})
                node={'self_ref':key,'label':'failed','parent':{'$ref':owner} if owner else None}
            ordered.append(node)
            active.add(key)
            for relation in ('children','captions','footnotes','references'):
                for child in node.get(relation,[]) or []:
                    walk(ref(child),relation,key)
            active.remove(key)

        for root in roots:
            walk(ref(root))
        for root in raw.get('furniture',{}).get('children',[]):
            walk(ref(root))
        for key in nodes:
            if key not in seen:
                errors.append({'kind':'orphan_element_recovered','ref':key})
                walk(key)
        represented_pages={p.get('page_no') for node in ordered for p in node.get('prov',[]) or []}
        for page_number in raw.get('pages',{}):
            number=int(page_number)
            if number not in represented_pages:
                key=f'#/pages/{page_number}'
                errors.append({'kind':'unrepresented_page','page':number,'blank_verified':False})
                ordered.append({'self_ref':key,'label':'unresolved_page','prov':[{'page_no':number}]})
        for node in ordered:
            key=node['self_ref']
            identities.setdefault(key,'N'+sha256(key.encode()).hexdigest()[:16])
        if len(set(identities.values()))!=len(identities):
            raise ValueError('Ambiguous canonical identity mapping')
        units,headings=[],[]
        classifier=ContentRoleClassifier()
        labels={'section_header':'heading','title':'heading','list_item':'list','caption':'caption',
                'formula':'formula','code':'code','table':'table','picture':'picture','failed':'unknown',
                'unresolved_page':'unknown'}
        for node in ordered:
            key,label=node['self_ref'],node.get('label','unknown')
            kind=labels.get(label,'group' if key.startswith('#/groups/') else 'paragraph')
            text=node.get('text')
            state='text' if isinstance(text,str) and text.strip() else None
            limitations=[]
            data=node.get('data') if kind=='table' else None
            chart=(node.get('meta') or {}).get('tabular_chart')
            if not chart:
                chart=next((a for a in node.get('annotations',[]) if a.get('kind')=='tabular_chart_data'),None)
            if data and data.get('table_cells'):
                text,state=canonical_json({'table':data}),'structured'
            elif chart and chart.get('chart_data'):
                text,state=canonical_json({'native_chart':chart}),'structured'
                limitations.append('Chart data retained; other visual relationships are not interpreted')
            script=(node.get('formatting') or {}).get('script')
            if state=='text' and script and script not in ('baseline','normal'):
                # Preserve script semantics explicitly, with original characters in metadata.
                text,state=canonical_json({'text':text,'script':script}),'structured'
            if state is None:
                text=None
                state=('failed' if label=='failed' else 'structural' if kind=='group' else
                       'awaiting_interpretation' if kind in ('picture','table','formula','unknown') else 'empty')
                if state in ('failed','awaiting_interpretation'):
                    limitations.append('No quotable source representation; interpretation or recovery required')
            if kind=='formula':
                limitations.append('Recognized expression; mathematical correctness is not independently verified')
            prov=node.get('prov') or []
            first=prov[0] if prov else {}
            box=first.get('bbox')
            bbox=BoundingBox(left=box['l'],top=box['t'],right=box['r'],bottom=box['b']) if box else None
            if kind=='heading' and text:
                level=node.get('level',0 if label=='title' else 1)
                headings=[(n,r,t) for n,r,t in headings if n<level]
                headings.append((level,key,text))
            metadata={'parser_version':PARSER_VERSION,'label':label,'docling_provenance':prov,
                'parent_ref':ref(node.get('parent')),'children_refs':[ref(c) for c in node.get('children',[])],
                'caption_refs':[ref(c) for c in node.get('captions',[])],
                'heading_ancestry':[{'level':l,'ref':r,'source_id':identities[r],'text':t} for l,r,t in headings],
                'formatting':node.get('formatting'),'code_language':node.get('code_language'),
                'content_layer':node.get('content_layer'),'heading_level':node.get('level'),
                'annotations':node.get('annotations',[]),'meta':node.get('meta'),
                'representation':state,'original_text':node.get('text')}
            if data is not None:
                metadata['table_data']=data
            unit=SourceUnit(source_id=identities[key],document_id=document_id,docling_ref=key,
                position=len(units)+1,type=kind,text=text,representation_status=state,
                page=first.get('page_no'),bbox=bbox,section=' / '.join(t for _,_,t in headings) or None,
                parent_id=identities.get(ref(node.get('parent'))),provenance=metadata,
                interpretation_limitations=limitations)
            unit.content_role=classifier.classify(unit)
            units.append(unit)
        incomplete=conversion_status not in ('success','replayed') or bool(errors)
        if incomplete:
            for unit in units:
                unit.interpretation_limitations.append('Document conversion is incomplete; missing source content must not be reconstructed')
        return SourceDocument(document_id=document_id,filename=filename or (raw.get('origin') or {}).get('filename',raw.get('name','document')),
            page_count=len(raw.get('pages',{})),source_units=units,
            ingestion={'version':PARSER_VERSION,'parser':fingerprint(),'source_sha256':source_sha256,
                'structured_sha256':sha256(canonical_json(raw).encode()).hexdigest(),
                'conversion_status':conversion_status,'status':'incomplete' if incomplete else 'success',
                'errors':errors,'element_to_source':{u.docling_ref:u.source_id for u in units},
                'relationships':relationships,
                'unresolved_source_ids':[u.source_id for u in units if u.representation_status in ('awaiting_interpretation','failed','incomplete')]})

    @staticmethod
    def save_sidecar(raw,document,directory):
        """Content-addressed immutable structured document and canonical mapping."""
        projected=document.model_dump(mode='json')
        projected['ingestion'].pop('sidecar',None)
        payload={'version':PARSER_VERSION,'document':raw,
            'ingestion':{k:v for k,v in document.ingestion.items() if k!='sidecar'},
            'source_document':projected}
        encoded=canonical_json(payload).encode('utf-8')
        path=Path(directory)/(sha256(encoded).hexdigest()+'.json')
        path.parent.mkdir(parents=True,exist_ok=True)
        try:
            with path.open('xb') as f:
                f.write(encoded)
        except FileExistsError:
            if path.read_bytes()!=encoded:
                raise ValueError('Structured sidecar collision')
        document.ingestion['sidecar']={'path':str(path.resolve()),'sha256':sha256(encoded).hexdigest()}
        return path
