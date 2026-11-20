"""Structural and acoustic checks; no second ASR engine or video-frame decoding."""
import json
from pathlib import Path
import re
import sys
import wave
import numpy as np

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from faster_whisper.audio import decode_audio

HERE = Path(__file__).resolve().parent
if len(sys.argv) > 1:
    HERE = HERE.parent / sys.argv[1]
data = json.loads((HERE / 'artifacts/transcript.json').read_text(encoding='utf-8'))
segments = data['segments']
audio = decode_audio(str(ROOT / 'video.mp4'), sampling_rate=16000)
words = [w for s in segments for w in s['words']]
duration = len(audio)/16000
invalid = [w for w in words if w['start'] is not None and w['end'] is not None
           and (w['start'] < 0 or w['end'] < w['start'] or w['end'] > duration+.1)]
norm = lambda s: re.sub(r'\W+', ' ', s.lower()).strip()
repeats = [{'index':i,'start':s['start'],'text':s['text']} for i,s in enumerate(segments)
           if i and norm(s['text']) == norm(segments[i-1]['text'])]
gaps = [{'start':a['end'],'end':b['start'],'duration':b['start']-a['end']}
        for a,b in zip(segments,segments[1:]) if b['start']-a['end'] > 10]
for gap in gaps:
    clip = audio[int(gap['start']*16000):int(gap['end']*16000)]
    gap['rms'] = float(np.sqrt(np.mean(clip**2)))
    frame_count = len(clip)//320
    levels = np.sqrt(np.mean(clip[:frame_count*320].reshape(-1,320)**2,axis=1))
    gap['fraction_20ms_frames_rms_below_0_003'] = float(np.mean(levels < .003))
clips = []
for start,end in [(0,15),(4490,4510),(5870,5908),(9030,9045)]:
    path = HERE / f'audio_review_{start}_{end}.wav'
    with wave.open(str(path),'wb') as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(16000)
        out.writeframes((np.clip(audio[start*16000:end*16000],-1,1)*32767).astype('<i2').tobytes())
    clips.append(dict(start=start,end=end,path=str(path)))
chosen = sorted(set([0,1,2,len(segments)//4,len(segments)//2,
                      3*len(segments)//4,len(segments)-2,len(segments)-1]))
representatives=[]
for i in chosen:
    s=segments[i]
    clip=audio[int(s['start']*16000):int(s['end']*16000)]
    representatives.append(dict(index=i, **s, rms=float(np.sqrt(np.mean(clip**2))) if len(clip) else None))
report = dict(audio_decoded_duration=duration, invalid_word_intervals=invalid,
              audio_review_clips=clips,
              adjacent_identical_segments=repeats, gaps_over_10_seconds=gaps,
              zero_duration_words=sum(w['start']==w['end'] for w in words),
              low_probability_words=[w for w in words if w['probability'] is not None and w['probability']<.3],
              representative_segments=representatives,
              alignment_limit='Bounds and acoustic energy only; no manual listening/reference-word alignment established.')
(HERE/'quality_checks.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k not in ['representative_segments','low_probability_words']},indent=2))
for s in representatives:
    print(f"{s['index']}: [{s['start']:.3f}-{s['end']:.3f}] RMS={s['rms']} {s['text']}")
print('Low probability words:',len(report['low_probability_words']))
