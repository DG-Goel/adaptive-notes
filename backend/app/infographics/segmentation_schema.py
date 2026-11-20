"""Strict provider-neutral segmentation schema and source ownership validation."""
from dataclasses import dataclass
import json

REASONS=frozenset({'objective_change','capacity_limit','category_incompatibility','document_end','context_limit','nonvisual_requirement'})


class SegmentationValidationError(ValueError):
    pass


@dataclass(frozen=True)
class SegmentDecision:
    start: str
    end: str
    category: str
    title: str
    focus: str
    density: str
    estimated_items: int
    boundary_reason: str
    supplementary_ids: tuple[str,...] = ()
    supports_start: str | None = None


@dataclass(frozen=True)
class SegmentationDecision:
    segments: tuple[SegmentDecision,...]
    pending_from: str | None


def parse_response(text,window,*,forced=False,previous_starts=()):
    def fail(message): raise SegmentationValidationError(message)
    def pairs(items):
        result={}
        for k,v in items:
            if k in result: fail('duplicate_json_key')
            result[k]=v
        return result
    if not isinstance(text,str) or len(text)>131072: fail('response_size')
    try:
        value=json.loads(text,object_pairs_hook=pairs,parse_constant=lambda _:fail('invalid_json_constant'))
    except (ValueError,TypeError,RecursionError):
        fail('invalid_json')
    if not isinstance(value,dict) or set(value)!={'segments','pending_from'}: fail('response_fields')
    if not isinstance(value['segments'],list) or len(value['segments'])>len(window.source): fail('segments_shape')
    ids=[b.id for b in window.source]
    position=0; result=[]; starts=set(previous_starts)
    required={'start','end','category','title','focus','density','estimated_items','boundary_reason'}
    for row in value['segments']:
        if not isinstance(row,dict) or not required<=set(row) or set(row)-required-{'supplementary_ids','supports_start'}: fail('segment_fields')
        if not isinstance(row['start'],str) or not isinstance(row['end'],str): fail('boundary_type')
        if position>=len(ids) or row['start']!=ids[position] or row['end'] not in ids: fail('noncontiguous_or_ineligible_boundary')
        end=ids.index(row['end'])
        if end<position: fail('overlapping_boundary')
        if not isinstance(row['category'],str) or row['category'] not in {'A','B','C','N'}: fail('invalid_category')
        if not isinstance(row['density'],str) or row['density'] not in {'low','medium','high'}: fail('invalid_density')
        if type(row['estimated_items']) is not int or not 0<=row['estimated_items']<=1000: fail('invalid_complexity')
        for key,maximum in (('title',120),('focus',240)):
            if not isinstance(row[key],str) or not 1<=len(row[key].strip())<=maximum or any(ord(c)<32 for c in row[key]): fail('metadata_length')
        reason=row['boundary_reason']
        if not isinstance(reason,str) or reason not in REASONS: fail('invalid_reason')
        if reason=='document_end' and (not window.final_document_window or end!=len(ids)-1): fail('premature_document_end')
        if reason=='context_limit' and not forced: fail('unrequested_context_boundary')
        if forced and reason!='context_limit': fail('forced_boundary_reason_required')
        if forced and end==len(ids)-1: fail('forced_boundary_must_leave_continuation')
        support=row.get('supplementary_ids',[])
        if not isinstance(support,list) or any(not isinstance(x,str) for x in support) or len(set(support))!=len(support) or not set(support)<=set(ids[position:end+1]): fail('invalid_supplementary_range')
        link=row.get('supports_start')
        if link is not None and (not isinstance(link,str) or row['category']!='N' or link not in starts): fail('invalid_support_link')
        result.append(SegmentDecision(**{k:row[k] for k in required},supplementary_ids=tuple(support),supports_start=link))
        starts.add(row['start']); position=end+1
    expected=ids[position] if position<len(ids) else None
    if value['pending_from']!=expected: fail('invalid_pending_boundary')
    return SegmentationDecision(tuple(result),expected)
