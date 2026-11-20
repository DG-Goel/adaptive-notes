"""Deterministic, transcript-only visual inspection priorities; no inference."""
from dataclasses import dataclass, asdict
import csv
import hashlib
import json
from pathlib import Path
import re
import time

VERSION = '1.0'
PATTERNS = {
 'CODE_VISUAL_DEPENDENCY': r'\b(?:type|typing|write|writing|edit|replace|change|define|create|declare)\b.{0,65}\b(?:code|method|function|variable|class|line|implementation)\b|\b(?:look at|display|show)\b.{0,35}\bcode\b|\b(?:IDE|IntelliJ|syntax|curly braces|semicolon|file path)\b',
 'FORMULA_VISUAL_DEPENDENCY': r'\b(?:formula|equation|denominator|numerator|exponent|square root|scientific notation|derivation)\b|\b(?:multiply|divide|raise|transform)\b.{0,65}\b(?:expression|power|fraction|this|following)\b',
 'SCREEN_OUTPUT_DEPENDENCY': r'\b(?:run|running|execute)\b.{0,35}\b(?:program|code|this)\b|\b(?:console output|error message|printed value)\b|\b(?:look at|see|display|print|prints|get)\b.{0,40}\b(?:output|result|error)\b',
 'DIAGRAM_VISUAL_DEPENDENCY': r'\b(?:flowchart|diagram|architecture|arrows?|connections?)\b',
 'TABLE_CHART_VISUAL_DEPENDENCY': r'\b(?:table|chart|graph|axes|plotted values|columns and rows)\b',
 'SLIDE_TEXT_DEPENDENCY': r'\b(?:slide|bullet points|displayed list|labelled|labeled|written example)\b|\b(?:first|second|third) item\b',
 'CORRECTION_OR_REVISION': r'\b(?:sorry|I meant|my mistake|instead of|correct this|fix this|replace (?:this|the|our|it|code|formula)|reorder|change this line|actually.{0,25}(?:should|meant))\b',
 'AMBIGUOUS_VISUAL_REFERENCE': r'\b(?:this one|as you can see|right here|like this|this expression|the one above|the following|here is|look at this)\b',
}
COMPILED = {k: re.compile(v, re.I) for k,v in PATTERNS.items()}
TECH = re.compile(r'\b(?:[A-Z]{2,8}|\d+\.\d+|variable|operator|semicolon|bytecode|JVM|JDK|denominator|numerator)\b|[A-Za-z]:\\\S+|\b\w+\.(?:java|py|cpp)\b')
DOMAINS = {
 'CODE_VISUAL_DEPENDENCY': re.compile(r'\b(?:code|java|python|method|function|variable|class|IDE|syntax|program|implementation)\b',re.I),
 'FORMULA_VISUAL_DEPENDENCY': re.compile(r'\b(?:math|formula|equation|expression|multiply|divide|power|fraction|mortgage|interest|denominator|root)\b',re.I),
 'DIAGRAM_VISUAL_DEPENDENCY': re.compile(r'\b(?:diagram|arrow|component|flowchart|architecture|connect)\b',re.I),
 'TABLE_CHART_VISUAL_DEPENDENCY': re.compile(r'\b(?:table|chart|graph|axis|axes|row|column|plot|trend)\b',re.I),
 'SLIDE_TEXT_DEPENDENCY': re.compile(r'\b(?:slide|bullet|definition|list|label)\b',re.I),
}
VISUAL = re.compile(r'\b(?:this|these|here|screen|shown|show|see|look|following|above|below|type|write|writing|display|now|lets|let\x27s)\b',re.I)


@dataclass(frozen=True)
class RiskConfig:
    context_seconds: float = 8
    context_segments: int = 3
    padding_before: float = 2
    padding_after: float = 3
    merge_gap: float = 2
    max_merged_seconds: float = 45
    low_word_probability: float = .3
    low_segment_logprob: float = -1
    high_threshold: float = 7
    medium_threshold: float = 4

    def __post_init__(self):
        if min(self.context_seconds,self.context_segments,self.padding_before,self.padding_after,self.merge_gap) < 0:
            raise ValueError('Windows and padding must be nonnegative')
        if self.max_merged_seconds <= 0 or not 0 <= self.low_word_probability <= 1:
            raise ValueError('Invalid duration/probability threshold')
        if self.high_threshold <= self.medium_threshold:
            raise ValueError('High threshold must exceed medium threshold')
        if not isinstance(self.context_segments,int):
            raise ValueError('context_segments must be an integer')


def clock(t):
    ms=round(t*1000); h,ms=divmod(ms,3600000); m,ms=divmod(ms,60000); s,ms=divmod(ms,1000)
    return f'{h:02}:{m:02}:{s:02}.{ms:03}'


def detect(data, fingerprint, config=None):
    started=time.perf_counter(); cfg=config or RiskConfig()
    ss=data['segments']; duration=data.get('audio_duration')
    if duration is None or duration <= 0:
        raise ValueError('Positive original audio_duration is required; no inferred duration')
    for i,s in enumerate(ss):
        if not 0 <= s['start'] <= s['end'] <= duration or (i and s['start'] < ss[i-1]['start']):
            raise ValueError('Invalid or nonchronological source timestamps')
    raw=[]
    for i,s in enumerate(ss):
        lo=max(0,i-cfg.context_segments); hi=min(len(ss),i+cfg.context_segments+1)
        neighbors=[j for j in range(lo,hi) if ss[j]['end'] >= s['start']-cfg.context_seconds and ss[j]['start'] <= s['end']+cfg.context_seconds]
        context=' '.join(ss[j]['text'] for j in neighbors)
        text=s['text']; hits=[]; cats=set(); reasons=[]
        for cat,pattern in COMPILED.items():
            for match in pattern.finditer(text):
                if cat == 'AMBIGUOUS_VISUAL_REFERENCE' and not any(p.search(context) for p in DOMAINS.values()):
                    continue
                # Domain nouns alone (e.g. a dinner table) need visual/technical support.
                if cat in ('DIAGRAM_VISUAL_DEPENDENCY','TABLE_CHART_VISUAL_DEPENDENCY','SLIDE_TEXT_DEPENDENCY') and not VISUAL.search(context):
                    continue
                cats.add(cat); hits.append(dict(category=cat,phrase=match.group(),source_segment_index=i,
                    char_start=match.start(),char_end=match.end(),method='direct_pattern'))
        if 'AMBIGUOUS_VISUAL_REFERENCE' in cats:
            for cat,p in DOMAINS.items():
                if p.search(context): cats.add(cat)
        # Join only adjacent, temporally nearby segments to detect split trigger phrases.
        if i and s['start']-ss[i-1]['end'] <= cfg.context_seconds:
            prior=ss[i-1]['text']; joined=prior+' '+text; boundary=len(prior)
            for cat,pattern in COMPILED.items():
                if cat == 'AMBIGUOUS_VISUAL_REFERENCE': continue
                for m in pattern.finditer(joined):
                    if m.start() < boundary and m.end() > boundary+1:
                        cats.add(cat); hits.append(dict(category=cat,phrase=m.group(),source_segment_indices=[i-1,i],
                            char_start=m.start(),char_end=m.end(),method='adjacent_segment_pattern'))
        technical=list(TECH.finditer(text))
        weak=[w for w in s.get('words',[]) if w.get('probability') is not None and w['probability'] < cfg.low_word_probability]
        zero=[w for w in s.get('words',[]) if w.get('start') is not None and w.get('end') == w['start']]
        logprob=s.get('avg_logprob'); poor=logprob is not None and logprob < cfg.low_segment_logprob
        if technical and (weak or zero or poor):
            cats.add('TECHNICAL_ASR_RISK')
            hits.extend(dict(category='TECHNICAL_ASR_RISK',phrase=m.group(),source_segment_index=i,char_start=m.start(),char_end=m.end(),method='technical_plus_asr_diagnostic') for m in technical)
            reasons.append('Technical content co-occurs with available low probability, zero-duration alignment or low segment logprob; not a confirmed error.')
        if not cats: continue
        explicit=bool(VISUAL.search(text)); ambiguous='AMBIGUOUS_VISUAL_REFERENCE' in cats
        score=2 + 2*explicit + min(2,len(cats)-1) + 2*('FORMULA_VISUAL_DEPENDENCY' in cats) + 2*('CORRECTION_OR_REVISION' in cats) + ('TECHNICAL_ASR_RISK' in cats)
        if ambiguous and len(cats)==1: score=2
        refs=sorted({i}|{j for h in hits for j in h.get('source_segment_indices',[])})
        begin=min(ss[j]['start'] for j in refs); end=max(ss[j]['end'] for j in refs)
        reasons.append('Matched transcript phrases with bounded nearby subject context; interval is for inspection, not confirmed visual presence.')
        raw.append(dict(detection_id=f'd{len(raw):05}',start=max(0,begin-cfg.padding_before),end=min(duration,end+cfg.padding_after),
            categories=sorted(cats),score=float(score),triggers=hits,source_segments=[dict(index=j,id=ss[j].get('id'),start=ss[j]['start'],end=ss[j]['end'],text=ss[j]['text']) for j in refs],
            contextual_evidence=[dict(index=j,id=ss[j].get('id'),start=ss[j]['start'],end=ss[j]['end'],text=ss[j]['text']) for j in neighbors],
            asr_evidence=dict(low_probability_words=weak,zero_duration_words=zero,avg_logprob=logprob),reasons=reasons))
    groups=[]
    for r in sorted(raw,key=lambda r:(r['start'],r['end'])):
        direct={h['category'] for h in r['triggers']} - {'AMBIGUOUS_VISUAL_REFERENCE','TECHNICAL_ASR_RISK'}
        if groups and r['start']<=groups[-1]['end']+cfg.merge_gap and max(groups[-1]['end'],r['end'])-groups[-1]['start']<=cfg.max_merged_seconds and direct & groups[-1]['direct']:
            g=groups[-1]; g['end']=max(g['end'],r['end']); g['categories']=sorted(set(g['categories'])|set(r['categories'])); g['members'].append(r)
        else: groups.append(dict(start=r['start'],end=r['end'],categories=r['categories'][:],members=[r],direct=direct))
    events=[]
    for g in groups:
        members=g.pop('members'); g.pop('direct'); score=max(r['score'] for r in members)
        eid=hashlib.sha256(json.dumps([fingerprint,asdict(cfg),[r['detection_id'] for r in members]],sort_keys=True).encode()).hexdigest()[:16]
        cats=g['categories']; recovery=[]
        for token,kind in [('CODE','code'),('FORMULA','formula'),('SCREEN','screen text'),('SLIDE','screen text'),('TABLE','general visual inspection'),('DIAGRAM','diagram')]:
            if any(c.startswith(token) for c in cats): recovery.append(kind)
        events.append(dict(event_id=eid,**g,start_timestamp=clock(g['start']),end_timestamp=clock(g['end']),
            score=score,priority='HIGH' if score>=cfg.high_threshold else 'MEDIUM' if score>=cfg.medium_threshold else 'LOW',
            detection_ids=[r['detection_id'] for r in members],triggers=[h for r in members for h in r['triggers']],
            source_segments=list({s['index']:s for r in members for s in r['source_segments']}.values()),
            contextual_evidence=list({s['index']:s for r in members for s in r['contextual_evidence']}.values()),
            reasons=sorted({v for r in members for v in r['reasons']}),recommended_recovery=sorted(set(recovery)) or ['general visual inspection'],
            detection_method=dict(version=VERSION,method='deterministic_contextual_heuristics'),linked_event_ids=[]))
    for a,b in zip(events,events[1:]):
        if b['start']-a['end'] <= cfg.context_seconds and 'CORRECTION_OR_REVISION' in b['categories'] and set(a['categories']) & set(b['categories']) - {'CORRECTION_OR_REVISION','AMBIGUOUS_VISUAL_REFERENCE','TECHNICAL_ASR_RISK'}:
            a['linked_event_ids'].append(b['event_id']); b['linked_event_ids'].append(a['event_id'])
    union=0; end=0
    for e in events: union+=max(0,e['end']-max(end,e['start'])); end=max(end,e['end'])
    return dict(source_sha256=fingerprint,source_metadata={k:data.get(k) for k in ('input','model','language','packages')},
        detector_version=VERSION,configuration=asdict(cfg),score_meaning='Heuristic inspection priority, not probability of error',
        raw_detections=raw,events=events,statistics=dict(video_duration=duration,transcript_segments=len(ss),raw_detections=len(raw),events=len(events),
            priority_counts={p:sum(e['priority']==p for e in events) for p in ('HIGH','MEDIUM','LOW')},
            category_counts={c:sum(c in e['categories'] for e in events) for c in list(PATTERNS)+['TECHNICAL_ASR_RISK']},
            unique_flagged_seconds=union,coverage_percent=100*union/duration,merged_detection_reduction=len(raw)-len(events),
            events_per_hour=len(events)*3600/duration,processing_seconds=time.perf_counter()-started))


def run(source, output, config=None):
    blob=Path(source).read_bytes(); result=detect(json.loads(blob),hashlib.sha256(blob).hexdigest(),config)
    target=Path(output)
    target.mkdir(parents=True,exist_ok=False)
    (target/'risk_intervals.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
    with (target/'risk_intervals.csv').open('w',encoding='utf-8',newline='') as f:
        writer=csv.writer(f); writer.writerow(['Start','End','Priority','Category','Score','Trigger Phrase','Reason'])
        for e in result['events']: writer.writerow([e['start'],e['end'],e['priority'],'; '.join(e['categories']),e['score'],' | '.join(h['phrase'] for h in e['triggers']),' '.join(e['reasons'])])
    for filename,events in [('risk_intervals.md',result['events']),('high_priority.md',[e for e in result['events'] if e['priority']=='HIGH'])]:
        lines=['# Transcript inspection intervals','',result['score_meaning'],'',f"Source SHA256: {result['source_sha256']}",'']
        for e in events:
            lines.extend([f"## {e['start_timestamp']}–{e['end_timestamp']} · {e['priority']} · {e['score']}",'',', '.join(e['categories']),''])
            lines.extend('> '+s['text'].strip() for s in e['source_segments'])
            lines.extend(['',' '.join(e['reasons']),''])
        (target/filename).write_text('\n'.join(lines),encoding='utf-8')
    (target/'statistics.json').write_text(json.dumps(result['statistics'],indent=2),encoding='utf-8')
    return result
