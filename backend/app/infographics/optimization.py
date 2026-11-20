"""Bounded global planning and source-grounded consolidation. No visual generation."""
from dataclasses import asdict
from collections import Counter
from pathlib import Path
import copy
import json
import time
from .optimization_model import (OptimizationConfig,canonical,validated_input,initial_groups,
    compact,discover,optimized_id,ownership)
from .source_index import digest
from .checkpoints import ReadingCheckpoint,SQLiteCheckpointStore
from .clients import ProviderError,LocalLimitError
from .segmentation_budget import recommendation,DEFAULT_CAPACITY
from .token_budget import RequestParts

PROMPT=Path(__file__).parent/'prompts/global_segment_optimizer.txt'
MERGE_REASONS={'shared_objective','complementary_components','complete_process','continuation_recovery','overlapping_explanation','related_classification'}
ATTACH_REASONS={'supporting_derivation','supporting_example'}


def strict_json(text):
    def pairs(items):
        value={}
        for k,v in items:
            if k in value: raise ValueError('duplicate_json_key')
            value[k]=v
        return value
    if not isinstance(text,str) or len(text)>131072: raise ValueError('response_size')
    return json.loads(text,object_pairs_hook=pairs,parse_constant=lambda _:(_ for _ in ()).throw(ValueError('invalid_constant')))


class OptimizationJob:
    def __init__(self,segmentation,*,planner=None,store=None,run_id='optimization',config=None,prompt=None):
        self.input_json=validated_input(segmentation)
        self.input_hash=digest(self.input_json.encode())
        self.index=segmentation.reading.index
        self.planner=planner or segmentation.planner
        if self.planner.config.role!='planner': raise ValueError('Only planner role is allowed')
        self.budget=segmentation.reading.budget
        self.config=config or OptimizationConfig()
        self.prompt=PROMPT.read_text(encoding='utf-8') if prompt is None else prompt
        self.prompt_hash=digest(self.prompt.encode())
        self.config_hash=digest(canonical(dict(schema=1,config=asdict(self.config),model=self.planner.config.model,
            budget=self.budget.public_config(),prompt=self.prompt_hash,input=self.input_hash,index=self.index.fingerprint)).encode())
        self.store=store or SQLiteCheckpointStore(Path(__file__).resolve().parents[2]/'data/infographics/optimization')
        self.run_id=run_id; self.parent=None; self.revision=0
        self.groups=initial_groups(json.loads(self.input_json),self.index,self.config)
        self.visual_budget=copy.deepcopy(segmentation.visual_budget)
        self.status='ready'; self.stage='plan'; self.round=0
        self.tasks=[]; self.task_cursor=0; self.proposals=[]; self.proposal_cursor=0
        self.accepted=[]; self.rejected=[]; self.attachments=[]; self.history=[]
        self.usage={k:0 for k in asdict(self.planner.accounting)}
        self.started=time.monotonic(); self.api_seconds=0.; self.local_seconds=0.
        self.requests=0; self.retries=0; self.resizes=0; self.cache_reuse=0
        self.round_hash=None; self.request_resume_stage=None

    @property
    def manifest(self):
        """Return a detached immutable serialized value, never an internal mutable list."""
        if self.status not in {'complete','optimization_skipped'}: raise ValueError('No completed optimized result')
        return canonical(self.groups)

    def _state(self):
        return dict(schema=1,index=self.index.fingerprint,source_hash=self.index.snapshot.sha256,input_hash=self.input_hash,
            prompt_hash=self.prompt_hash,model=self.planner.config.model,config_hash=self.config_hash,
            groups=self.groups,status=self.status,stage=self.stage,round=self.round,tasks=self.tasks,
            task_cursor=self.task_cursor,proposals=self.proposals,proposal_cursor=self.proposal_cursor,
            accepted=self.accepted,rejected=self.rejected,attachments=self.attachments,history=self.history,
            usage=self.usage,requests=self.requests,retries=self.retries,resizes=self.resizes,
            api_seconds=self.api_seconds,local_seconds=self.local_seconds,round_hash=self.round_hash,
            request_resume_stage=self.request_resume_stage,
            state=dict(cursor=0,committed_ranges=[],revision=self.revision+1))

    def save(self):
        payload=self._state()
        checkpoint=ReadingCheckpoint(1,self.run_id,'optimization_v1',
            ((self.index.snapshot.source_id,self.index.snapshot.sha256),),self.config_hash,(),canonical(payload),self.parent)
        identifier=self.store.append(checkpoint)
        self.parent=identifier; self.revision=payload['state']['revision']

    @classmethod
    def resume(cls,segmentation,**options):
        job=cls(segmentation,**options)
        record=job.store.latest(job.run_id)
        if not isinstance(record,ReadingCheckpoint) or record.stage!='optimization_v1' or record.run_id!=job.run_id:
            raise ValueError('No compatible optimization checkpoint')
        value=strict_json(record.state_json)
        if record.config_sha256!=job.config_hash or record.source_hashes!=((job.index.snapshot.source_id,job.index.snapshot.sha256),):
            raise ValueError('Optimization input/configuration changed')
        for key,expected in (('schema',1),('index',job.index.fingerprint),('input_hash',job.input_hash),
            ('prompt_hash',job.prompt_hash),('source_hash',job.index.snapshot.sha256),('config_hash',job.config_hash),('model',job.planner.config.model)):
            if value[key]!=expected: raise ValueError('Optimization checkpoint integrity: '+key)
        # Rebuild every accepted transformation from immutable validated input.
        for operation in value['accepted']:
            job._apply(operation,persist=False)
        for attachment in value['attachments']:
            job._attach(attachment,persist=False)
        if canonical(job.groups)!=canonical(value['groups']): raise ValueError('Optimized manifest integrity mismatch')
        ownership(job.groups,job.index)
        for key in ('groups','status','stage','round','tasks','task_cursor','proposals','proposal_cursor','accepted',
                    'rejected','attachments','history','usage','requests','retries','resizes','api_seconds',
                    'local_seconds','round_hash','request_resume_stage'):
            setattr(job,key,value[key])
        if not 0<=job.task_cursor<=len(job.tasks) or not 0<=job.proposal_cursor<=len(job.proposals):
            raise ValueError('Optimization checkpoint cursor mismatch')
        job.parent=record.checkpoint_id; job.revision=value['state']['revision']
        if job.status=='request_in_flight': job.status='paused_uncertain_request'
        if job.status in {'complete','optimization_skipped'}: job.cache_reuse=1
        return job

    def _fits(self,body):
        payload=canonical(body)
        report=self.budget.check(self.index,RequestParts(),payload=payload)
        # Preserve unchanged RoleClient's byte-bound admission even if an injected
        # budget uses a different tokenizer or framing configuration.
        byte_count=len(payload.encode())+256
        output=self.budget.response_tokens+self.budget.config.thinking_tokens
        return report.fits and byte_count+output<=self.planner.config.context_tokens

    def _body(self,task,data,feedback=''):
        return dict(prompt=self.prompt,task=task,data=data,validation_feedback=feedback,
                    category_capacity=DEFAULT_CAPACITY,visualization_budget=self.visual_budget)

    def _call(self,task,data,validator):
        for attempt in range(self.config.response_attempts):
            body=self._body(task,data,'' if attempt==0 else 'Invalid response; follow the exact schema and eligible adjacent IDs.')
            if not self._fits(body): self.status='paused_context_limit'; self.save(); return None
            if self.usage['attempts']+self.planner.config.max_attempts>self.config.max_requests: self.status='paused_request_budget'; self.save(); return None
            self.request_resume_stage=self.stage
            self.status='request_in_flight'; self.save()
            before=asdict(self.planner.accounting); start=time.monotonic(); result=None; failure=None
            try:
                result=self.planner.complete('global_consolidation',canonical(body),
                    max_output_tokens=self.budget.response_tokens+self.budget.config.thinking_tokens)
            except (ProviderError,LocalLimitError,RuntimeError) as error:
                failure=error.category if isinstance(error,ProviderError) else 'local_limit_or_unverified_model'
            finally:
                self.api_seconds+=time.monotonic()-start; self.requests+=1
                after=asdict(self.planner.accounting)
                for k in self.usage: self.usage[k]+=after[k]-before[k]
            if failure:
                self.status='paused_'+failure; self.history.append(dict(event='provider_failure',category=failure)); self.save(); return None
            try: value=validator(strict_json(result.text))
            except (ValueError,TypeError,KeyError,IndexError,RecursionError):
                self.retries+=1; self.history.append(dict(event='invalid_response',task=task)); self.status='ready'; self.save()
                continue
            self.status='ready'; return value
        self.status='paused_invalid_response'; self.save(); return None

    def _plan_tasks(self):
        rows=compact(self.groups,self.index); candidates=discover(rows,self.config)
        if not candidates: return []
        if sum(r['category']!='N' for r in rows)<=self.visual_budget['target_min'] and all(r['category']!='N' for r in rows):
            return []
        overview=dict(segment_count=len(rows),categories=dict(Counter(r['category'] for r in rows)),
            current_visuals=sum(r['category']!='N' for r in rows),
            pressure='high' if sum(r['category']!='N' for r in rows)>self.visual_budget['soft_upper_limit'] else 'lightweight')
        tasks=[]; cursor=0
        while cursor<len(rows):
            end=cursor; best=None
            while end<len(rows):
                subset=rows[cursor:end+1]
                data=dict(overview=overview,segments=subset,eligible_segments=[r['id'] for r in subset],
                    previous_context=rows[max(0,cursor-1):cursor],forward_context=rows[end+1:end+2],
                    candidates=[c for c in candidates if set(c['segments'])<=set(r['id'] for r in subset)])
                if not self._fits(self._body('plan',data,'Invalid response; follow the exact schema and eligible adjacent IDs.')): break
                best=data; end+=1
            if best is None or len(best['segments'])<2:
                raise ValueError('capacity_error: fewer than two compact segments fit')
            best['mapping']={r['id']:self.groups[r['position']]['id'] for r in best['segments']}
            tasks.append(best)
            if end>=len(rows): break
            next_cursor=max(cursor+1,end-self.config.overlap_segments)
            self.resizes+=1; cursor=next_cursor
        return tasks

    def _parse_plan(self,value,task):
        if not isinstance(value,dict) or set(value)!={'merges','attachments'}: raise ValueError('plan_fields')
        if not isinstance(value['merges'],list) or not isinstance(value['attachments'],list): raise ValueError('plan_arrays')
        mapping=task['mapping']; used=set(); operations=[]
        if len(value['merges'])+len(value['attachments'])>len(mapping): raise ValueError('too_many_operations')
        for row in value['merges']:
            if not isinstance(row,dict) or set(row)!={'segments','category','title','focus','density','estimated_items','reason'}: raise ValueError('merge_fields')
            ids=row['segments']
            if not isinstance(ids,list) or len(ids)<2 or any(not isinstance(i,str) or i not in mapping for i in ids) or len(ids)!=len(set(ids)): raise ValueError('merge_ids')
            positions=[list(mapping).index(i) for i in ids]
            if positions!=list(range(positions[0],positions[0]+len(ids))) or used.intersection(ids): raise ValueError('nonadjacent_or_conflicting')
            used.update(ids)
            if row['category'] not in {'A','B','C','N'} or row['density'] not in {'low','medium','high'} or row['reason'] not in MERGE_REASONS: raise ValueError('merge_enum')
            if type(row['estimated_items']) is not int or not 1<=row['estimated_items']<=1000: raise ValueError('merge_items')
            for key,limit in (('title',120),('focus',240)):
                if not isinstance(row[key],str) or not 1<=len(row[key].strip())<=limit or any(ord(c)<32 for c in row[key]): raise ValueError('merge_metadata')
            operations.append(dict(kind='merge',members=[mapping[i] for i in ids],**{k:v for k,v in row.items() if k!='segments'}))
        for row in value['attachments']:
            if not isinstance(row,dict) or set(row)!={'source','target','reason'} or row['reason'] not in ATTACH_REASONS: raise ValueError('attachment_fields')
            if row['source'] not in mapping or row['target'] not in mapping or row['source']==row['target']: raise ValueError('attachment_reference')
            operations.append(dict(kind='attachment',source=mapping[row['source']],target=mapping[row['target']],reason=row['reason']))
        return operations

    def _resolve(self,identifier):
        for g in self.groups:
            if g['id']==identifier or identifier in g.get('ancestor_ids',[]): return g
        raise ValueError('Unknown or stale group ID')

    def _validate_operation(self,operation):
        if operation['kind']=='attachment':
            if operation['reason'] not in ATTACH_REASONS: raise ValueError('Invalid attachment reason')
            source=self._resolve(operation['source']); target=self._resolve(operation['target'])
            if source['category']!='N' or target['category']=='N': raise ValueError('Only N-to-visual display associations allowed')
            return [source,target]
        if operation['category'] not in {'A','B','C','N'} or operation['density'] not in {'low','medium','high'} or operation['reason'] not in MERGE_REASONS:
            raise ValueError('Invalid merge metadata')
        if type(operation['estimated_items']) is not int or not 1<=operation['estimated_items']<=1000: raise ValueError('Invalid merge items')
        for field,limit in (('title',120),('focus',240)):
            if not isinstance(operation[field],str) or not 1<=len(operation[field].strip())<=limit or any(ord(c)<32 for c in operation[field]): raise ValueError('Invalid merge text')
        if len(operation['members'])<2: raise ValueError('Merge requires two members')
        groups=[self._resolve(i) for i in operation['members']]
        if any(g['id']!=i for g,i in zip(groups,operation['members'])): raise ValueError('Conflicting previously merged group')
        positions=[self.groups.index(g) for g in groups]
        if len(set(positions))!=len(positions) or positions!=list(range(positions[0],positions[0]+len(positions))): raise ValueError('Nonadjacent merge')
        if any(g['category']=='N' for g in groups): raise ValueError('Nonvisual ownership must remain separate; propose an attachment')
        if operation['category']=='N': raise ValueError('Do not turn visual content into nonvisual solely to consolidate')
        if max(operation['estimated_items'],sum(g['estimated_items'] for g in groups))>dict(self.config.capacity_items)[operation['category']]: raise ValueError('Readability capacity exceeded')
        if not self.config.capacity(self.index,groups[0]['start_position'],groups[-1]['end_position'])['fits']: raise ValueError('Downstream context overflow')
        visual_count=sum(g['category']!='N' for g in self.groups)-len(groups)+1
        if visual_count<self.visual_budget['target_min']: raise ValueError('Preferred minimum protected')
        return groups

    def _apply(self,operation,persist=True):
        groups=self._validate_operation(operation)
        first,last=groups[0],groups[-1]; members=[i for g in groups for i in g['constituents']]
        row=copy.deepcopy(first)
        row.update({k:operation[k] for k in ('category','title','focus','density','estimated_items')})
        row.update(id=optimized_id(self.index,members),constituents=members,end=last['end'],
            end_position=last['end_position'],source_end=last['source_end'],
            source_tokens=sum(g['source_tokens'] for g in groups),source_words=sum(g['source_words'] for g in groups),
            ancestor_ids=[i for g in groups for i in [g['id'],*g.get('ancestor_ids',[])]],
            continuation_groups=list(dict.fromkeys(i for g in groups for i in g['continuation_groups'])),
            supplementary_links=[i for g in groups for i in g['supplementary_links']],
            supplementary_ids=[i for g in groups for i in g['supplementary_ids']],
            merge_history=[h for g in groups for h in g['merge_history']]+[dict(reason=operation['reason'],
                original_categories=[g['category'] for g in groups],final_category=operation['category'],members=members,
                semantic_status='planner_confirmed_not_fact_verified')])
        row['downstream_context']=self.config.capacity(self.index,row['start_position'],row['end_position'])
        left=self.groups.index(first); right=self.groups.index(last)
        self.groups[left:right+1]=[row]
        # Resolve display associations independently of ownership after target merging.
        for g in self.groups:
            for link in g['supplementary_links']:
                link['target']=self._resolve(link['target'])['id']
        ownership(self.groups,self.index)

    def _attach(self,operation,persist=True):
        source,target=self._validate_operation(operation)
        link=dict(target=target['id'],reason=operation['reason'],semantically_represented=False)
        if source['supplementary_links'] and link not in source['supplementary_links']: raise ValueError('Conflicting support target')
        if link not in source['supplementary_links']: source['supplementary_links'].append(link)

    def _confirmation_data(self,operations):
        data=[]
        for operation in operations:
            groups=self._validate_operation(operation)
            positions=sorted(set(i for g in groups for i in range(g['start_position'],g['end_position']+1)))
            data.append(dict(id='p'+digest(canonical(operation).encode())[:16],proposal=operation,
                source=[dict(id=self.index.units[i].id,text=self.index.units[i].text) for i in positions]))
        return data

    def _parse_confirmation(self,value,items):
        if not isinstance(value,dict) or set(value)!={'confirmations'} or not isinstance(value['confirmations'],list): raise ValueError('confirmation_fields')
        expected={i['id'] for i in items}; seen=set(); accepted=[]
        for row in value['confirmations']:
            if not isinstance(row,dict) or set(row)!={'id','supported','preserves_distinctions','readable','category'}: raise ValueError('confirmation_shape')
            if row['id'] not in expected or row['id'] in seen: raise ValueError('confirmation_id')
            seen.add(row['id'])
            if any(type(row[k]) is not bool for k in ('supported','preserves_distinctions','readable')) or row['category'] not in {'A','B','C','N'}: raise ValueError('confirmation_type')
            item=next(i for i in items if i['id']==row['id'])
            category=item['proposal'].get('category',self._resolve(item['proposal'].get('source'))['category'] if item['proposal']['kind']=='attachment' else '')
            if all(row[k] for k in ('supported','preserves_distinctions','readable')) and row['category']==category: accepted.append(item['proposal'])
        if seen!=expected: raise ValueError('missing_confirmation')
        return accepted

    def run(self,*,retry_paused=False):
        if self.status in {'complete','optimization_skipped'}: self.cache_reuse+=1; return self.status
        if self.status.startswith('paused'):
            if not retry_paused: return self.status
            self.stage=self.request_resume_stage or self.stage; self.status='ready'
        local_start=time.monotonic(); api_start=self.api_seconds
        while self.round<self.config.max_rounds:
            if self.stage=='plan':
                if not self.tasks:
                    try: self.tasks=self._plan_tasks()
                    except ValueError:
                        self.status='paused_capacity_error'; self.save(); return self.status
                    if not self.tasks:
                        self.status='complete' if self.accepted else 'optimization_skipped'; self.stage='done'; self.save(); return self.status
                    self.round_hash=digest(canonical(self.groups).encode())
                while self.task_cursor<len(self.tasks):
                    task=self.tasks[self.task_cursor]; transmitted={k:v for k,v in task.items() if k!='mapping'}
                    proposals=self._call('plan',transmitted,lambda value:self._parse_plan(value,task))
                    if proposals is None: return self.status
                    for operation in proposals:
                        if operation not in self.proposals: self.proposals.append(operation)
                    self.task_cursor+=1; self.save()
                self.stage='validate'; self.save()
            while self.proposal_cursor<len(self.proposals):
                batch=[]; items=[]; cursor=self.proposal_cursor
                while cursor<len(self.proposals):
                    operation=self.proposals[cursor]
                    try: item=self._confirmation_data([operation])[0]
                    except ValueError as error:
                        if batch: break
                        self.rejected.append(dict(operation=operation,reason=str(error))); self.proposal_cursor+=1; cursor+=1; self.save(); continue
                    candidate=items+[item]
                    if not self._fits(self._body('confirm',candidate,'Invalid response; follow the exact schema and eligible adjacent IDs.')):
                        if batch: break
                        self.rejected.append(dict(operation=operation,reason='Source confirmation capacity exceeded'))
                        self.proposal_cursor+=1; cursor+=1; self.resizes+=1; self.save(); continue
                    batch.append(operation); items=candidate; cursor+=1
                if not batch: continue
                confirmations=self._call('confirm',items,lambda value:self._parse_confirmation(value,items))
                if confirmations is None: return self.status
                self.history.append(dict(event='source_suitability_validation',
                    results=[dict(proposal_id=item['id'],confirmed=item['proposal'] in confirmations,
                                  status='planner_judgment_not_fact_verification') for item in items]))
                previous=copy.deepcopy((self.groups,self.accepted,self.attachments,self.rejected,self.proposal_cursor))
                for operation in batch:
                    if operation not in confirmations:
                        self.rejected.append(dict(operation=operation,reason='Semantic suitability not confirmed')); continue
                    operation_snapshot=copy.deepcopy(self.groups)
                    try:
                        if operation['kind']=='merge': self._apply(operation); self.accepted.append(operation)
                        else: self._attach(operation); self.attachments.append(operation)
                    except ValueError as error:
                        self.groups=operation_snapshot
                        self.rejected.append(dict(operation=operation,reason=str(error)))
                self.proposal_cursor+=len(batch)
                try: self.save()
                except Exception:
                    self.groups,self.accepted,self.attachments,self.rejected,self.proposal_cursor=previous
                    self.status='paused_persistence'; raise
            self.round+=1
            changed=digest(canonical(self.groups).encode())!=self.round_hash
            if not changed: break
            self.stage='plan'; self.tasks=[]; self.task_cursor=0; self.proposals=[]; self.proposal_cursor=0
        self.status='complete'; self.stage='done'; self.local_seconds+=max(0,time.monotonic()-local_start-(self.api_seconds-api_start))
        ownership(self.groups,self.index); self.save(); return self.status

    def metrics(self):
        before=json.loads(self.input_json); after=self.groups
        visual=lambda rows:[r for r in rows if r['category']!='N']
        first,last=visual(before),visual(after)
        coverage=ownership(after,self.index)
        return dict(provisional_visuals=len(first),optimized_visuals=len(last),visual_count_reduction=len(first)-len(last),
            reduction_ratio=(len(first)-len(last))/len(first) if first else 0,accepted_merges=len(self.accepted),
            rejected_merges=len(self.rejected),category_before=dict(Counter(g['category'] for g in before)),
            category_after=dict(Counter(g['category'] for g in after)),supplementary_attachments=len(self.attachments),
            continuation_groups_consolidated=sum(bool(set(g['continuation_groups'])) for g in after if len(g['constituents'])>1),
            source_range_coverage=1 if coverage else 0,missing_source_blocks=0,duplicate_ownership=0,
            average_source_words_per_visual=sum(g['source_words'] for g in last)/max(1,len(last)),
            average_source_tokens_per_visual=sum(g['source_tokens'] for g in last)/max(1,len(last)),
            information_density=dict(Counter(g['density'] for g in last)),
            above_preferred_capacity=sum(g['estimated_items']>dict(self.config.capacity_items)[g['category']] for g in last),
            downstream_status=dict(Counter(g['downstream_context']['status'] for g in after)),
            requests=self.requests,usage=self.usage,api_seconds=self.api_seconds,local_seconds=self.local_seconds,
            retries=self.retries,cache_reuse=self.cache_reuse,context_resizes=self.resizes,
            budget_adherence=len(last)<=self.visual_budget['soft_upper_limit'],
            unresolved_budget_excess_reason='No further source-confirmed context-safe merges accepted' if len(last)>self.visual_budget['soft_upper_limit'] else None,
            semantic_fact_coverage_verified=False,status=self.status)


def prepare_optimization(segmentation,*,environment=None,**options):
    import os
    env=os.environ if environment is None else environment
    flag=env.get('NOETRA_INFOGRAPHIC_ENGINE_ENABLED','false').strip().lower()
    if flag=='false': return None
    if flag!='true': raise ValueError('NOETRA_INFOGRAPHIC_ENGINE_ENABLED must be true or false')
    return OptimizationJob(segmentation,**options)
