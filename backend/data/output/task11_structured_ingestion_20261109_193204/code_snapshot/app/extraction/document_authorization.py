"""Source-bound document authorization using production parsing and prompts."""
from pathlib import Path
from hashlib import sha256

from app.ingestion.router import ingest_document
from app.extraction.chunker import ContentChunker
from app.extraction.organization_extraction import prepare_request
from app.extraction.organization_scheduler import digest, SchedulerHold
from app.extraction.stage_a_bridge import StageAAuthorization
from app.extraction.stage_a_bridge import LocalStageARecord
from typing import Literal


class DocumentStageARecord(LocalStageARecord):
    source_id: Literal['DOCUMENT']


def request_slots(manifest, slots):
    """Primary requests rotate; recovery stays with its parent's organization."""
    slots=tuple(slots)
    if slots not in ((1,), (1,2,3,4,5)):
        raise SchedulerHold('Unsupported organization rotation')
    assigned={};index=0
    for entry in manifest['requests']:
        parent=entry.get('parent_request_id')
        if parent:
            if parent not in assigned:raise SchedulerHold('Recovery parent missing')
            assigned[entry['request_id']]=assigned[parent]
        else:
            assigned[entry['request_id']]=slots[index%len(slots)];index+=1
    return assigned


def planned_chunks(document, split_depth=0):
    from app.extraction.chunk_splitter import ChunkSplitter
    if split_depth not in (0,1,2):
        raise SchedulerHold('Unsupported split depth')
    chunks=ContentChunker().chunk(document.source_units,document.document_id)
    splitter=ChunkSplitter(max_split_depth=2)
    for _ in range(split_depth):
        chunks=[child for chunk in chunks for child in (splitter.split_chunk(chunk,document.source_units) or [chunk])]
    if [sid for c in chunks for sid in c.source_units] != [u.source_id for u in document.source_units if not u.educational_assessment.excluded]:
        raise SchedulerHold('Split plan changed source coverage or order')
    return chunks


def document_plan(path, configuration, run_id, split_depth=0, output_policy=None, *, parser_options=None):
    path = Path(path).resolve()
    before = sha256(path.read_bytes()).hexdigest()
    doc = ingest_document(path, parser_options=parser_options)
    chunks = planned_chunks(doc,split_depth)
    from app.extraction.source_context import bind_context
    binding=digest({'source_sha256':before,'source_document':doc.model_dump(mode='json')})
    def contextual(chunk):
        chunk=chunk.model_copy(update={'ingestion_binding':binding})
        return bind_context(chunk,doc.source_units) if configuration.prompt_policy in ('context_grounded_v3','canonical_grounded_v4') else chunk
    chunks=[contextual(c) for c in chunks]
    # Keep non-quotable material in the manifest inventory, never in a fake request.
    def quotable(chunk):
        return any(s not in chunk.uninterpreted_source_ids for s in chunk.source_units)
    pending_chunks=[c.model_dump(mode='json') for c in chunks if not quotable(c)]
    chunks=[c for c in chunks if quotable(c)]
    entries = []
    if output_policy not in (None,'reserve_preferred_v1'):
        raise SchedulerHold('Unsupported output budgeting policy')
    if output_policy:
        from app.extraction.output_splitting import smaller_chunks
        def fitting(chunk):
            chunk=contextual(chunk)
            try:
                _,budget=prepare_request(chunk,configuration)
            except SchedulerHold:
                budget=None
            if budget and budget.max_output_tokens>=configuration.preferred_output_tokens:
                return [chunk]
            children=smaller_chunks(chunk,doc.source_units)
            if not children:
                raise SchedulerHold(f'Unsplittable chunk {chunk.chunk_id} cannot reserve full output allowance')
            return [leaf for child in children for leaf in fitting(child)]
        chunks=[leaf for chunk in chunks for leaf in fitting(chunk)]
        offsets={u.source_id:0 for u in doc.source_units}
        texts={u.source_id:u.text or '' for u in doc.source_units}
        order={u.source_id:i for i,u in enumerate(doc.source_units)}
        last=-1
        for chunk in chunks:
            for sid in chunk.source_units:
                if not texts[sid]:
                    continue
                a,b=(chunk.source_spans or {}).get(sid,(0,len(texts[sid])))
                if a!=offsets[sid] or not a<b<=len(texts[sid]) or order[sid]<last:
                    raise SchedulerHold('Output plan lost, duplicated or reordered source text')
                offsets[sid]=b
                last=order[sid]
        if any(offsets[sid]!=len(text) for sid,text in texts.items()):
            raise SchedulerHold('Output plan omitted source text')
        def add(chunk,parent=None,recovery_depth=0):
            chunk=contextual(chunk)
            payload,_=prepare_request(chunk,configuration)
            request_id=f'{run_id}-{len(entries):04d}'
            entries.append(dict(request_id=request_id,chunk_id=chunk.chunk_id,source_ids=chunk.source_units,
                payload=payload,request_sha256=digest(payload),parent_request_id=parent,chunk=chunk.model_dump(mode='json')))
            if recovery_depth<2:
                for child in smaller_chunks(chunk,doc.source_units):
                    add(child,request_id,recovery_depth+1)
        for chunk in chunks:
            add(chunk)
    for index, chunk in enumerate(chunks):
        if output_policy:
            break
        payload, budget = prepare_request(chunk, configuration)
        entries.append(dict(request_id=f'{run_id}-{index:04d}', chunk_id=chunk.chunk_id,
                            source_ids=chunk.source_units, payload=payload, request_sha256=digest(payload),
                            chunk=chunk.model_dump(mode='json')))
    if sha256(path.read_bytes()).hexdigest() != before:
        raise SchedulerHold('Source changed while planning')
    result = dict(source_path=str(path), source_sha256=before, run_id=run_id,
                configuration=configuration.model_dump(mode='json'), requests=entries)
    result.update(manifest_version='structured_document_plan_v2',parser_options=parser_options or {},
        ingestion=doc.ingestion,source_document_sha256=digest(doc.model_dump(mode='json')),
        pending_chunks=pending_chunks,
        source_inventory=[{'source_id':u.source_id,'state':u.representation_status or ('text' if u.text else 'awaiting_interpretation'),
                           'limitations':u.interpretation_limitations,'docling_ref':u.docling_ref} for u in doc.source_units])
    if split_depth:
        result['split_depth']=split_depth
    if output_policy:
        result['output_policy']=output_policy
    return result


class DocumentStageAAuthorization(StageAAuthorization):
    """The caller pins the manifest hash in its trusted approval record."""
    def __init__(self, record, approval, manifest, approved_manifest_sha256, configuration, rotation_slots=None):
        import json
        if isinstance(record, dict):
            record = DocumentStageARecord.model_validate_json(json.dumps(record))
        super().__init__(record, approval)
        import copy
        self.manifest = copy.deepcopy(manifest)
        self.approved_manifest_sha256 = approved_manifest_sha256
        self.configuration = configuration
        self.rotation_slots=tuple(rotation_slots or ())

    def permits_registry(self,scheduler):
        if not self.rotation_slots:
            return super().permits_registry(scheduler)
        return (self.rotation_slots==(1,2,3,4,5)
                and tuple(sorted(scheduler.organizations.enabled))==self.rotation_slots)

    def expected_payload(self, request_id):
        if digest(self.manifest) != self.approved_manifest_sha256:
            raise SchedulerHold('Approved manifest changed')
        current = document_plan(self.manifest['source_path'], self.configuration, self.manifest['run_id'],self.manifest.get('split_depth',0),self.manifest.get('output_policy'),parser_options=self.manifest.get('parser_options'))
        if current != self.manifest:
            raise SchedulerHold('Source, configuration or production request changed')
        matches = [r for r in current['requests'] if r['request_id'] == request_id]
        if len(matches) != 1:
            raise SchedulerHold('Request is not uniquely authorized by document manifest')
        return matches[0]['payload']

    def local_record_type(self):
        return DocumentStageARecord

    def claim(self,scheduler,identity,admission,request_id,payload,budget):
        entry=next((e for e in self.manifest['requests'] if e['request_id']==request_id),None)
        if entry and entry.get('parent_request_id'):
            if not confirmed_truncation(scheduler,entry['parent_request_id']):
                raise SchedulerHold('Recovery request requires confirmed parent truncation')
        return super().claim(scheduler,identity,admission,request_id,payload,budget)


def confirmed_truncation(scheduler,request_id):
    import json
    with scheduler.transaction() as db:
        op=db.execute('SELECT state FROM operations WHERE id=?',(request_id,)).fetchone()
        attempt=db.execute('SELECT * FROM attempts WHERE request_id=? ORDER BY number DESC LIMIT 1',(request_id,)).fetchone()
        if not op or op['state'] not in ('failed','validation_failed') or not attempt or attempt['completed'] is None:
            return False
        if attempt['finish']=='length':
            return True
        if attempt['http_status']!=400:
            return False
        for row in db.execute("SELECT details FROM audit_events WHERE request_id=? AND event='provider_error'",(request_id,)):
            error=json.loads(row[0])
            message=error.get('message','').lower()
            # Check for explicit truncation message
            if error.get('error_code')=='json_validate_failed' and 'max completion tokens reached' in message:
                return True
            # Check for truncated JSON in failed_generation (Groq JSON mode truncation)
            if error.get('error_code')=='json_validate_failed':
                # In JSON mode, Groq returns truncated JSON in failed_generation field
                # The JSON is incomplete if it ends mid-field, mid-string, or with incomplete structure
                failed_gen_start = message.find("'failed_generation': '")
                if failed_gen_start >= 0:
                    json_start = failed_gen_start + len("'failed_generation': '")
                    json_end = message.find("'", json_start)
                    if json_end > json_start:
                        json_part = message[json_start:json_end].rstrip()
                        # Check for truncation indicators:
                        # 1. Ends mid-field like "/concept_" or incomplete paths
                        # 2. Ends with incomplete structures like ',"fields' or ',{' or ':[' 
                        # 3. Ends with backslash (mid-escape sequence) like 'i\' or 'name\'
                        # 4. Ends mid-string (not closed properly)
                        truncation_indicators = [
                            '/concept_', '/content_', '/source_', '/field',  # Incomplete JSON pointers
                            ',"fields', ',"field', ',"content', ',"concept', ',"source',  # Incomplete field names
                            '["/', '":',  ',{', ',[', '{"', '":["',  # Incomplete structures
                            '\\'  # Mid-escape (backslash at end)
                        ]
                        if any(json_part.endswith(indicator) for indicator in truncation_indicators):
                            return True
                        # Additional check: try to parse as JSON - if it fails with incomplete structure, it's truncated
                        try:
                            json.loads(json_part)
                        except json.JSONDecodeError as e:
                            # If error mentions EOF or unterminated, it's truncated
                            if any(keyword in str(e).lower() for keyword in ['unterminated', 'eof', 'expecting']):
                                return True
    return False
