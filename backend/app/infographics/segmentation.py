"""Planner-only sequential segmentation; atomic manifest/cursor checkpoints."""
from dataclasses import asdict,dataclass,replace
from collections import Counter
import json
from pathlib import Path
import time

from .checkpoints import ReadingCheckpoint
from .clients import ProviderError,LocalLimitError
from .reading_windows import ReadingSession,ReadingState,BoundaryDecision
from .source_index import digest,build_index
from .token_budget import RequestParts,TokenBudgetManager,ModelLimits
from .segmentation_budget import VisualizationBudgetConfig,recommendation,words,DEFAULT_CAPACITY
from .segmentation_schema import parse_response,SegmentationValidationError

PROMPT_PATH=Path(__file__).parent/'prompts/master_segmentation_router.txt'


@dataclass(frozen=True)
class PlannerSettings:
    response_attempts: int = 2
    forced_attempts: int = 1
    downstream_source_tokens: int = 16000
    capacity: tuple = DEFAULT_CAPACITY
    resize_attempts: int = 8

    def __post_init__(self):
        if any(type(x) is not int or x<=0 for x in (self.response_attempts,self.forced_attempts,self.downstream_source_tokens,self.resize_attempts)):
            raise ValueError('Planner bounds must be positive')


class SegmentationJob:
    def __init__(self,index,planner,budget,store,run_id,*,settings=None,visual_budget=None,prompt=None):
        if planner.config.role!='planner': raise ValueError('Only the dedicated planner client is allowed')
        self.planner=planner; self.store=store; self.run_id=run_id
        self.settings=settings or PlannerSettings()
        self.visual_config=visual_budget or VisualizationBudgetConfig()
        self.prompt=PROMPT_PATH.read_text(encoding='utf-8') if prompt is None else prompt
        self.prompt_hash=digest(self.prompt.encode('utf-8'))
        self.reading=ReadingSession(index,budget,RequestParts(segmentation_prompt=self.prompt))
        self.visual_budget=recommendation(self.reading.index,self.visual_config)
        public=dict(prompt=self.prompt_hash,model=planner.config.model,settings=asdict(self.settings),
                    visual=asdict(self.visual_config),reading=self.reading.configuration_hash)
        self.config_hash=digest(json.dumps(public,sort_keys=True).encode())
        self.manifest=[]; self.history=[]; self.parent=None; self.continuation=None
        self.status='complete' if not self.reading.index.units else 'ready'
        self.forced_counts={}; self.usage={k:0 for k in asdict(planner.accounting)}
        self.invalid_responses=0; self.requests=0; self.elapsed=0.; self.no_progress_events=0

    def _payload(self):
        value=self.reading.checkpoint_payload()
        value.update(manifest=self.manifest,history=self.history,prompt_hash=self.prompt_hash,
            prompt_version='master-segmentation-v1',model=self.planner.config.model,
            visualization_budget=self.visual_budget,continuation=self.continuation,
            forced_counts=self.forced_counts,processing_status=self.status,usage=self.usage,
            invalid_responses=self.invalid_responses,planner_requests=self.requests,
            elapsed_seconds=self.elapsed,no_progress_events=self.no_progress_events)
        return value

    def save(self):
        value=self._payload()
        # Failure/usage-only revisions must also advance the checkpoint revision.
        state=replace(self.reading.state,revision=self.reading.state.revision+1)
        value['state']=asdict(state)
        record=ReadingCheckpoint(1,self.run_id,'segmentation_v1',
            ((self.reading.index.snapshot.source_id,self.reading.index.snapshot.sha256),),self.config_hash,(),
            json.dumps(value,sort_keys=True,separators=(',',':')),self.parent)
        identifier=self.store.append(record)
        self.reading.state=state; self.parent=identifier
        return identifier

    @classmethod
    def resume(cls,reader,source_id,planner,budget,store,run_id,**options):
        record=store.latest(run_id)
        if not isinstance(record,ReadingCheckpoint) or record.stage!='segmentation_v1' or record.schema_version!=1:
            raise ValueError('No compatible segmentation checkpoint')
        job=cls(build_index(reader.snapshot(source_id)),planner,budget,store,run_id,**options)
        value=json.loads(record.state_json)
        if record.config_sha256!=job.config_hash or record.source_hashes!=((source_id,job.reading.index.snapshot.sha256),):
            raise ValueError('Source, model, prompt or configuration changed')
        if value['index_fingerprint']!=job.reading.index.fingerprint: raise ValueError('Source index changed')
        from .planner_integrity import validate_checkpoint
        validate_checkpoint(job,value,record)
        state=dict(value['state']); state['committed_ranges']=tuple(tuple(r) for r in state['committed_ranges'])
        if state['pending_range'] is not None: state['pending_range']=tuple(state['pending_range'])
        job.reading.state=ReadingState(**state); job.reading._validate_state(job.reading.state)
        cursor=0
        for segment in value['manifest']:
            if segment['start_position']!=cursor or not cursor<=segment['end_position']<len(job.reading.index.units):
                raise ValueError('Manifest ownership mismatch')
            cursor=segment['end_position']+1
        if cursor!=job.reading.state.cursor: raise ValueError('Manifest/cursor mismatch')
        job.manifest=value['manifest']; job.history=value['history']; job.parent=record.checkpoint_id
        job.continuation=value['continuation']; job.forced_counts=value['forced_counts']
        job.status=value['processing_status']; job.usage=value['usage']
        job.invalid_responses=value['invalid_responses']; job.requests=value['planner_requests']
        job.elapsed=value['elapsed_seconds']; job.no_progress_events=value['no_progress_events']
        if job.status=='request_in_flight': job.status='paused_uncertain_request'
        return job

    def _progress(self):
        units=self.reading.index.units; cursor=self.reading.state.cursor
        processed=round(self.visual_budget['source_words']*cursor/max(1,len(units)))
        visuals=sum(s['category']!='N' for s in self.manifest)
        return dict(total_source_words=self.visual_budget['source_words'],processed_percent=100*cursor/max(1,len(units)),
            committed_visuals=visuals,remaining_source_words=self.visual_budget['source_words']-processed,progress_word_count_kind='estimated_block_fraction',
            remaining_target_min=max(0,self.visual_budget['target_min']-visuals),
            remaining_target_max=max(0,self.visual_budget['target_max']-visuals),
            soft_upper_limit=self.visual_budget['soft_upper_limit'],processed_words=processed)

    def step(self,*,retry_paused=False):
        if self.status=='complete': return self.status
        if self.status.startswith('paused') and not retry_paused: return self.status
        if self.status in {'unresolved','unsupported_atomic_block'}: return self.status
        reading=self.reading
        forced=reading.state.status in {'forced_boundary_required','oversized_concept'}
        cursor_key=str(reading.state.cursor)
        if forced and self.forced_counts.get(cursor_key,0)>=self.settings.forced_attempts:
            self.status='unresolved'; self.save(); return self.status
        feedback=''
        for attempt in range(self.settings.response_attempts):
            from .planner_context import construct_request
            result,payload=construct_request(self,forced,feedback)
            if result.window is None:
                self.status='unsupported_atomic_block' if result.status=='unsupported_atomic_block' else 'paused_capacity_error'
                self.history.append(dict(event='capacity_error',reason=result.reason)); self.save(); return self.status
            window=result.window
            self.status='request_in_flight'; self.save()
            before=asdict(self.planner.accounting); started=time.monotonic()
            response=None; failure=None
            try:
                response=self.planner.complete('adaptive_segmentation',payload,
                    max_output_tokens=reading.budget.response_tokens+reading.budget.config.thinking_tokens)
            except (ProviderError,LocalLimitError,RuntimeError) as error:
                failure=error.category if isinstance(error,ProviderError) else 'local_limit_or_unverified_model'
            finally:
                after=asdict(self.planner.accounting)
                for key in self.usage: self.usage[key]+=after[key]-before[key]
                self.requests+=1; self.elapsed+=time.monotonic()-started
            if failure=='context_limit' and attempt+1<self.settings.response_attempts:
                self.history.append(dict(event='provider_context_resize'))
                self._provider_scale=getattr(self,'_provider_scale',1)*0.7
                continue
            if failure:
                self.status='paused_'+failure; self.history.append(dict(event='provider_failure',category=failure))
                self.save(); return self.status
            try:
                decision=parse_response(response.text,window,forced=forced,
                    previous_starts=[s['start'] for s in self.manifest])
                for segment in decision.segments:
                    ids=[b.id for b in window.source]
                    blocks=window.source[ids.index(segment.start):ids.index(segment.end)+1]
                    if sum(b.token_count for b in blocks)>self.settings.downstream_source_tokens:
                        raise SegmentationValidationError('downstream_source_limit')
            except SegmentationValidationError as error:
                feedback=str(error); self.invalid_responses+=1
                self.history.append(dict(event='invalid_response',code=feedback,attempt=attempt+1))
                self.status='paused_invalid_response' if attempt+1==self.settings.response_attempts else 'ready'
                self.save()
                if self.status.startswith('paused'): return self.status
                continue
            old_state=reading.state; old_manifest=list(self.manifest); old_continuation=self.continuation
            if forced:
                self.forced_counts[cursor_key]=self.forced_counts.get(cursor_key,0)+1
                if decision.segments and not self.continuation:
                    self.continuation='CG'+digest((reading.index.fingerprint+window.source[0].id).encode())[:24]
            for segment in decision.segments:
                ids=[b.id for b in window.source]
                blocks=window.source[ids.index(segment.start):ids.index(segment.end)+1]
                identity=reading.index.fingerprint+segment.start+segment.end
                row=asdict(segment)
                row.update(id='S'+digest(identity.encode())[:24],source_artifact_id=reading.index.snapshot.source_id,
                    source_sha256=reading.index.snapshot.sha256,source_start=blocks[0].source_start,
                    source_end=blocks[-1].source_end,start_position=blocks[0].position,end_position=blocks[-1].position,
                    continuation_group=self.continuation,source_tokens=sum(b.token_count for b in blocks),
                    source_token_kind='estimated',source_words=words(''.join(b.text for b in blocks)))
                self.manifest.append(row)
                if not forced: self.continuation=None
            reading.apply(BoundaryDecision(window.id,decision.segments[-1].end if decision.segments else None,decision.pending_from))
            if not decision.segments: self.no_progress_events+=1
            self.status='complete' if reading.state.status=='complete' else 'ready'
            if forced and not decision.segments: self.status='unresolved'
            self.history.append(dict(event='validated',segments=len(decision.segments),forced=forced))
            try: self.save()
            except Exception:
                reading.state=old_state; self.manifest=old_manifest; self.continuation=old_continuation
                self.status='paused_persistence'; raise
            return self.status
        return self.status

    def run(self,max_steps=100):
        if type(max_steps) is not int or max_steps<=0: raise ValueError('max_steps must be positive')
        for _ in range(max_steps):
            if self.step()!='ready': break
        return self.status

    def metrics(self):
        ledger=self.reading.ledger(); count=len(self.manifest); categories=Counter(s['category'] for s in self.manifest)
        submissions=Counter(i for h in self.history if h['event']=='request_budget'
            for i in range(h.get('source_start_position',0),h.get('source_end_position',0)))
        redundant=sum(max(0,n-1)*self.reading.index.units[i].token_count for i,n in submissions.items())
        nonvisual=sum(s['end_position']-s['start_position']+1 for s in self.manifest if s['category']=='N')
        return dict(total_source_blocks=ledger['total_reading_units'],committed_source_blocks=self.reading.state.cursor,
            pending_source_blocks=len(self.reading.index.units)-self.reading.state.cursor,nonvisual_blocks=nonvisual,
            source_range_coverage=self.reading.state.cursor/max(1,len(self.reading.index.units)),
            provisional_visuals=count-categories['N'],nonvisual_segments=categories['N'],categories=dict(categories),
            average_source_tokens=sum(s['source_tokens'] for s in self.manifest)/max(1,count),
            average_source_words=sum(s['source_words'] for s in self.manifest)/max(1,count),
            planner_requests=self.requests,usage=self.usage,invalid_responses=self.invalid_responses,
            validation_retries=sum(h['event']=='invalid_response' and h.get('attempt',0)<self.settings.response_attempts for h in self.history),
            no_progress_events=self.no_progress_events,context_splits=sum(s['boundary_reason']=='context_limit' for s in self.manifest),
            duration_seconds=self.elapsed,estimated_redundant_primary_tokens=redundant,
            automatic_resizes=sum(h.get('resizes',0) for h in self.history if h['event']=='request_budget'),
            semantic_coverage_verified=False)


def prepare_segmentation(reader,source_id,planner,budget,store,run_id,*,environment=None,**options):
    import os
    env=os.environ if environment is None else environment
    flag=env.get('NOETRA_INFOGRAPHIC_ENGINE_ENABLED','false').strip().lower()
    if flag=='false': return None
    if flag!='true': raise ValueError('NOETRA_INFOGRAPHIC_ENGINE_ENABLED must be true or false')
    return SegmentationJob(build_index(reader.snapshot(source_id)),planner,budget,store,run_id,**options)
