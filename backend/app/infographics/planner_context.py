"""Bounded local resizing adapter, preserving Phase 2 index and cursor."""
from dataclasses import replace
import json
from .reading_windows import WindowResult
from .token_budget import RequestParts


def construct_request(job,forced,feedback):
    reading=job.reading
    original_budget,original_parts=reading.budget,reading.parts
    metadata=dict(progress=job._progress(),capacity=job.settings.capacity,forced=forced,
        final_document_window=False,validation_feedback=feedback)
    # Reserve the larger spelling of the final flag and feedback before packing.
    parts=replace(original_parts,request_metadata=json.dumps(metadata,separators=(',',':')))
    from .token_budget import TokenBudgetManager
    target=reading.state.target_source_tokens
    maximum=original_budget.config.max_source_tokens
    previous=original_budget.config.previous_context_tokens
    scale=getattr(job,'_provider_scale',1)
    try:
        for attempt in range(job.settings.resize_attempts):
            config=replace(original_budget.config,target_source_tokens=min(target,maximum),
                max_source_tokens=maximum,previous_context_tokens=previous)
            limits=replace(original_budget.limits,input_tokens=max(1,int(original_budget.limits.input_tokens*scale)))
            reading.budget=TokenBudgetManager(limits,config,original_budget.counter)
            reading.parts=parts
            result=reading._construct(min(target,maximum))
            if result.window is not None:
                window=result.window
                body=json.loads(window.payload)
                meta=json.loads(body['request_metadata'])
                meta['final_document_window']=window.final_document_window
                body['request_metadata']=json.dumps(meta,separators=(',',':'))
                payload=json.dumps(body,ensure_ascii=False,separators=(',',':'))
                report=reading.budget.check(reading.index,parts,window.previous,window.source,window.lookahead,payload=payload)
                if report.fits:
                    window=replace(window,payload=payload,budget=report)
                    reading._active=window
                    job.history.append(dict(event='request_budget',resizes=attempt,
                        source_start_position=window.cursor,source_end_position=window.end,
                        serialized_overhead_tokens=max(0,report.input_count.value-sum(b.token_count for b in window.source)),
                        static_prompt_tokens=len(job.prompt.encode()),dynamic_metadata_tokens=len(parts.request_metadata.encode()),
                        source_tokens=sum(b.token_count for b in window.source),input_tokens=report.input_with_framing,
                        utilization=report.input_with_framing/max(1,report.input_limit),forced=forced))
                    return replace(result,window=window),payload
            if previous:
                previous=0
            else:
                maximum=max(1,int(maximum*0.7)); target=min(target,maximum)
        return WindowResult('capacity_error',reason='No whole source group fits after bounded local resizing'),' '
    finally:
        reading.budget,reading.parts=original_budget,original_parts
