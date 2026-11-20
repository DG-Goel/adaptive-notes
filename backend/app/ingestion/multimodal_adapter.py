"""Opt-in Stage 5 source units. Unverified OCR never becomes quotable text."""
import hashlib
import json
from pathlib import Path
from app.models.source import SourceDocument,SourceUnit


def parse_multimodal(path,document_id='DOC001'):
    path=Path(path); blob=path.read_bytes(); data=json.loads(blob)
    if data.get('schema_version')!='1.0': raise ValueError('Unsupported Stage 4 schema')
    index_path=path.with_name('visual_evidence_index.json')
    index=json.loads(index_path.read_text(encoding='utf-8'))
    for name,source in index['source_paths'].items():
        if hashlib.sha256(Path(source).read_bytes()).hexdigest()!=index['source_fingerprints'][name]:
            raise ValueError('Historical source hash mismatch: '+name)
    if index['source_fingerprints']!=data['source_fingerprints']: raise ValueError('Stage 4 lineage mismatch')
    visuals={r['evidence_id']:r for r in data['visual_evidence']}
    if len(visuals)!=len(data['visual_evidence']): raise ValueError('Duplicate visual identity')
    checked={}; originals={}
    for r in visuals.values():
        for field,key in [('frame','frame_sha256'),('image','image_sha256')]:
            p=r[field]
            if p not in checked: checked[p]=hashlib.sha256(Path(p).read_bytes()).hexdigest()
            if checked[p]!=r[key]: raise ValueError('Visual hash mismatch')
        if r['duplicate_of'] and r['duplicate_of'] not in visuals: raise ValueError('Unresolved OCR repeat')
        if r['duplicate_of'] and visuals[r['duplicate_of']]['raw_output']!=r['raw_output']: raise ValueError('OCR repeat changed content')
        name=r['source_artifact']
        if name not in originals: originals[name]=json.loads(Path(index['source_paths'][name]).read_text(encoding='utf-8'))
        source=originals[name]
        original=source['records'][r['source_record_index']]
        if original.get('raw_output')!=r['raw_output'] or original['timestamp']!=r['timestamp']: raise ValueError('Evidence reference mismatch')
    units=[]; groups=[]; current=[]; words=0
    for s in data['speech_segments']:
        count=len(s['text'].split())
        if current and words+count>250:
            groups.append(current); current=[]; words=0
        current.append(s); words+=count
        if words>=160 and s['text'].rstrip().endswith(('.','?','!')):
            groups.append(current); current=[]; words=0
    if current: groups.append(current)
    speech_owner={}
    for number,segments in enumerate(groups,1):
        sid=f'G{number:05}'; text=''; spans=[]
        for s in segments:
            if text: text+='\n'
            start=len(text); text+=s['text']; spans.append(dict(segment_id=s['id'],start=start,end=len(text)))
            speech_owner[s['id']]=sid
        units.append(SourceUnit(source_id=sid,document_id=document_id,type='speech',text=text,position=number,
            content_role='content',representation_status='text',provenance=dict(modality='speech',start=segments[0]['start'],end=segments[-1]['end'],
                original_segments=segments,segment_character_spans=spans),interpretation_limitations=['ASR speech evidence; exact code/formula unavailable unless separately verified.']))
    for i,item in enumerate(data['timeline']):
        if item['kind']=='LITERAL_SPEECH':
            continue
        else:
            r=visuals[item['evidence_id']]
            limitations=['UNVERIFIED NONQUOTABLE OCR: supplementary candidate only; never cite it as a factual/code/formula excerpt. Preserve gaps.']
            if r['duplicate_of']: limitations.append('Exact repeated reading of '+r['duplicate_of']+'; do not duplicate content.')
            elif r['raw_output']: limitations.append(json.dumps(dict(candidate_id=r['evidence_id'],timestamp=r['timestamp'],reading=r['raw_output'],state=r['reading_status']),ensure_ascii=False))
            unit=SourceUnit(source_id='V'+r['evidence_id'],document_id=document_id,type='visual_candidate',position=i,content_role='content',
                text=None,parent_id=speech_owner.get(r['speech_segment_id']),representation_status='awaiting_interpretation',provenance=dict(modality='visual',**r),interpretation_limitations=limitations)
        units.append(unit)
    units.sort(key=lambda u:u.provenance.get('start',u.provenance.get('timestamp',0)))
    for i,u in enumerate(units): u.position=i
    if len({u.source_id for u in units})!=len(units): raise ValueError('Source ID collision')
    return SourceDocument(document_id=document_id,filename=path.name,page_count=0,source_units=units,
        ingestion=dict(status='success',adapter='multimodal_source_v2_bounded_speech',original_speech_segment_count=len(data['speech_segments']),speech_passage_count=len(groups),adapter_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            stage4_sha256=hashlib.sha256(blob).hexdigest(),source_fingerprints=data['source_fingerprints'],unresolved_gaps=data['unresolved_gaps'],
            high_risk_events=data['high_risk_events'],policy='All visual units nonquotable; raw candidates retained for review, never approved facts'))
