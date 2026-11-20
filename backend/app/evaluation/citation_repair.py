"""Explicit offline evidence association; never changes provider success/history."""
from app.evaluation.field_faithfulness import leaves


def add_reviewed_evidence(item,path,source,source_id,quote,*,reviewer,rationale):
    if not reviewer.strip() or not rationale.strip():raise ValueError('Reviewer and rationale required')
    if path not in dict(leaves(item.model_dump(mode='json'))):raise ValueError('Unknown substantive field')
    units={u.source_id:u for u in source.source_units}
    if source_id not in units or not quote.strip() or quote not in (units[source_id].text or ''):raise ValueError('Exact source evidence required')
    item.extraction_metadata=item.extraction_metadata or {}
    meta=item.extraction_metadata
    original=list(item.source_unit_ids)
    meta.setdefault('primary_source_ids',original)
    if source_id not in original:
        item.source_unit_ids.append(source_id)
        meta['context_source_ids']=list(dict.fromkeys(meta.get('context_source_ids',[])+[source_id]))
    start=units[source_id].text.index(quote)
    entry=dict(source_id=source_id,quote=quote,fields=[path],start_char=start,end_char=start+len(quote),match_count=units[source_id].text.count(quote),offset_basis='canonical source text; offline reviewed association')
    meta.setdefault('source_grounding',{}).setdefault('evidence',[]).append(entry)
    record=dict(item_id=item.knowledge_id,path=path,added_source=source_id,quote=quote,reviewer=reviewer,rationale=rationale,primary_coverage_unchanged=True,provider_history_changed=False)
    meta.setdefault('offline_citation_repairs',[]).append(record)
    return record


def revise_reviewed_text(item,path,text,source,source_id,quote,*,reviewer,rationale):
    import copy
    if not isinstance(text,str) or not text.strip():raise ValueError('Nonempty reviewed text required')
    values=dict(leaves(item.model_dump(mode='json')))
    if path not in values:raise ValueError('Unknown text field')
    record=add_reviewed_evidence(item,path,source,source_id,quote,reviewer=reviewer,rationale=rationale)
    keys=[s.replace('~1','/').replace('~0','~') for s in path.split('/')[1:]]
    if len(keys)==1:setattr(item,keys[0],text)
    else:
        value=copy.deepcopy(getattr(item,keys[0]));target=value
        for key in keys[1:-1]:target=target[int(key)] if isinstance(target,list) else target[key]
        if isinstance(target,list):target[int(keys[-1])]=text
        else:target[keys[-1]]=text
        setattr(item,keys[0],value)
    edit={**record,'original_output':values[path],'reviewed_output':text}
    item.extraction_metadata.setdefault('offline_text_revisions',[]).append(edit)
    return edit
