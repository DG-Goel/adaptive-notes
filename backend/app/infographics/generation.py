"""Category-batched generator workflow; no semantic verification or rendering."""
from dataclasses import dataclass,asdict
from pathlib import Path
import copy
import json
import time
from .optimization_model import canonical,initial_groups,ownership
from .source_index import digest
from .template_registry import REGISTRY,REGISTRY_VERSION,choices
from .generation_schema import SCHEMA_VERSION,parse_batch,validate_record
from .antv_adapter import convert,ADAPTER_VERSION
from .token_budget import TokenBudgetManager,ModelLimits,ContextConfig,RequestParts
from .checkpoints import ReadingCheckpoint,SQLiteCheckpointStore
from .clients import ProviderError,LocalLimitError

PROMPTS=Path(__file__).parent/'prompts'
PROMPT_FILES={'A':'master_A_structure.txt','B':'master_B_mechanism.txt','C':'master_C_analysis.txt'}


def prompt_for(category):
    return (PROMPTS/'generation_common.txt').read_text(encoding='utf-8')+'\n'+(PROMPTS/PROMPT_FILES[category]).read_text(encoding='utf-8')


def validate_optimized(optimizer,allow_skipped=False):
    if optimizer.status!='complete' and not (allow_skipped and optimizer.status=='optimization_skipped'):
        raise ValueError('Completed validated Phase 4 result required; skipped results need explicit authorization')
    optimizer.index.validate()
    if digest(optimizer.input_json.encode())!=optimizer.input_hash: raise ValueError('Provisional manifest hash mismatch')
    from types import SimpleNamespace
    from .segmentation_schema import parse_response
    from .segmentation_budget import words
    manifest=json.loads(optimizer.input_json);cursor=0;starts=[];continuation=None
    for row in manifest:
        if type(row['start_position']) is not int or type(row['end_position']) is not int or row['start_position']!=cursor or row['end_position']<cursor: raise ValueError('Invalid provisional range')
        blocks=optimizer.index.units[cursor:row['end_position']+1]
        if not blocks: raise ValueError('Missing provisional source')
        expected=dict(start=blocks[0].id,end=blocks[-1].id,source_start=blocks[0].source_start,source_end=blocks[-1].source_end,
            source_artifact_id=optimizer.index.snapshot.source_id,source_sha256=optimizer.index.snapshot.sha256,
            id='S'+digest((optimizer.index.fingerprint+blocks[0].id+blocks[-1].id).encode())[:24])
        if any(row.get(k)!=v for k,v in expected.items()): raise ValueError('Provisional identity mismatch')
        forced=row['boundary_reason']=='context_limit'
        remaining=optimizer.index.units[row['end_position']+1:row['end_position']+2] if forced else ()
        window=SimpleNamespace(source=blocks+remaining,final_document_window=row['end_position']==len(optimizer.index.units)-1)
        fields=('start','end','category','title','focus','density','estimated_items','boundary_reason','supplementary_ids','supports_start')
        parse_response(json.dumps(dict(segments=[{k:row[k] for k in fields}],pending_from=remaining[0].id if remaining else None)),window,forced=forced,previous_starts=starts)
        if row['source_tokens']!=sum(b.token_count for b in blocks) or row['source_words']!=words(''.join(b.text for b in blocks)) or row['source_token_kind']!='estimated':raise ValueError('Provisional source count mismatch')
        if forced and continuation is None:continuation='CG'+digest((optimizer.index.fingerprint+blocks[0].id).encode())[:24]
        if row['continuation_group']!=continuation:raise ValueError('Invalid provisional continuation')
        if not forced:continuation=None
        starts.append(row['start'])
        cursor=row['end_position']+1
    if cursor!=len(optimizer.index.units): raise ValueError('Incomplete source ownership')
    replay=copy.copy(optimizer)
    replay.groups=initial_groups(manifest,optimizer.index,optimizer.config)
    for operation in optimizer.accepted: replay._apply(operation,persist=False)
    for operation in optimizer.attachments: replay._attach(operation,persist=False)
    if canonical(replay.groups)!=optimizer.manifest: raise ValueError('Optimized manifest does not match validated operations')
    ownership(replay.groups,optimizer.index)
    return json.loads(optimizer.manifest)


@dataclass(frozen=True)
class GenerationConfig:
    max_batch_segments: int=4
    response_attempts: int=2
    max_items: int=80
    max_depth: int=6
    output_per_item: int=350
    support_output_tokens: int=1000
    base_output_tokens: int=500
    thinking_tokens: int=0
    max_requests: int=100
    automatic_reroute: bool=False

    def __post_init__(self):
        for key,value in asdict(self).items():
            if key=='automatic_reroute': continue
            if type(value) is not int or value<0 or (key!='thinking_tokens' and value==0): raise ValueError('Invalid generation setting: '+key)


class GenerationJob:
    def __init__(self,optimizer,generator,metadata,*,store=None,run_id='generation',config=None,allow_skipped=False):
        self.groups=validate_optimized(optimizer,allow_skipped)
        if generator.config.role!='generator': raise ValueError('Only generator role performs generation')
        self.index=optimizer.index;self.generator=generator;self.metadata=metadata
        self.config=config or GenerationConfig()
        self.limits=ModelLimits.from_client(generator.config,metadata)
        self.source_hash=self.index.snapshot.sha256
        self.optimized_hash=digest(canonical(self.groups).encode());self.provisional_hash=optimizer.input_hash
        self.prompts={c:prompt_for(c) for c in 'ABC'}
        self.prompt_hashes={c:digest(v.encode()) for c,v in self.prompts.items()}
        self.config_hash=digest(canonical(dict(schema=SCHEMA_VERSION,registry=REGISTRY_VERSION,adapter=ADAPTER_VERSION,
            registry_hash=digest(canonical([asdict(t) for t in REGISTRY.values()]).encode()),
            prompts=self.prompt_hashes,model=generator.config.model,config=asdict(self.config),limits=asdict(self.limits),
            index=self.index.fingerprint,optimized=self.optimized_hash,provisional=self.provisional_hash)).encode())
        self.store=store or SQLiteCheckpointStore(Path(__file__).resolve().parents[2]/'data/infographics/generation')
        self.run_id=run_id;self.parent=None;self.revision=0
        self.category_overrides={};self.reroutes={};self.results={};self.history=[];self.inflight=None
        self.status='ready';self.requests=0;self.cache_reuse=0;self.resizes=0;self.elapsed=0.
        self.usage={k:0 for k in asdict(generator.accounting)}
        self._aliases={g['id']:'g'+str(i) for i,g in enumerate(self.groups)}
        for group in self.groups:
            if group['category']=='N':
                self.results[group['id']]=dict(status='preserved_nonvisual',source_refs=[b.id for b in self.index.units[group['start_position']:group['end_position']+1]])

    def _authorized(self,group):
        positions=list(range(group['start_position'],group['end_position']+1))
        for support in self.groups:
            if support['category']=='N' and any(link['target']==group['id'] for link in support['supplementary_links']):
                positions+=range(support['start_position'],support['end_position']+1)
        positions=list(dict.fromkeys(positions))
        blocks=[self.index.units[i] for i in positions]
        return {'p'+str(b.position):b for b in blocks}

    def _request(self,category,groups,feedback=''):
        requests=[]
        for group in groups:
            sources=self._authorized(group)
            primary_end=group['end_position']-group['start_position']+1
            requests.append(dict(segment_id=self._aliases[group['id']],title=group['title'],focus=group['focus'],density=group['density'],
                estimated_items=group['estimated_items'],visible_word_target=round(self._educational_words(group)*.25),
                source=[dict(id=alias,text=b.text,role='primary' if i<primary_end else 'linked_support') for i,(alias,b) in enumerate(sources.items())]))
        body=dict(prompt=self.prompts[category],choices=choices(category),segments=requests,validation_feedback=feedback)
        payload=canonical(body)
        expected=sum(self.config.base_output_tokens+self.config.support_output_tokens+
            self.config.output_per_item*max(1,g['estimated_items'])*(1.25 if g['density']=='high' else 1) for g in groups)
        output=int(expected)+self.config.thinking_tokens
        if output>self.limits.output_tokens:return payload,output,False,None
        budget=TokenBudgetManager(self.limits,ContextConfig(reserved_output_tokens=int(expected),thinking_tokens=self.config.thinking_tokens))
        report=budget.check(self.index,RequestParts(),payload=payload)
        return payload,output,report.fits,report

    def _educational_words(self,group):
        from .segmentation_budget import words
        from .educational_content import educational_text
        from types import SimpleNamespace
        blocks=self.index.units[group['start_position']:group['end_position']+1]
        if self.index.snapshot.media_type!='application/json':return words(''.join(b.text for b in blocks))
        texts=[]
        for block in blocks:
            if block.type=='json_structure':continue
            try:texts.append(educational_text(SimpleNamespace(snapshot=self.index.snapshot,text=block.text)))
            except ValueError:texts.append(block.text)  # Conservative unknown-fragment fallback.
        titles=list(dict.fromkeys(title for b in blocks for title in b.section_path))
        return words('\n'.join(titles+texts))

    def _artifact(self,group,record,category):
        aliases=self._authorized(group)
        visual_id='V'+digest((self.index.fingerprint+group['id']+canonical(record)).encode())[:24]
        adapter=convert(record,visual_id) if record['status']=='generated' else None
        return dict(visual_id=visual_id,optimized_segment_id=group['id'],constituents=group['constituents'],
            source_artifact_id=self.index.snapshot.source_id,source_sha256=self.source_hash,
            source_start=group['source_start'],source_end=group['source_end'],start=group['start'],end=group['end'],
            category=category,status=record['status'],type=record.get('type'),
            antv_template=REGISTRY[record['type']].antv if record['status']=='generated' else None,
            record=record,source_aliases={k:dict(id=b.id,start=b.source_start,end=b.source_end,sha256=b.content_hash) for k,b in aliases.items()},
            registry_version=REGISTRY_VERSION,schema_version=SCHEMA_VERSION,adapter_version=ADAPTER_VERSION,
            model=self.generator.config.model,prompt_hash=self.prompt_hashes[category],prompt_version='generation-v1',
            deterministic_validation='passed',semantic_verification='pending',adapter=adapter,
            token_usage=dict(scope='job_cumulative_at_commit',**self.usage))

    def _state(self):
        return dict(source_hash=self.source_hash,index=self.index.fingerprint,optimized_hash=self.optimized_hash,
            provisional_hash=self.provisional_hash,config_hash=self.config_hash,results=self.results,
            overrides=self.category_overrides,reroutes=self.reroutes,status=self.status,inflight=self.inflight,
            history=self.history,usage=self.usage,requests=self.requests,resizes=self.resizes,elapsed=self.elapsed,
            queues={c:[g['id'] for g in self.groups if g['id'] not in self.results and self.category_overrides.get(g['id'],g['category'])==c] for c in 'ABC'},
            state=dict(cursor=0,committed_ranges=[],revision=self.revision+1))

    def save(self):
        value=self._state()
        record=ReadingCheckpoint(1,self.run_id,'generation_v1',((self.index.snapshot.source_id,self.source_hash),),self.config_hash,(),canonical(value),self.parent)
        self.parent=self.store.append(record);self.revision=value['state']['revision']

    @classmethod
    def resume(cls,optimizer,generator,metadata,**options):
        job=cls(optimizer,generator,metadata,**options)
        record=job.store.latest(job.run_id)
        if not isinstance(record,ReadingCheckpoint) or record.stage!='generation_v1' or record.run_id!=job.run_id: raise ValueError('No compatible generation checkpoint')
        value=json.loads(record.state_json)
        if record.config_sha256!=job.config_hash or record.source_hashes!=((job.index.snapshot.source_id,job.source_hash),): raise ValueError('Generation source/configuration changed')
        for key in ('source_hash','index','optimized_hash','provisional_hash','config_hash'):
            if value[key]!=job._state()[key]: raise ValueError('Generation checkpoint binding mismatch')
        known={g['id']:g for g in job.groups}
        if not set(job.results)<=set(value['results']):raise ValueError('Missing nonvisual ownership')
        for identifier,result in value['results'].items():
            if identifier not in known: raise ValueError('Unknown persisted segment')
            group=known[identifier]
            if group['category']=='N':
                if result!=job.results[identifier]: raise ValueError('Nonvisual checkpoint mismatch')
                continue
            category=value['overrides'].get(identifier,group['category'])
            aliases={k:b.text for k,b in job._authorized(group).items()}
            validate_record(result['record'],job._aliases[identifier],category,aliases,max_items=job.config.max_items,max_depth=job.config.max_depth)
            expected=job._artifact(group,result['record'],category)
            expected['token_usage']=result['token_usage']
            if canonical(expected)!=canonical(result): raise ValueError('Generation artifact integrity mismatch')
        for identifier,category in value['overrides'].items():
            if not job.config.automatic_reroute:raise ValueError('Unauthorized persisted reroute')
            if identifier not in known or category not in 'ABC' or known[identifier]['category']==category or value['reroutes'].get(identifier)!=1: raise ValueError('Invalid persisted reroute')
        for key,attr in (('results','results'),('overrides','category_overrides'),('reroutes','reroutes'),('status','status'),('inflight','inflight'),('history','history'),('usage','usage'),('requests','requests'),('resizes','resizes'),('elapsed','elapsed')):
            setattr(job,attr,value[key])
        if job.inflight is not None:
            if job.inflight.get('category') not in 'ABC' or any(i not in known or i in job.results for i in job.inflight.get('segments',[])):raise ValueError('Invalid in-flight generation request')
        if (job.status=='complete')!=(len(job.results)==len(job.groups)): raise ValueError('Generation completion mismatch')
        if job._state()['queues']!=value['queues']: raise ValueError('Generation queue mismatch')
        job.parent=record.checkpoint_id;job.revision=value['state']['revision']
        if job.status=='request_in_flight':job.status='paused_uncertain_request'
        if job.status=='complete':job.cache_reuse=1
        return job

    def step(self,*,retry_paused=False):
        if self.status=='complete':self.cache_reuse+=1;return self.status
        if self.status.startswith('paused') and not retry_paused:return self.status
        pending=[g for g in self.groups if g['id'] not in self.results]
        if not pending:self.status='complete';self.save();return self.status
        category=self.category_overrides.get(pending[0]['id'],pending[0]['category'])
        eligible=[g for g in pending if self.category_overrides.get(g['id'],g['category'])==category][:self.config.max_batch_segments]
        groups=[]
        for group in eligible:
            if self._request(category,groups+[group],'Invalid record; follow exact schema and authorized references.')[2]:groups.append(group)
            else:self.resizes+=1;break
        if not groups:
            self.status='paused_capacity_issue';self.history.append(dict(event='capacity_issue',segment=pending[0]['id']));self.save();return self.status
        feedback=''
        for attempt in range(self.config.response_attempts):
            payload,output,fits,report=self._request(category,groups,feedback)
            if not fits:self.status='paused_capacity_issue';self.save();return self.status
            if self.usage['attempts']+self.generator.config.max_attempts>self.config.max_requests:self.status='paused_request_budget';self.save();return self.status
            self.status='request_in_flight';self.inflight=dict(category=category,segments=[g['id'] for g in groups]);self.save()
            before=asdict(self.generator.accounting);start=time.monotonic();failure=None;response=None
            try:response=self.generator.complete('structured_generation',payload,max_output_tokens=output)
            except (ProviderError,LocalLimitError,RuntimeError) as error:failure=error.category if isinstance(error,ProviderError) else 'local_limit_or_unverified_model'
            finally:
                self.elapsed+=time.monotonic()-start;self.requests+=1
                after=asdict(self.generator.accounting)
                for key in self.usage:self.usage[key]+=after[key]-before[key]
            if failure:self.status='paused_'+failure;self.history.append(dict(event='provider_failure',category=failure));self.save();return self.status
            try:
                records=parse_batch(response.text,{self._aliases[g['id']]:{k:b.text for k,b in self._authorized(g).items()} for g in groups},category,max_items=self.config.max_items,max_depth=self.config.max_depth)
                for record in records:
                    if record['status']=='needs_split':
                        group=next(g for g in groups if self._aliases[g['id']]==record['segment_id'])
                        primary_count=group['end_position']-group['start_position']+1
                        primary_boundaries=list(self._authorized(group))[:primary_count-1]
                        if any(boundary not in primary_boundaries for boundary in record['boundaries']):raise ValueError('Split must be internal to primary source')
            except (ValueError,TypeError,KeyError,IndexError,RecursionError):
                feedback='Invalid record; follow exact schema and authorized references.'
                self.history.append(dict(event='invalid_response',attempt=attempt+1));self.status='ready' if attempt+1<self.config.response_attempts else 'paused_invalid_response';self.save()
                if self.status.startswith('paused'):return self.status
                continue
            prior=copy.deepcopy((self.results,self.category_overrides,self.reroutes))
            for record in records:
                group=next(g for g in groups if self._aliases[g['id']]==record['segment_id'])
                if record['status']=='reroute' and self.config.automatic_reroute and not self.reroutes.get(group['id']):
                    self.category_overrides[group['id']]=record['category'];self.reroutes[group['id']]=1
                    self.history.append(dict(event='reroute',segment=group['id'],category=record['category']));continue
                self.results[group['id']]=self._artifact(group,record,category)
            self.inflight=None;self.status='complete' if len(self.results)==len(self.groups) else 'ready'
            self.history.append(dict(event='batch_committed',category=category,size=len(groups),prompt_estimate=len(self.prompts[category].encode()),
                schema_estimate=len(canonical(choices(category)).encode()),input_estimate=report.input_with_framing,output_reserve=output))
            self.history[-1]['source_estimate']=sum(len(b.text.encode()) for g in groups for b in self._authorized(g).values())
            self.history[-1]['metadata_and_serialization_estimate']=max(0,report.input_count.value-self.history[-1]['source_estimate']-
                self.history[-1]['prompt_estimate']-self.history[-1]['schema_estimate'])
            try:self.save()
            except Exception:
                self.results,self.category_overrides,self.reroutes=prior;self.status='paused_persistence';raise
            return self.status
        return self.status

    def run(self,max_steps=100,*,retry_paused=False):
        if type(max_steps) is not int or max_steps<=0:raise ValueError('Positive bounded max_steps required')
        for i in range(max_steps):
            if self.step(retry_paused=retry_paused if i==0 else False)!='ready':break
        return self.status

    def artifacts(self):
        return json.loads(canonical([self.results[g['id']] for g in self.groups if g['id'] in self.results]))

    def metrics(self):
        from collections import Counter
        from .segmentation_budget import words
        from .educational_content import educational_text
        generated=[v for v in self.results.values() if v['status']=='generated']
        def visible_text(value):
            if isinstance(value,list):return ' '.join(visible_text(v) for v in value)
            if isinstance(value,dict):
                return ' '.join(str(v) if k in {'label','desc','time','value','unit','whole','order_basis','low','high'} else visible_text(v)
                    for k,v in value.items() if k not in {'id','refs','from','to','actor','step','cycle_refs','whole_refs','exclusive_refs'})
            return ''
        visible=sum(words(v['record']['title']+' '+visible_text(v['record']['data'])) for v in generated)
        support=sum(words(s['text']) for v in generated for s in v['record']['support'])
        source_words=words(educational_text(self.index))
        references=set()
        def collect(obj,artifact):
            if isinstance(obj,dict):
                for key,value in obj.items():
                    if key=='refs' or key.endswith('_refs'):references.update(artifact['source_aliases'][r]['id'] for r in value)
                    else:collect(value,artifact)
            elif isinstance(obj,list):
                for value in obj:collect(value,artifact)
        for artifact in generated:collect(artifact['record'],artifact)
        return dict(optimized_segments=len(self.groups),generated_infographics=len(generated),status=self.status,
            outcomes=dict(Counter(r['status'] for r in self.results.values())),templates=dict(Counter(v['type'] for v in generated)),
            categories=dict(Counter(v['category'] for v in generated)),success_rate=len(generated)/max(1,sum(g['category']!='N' for g in self.groups)),
            original_educational_words=source_words,visible_words_estimate=visible,support_words=support,
            visible_compression_ratio=visible/max(1,source_words),total_content_ratio=(visible+support)/max(1,source_words),
            source_reference_coverage=len(references)/max(1,len(self.index.units)),requests=self.requests,usage=self.usage,
            tokens_per_visual=(self.usage['reported_input_tokens']+self.usage['reported_output_tokens'])/max(1,len(generated)),
            retries=sum(h['event']=='invalid_response' for h in self.history),cache_reuse=self.cache_reuse,elapsed_seconds=self.elapsed,
            schema_valid_response_rate=sum(h['event']=='batch_committed' for h in self.history)/max(1,sum(h['event'] in {'batch_committed','invalid_response'} for h in self.history)),
            batch_sizes=[h['size'] for h in self.history if h['event']=='batch_committed'],
            split_proposals=sum(r['status']=='needs_split' for r in self.results.values()),reroute_corrections=sum(self.reroutes.values()),
            prompt_estimates={c:len(p.encode()) for c,p in self.prompts.items()},
            context_resizes=self.resizes,semantic_verification='pending')


def prepare_generation(optimizer,generator,metadata,*,environment=None,**options):
    import os
    env=os.environ if environment is None else environment
    flag=env.get('NOETRA_INFOGRAPHIC_ENGINE_ENABLED','false').strip().lower()
    if flag=='false':return None
    if flag!='true':raise ValueError('NOETRA_INFOGRAPHIC_ENGINE_ENABLED must be true or false')
    return GenerationJob(optimizer,generator,metadata,**options)
