"""Bounded source-relationship context; primary coverage never changes."""
def bind_context(chunk, units):
    selected=select_context(chunk,units)
    literal={s:t for s,t in chunk.literal_source_texts.items() if s in chunk.source_units}
    literal.update({u.source_id:u.text for u in units if u.source_id in selected['context_ids'] and u.type=='code'})
    return chunk.model_copy(update={'context_source_ids':selected['context_ids'],
        'context_text':selected['text'],'context_limitations':selected['limitations'],
        'literal_source_texts':literal})


def evidence_view(chunk):
    return chunk.model_copy(update={'source_units':chunk.source_units+chunk.context_source_ids,
        'text_content':chunk.text_content+'\n'+chunk.context_text})


def select_context(chunk, units, max_characters=1000):
    if max_characters < 0:
        raise ValueError('Negative context budget')
    ids=[u.source_id for u in units]
    if len(ids)!=len(set(ids)) or any(s not in ids for s in chunk.source_units):
        raise ValueError('Ambiguous canonical sources')
    positions=[ids.index(s) for s in chunk.source_units]
    if not positions:
        return {'primary_ids':[], 'context_ids':[], 'text':'', 'limitations':[]}
    by_id={u.source_id:u for u in units}
    by_ref={u.docling_ref:u.source_id for u in units if u.docling_ref}
    related=[]
    for sid in chunk.source_units:
        unit=by_id[sid]
        related.extend(h['source_id'] for h in unit.provenance.get('heading_ancestry',[]) if 'source_id' in h)
        if unit.parent_id:
            related.append(unit.parent_id)
        for key in ('caption_refs','children_refs'):
            related.extend(by_ref[r] for r in unit.provenance.get(key,[]) if r in by_ref)
        # A caption may point at its associated figure via the reverse relationship.
        related.extend(u.source_id for u in units if unit.docling_ref and unit.docling_ref in u.provenance.get('caption_refs',[]))
    adjacent=[ids[i] for i in (min(positions)-1,max(positions)+1) if 0<=i<len(units)]
    candidates=[ids.index(s) for s in dict.fromkeys(related+adjacent) if s in by_id and s not in chunk.source_units]
    selected=[]; remaining=max_characters; limitations=[]
    for i in candidates:
        unit=units[i]
        if unit.educational_assessment.excluded:
            continue
        text=f'[{unit.source_id}] {unit.text}\n' if unit.text else ''
        if not text:
            if unit.representation_status not in ('structural','empty'):
                limitations.append(f'{unit.source_id}: nontext context requires interpretation')
        elif len(text)<=remaining:
            selected.append((unit.source_id,text)); remaining-=len(text)
        else:
            limitations.append(f'{unit.source_id}: adjacent context exceeds budget; boundary review required')
    for sid in chunk.source_units:
        limitations.extend(f'{sid}: {v}' for v in by_id[sid].interpretation_limitations)
    return {'primary_ids':list(chunk.source_units),'context_ids':[s for s,_ in selected],
            'text':''.join(t for _,t in selected),'limitations':limitations}
