"""Offline Stage 4 evidence alignment. No inference or source promotion."""
import argparse
import bisect
import hashlib
import json
from pathlib import Path
import re
import time

VERSION='1.0'
BASE=Path('data/transcriptions')
DEFAULTS=dict(speech=BASE/'video_stage1/run_20261109_retry/artifacts/transcript.json',
    risks=BASE/'video_stage2/final_20261109/risk_intervals.json',
    stage3=BASE/'video_stage3/run_20261110/visual_ocr_results.json',
    cleanup=BASE/'video_stage3_1/run_20261110/ocr_records.json',
    cleanup_manifest=BASE/'video_stage3_1/run_20261110/manifest.json')


def digest(blob): return hashlib.sha256(blob).hexdigest()
def stamp(t):
    ms=round(t*1000); h,ms=divmod(ms,3600000); m,ms=divmod(ms,60000); s,ms=divmod(ms,1000)
    return f'{h:02}:{m:02}:{s:02}.{ms:03}'


def align(segments, timestamps):
    """Half-open speech intervals. Gap evidence stays unassigned, never snapped."""
    starts=[s['start'] for s in segments]; ends=[s['end'] for s in segments]
    if any(s['end']<s['start'] or (i and s['start']<segments[i-1]['end']) for i,s in enumerate(segments)):
        raise ValueError('Speech must be ordered and nonoverlapping')
    result=[]
    for t in timestamps:
        i=bisect.bisect_right(starts,t)-1
        result.append(i if i>=0 and t<ends[i] else None)
    return result


def build(speech,risks,s3,cleanup,fingerprints,verify_images=True, *, legacy_java=True):
    duration=speech['audio_duration']; segments=speech['segments']
    if fingerprints['speech']!=risks['source_sha256']: raise ValueError('Stage 2 speech fingerprint mismatch')
    records=[]; seen_content={}; image_cache={}
    for source,data in [('stage3',s3),('cleanup',cleanup)]:
        for i,r in enumerate(data['records']):
            t=r['timestamp']
            if not 0<=t<=duration: raise ValueError('Visual timestamp outside source duration')
            raw=r.get('raw_output'); frame=r.get('original_frame',r.get('filename'))
            frame_hash=r.get('original_frame_sha256',r.get('sha256'))
            payload=r.get('crop_filename',r.get('inference_filename',frame))
            payload_hash=r.get('crop_sha256',r.get('inference_sha256',frame_hash))
            for path,expected in [(frame,frame_hash),(payload,payload_hash)]:
                if verify_images:
                    if path not in image_cache: image_cache[path]=digest(Path(path).read_bytes())
                    if image_cache[path]!=expected: raise ValueError('Image integrity mismatch: '+path)
            rid=digest(f'{fingerprints[source]}:{i}'.encode())[:20]
            task=r.get('recognition_task',r.get('task'))
            record=dict(evidence_id=rid,source_artifact=source,source_record_index=i,timestamp=t,
                timestamp_label=stamp(t),frame=frame,frame_sha256=frame_hash,image=payload,image_sha256=payload_hash,
                image_dimensions=r.get('image_dimensions',r.get('dimensions')),
                inference_dimensions=r.get('crop_dimensions',r.get('inference_dimensions')),
                crop_coordinates=r.get('crop_coordinates',r.get('crop')),recognition_task=task,
                model=r.get('model'),model_version=r.get('model_version',r.get('model')),
                raw_output=raw,execution_status=r['status'],error=r.get('error'),
                case=r.get('case'),stage2_context_event_ids=r.get('stage2_event_ids',[r['event_id']] if 'event_id' in r else []),
                content_type='VISUAL_OCR_CANDIDATE' if raw else 'NO_OCR_CONTENT',
                verification_status='UNVERIFIED',approved_for_canonical_integration=False,
                uncertainty=r.get('uncertainty','Unverified OCR candidate'),duplicate_of=None)
            if raw:
                # Exact bytes only: indentation, punctuation, slashes and meaningful edits survive.
                key=(task,raw)
                if key in seen_content: record['duplicate_of']=seen_content[key]
                else: seen_content[key]=rid
                record['content_sha256']=digest(raw.encode())
            records.append(record)
    records.sort(key=lambda r:(r['timestamp'],r['source_artifact'],r['source_record_index']))
    # Reanchor duplicates chronologically so Markdown never points forward unnecessarily.
    seen_content={}
    for r in records:
        if r['raw_output']:
            key=(r['recognition_task'],r['raw_output']); r['duplicate_of']=seen_content.get(key); seen_content.setdefault(key,r['evidence_id'])
    assignment=align(segments,[r['timestamp'] for r in records])
    for r,i in zip(records,assignment): r['speech_segment_index']=i; r['speech_segment_id']=segments[i].get('id') if i is not None else None
    conflicts=[]; groups={}
    for r in records:
        if not r['raw_output']: continue
        groups.setdefault(r['frame_sha256'],[]).append(r)
    for frame,rs in groups.items():
        lines={}
        for r in rs:
            for line in r['raw_output'].splitlines():
                if re.search(r'\bString\s+message\s*=',line): lines.setdefault(line.strip(),[]).append(r['evidence_id'])
        if len(lines)>1:
            conflicts.append(dict(kind='CONFLICTING_CHARACTERS',frame_sha256=frame,readings=[dict(literal_line=k,evidence_ids=v) for k,v in lines.items()],resolution='UNRESOLVED'))
        elif len({r['raw_output'] for r in rs})>1:
            conflicts.append(dict(kind='DIVERGENT_SAME_FRAME_READINGS',frame_sha256=frame,evidence_ids=[r['evidence_id'] for r in rs],
                resolution='UNRESOLVED; differences may reflect crop coverage, formatting or OCR errors'))
    gaps=[dict(kind='VISUAL_CONTEXT_REQUIRED',case='mortgage',start=5725,end=5780,
        reason='Source code is horizontally clipped; no complete equation established. Never reconstruct from fragments.'),
        dict(kind='UNVERIFIED_OCR_CANDIDATE',case='windows_path',start=3110,end=3152,
        reason='Doubled-backslash focused candidates and competing broad readings retained; exact characters not promoted as verified.'),
        dict(kind='UNRESOLVED_CLIPPED_CHARACTERS',case='failed_task',start=8775.0663,end=8775.0663,
        reason='Changed text-recognition retry succeeded, but monthly-interest line remains clipped; historical formula errors retained.')]
    if not legacy_java:
        gaps = []
    for c in conflicts: gaps.append(c)
    for r in records:
        r['reading_status']='AMBIGUOUS_READING' if any(c['frame_sha256']==r['frame_sha256'] for c in conflicts) else 'UNVERIFIED_CANDIDATE'
        r['possible_model_interpretation_lines']=[line for line in (r['raw_output'] or '').splitlines() if re.search(r'\b(?:the image shows|this image|appears to|the screenshot|this code shows|the diagram shows)\b',line,re.I)]
        r['interpretation_policy']='Descriptive lines are MODEL_INTERPRETATION; unclassified raw OCR remains unverified and may also contain interpretation.'
    for r in records:
        if r['execution_status']!='success': gaps.append(dict(kind='OCR_EXECUTION_UNRESOLVED',evidence_id=r['evidence_id'],timestamp=r['timestamp'],status=r['execution_status'],error=r['error']))
    high=[]
    for e in risks['events']:
        if e['priority']!='HIGH': continue
        actual=[r for r in records if e['start']<=r['timestamp']<=e['end']]
        high.append(dict(event_id=e['event_id'],start=e['start'],end=e['end'],categories=e['categories'],
            usable_candidate_evidence_ids=[r['evidence_id'] for r in actual if r['execution_status']=='success' and r['raw_output']],
            unresolved_evidence_ids=[r['evidence_id'] for r in actual if r['execution_status']!='success'],
            source_content_status='VISUAL_CONTEXT_REQUIRED' if legacy_java and e['start']<5780 and e['end']>5725 else 'UNVERIFIED_SOURCE_CONTENT',
            canonical_approval=False,linked_correction_event_ids=e.get('linked_event_ids',[])))
    timeline=[dict(kind='LITERAL_SPEECH',timestamp=s['start'],segment_index=i) for i,s in enumerate(segments)]
    timeline += [dict(kind='VISUAL_EVIDENCE',timestamp=r['timestamp'],evidence_id=r['evidence_id']) for r in records]
    timeline.sort(key=lambda x:(x['timestamp'],x['kind']))
    return dict(schema_version=VERSION,source_fingerprints=fingerprints,source_metadata={k:v for k,v in speech.items() if k!='segments'},
        speech_segments=segments,timeline=timeline,visual_evidence=records,high_risk_events=high,
        unresolved_gaps=gaps,policy=dict(speech='verbatim',visual='unverified candidates only',model_interpretations='No OCR description promoted to literal facts; raw output may contain model interpretation',
        alignment='Original timestamps; half-open speech containment, no nearest-segment snapping',deduplication='Exact task/output bytes; all occurrences retained',
        corrections='Chronological observed states retained. OCR differences alone do not establish instructor correction. No code stitching.'))


def run(output,paths=None, *, legacy_java=True):
    start=time.perf_counter(); paths=paths or DEFAULTS
    blobs={k:Path(p).read_bytes() for k,p in paths.items()}; fps={k:digest(v) for k,v in blobs.items()}; data={k:json.loads(v) for k,v in blobs.items()}
    # Confirm Stage 3 and cleanup were generated from these same historical artifacts.
    if data['stage3']['identity']['transcript_sha256']!=fps['speech'] or data['stage3']['identity']['risks_sha256']!=fps['risks']: raise ValueError('Stage 3 source mismatch')
    for path,expected in data.get('cleanup_manifest',{}).get('source_hashes',{}).items():
        if digest(Path(path).read_bytes())!=expected: raise ValueError('Cleanup historical source mismatch')
    result=build(data['speech'],data['risks'],data['stage3'],data.get('cleanup',{'records':[]}),fps,legacy_java=legacy_java)
    out=Path(output); out.mkdir(parents=True,exist_ok=False)
    evidence={r['evidence_id']:r for r in result['visual_evidence']}
    lines=['# Multimodal transcript','','Speech is verbatim. Visual content is unverified OCR, never approved code or a reconstructed equation.',
        ('Mortgage: VISUAL_CONTEXT_REQUIRED. Windows-path strings remain unverified. ' if legacy_java else '')
        +'Any prose interpretation in raw OCR is MODEL_INTERPRETATION, not literal evidence.','']
    for item in result['timeline']:
        if item['kind']=='LITERAL_SPEECH':
            s=result['speech_segments'][item['segment_index']]
            lines.extend([f"[{stamp(s['start'])}–{stamp(s['end'])}] **SPEECH**",s['text'],''])
        else:
            r=evidence[item['evidence_id']]; rid=r['evidence_id']
            lines.extend([f"<a id=\"{rid}\"></a>",f"[{r['timestamp_label']}] **UNVERIFIED VISUAL** · {r['recognition_task']} · {r['execution_status']}",
                f"[Frame]({r['frame']}) · [OCR input]({r['image']}) · evidence `{rid}`"])
            if r['reading_status']=='AMBIGUOUS_READING': lines.append('**AMBIGUOUS READING**: competing readings of this frame remain unresolved; see unresolved_source_gaps.json.')
            if r['possible_model_interpretation_lines']: lines.append('**MODEL_INTERPRETATION present**: descriptive text below is not literal source transcription.')
            if r['duplicate_of']: lines.append(f"Exact repeated reading: [earlier occurrence](#{r['duplicate_of']}).")
            elif r['raw_output']: lines.extend(['`````text',r['raw_output'],'`````'])
            else: lines.append('No OCR content returned. '+str(r['error'] or ''))
            lines.append('')
    (out/'multimodal_transcript.md').write_text('\n'.join(lines),encoding='utf-8')
    for name,value in [('multimodal_transcript.json',result),('visual_evidence_index.json',dict(source_paths={k:str(Path(p).resolve()) for k,p in paths.items()},source_fingerprints=fps,records=result['visual_evidence'])),
                       ('unresolved_source_gaps.json',dict(gaps=result['unresolved_gaps'],high_risk_events=result['high_risk_events']))]:
        (out/name).write_text(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False),encoding='utf-8')
    if any(digest(Path(paths[k]).read_bytes())!=fps[k] for k in paths): raise ValueError('Source changed during integration')
    stats=dict(speech_segments=len(result['speech_segments']),visual_records=len(evidence),
        exact_repeated_readings=sum(bool(r['duplicate_of']) for r in evidence.values()),
        high_events=len(result['high_risk_events']),high_events_with_candidates=sum(bool(e['usable_candidate_evidence_ids']) for e in result['high_risk_events']),
        visual_records_in_speech_gaps=sum(r['speech_segment_index'] is None for r in evidence.values()),
        unresolved_items=len(result['unresolved_gaps']),verified_visual_records=0,processing_seconds=time.perf_counter()-start)
    (out/'integration_report.md').write_text('# Stage 4 integration report\n\n```json\n'+json.dumps(stats,indent=2)+'\n```\n\n'
        +'No inference performed. Image hashes verified; historical artifact hashes checked before and after.\n\n'
        +'All raw readings retain source-artifact/index pointers, hashes, crop/task/model metadata and errors. No canonical content approved.\n\n'
        +'Same-frame conflicting path strings and other divergent readings remain unresolved. Different-time OCR changes are chronological candidates, not automatic corrections.\n\n'
        +('Mortgage remains VISUAL_CONTEXT_REQUIRED; Windows-path candidate remains unverified; successful changed-task retry and historical errors are retained. Clipped monthly-interest characters remain unresolved.\n\n' if legacy_java else '')
        +'Future Source Unit integration must retain modality, verification status, provenance and unresolved flags; it must not treat candidate availability as verified source completeness.\n',encoding='utf-8')
    print(json.dumps(stats,indent=2)); return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('--output',required=True)
    run(parser.parse_args().output)
