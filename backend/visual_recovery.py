"""Stage 3 local, sequential GLM-OCR evidence pipeline. Never rewrites sources."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import time
import urllib.request
import urllib.error
import subprocess
import numpy as np
import av

MODEL='glm-ocr:q8_0'


def sha(blob): return hashlib.sha256(blob).hexdigest()


def save(path, data):
    tmp=path.with_suffix(path.suffix+'.tmp')
    tmp.write_text(json.dumps(data,indent=2,ensure_ascii=False),encoding='utf-8')
    tmp.replace(path)


def api(route, data=None, timeout=30):
    req=urllib.request.Request('http://127.0.0.1:11434/api/'+route,
        data=json.dumps(data).encode() if data is not None else None,
        headers={'Content-Type':'application/json'})
    try:
        with urllib.request.urlopen(req,timeout=timeout) as r: return json.load(r)
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f'Ollama HTTP {exc.code}: {exc.read().decode(errors="replace")}') from exc


def tasks(event):
    cats=event['categories']; result=['Text Recognition:']
    if 'FORMULA_VISUAL_DEPENDENCY' in cats: result.append('Formula Recognition:')
    if 'TABLE_CHART_VISUAL_DEPENDENCY' in cats: result.append('Table Recognition:')
    return result


def schedule(start,end,period):
    return sorted(set([start,(start+end)/2,max(start,end-.1)]+list(np.arange(start,end,period))))


def png(frame):
    codec=av.CodecContext.create('png','w'); codec.width=frame.width; codec.height=frame.height
    codec.pix_fmt='rgb24'
    return b''.join(bytes(p) for p in list(codec.encode(frame.reformat(format='rgb24')))+list(codec.encode(None)))


def extract(video,event,folder,period,limit,resolution):
    folder.mkdir(parents=True,exist_ok=True); candidates=[]; retained=[]; seen={}; last=None
    with av.open(str(video)) as c:
        stream=c.streams.video[0]
        for requested in schedule(event['start'],event['end'],period):
            c.seek(int(requested/stream.time_base),stream=stream,backward=True)
            frame=next((f for f in c.decode(stream) if f.time is not None and f.time>=requested),None)
            if frame is None or frame.time>event['end']:
                candidates.append(dict(requested=float(requested),decision='no_frame_inside_interval')); continue
            pixels=frame.to_ndarray(format='rgb24'); identity=sha(pixels.tobytes())
            gray=pixels.astype(np.float32).mean(axis=2)
            # Local high-frequency differences expose small code edits hidden by whole-screen averages.
            edges=np.abs(np.diff(gray,axis=1)); tile=edges[::4,::4]
            changed=float(np.mean(np.abs(tile-last)>12)) if last is not None and last.shape==tile.shape else None
            sharpness=float(np.var(np.diff(gray,axis=1)))
            item=dict(timestamp=float(frame.time),requested=float(requested),pixel_sha256=identity,
                dimensions=[frame.width,frame.height],sharpness=sharpness,text_edge_change_fraction=changed,crop=None)
            if identity in seen:
                item.update(decision='exact_pixel_duplicate',duplicate_of=seen[identity]); candidates.append(item); continue
            name=f'{frame.time:.6f}.png'; original=folder/name; original.write_bytes(png(frame))
            ratio=min(1,resolution/max(frame.width,frame.height))
            inference=frame.reformat(width=max(1,round(frame.width*ratio)),height=max(1,round(frame.height*ratio)))
            image=folder/(name+'.inference.png'); image.write_bytes(png(inference))
            item.update(filename=str(original),sha256=sha(original.read_bytes()),inference_filename=str(image),
                        inference_sha256=sha(image.read_bytes()),inference_dimensions=[inference.width,inference.height],decision='retained')
            seen[identity]=str(original); last=tile; retained.append(item); candidates.append(item)
    # Keep chronological endpoints and strongest local changes within explicit OCR budget.
    if len(retained)>limit:
        selected={0,len(retained)-1,len(retained)//2}
        selected.update(sorted(range(len(retained)),key=lambda i:retained[i]['text_edge_change_fraction'] or 0,reverse=True)[:max(0,limit-3)])
        for i,item in enumerate(retained):
            if i not in selected: item['decision']='preserved_not_ocr_resource_limit'
        retained=[x for x in retained if x['decision']=='retained']
    return dict(event_id=event['event_id'],candidates=candidates,selected=retained,
                limitations=['Exact-pixel deduplication only; blur scored but frames not discarded on blur alone.',
                            'Sampling can miss changes between candidates; resource-capped frames remain on disk.'])


def reports(out,state,manifest,events,transcript):
    lines=['# Visual transcript supplement','', 'OCR candidates are unverified source evidence, not approved educational knowledge.','']
    complete=0
    for e in events:
        records=[r for r in state['records'] if r['event_id']==e['event_id']]
        frames=next((m['selected'] for m in manifest['events'] if m['event_id']==e['event_id']),[])
        if frames and all(any(r['inference_sha256']==f['inference_sha256'] and r['task']==task and r['status']=='success' for r in records) for f in frames for task in tasks(e)): complete+=1
        lines.extend([f"## {e['start_timestamp']}–{e['end_timestamp']} · {e['event_id']}",'',', '.join(e['categories']),'','### Original speech',''])
        for s in transcript['segments']:
            if s['end']>=e['start'] and s['start']<=e['end']: lines.append('> '+s['text'].strip())
        lines.extend(['','Risk: '+' '.join(e['reasons']),''])
        for r in records:
            lines.extend([f"### Frame {r['timestamp']:.6f}s · {r['task']} · {r['status']}",'',f"[Source image]({r['filename']})",'',
                '````text',r.get('raw_output',''),'````','',str(r.get('error') or ''),''])
        if not records: lines.append('NOT_RUN: no OCR requests completed for this event.')
        lines.extend(['','Distinct frames and outputs remain chronological; no snippets are combined or corrected.',''])
    content='\n'.join(lines)
    (out/'visual_transcript.md').write_text(content,encoding='utf-8')
    (out/'high_priority_ocr_report.md').write_text(content,encoding='utf-8')
    times=[r['duration_seconds'] for r in state['records'] if not r.get('reused_from')]
    report=dict(high_intervals=len(events),successfully_processed=complete,failed_or_unresolved=len(events)-complete,
        screenshots_examined=sum(len(m['candidates']) for m in manifest['events']),screenshots_retained=sum(len(m['selected']) for m in manifest['events']),
        ocr_requests=len(times),inference_seconds=sum(times),average_request_seconds=sum(times)/len(times) if times else None,
        model=MODEL,model_info=state.get('model_info'),ollama_version=state.get('ollama_version'),
        sampled_peak_whole_gpu_mib=max((int(r['gpu_memory_sample'].split(',')[0]) for r in state['records'] if r.get('gpu_memory_sample')),default=None),
        unique_images_requested=len({r['inference_sha256'] for r in state['records'] if not r.get('reused_from')}),
        blocker=state.get('blocker'),gpu_observations=state.get('gpu_observations',[]),
        limitations=['OCR is not independently verified. Empty/truncated output unresolved.',
          'No formula reconstructed; completeness requires visual inspection.',
          'No figure descriptions requested; any generated descriptions are MODEL_INTERPRETATION, not literal OCR.'])
    (out/'execution_report.md').write_text('# Execution report\n\n```json\n'+json.dumps(report,indent=2)+'\n```',encoding='utf-8')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--video',default='video.mp4'); p.add_argument('--transcript',required=True); p.add_argument('--risks',required=True); p.add_argument('--output',required=True)
    p.add_argument('--period',type=float,default=3); p.add_argument('--max-frames',type=int,default=12)
    p.add_argument('--resolution',type=int,default=1600); p.add_argument('--timeout',type=int,default=180); p.add_argument('--max-tokens',type=int,default=2048)
    p.add_argument('--chronological', action='store_true', help='Process this video in timestamp order')
    a=p.parse_args()
    if a.period<=0 or a.max_frames<3 or a.resolution<64: p.error('Invalid frame limits')
    blob=Path(a.transcript).read_bytes(); transcript=json.loads(blob); rb=Path(a.risks).read_bytes(); risks=json.loads(rb)
    if sha(blob)!=risks['source_sha256']: raise ValueError('Transcript fingerprint mismatch')
    events=[e for e in risks['events'] if e['priority']=='HIGH']
    out=Path(a.output).resolve(); out.mkdir(parents=True,exist_ok=True)
    config=vars(a); config['video_identity']=dict(size=Path(a.video).stat().st_size,mtime_ns=Path(a.video).stat().st_mtime_ns)
    identity=dict(transcript_sha256=sha(blob),risks_sha256=sha(rb),configuration=config)
    state_path=out/'visual_ocr_results.json'; manifest_path=out/'frame_manifest.json'
    state=json.loads(state_path.read_text(encoding='utf-8')) if state_path.exists() else dict(identity=identity,records=[],gpu_observations=[])
    if state['identity']!=identity: raise ValueError('Resume identity/config mismatch')
    state['high_priority_events']=events
    manifest=json.loads(manifest_path.read_text(encoding='utf-8')) if manifest_path.exists() else dict(identity=identity,events=[])
    try:
        state['ollama_version']=api('version')
        tags=api('tags')['models']; model=next((m for m in tags if m['name']==MODEL),None)
        if model is None: raise RuntimeError('Missing glm-ocr:q8_0. Explicit permission required before: ollama pull glm-ocr:q8_0')
        state['model_info']=model
        if any(m['name']!=MODEL for m in api('ps')['models']): raise RuntimeError('Another heavy Ollama model is loaded; unload it before proceeding')
        # Smoke test code and mortgage events first, then every remaining HIGH event.
        mortgage=[e for e in events if e['start']<=5760 and e['end']>=5745]
        code=[e for e in events if 'CODE_VISUAL_DEPENDENCY' in e['categories']]
        order=sorted(events,key=lambda e:e['start']) if a.chronological else list({e['event_id']:e for e in code[:1]+mortgage+events}.values())
        cache={}
        for r in state['records']:
            if r['status']=='success': cache[(r['inference_sha256'],r['task'])]=r
        for e in order:
            m=next((m for m in manifest['events'] if m['event_id']==e['event_id']),None)
            if m is None:
                m=extract(a.video,e,out/e['event_id'],a.period,a.max_frames,a.resolution)
                manifest['events'].append(m); save(manifest_path,manifest)
            for frame in m['selected']:
                for task in tasks(e):
                    key=(frame['inference_sha256'],task)
                    if any(r['event_id']==e['event_id'] and (r['inference_sha256'],r['task'])==key and r['status']=='success' for r in state['records']): continue
                    if any(r['event_id']==e['event_id'] and (r['inference_sha256'],r['task'])==key and 'token repeat limit reached' in r.get('error','') for r in state['records']): continue
                    record=dict(**frame,event_id=e['event_id'],source_interval=e,task=task,model=MODEL,model_version=model,
                        uncertainty='Unverified OCR candidate; generated descriptions must be treated as MODEL_INTERPRETATION.',status='pending')
                    t=time.perf_counter()
                    if key in cache:
                        record.update(raw_output=cache[key]['raw_output'],status='success',reused_from=cache[key]['event_id'])
                    else:
                        try:
                            result=api('generate',dict(model=MODEL,prompt=task,images=[base64.b64encode(Path(frame['inference_filename']).read_bytes()).decode()],
                                stream=False,keep_alive='5m',options=dict(temperature=0,num_predict=a.max_tokens,num_ctx=4096)),a.timeout)
                            text=result.get('response',''); record.update(raw_output=text,raw_response=result,
                                status='success' if text.strip() and result.get('done_reason')!='length' else 'unresolved_empty_or_truncated')
                            state['gpu_observations'].append(api('ps'))
                            gpu=subprocess.run(['nvidia-smi','--query-gpu=memory.used,memory.total','--format=csv,noheader,nounits'],capture_output=True,text=True)
                            record['gpu_memory_sample']=gpu.stdout.strip()
                        except Exception as exc:
                            record.update(status='failed',error=f'{type(exc).__name__}: {exc}')
                    record['duration_seconds']=time.perf_counter()-t; state['records'].append(record)
                    save(state_path,state); reports(out,state,manifest,events,transcript)
                    if record['status']=='success': cache[key]=record
                    if record['status']=='failed' and 'token repeat limit reached' not in record.get('error',''):
                        raise RuntimeError(record['error'])
        state.pop('blocker',None)
    except Exception as exc:
        state['blocker']=f'{type(exc).__name__}: {exc}'; print(state['blocker'],flush=True)
    finally:
        save(state_path,state); save(manifest_path,manifest); reports(out,state,manifest,events,transcript)
    return 1 if state.get('blocker') else 0


if __name__=='__main__': raise SystemExit(main())
