"""Immutable Phase 4 inputs, conservative capacity and lexical discovery."""
from dataclasses import dataclass,asdict
import json
import math
import re
from .source_index import digest
from .planner_integrity import validate_checkpoint
from .segmentation_budget import recommendation,DEFAULT_CAPACITY


def canonical(value):
    return json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':'))


@dataclass(frozen=True)
class OptimizationConfig:
    generation_input_tokens: int = 24000
    generation_shared_tokens: int = 32000
    category_prompt_tokens: int = 1500
    five_schema_tokens: int = 3000
    generation_output_tokens: int = 6000
    supporting_output_tokens: int = 1500
    thinking_tokens: int = 0
    serialization_tokens: int = 512
    safety_ratio: float = .10
    generation_limits_verified: bool = False
    capacity_items: tuple = (('A',20),('B',15),('C',15),('N',20))
    response_attempts: int = 2
    max_rounds: int = 2
    max_requests: int = 100
    overlap_segments: int = 2

    def __post_init__(self):
        for name,value in asdict(self).items():
            if name in {'generation_limits_verified','capacity_items','safety_ratio'}: continue
            if type(value) is not int or value<0: raise ValueError('Invalid optimizer setting: '+name)
        if not 0<=self.safety_ratio<1 or not all(getattr(self,n)>0 for n in ('generation_input_tokens','generation_shared_tokens','response_attempts','max_rounds','max_requests','overlap_segments')):
            raise ValueError('Invalid optimizer bounds')
        if set(dict(self.capacity_items))!={'A','B','C','N'} or any(type(v) is not int or v<=0 for _,v in self.capacity_items):
            raise ValueError('Invalid category capacity')

    def capacity(self,index,first,last):
        blocks=index.units[first:last+1]
        source_cost=len(canonical([dict(id=b.id,text=b.text,references=b.references) for b in blocks]).encode())
        input_cost=source_cost+self.category_prompt_tokens+self.five_schema_tokens+self.serialization_tokens
        total=input_cost+self.generation_output_tokens+self.supporting_output_tokens+self.thinking_tokens
        fits=input_cost<=math.floor(self.generation_input_tokens*(1-self.safety_ratio)) and total<=math.floor(self.generation_shared_tokens*(1-self.safety_ratio))
        return dict(fits=fits,status=('verified_limits' if self.generation_limits_verified else 'provisional_limits') if fits else 'overflow',
                    estimated_input_tokens=input_cost,estimated_total_tokens=total,token_kind='estimated')


def validated_input(job):
    if job.status!='complete' or not job.reading.ledger()['complete']: raise ValueError('Completed Phase 3 segmentation required')
    job.reading.index.validate(); job.reading._validate_state(job.reading.state)
    value=job._payload()
    validate_checkpoint(job,value,None)
    return canonical(value['manifest'])


def initial_groups(manifest,index,config):
    groups=[]
    for segment in manifest:
        row=dict(segment)
        row.update(constituents=[segment['id']],merge_history=[],supplementary_links=[],
                   continuation_groups=[segment['continuation_group']] if segment['continuation_group'] else [])
        row['id']=optimized_id(index,row['constituents'])
        row['downstream_context']=config.capacity(index,row['start_position'],row['end_position'])
        groups.append(row)
    by_start={g['start']:g['id'] for g in groups}
    for g in groups:
        if g.get('supports_start') is not None:
            g['supplementary_links']=[dict(target=by_start[g['supports_start']],reason='phase3_support_link',semantically_represented=False)]
    return groups


def optimized_id(index,constituents):
    return 'O'+digest(canonical([index.fingerprint,constituents]).encode())[:24]


def compact(groups,index):
    result=[]
    for i,g in enumerate(groups):
        paths=list(dict.fromkeys(tuple(b.section_path) for b in index.units[g['start_position']:g['end_position']+1]))
        anchors=[]
        for word in re.findall(r'\w+',index.units[g['start_position']].text):
            if len(word)>3 and word.lower() not in anchors: anchors.append(word.lower())
            if len(anchors)==6: break
        result.append(dict(id='s'+str(i),position=i,start=g['start'],end=g['end'],category=g['category'],
            title=g['title'],focus=g['focus'],words=g['source_words'],tokens=g['source_tokens'],density=g['density'],
            items=g['estimated_items'],sections=paths,continuations=g['continuation_groups'],
            supplementary=g['supplementary_links'],anchors=anchors))
    return result


def discover(rows,config):
    candidates=[]
    for a,b in zip(rows,rows[1:]):
        left=set(re.findall(r'\w+',a['title'].lower()+' '+a['focus'].lower()))
        right=set(re.findall(r'\w+',b['title'].lower()+' '+b['focus'].lower()))
        shared=left&right
        reasons=[]
        if set(a['continuations'])&set(b['continuations']): reasons.append('continuation')
        if a['sections'] and b['sections'] and a['sections'][0] and a['sections'][0]==b['sections'][0]: reasons.append('section')
        if len(shared)>=2 or len(shared)/max(1,len(left|right))>=.25: reasons.append('lexical')
        if 'N' in {a['category'],b['category']}: reasons.append('possible_support')
        if reasons: candidates.append(dict(segments=[a['id'],b['id']],signals=reasons,
            combined_items=a['items']+b['items'],same_category=a['category']==b['category']))
    return candidates


def ownership(groups,index):
    cursor=0; seen=[]
    for g in groups:
        if g['start_position']!=cursor or g['end_position']<cursor: raise ValueError('Optimized ownership gap/overlap')
        blocks=index.units[cursor:g['end_position']+1]
        if not blocks or g['start']!=blocks[0].id or g['end']!=blocks[-1].id: raise ValueError('Optimized boundary mismatch')
        if g['id']!=optimized_id(index,g['constituents']): raise ValueError('Optimized ID mismatch')
        seen+=g['constituents']; cursor=g['end_position']+1
    if cursor!=len(index.units) or len(seen)!=len(set(seen)): raise ValueError('Optimized incomplete/duplicate ownership')
    return True
