"""Versioned exact-source references. No fuzzy matching or invented quotations."""
import copy
import json
import re
from app.extraction.prompts import build_extraction_prompt


def evidence_source_ids(chunk):
    """Only explicit, internally consistent non-quotable states may omit markers."""
    pending=set(chunk.uninterpreted_source_ids)
    states=chunk.source_states
    nontext={'awaiting_interpretation','failed','incomplete','empty','structural'}
    if len(chunk.source_units)!=len(set(chunk.source_units)) or len(pending)!=len(chunk.uninterpreted_source_ids):
        raise ValueError('Duplicate source identity')
    if not pending<=set(chunk.source_units) or any(states.get(s) not in nontext for s in pending):
        raise ValueError('Unregistered nontext evidence state')
    if any(state in nontext and sid not in pending for sid,state in states.items() if sid in chunk.source_units):
        raise ValueError('Contradictory source evidence state')
    return [sid for sid in chunk.source_units if sid not in pending]


def catalog(chunk):
    evidence_ids=evidence_source_ids(chunk)
    allowed=set(chunk.source_units)
    markers=list(re.finditer(r'(?m)^\[([^\]\r\n]+)\] ',chunk.text_content))
    markers=[m for m in markers if m.group(1) in allowed]
    if [m.group(1) for m in markers]!=evidence_ids:
        raise ValueError('Source markers are ambiguous or incomplete')
    result={}
    for index,marker in enumerate(markers):
        text=chunk.text_content[marker.end():markers[index+1].start() if index+1<len(markers) else len(chunk.text_content)]
        literal=chunk.literal_source_texts.get(marker.group(1))
        if literal is not None:
            if text.rstrip('\n')!=literal.rstrip('\n'):
                raise ValueError('Literal source marker text changed')
            text=literal
        # Sentence boundaries retain text verbatim. Long sentences are partitioned
        # at whitespace; concatenation (including whitespace) preserves the source.
        parts=[text] if literal is not None else re.split(r'(?<=[.!?])(?=\s)',text)
        for part in parts:
            while part:
                if len(part)>500:
                    boundaries=[m.end() for m in re.finditer(r'\s+',part[:501])]
                    end=max(boundaries) if boundaries else len(part)
                else:
                    end=len(part)
                piece,part=part[:end],part[end:]
                if piece.strip() or (literal is not None and piece):
                    result[f'Q{len(result):04d}']={'source_id':marker.group(1),'quote':piece if literal is not None else piece.strip()}
    return result


def chunk_prompt(chunk):
    entries=catalog(chunk)
    text='\n'.join(f"[{e['source_id']}] <{key}> {e['quote']}" for key,e in entries.items())
    prompt=build_extraction_prompt(text,chunk.chunk_id,allowed_source_ids=chunk.source_units)
    return prompt+'''\nEXACT EXCERPT REFERENCES (quote-catalog-v1): Each source excerpt is labeled <Q0000>, etc.
Include quote_id in every source_evidence object, selecting the excerpt that supports its fields.
Keep source_id, quote and fields required. quote must contain source text; quote_id is a separate reference.
The application resolves a valid quote_id to the original exact excerpt and records that resolution.
Use multiple excerpt references when necessary. Never use Q identifiers as source_unit_ids.
Exclude advertisements and instructor marketing from study notes. Do not infer unstated technical claims.
'''


def resolve_response(content,chunk):
    """Require the original required fields; only explicit valid IDs can resolve."""
    def unique(pairs):
        result={}
        for k,v in pairs:
            if k in result:
                raise ValueError('Duplicate JSON field')
            result[k]=v
        return result
    def invalid(_):
        raise ValueError('Invalid JSON numeric constant')
    data=json.loads(content,object_pairs_hook=unique,parse_constant=invalid)
    resolved=copy.deepcopy(data)
    corrections=[]
    entries=catalog(chunk)
    if not isinstance(resolved,dict):
        raise ValueError('Expected object')
    for category,items in resolved.items():
        if not isinstance(items,list):
            continue  # strict raw-contract validator reports the schema error
        for index,item in enumerate(items):
            if not isinstance(item,dict) or not isinstance(item.get('source_evidence'),list):
                continue
            for ei,evidence in enumerate(item['source_evidence']):
                if not isinstance(evidence,dict) or 'quote_id' not in evidence:
                    continue  # original exact-quote validation remains required
                if not isinstance(evidence.get('quote'),str) or not evidence['quote'].strip():
                    raise ValueError('Missing required source quote')
                key=evidence['quote_id']
                if not isinstance(key,str) or key not in entries:
                    raise ValueError('Unknown excerpt reference')
                entry=entries[key]
                if evidence.get('source_id')!=entry['source_id'] or entry['source_id'] not in item.get('source_unit_ids',[]):
                    raise ValueError('Excerpt reference/source mismatch')
                original_fields=copy.deepcopy(evidence.get('fields'))
                fields=evidence.get('fields')
                if isinstance(fields,list):
                    expanded=[]
                    for path in fields:
                        # Expand only an existing top-level array. No field is
                        # created and invalid/unknown pointers remain invalid.
                        value=item.get(path[1:]) if isinstance(path,str) and path.count('/')==1 else None
                        if isinstance(value,list) and value and all(isinstance(v,str) for v in value):
                            expanded.extend(f'{path}/{i}' for i,v in enumerate(value) if v)
                        else:
                            expanded.append(path)
                    evidence['fields']=list(dict.fromkeys(expanded))
                corrections.append({'path':f'/{category}/{index}/source_evidence/{ei}',
                    'quote_id':key,'original_quote':evidence['quote'],'resolved_quote':entry['quote'],
                    'source_id':entry['source_id'],'original_fields':original_fields,'resolved_fields':evidence.get('fields')})
                evidence['quote']=entry['quote']
    return json.dumps(resolved,ensure_ascii=False),corrections
