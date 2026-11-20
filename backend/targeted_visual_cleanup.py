"""Bounded Stage 3.1 evidence recovery using existing Stage 3 utilities."""
import argparse
import base64
import json
from pathlib import Path
import time
import av
import numpy as np
from visual_recovery import extract,api,png,sha,save,MODEL

BASE=Path('data/transcriptions')
OUT=BASE/'video_stage3_1/run_20261110'
STAGE3=BASE/'video_stage3/run_20261110'
SOURCES=[BASE/'video_stage1/run_20261109_retry/artifacts/transcript.json',BASE/'video_stage2/final_20261109/risk_intervals.json',STAGE3/'visual_ocr_results.json',STAGE3/'frame_manifest.json']


def prepare():
    OUT.mkdir(parents=True,exist_ok=False)
    risks=json.loads(SOURCES[1].read_text(encoding='utf-8'))
    old=json.loads(SOURCES[2].read_text(encoding='utf-8'))
    manifest=dict(source_hashes={str(p):sha(p.read_bytes()) for p in SOURCES},events=[],
        windows=dict(mortgage=[5725,5780],windows_path=[3110,3152]),
        prior_failures=[r for r in old['records'] if r['status']=='failed'])
    for case,start,end,period,limit in [('mortgage',5725,5780,5,15),('windows_path',3110,3152,4,14)]:
        refs=[e for e in risks['events'] if e['start']<=end and e['end']>=start]
        m=extract('video.mp4',dict(event_id=case,start=start,end=end),OUT/case,period,limit,1600)
        m['stage2_events']=refs; manifest['events'].append(m)
        # Contact sheets are review derivatives only; originals retained unchanged.
        frames=[]
        for f in m['selected']:
            with av.open(f['filename']) as c: frame=next(c.decode(video=0))
            frames.append(frame.reformat(width=427,height=240).to_ndarray(format='rgb24'))
        sheet=np.zeros((((len(frames)+2)//3)*240,3*427,3),dtype=np.uint8)
        for i,im in enumerate(frames): sheet[(i//3)*240:(i//3+1)*240,(i%3)*427:(i%3+1)*427]=im
        (OUT/(case+'_contact.png')).write_bytes(png(av.VideoFrame.from_ndarray(sheet,format='rgb24')))
    save(OUT/'manifest.json',manifest)
    print([(m['event_id'],[(i,f['timestamp']) for i,f in enumerate(m['selected'])]) for m in manifest['events']])


def recognize():
    manifest=json.loads((OUT/'manifest.json').read_text(encoding='utf-8'))
    for p,digest in manifest['source_hashes'].items():
        if sha(Path(p).read_bytes())!=digest: raise ValueError('Historical source changed: '+p)
    model=next(m for m in api('tags')['models'] if m['name']==MODEL)
    statefile=OUT/'ocr_records.json'
    state=json.loads(statefile.read_text(encoding='utf-8')) if statefile.exists() else dict(model=model,records=[])
    # Fixed bounded crops chosen from source dimensions, never completed with transcript hints.
    jobs=[]
    for m in manifest['events']:
        for f in m['selected']:
            if m['event_id']=='mortgage':
                jobs.append(('mortgage',f,[80,200,854,440],'Text Recognition:',m['stage2_events']))
                jobs.append(('mortgage',f,[80,200,854,440],'Formula Recognition:',m['stage2_events']))
            else:
                jobs.append(('windows_path',f,[85,45,854,330],'Text Recognition:',m['stage2_events']))
    prior=manifest['prior_failures'][-1]
    jobs.append(('failed_task',prior,[90,90,840,400],'Text Recognition:',[prior['source_interval']]))
    path_event=next(m for m in manifest['events'] if m['event_id']=='windows_path')
    for f in path_event['selected']:
        if 3146 <= f['timestamp'] <= 3151:
            jobs.append(('windows_path_literal',f,[195,88,745,130],'Text Recognition:',path_event['stage2_events']))
    for index,(case,f,box,task,refs) in enumerate(jobs):
        key=sha(json.dumps([case,f['sha256'],box,task,512]).encode())
        if any(r['request_id']==key for r in state['records']): continue
        with av.open(f['filename']) as c: frame=next(c.decode(video=0))
        original=frame.to_ndarray(format='rgb24'); x1,y1,x2,y2=box
        cropped=av.VideoFrame.from_ndarray(original[y1:y2,x1:x2].copy(),format='rgb24')
        payload=png(cropped); folder=OUT/case; folder.mkdir(exist_ok=True)
        image=folder/f"crop_{f['timestamp']:.6f}_{task.split()[0]}.png"; image.write_bytes(payload)
        # Copy the original failed frame as well; historical frame never altered.
        originalfile=folder/f"original_{f['timestamp']:.6f}.png"
        originalfile.write_bytes(Path(f['filename']).read_bytes())
        r=dict(request_id=key,case=case,timestamp=f['timestamp'],original_frame=str(originalfile.resolve()),
            original_frame_sha256=sha(originalfile.read_bytes()),historical_frame=f['filename'],
            crop_filename=str(image.resolve()),crop_sha256=sha(payload),crop_coordinates=box,
            image_dimensions=[frame.width,frame.height],crop_dimensions=[cropped.width,cropped.height],
            stage2_event_ids=[e['event_id'] for e in refs],recognition_task=task,prompt=task,
            model=model,options=dict(temperature=0,num_predict=512,num_ctx=4096),
            uncertainty='Unverified OCR; backslashes and clipped characters require image comparison. No completion/correction permitted.')
        t=time.perf_counter()
        try:
            response=api('generate',dict(model=MODEL,prompt=task,images=[base64.b64encode(payload).decode()],stream=False,
                options=r['options'],keep_alive='5m'),120)
            r.update(raw_response=response,raw_output=response.get('response',''),status='success' if response.get('response','').strip() and response.get('done_reason')!='length' else 'unresolved')
        except Exception as exc: r.update(status='failed',error=str(exc))
        r['duration_seconds']=time.perf_counter()-t; state['records'].append(r); save(statefile,state)
        print(case,f['timestamp'],task,r['status'],flush=True)
        if r['status']=='failed' and 'token repeat limit' not in r.get('error',''): break


def finalize():
    manifest=json.loads((OUT/'manifest.json').read_text(encoding='utf-8'))
    state=json.loads((OUT/'ocr_records.json').read_text(encoding='utf-8'))
    audit=[]
    for path,digest in manifest['source_hashes'].items():
        if sha(Path(path).read_bytes())!=digest: audit.append('Changed source '+path)
    for r in state['records']:
        for field,key in [('original_frame','original_frame_sha256'),('crop_filename','crop_sha256')]:
            if sha(Path(r[field]).read_bytes())!=r[key]: audit.append('Changed image '+r[field])
    transcript=json.loads(SOURCES[0].read_text(encoding='utf-8'))
    lines=['# Stage 3.1 visual supplement','','All raw OCR below is unverified. No transcript merging or code completion.','',
           'Stage 2 associations on new frames refer to events overlapping the targeted search window, not necessarily the individual frame.','']
    for case in ['mortgage','windows_path','windows_path_literal','failed_task']:
        records=[r for r in state['records'] if r['case']==case]
        lines.extend(['## '+case,''])
        window=manifest['windows'].get('windows_path' if case=='windows_path_literal' else case,[8775.0663,8775.0663])
        lines.extend(['### Original spoken context',''])
        lines.extend('> '+s['text'].strip() for s in transcript['segments'] if s['start']<=window[1] and s['end']>=window[0])
        for r in records:
            lines.extend(['',f"### {r['timestamp']:.6f}s · {r['recognition_task']} · {r['status']}",'',
               f"[Original]({r['original_frame']}) · [Crop]({r['crop_filename']})",'',
               'Stage 2 context IDs: '+', '.join(r['stage2_event_ids']),'','````text',r.get('raw_output',''),'````','',r.get('error','')])
    (OUT/'visual_supplement.md').write_text('\n'.join(lines),encoding='utf-8')
    save(OUT/'audit.json',dict(issues=audit,records=len(state['records']),
         status_counts={s:sum(r['status']==s for r in state['records']) for s in ['success','unresolved','failed']},
         request_seconds=sum(r['duration_seconds'] for r in state['records']),
         competing_readings=[dict(timestamp=f['timestamp'],readings=[dict(task=r['recognition_task'],raw_output=r.get('raw_output'),crop_sha256=r['crop_sha256']) for r in state['records'] if r['timestamp']==f['timestamp']]) for m in manifest['events'] if m['event_id']=='mortgage' for f in m['selected']]))
    print('Audit issues',audit)


if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('action',choices=['prepare','recognize','finalize']); a=p.parse_args()
    {'prepare':prepare,'recognize':recognize,'finalize':finalize}[a.action]()
