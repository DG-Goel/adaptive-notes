"""Exact substantive equality only; uncertain equivalence remains reviewable."""
import json
from difflib import SequenceMatcher
from app.extraction.knowledge_merge import CATEGORIES, normalize_knowledge_ids


def consolidate(document):
    normalized=normalize_knowledge_ids(document,artifact_id='consolidation')
    result=normalized.document.model_copy(deep=True)
    decisions=[]; originals={}; reviews=[]
    ignored={'knowledge_id','source_unit_ids','extraction_metadata','confidence','page_range'}
    for category in CATEGORIES:
        kept=[]; seen={}
        for item in getattr(result,category):
            substantive=item.model_dump(mode='json',exclude=ignored)
            generation=(item.extraction_metadata or {}).get('source_grounding',{})
            # Distinct availability/teaching contexts cannot disappear in deduplication.
            substantive['_generation_annotations']=generation.get('generation_annotations')
            substantive['_generation_dispositions']=[{'path':f['path'],'claims':[
                {k:c.get(k) for k in ('text','availability','eligible_for_preview','instructional_role','literal_kind')}
                for c in f['claims']]} for f in generation.get('generation_policy',{}).get('fields',[])]
            key=json.dumps(substantive,sort_keys=True,ensure_ascii=False)
            if key in seen:
                target=seen[key]
                originals[target.knowledge_id].append(item.knowledge_id)
                target.source_unit_ids=list(dict.fromkeys(target.source_unit_ids+item.source_unit_ids))
                metadata=target.extraction_metadata or {}
                histories=metadata.setdefault('consolidated_metadata',[])
                histories.append(item.extraction_metadata)
                incoming=(item.extraction_metadata or {}).get('source_grounding')
                current=metadata.get('source_grounding')
                if current is not None and incoming is not None:
                    evidence=current.get('evidence',[])+incoming.get('evidence',[])
                    current['evidence']=list({json.dumps(e,sort_keys=True,ensure_ascii=False):e for e in evidence}.values())
                    current['validation_errors']=current.get('validation_errors',[])+incoming.get('validation_errors',[])
                    current['mechanically_valid']=bool(current.get('mechanically_valid') and incoming.get('mechanically_valid'))
                    current['semantic_entailment_verified']=False
                    if current.get('abstentions') or incoming.get('abstentions'):
                        current['abstentions']=list({json.dumps(a,sort_keys=True):a
                            for a in current.get('abstentions',[])+incoming.get('abstentions',[])}.values())
                # Primary ownership is unioned independently from contextual citations.
                for name in ('primary_source_ids','context_source_ids'):
                    if name in metadata or name in (item.extraction_metadata or {}):
                        metadata[name]=list(dict.fromkeys(metadata.get(name,[])+(item.extraction_metadata or {}).get(name,[])))
                target.extraction_metadata=metadata
                decisions.append(dict(action='exact_duplicate',original=item.knowledge_id,target=target.knowledge_id))
            else:
                for previous in kept:
                    if SequenceMatcher(None,previous.content,item.content).ratio()>.55:
                        reviews.append(dict(left=previous.knowledge_id,right=item.knowledge_id,
                            status='NEEDS_REVIEW',reason='Possible paraphrase, overlap or conflict; both retained'))
                seen[key]=item;kept.append(item);originals[item.knowledge_id]=[item.knowledge_id]
                decisions.append(dict(action='retain',original=item.knowledge_id,target=item.knowledge_id))
        setattr(result,category,kept)
    result.update_statistics()
    return result,dict(decisions=decisions,original_ids=originals,
                       id_normalization=[m.model_dump() for m in normalized.mappings],review_pairs=reviews)
