"""Source-first, bidirectional verification with immutable bounded repair revisions."""
from dataclasses import dataclass,asdict
from pathlib import Path
from collections import Counter
import copy
import json
import time
from .role_environment import initialize_role
from .clients import ProviderError,LocalLimitError
from .token_budget import TokenBudgetManager,ModelLimits,ContextConfig,RequestParts
from .checkpoints import ReadingCheckpoint,SQLiteCheckpointStore
from .optimization import strict_json
from .optimization_model import canonical
from .source_index import digest
from .generation_schema import validate_record,fields
from .antv_adapter import convert,ADAPTER_VERSION
from .template_registry import REGISTRY_VERSION,REGISTRY
from .verification_schema import inventory,report,INVENTORY_VERSION,VERIFICATION_VERSION,ISSUES,PRESERVED,SUPPORTED
from .verification_model import validate_generation,claims,item_map,assess,coverage_metrics,TEMPLATE_CONSTRAINTS,AcceptancePolicy
from .visual_repair import apply_repairs

PROMPT_DIR=Path(__file__).parent/'prompts'
PROMPT_NAMES={'inventory':'source_fact_inventory.txt','verify':'semantic_verifier.txt','compact':'semantic_verifier.txt',
              'repair':'targeted_visual_repair.txt','consistency':'semantic_verifier.txt'}


@dataclass(frozen=True)
class VerificationConfig:
    mode: str='strict'
    response_attempts: int=2
    repair_rounds: int=2
    max_requests: int=100
    max_batch_visuals: int=3
    output_tokens: int=6000
    thinking_tokens: int=0
    max_facts_per_part: int=128
    inventory_source_tokens: int=6000
    whole_lecture_check: bool=True

    def __post_init__(self):
        if self.mode not in {'strict','compact'}:raise ValueError('Verification mode must be strict or compact')
        if type(self.whole_lecture_check) is not bool:raise ValueError('whole_lecture_check must be a boolean')
        for key,value in asdict(self).items():
            if key in {'mode','whole_lecture_check'}:continue
            if type(value) is not int or value<0 or (key not in {'repair_rounds','thinking_tokens'} and value==0):raise ValueError('Invalid verifier setting: '+key)


class VerificationJob:
    def __init__(self,generation,optimizer,verifier,metadata,*,store=None,run_id='verification',config=None,policy=None,allow_skipped=False,source_reader=None):
        if verifier.config.role!='verifier':raise ValueError('Only verifier role is authorized for Phase 6')
        self.originals=validate_generation(generation,optimizer,allow_skipped=allow_skipped)
        self.generation=generation;self.index=generation.index;self.groups=copy.deepcopy(generation.groups)
        if source_reader is not None:
            fresh=source_reader.snapshot(self.index.snapshot.source_id)
            if fresh.sha256!=self.index.snapshot.sha256 or fresh.content!=self.index.snapshot.content:raise ValueError('Original source changed since generation')
        self.verifier=verifier;self.metadata=metadata;self.config=config or VerificationConfig();self.policy=policy or AcceptancePolicy()
        self.budget=TokenBudgetManager(ModelLimits.from_client(verifier.config,metadata),ContextConfig(
            reserved_output_tokens=self.config.output_tokens,thinking_tokens=self.config.thinking_tokens))
        self.prompts={task:(PROMPT_DIR/name).read_text(encoding='utf-8') for task,name in PROMPT_NAMES.items()}
        self.prompt_hashes={k:digest(v.encode()) for k,v in self.prompts.items()}
        self.original_hashes={identifier:digest(canonical(artifact).encode()) for identifier,artifact in self.originals.items()}
        self.config_hash=digest(canonical(dict(version=VERIFICATION_VERSION,inventory=INVENTORY_VERSION,registry=REGISTRY_VERSION,
            adapter=ADAPTER_VERSION,source=self.index.snapshot.sha256,index=self.index.fingerprint,
            optimized=generation.optimized_hash,provisional=generation.provisional_hash,originals=self.original_hashes,
            prompts=self.prompt_hashes,config=asdict(self.config),policy=asdict(self.policy),
            model=verifier.config.model,budget=self.budget.public_config())).encode())
        self.store=store or SQLiteCheckpointStore(Path(__file__).resolve().parents[2]/'data/infographics/verification')
        self.run_id=run_id;self.parent=None;self.revision=0;self.requests=0;self.duration=0.;self.cache_reuse=0
        self.usage={key:0 for key in asdict(verifier.accounting)}
        self.artifacts={a['visual_id']:a for a in self.originals.values() if a['status']=='generated'}
        self.group_by_visual={a['visual_id']:next(g for g in self.groups if g['id']==a['optimized_segment_id']) for a in self.artifacts.values()}
        self.records={v:copy.deepcopy(a['record']) for v,a in self.artifacts.items()}
        self.inventories={v:[] for v in self.artifacts};self.inventory_cache={};self.evaluations={};self.pending={}
        self.repairs={v:[] for v in self.artifacts};self.rounds={v:0 for v in self.artifacts};self.escalations={}
        self.tasks=[];self.cursor=0;self.parts={};self.history=[];self.inflight=None
        self.phase='inventory' if self.config.mode=='strict' else 'compact';self.status='ready';self.consistency=None
        self.skipped={g['id']:copy.deepcopy(self.originals[g['id']]) for g in self.groups if self.originals[g['id']]['status']!='generated'}

    def _source(self,visual_id):
        return {k:b.text for k,b in self.generation._authorized(self.group_by_visual[visual_id]).items()}

    def _record(self,visual_id):return self.pending.get(visual_id,{}).get('record',self.records[visual_id])

    def _body(self,task,data,feedback=''):
        return dict(task=task,prompt=self.prompts[task],data=data,validation_feedback=feedback,
                    issue_types=sorted(ISSUES) if task in {'verify','compact'} else [])

    def _fits(self,task,data):
        payload=canonical(self._body(task,data,'Invalid response; return every supplied ID exactly once with authorized evidence.'))
        report=self.budget.check(self.index,RequestParts(),payload=payload)
        return report.fits

    def _save_state(self):
        return dict(config_hash=self.config_hash,source_hash=self.index.snapshot.sha256,index=self.index.fingerprint,
            optimized_hash=self.generation.optimized_hash,original_hashes=self.original_hashes,prompt_hashes=self.prompt_hashes,
            inventory_version=INVENTORY_VERSION,verification_version=VERIFICATION_VERSION,
            phase=self.phase,status=self.status,records=self.records,inventories=self.inventories,inventory_cache=self.inventory_cache,
            evaluations=self.evaluations,pending=self.pending,repairs=self.repairs,rounds=self.rounds,escalations=self.escalations,
            tasks=self.tasks,cursor=self.cursor,parts=self.parts,history=self.history,inflight=self.inflight,consistency=self.consistency,
            requests=self.requests,usage=self.usage,duration=self.duration,
            final_result_hash=digest(canonical(self.results()).encode()) if self.status in {'complete_accepted','complete_unresolved'} else None,
            state=dict(cursor=0,committed_ranges=[],revision=self.revision+1))

    def save(self):
        value=self._save_state()
        record=ReadingCheckpoint(1,self.run_id,'verification_v1',((self.index.snapshot.source_id,self.index.snapshot.sha256),),self.config_hash,(),canonical(value),self.parent)
        self.parent=self.store.append(record);self.revision=value['state']['revision']

    def _call(self,task,data,validator):
        for attempt in range(self.config.response_attempts):
            body=self._body(task,data,'' if attempt==0 else 'Invalid response; return every supplied ID exactly once with authorized evidence.')
            payload=canonical(body);budget=self.budget.check(self.index,RequestParts(),payload=payload)
            if not budget.fits:self.status='unresolved_capacity';self.history.append(dict(event='capacity_error',task=task));self.save();return None
            if self.usage['attempts']+self.verifier.config.max_attempts>self.config.max_requests:self.status='paused_request_budget';self.save();return None
            self.status='request_in_flight';self.inflight=dict(task=task,cursor=self.cursor,phase=self.phase,payload_hash=digest(payload.encode()));self.save()
            before=asdict(self.verifier.accounting);start=time.monotonic();failure=None;response=None
            try:
                workload={'inventory':'coverage_verification','compact':'coverage_verification','verify':'reverification' if self.pending else 'coverage_verification','repair':'targeted_repair','consistency':'factual_grounding'}[task]
                response=self.verifier.complete(workload,payload,max_output_tokens=self.budget.response_tokens+self.config.thinking_tokens)
            except (ProviderError,LocalLimitError,RuntimeError) as error:failure=error.category if isinstance(error,ProviderError) else 'local_limit_or_unverified_model'
            finally:
                self.duration+=time.monotonic()-start;self.requests+=1
                after=asdict(self.verifier.accounting)
                for key in self.usage:self.usage[key]+=after[key]-before[key]
            if failure:self.status='paused_'+failure;self.history.append(dict(event='provider_failure',category=failure));self.save();return None
            try:value=validator(strict_json(response.text))
            except (ValueError,TypeError,KeyError,IndexError,RecursionError):
                self.history.append(dict(event='invalid_response',task=task,attempt=attempt+1));self.status='ready';self.save();continue
            self.history.append(dict(event='validated_response',task=task,batch_size=len(data) if isinstance(data,list) else 1,
                prompt_estimate=len(self.prompts[task].encode()),serialized_input_estimate=budget.input_with_framing,
                output_reserved=self.budget.response_tokens,usage_kind='local_estimates_and_separate_provider_usage'))
            self.status='ready';self.inflight=None;return value
        self.status='paused_invalid_response';self.save();return None

    def _inventory_tasks(self):
        tasks=[]
        for visual_id in self.artifacts:
            sources=list(self._source(visual_id).items());cursor=0
            while cursor<len(sources):
                end=cursor;best=None
                while end<len(sources):
                    if end>cursor and sum(len(t.encode()) for _,t in sources[cursor:end+1])>self.config.inventory_source_tokens:break
                    values=[dict(ref=key,text=value,role='primary') for key,value in sources[cursor:end+1]]
                    record=dict(visual_id=visual_id,source=values)
                    if not self._fits('inventory',[record]):break
                    best=record;end+=1
                if best is None:raise ValueError('An atomic source block cannot fit source-first inventory')
                if cursor:
                    previous=dict(ref=sources[cursor-1][0],text=sources[cursor-1][1],role='read_only_context')
                    candidate=dict(best,source=[previous]+best['source'])
                    if self._fits('inventory',[candidate]):best=candidate
                tasks.append(best);cursor=end
        return self._batch(tasks,'inventory')

    def _batch(self,records,task):
        batches=[];current=[]
        for record in records:
            if current and (len(current)>=self.config.max_batch_visuals or record['visual_id'] in {r['visual_id'] for r in current} or not self._fits(task,current+[record])):
                batches.append(current);current=[]
            if not self._fits(task,[record]):raise ValueError('Required verification evidence cannot fit')
            current.append(record)
        if current:batches.append(current)
        return batches

    def _verify_record(self,visual_id,facts,claim_list):
        record=self._record(visual_id);source=self._source(visual_id)
        needed=set(r for fact in facts for r in fact['refs'])|set(r for claim in claim_list for r in claim['refs'])
        if not needed:needed=set(source)
        return dict(visual_id=visual_id,template=record['type'],template_constraint=TEMPLATE_CONSTRAINTS[record['type']],
            source=[dict(ref=r,text=source[r]) for r in source if r in needed],facts=facts,claims=claim_list,visual=record)

    def _verification_tasks(self,visuals):
        tasks=[]
        for visual_id in visuals:
            all_claims,_,_=claims(self._record(visual_id),visual_id,self._source(visual_id));facts=self.inventories[visual_id]
            full=self._verify_record(visual_id,facts,all_claims)
            if self._fits('verify',[full]):tasks.append(full);continue
            # Each fact and generated claim is owned by exactly one verification
            # part. Global title/structure evidence is never silently narrowed.
            atoms=[('fact',f) for f in facts]+[('claim',c) for c in all_claims];current_f=[];current_c=[]
            for kind,value in atoms:
                f=current_f+([value] if kind=='fact' else []);c=current_c+([value] if kind=='claim' else [])
                candidate=self._verify_record(visual_id,f,c)
                if not self._fits('verify',[candidate]):
                    if current_f or current_c:tasks.append(self._verify_record(visual_id,current_f,current_c))
                    current_f=[value] if kind=='fact' else [];current_c=[value] if kind=='claim' else []
                    if not self._fits('verify',[self._verify_record(visual_id,current_f,current_c)]):raise ValueError('Cross-block fact or visual claim requires more evidence capacity')
                else:current_f,current_c=f,c
            if current_f or current_c:tasks.append(self._verify_record(visual_id,current_f,current_c))
        return self._batch(tasks,'verify')

    def _parse_inventories(self,value,data):
        fields(value,('records',))
        if not isinstance(value['records'],list) or len(value['records'])!=len(data):raise ValueError('Missing source inventories')
        expected={r['visual_id']:r for r in data};result={}
        for row in value['records']:
            visual_id=row.get('visual_id')
            if visual_id not in expected or visual_id in result:raise ValueError('Unknown/duplicate inventory visual')
            request=expected[visual_id];source={s['ref']:s['text'] for s in request['source']}
            primary=[s['ref'] for s in request['source'] if s['role']=='primary']
            facts,mapping=inventory(row,visual_id,source,self.index.fingerprint,max_facts=self.config.max_facts_per_part,primary=primary)
            result[visual_id]=facts
        return result

    def _parse_reports(self,value,data):
        fields(value,('records',))
        if not isinstance(value['records'],list) or len(value['records'])!=len(data):raise ValueError('Missing semantic reports')
        expected={r['visual_id']:r for r in data};result={}
        for row in value['records']:
            visual_id=row.get('visual_id')
            if visual_id not in expected or visual_id in result:raise ValueError('Unknown/duplicate verification visual')
            request=expected[visual_id];_,items,support=claims(self._record(visual_id),visual_id,self._source(visual_id))
            result[visual_id]=report(row,visual_id,request['facts'],request['claims'],items,support,{s['ref']:s['text'] for s in request['source']})
        return result

    def _compact_tasks(self):
        tasks=[]
        for visual_id in self.artifacts:
            record=self.records[visual_id];source=self._source(visual_id);claim_list,_,_=claims(record,visual_id,source)
            tasks.append(dict(visual_id=visual_id,template=record['type'],template_constraint=TEMPLATE_CONSTRAINTS[record['type']],
                source=[dict(ref=k,text=v,role='primary') for k,v in source.items()],visual=record,claims=claim_list))
        return self._batch(tasks,'compact')

    def _parse_compact(self,value,data):
        fields(value,('records',));expected={r['visual_id']:r for r in data};result={}
        if not isinstance(value['records'],list) or len(value['records'])!=len(data):raise ValueError('Missing compact results')
        for row in value['records']:
            fields(row,('visual_id','complete','facts','coverage','grounding','issues'))
            visual_id=row['visual_id']
            if visual_id not in expected or visual_id in result:raise ValueError('Unknown/duplicate compact visual')
            request=expected[visual_id];source={s['ref']:s['text'] for s in request['source']}
            facts,mapping=inventory({k:row[k] for k in ('visual_id','complete','facts')},visual_id,source,self.index.fingerprint,max_facts=self.config.max_facts_per_part)
            _,items,support=claims(self.records[visual_id],visual_id,source)
            semantic=report({k:row[k] for k in ('visual_id','coverage','grounding','issues')},visual_id,facts,request['claims'],items,support,source,fact_mapping=mapping)
            result[visual_id]=dict(facts=facts,report=semantic)
        return result

    def _aggregate(self,visual_id):
        parts=self.parts[visual_id]
        raw=dict(visual_id=visual_id,coverage=[row for part in parts for row in part['coverage']],grounding=[row for part in parts for row in part['grounding']],
                 issues=list({i['id']:i for part in parts for i in part['issues']}.values()))
        # Revalidate complete global fact/claim accounting after part reconciliation.
        all_claims,items,support=claims(self._record(visual_id),visual_id,self._source(visual_id))
        raw['issues']=[{k:v for k,v in i.items() if k!='id'} for i in raw['issues']]
        return report(raw,visual_id,self.inventories[visual_id],all_claims,items,support,self._source(visual_id))

    def _finish_report(self,visual_id,semantic):
        if visual_id in self.pending:
            candidate=self.pending[visual_id];previous=self.evaluations[visual_id]
            old_good={r['fact_id'] for r in previous['coverage'] if r['status'] in PRESERVED}
            new_good={r['fact_id'] for r in semantic['coverage'] if r['status'] in PRESERVED}
            old_claims,_,_=claims(self.records[visual_id],visual_id,self._source(visual_id))
            new_claims,_,_=claims(candidate['record'],visual_id,self._source(visual_id))
            def bad_paths(evaluation,values):
                bad={r['claim_id'] for r in evaluation['grounding'] if r['status'] not in SUPPORTED}
                return {c['path'] for c in values if c['id'] in bad}
            old_bad=bad_paths(previous,old_claims);new_bad=bad_paths(semantic,new_claims)
            issue_scopes=lambda evaluation:{canonical([i['type'],sorted(i['fact_ids']),sorted(i['item_ids'])]) for i in evaluation['issues']}
            decision=assess(self.inventories[visual_id],semantic,self.policy)
            improves=decision['accepted'] or new_good>old_good or new_bad<old_bad
            safe=old_good<=new_good and new_bad<=old_bad and issue_scopes(semantic)<=issue_scopes(previous)
            audit=dict(round=self.rounds[visual_id],candidate_hash=digest(canonical(candidate['record']).encode()),
                before_hash=digest(canonical(self.records[visual_id]).encode()),patches=candidate['audit'],report=semantic,
                source_report=copy.deepcopy(previous),accepted=safe and improves)
            self.repairs[visual_id].append(audit)
            if safe and improves:self.records[visual_id]=candidate['record'];self.evaluations[visual_id]=semantic
            else:self.escalations[visual_id]=dict(status='needs_regeneration',reason='Repair introduced regression or failed to improve identified defects')
            del self.pending[visual_id]
        else:self.evaluations[visual_id]=semantic

    def _repair(self,visual_id):
        semantic=self.evaluations[visual_id];issues=semantic['issues']
        if not issues:
            self.escalations[visual_id]=dict(status='needs_regeneration',reason='Acceptance gate failed without a safely scoped patch target');return True
        data=dict(visual_id=visual_id,visual=self.records[visual_id],issues=issues,facts=self.inventories[visual_id],
            source=[dict(ref=k,text=v) for k,v in self._source(visual_id).items()])
        result=self._call('repair',data,lambda value:apply_repairs(self.records[visual_id],value,visual_id,issues,self._source(visual_id),self.artifacts[visual_id]['category'],
            max_items=self.generation.config.max_items,max_depth=self.generation.config.max_depth))
        if result is None:return False
        revised,audit,escalation=result;self.rounds[visual_id]+=1
        if escalation:self.escalations[visual_id]=escalation
        else:self.pending[visual_id]=dict(record=revised,audit=audit)
        return True

    def _whole_lecture(self):
        labels={};candidates=set()
        for visual_id,record in self.records.items():
            for node in item_map(record).values():
                if 'label' in node and 'desc' in node:
                    key=node['label'].casefold()
                    if key in labels and labels[key][0]!=visual_id and labels[key][1]!=node['desc']:candidates.update([visual_id,labels[key][0]])
                    labels[key]=(visual_id,node['desc'])
        continuations={}
        for visual_id,group in self.group_by_visual.items():
            for c in group['continuation_groups']:continuations.setdefault(c,[]).append(visual_id)
        for values in continuations.values():
            if len(values)>1:candidates.update(values)
        if not candidates or not self.config.whole_lecture_check:
            self.consistency=dict(status='no_flagged_semantic_reconciliation' if self.config.whole_lecture_check else 'disabled',issues=[],scope='deterministic_candidate_screening_only');return True
        data=[dict(visual_id=v,visual=self.records[v],facts=self.inventories[v],source=[dict(ref=k,text=t) for k,t in self._source(v).items()]) for v in sorted(candidates)]
        def parse(value):
            fields(value,('status','issues'))
            if value['status'] not in {'consistent','unresolved'} or not isinstance(value['issues'],list):raise ValueError('Invalid lecture consistency result')
            for issue in value['issues']:
                fields(issue,('visual_ids','message'))
                if not isinstance(issue['visual_ids'],list) or not issue['visual_ids'] or any(v not in candidates for v in issue['visual_ids']):raise ValueError('Unknown consistency visual')
                from .generation_schema import text
                text(issue['message'],500)
            if value['status']=='consistent' and value['issues']:raise ValueError('Contradictory consistency result')
            return value
        value=self._call('consistency',data,parse)
        if value is None:return False
        self.consistency=value;return True

    def run(self,*,retry_paused=False):
        if self.status in {'complete_accepted','complete_unresolved'}:self.cache_reuse+=1;return self.status
        if self.status.startswith('paused') or self.status in {'request_in_flight','unresolved_capacity'}:
            if not retry_paused:return self.status
            self.status='ready'
        while True:
            if self.phase in {'inventory','compact','verify'}:
                if not self.tasks:
                    try:
                        self.tasks=self._inventory_tasks() if self.phase=='inventory' else self._compact_tasks() if self.phase=='compact' else self._verification_tasks(list(self.pending) if self.pending else [v for v in self.artifacts if v not in self.evaluations])
                    except ValueError:
                        self.status='unresolved_capacity';self.history.append(dict(event='evidence_capacity_unresolved',phase=self.phase));self.save();return self.status
                    self.cursor=0;self.parts={}
                while self.cursor<len(self.tasks):
                    data=self.tasks[self.cursor];task=self.phase
                    cache_key=digest(canonical([self.prompt_hashes[task],data]).encode())
                    if task=='inventory' and cache_key in self.inventory_cache:
                        value=self.inventory_cache[cache_key];self.cache_reuse+=1
                    else:
                        validator=(lambda raw:self._parse_inventories(raw,data)) if task=='inventory' else (lambda raw:self._parse_compact(raw,data)) if task=='compact' else (lambda raw:self._parse_reports(raw,data))
                        value=self._call(task,data,validator)
                        if value is None:return self.status
                    previous=copy.deepcopy((self.inventories,self.inventory_cache,self.parts,self.evaluations,self.cursor))
                    if task=='inventory':
                        self.inventory_cache[cache_key]=value
                        for v,facts in value.items():
                            known={f['id']:f for f in self.inventories[v]}
                            for fact in facts:
                                if fact['id'] in known and canonical(known[fact['id']])!=canonical(fact):raise ValueError('Conflicting source fact inventory')
                                known[fact['id']]=fact
                            self.inventories[v]=list(known.values())
                    elif task=='compact':
                        for v,result in value.items():self.inventories[v]=result['facts'];self.evaluations[v]=result['report']
                    else:
                        for v,semantic in value.items():self.parts.setdefault(v,[]).append(semantic)
                    self.cursor+=1
                    try:self.save()
                    except Exception:
                        self.inventories,self.inventory_cache,self.parts,self.evaluations,self.cursor=previous;self.status='paused_persistence';raise
                transition=copy.deepcopy((self.phase,self.records,self.evaluations,self.pending,self.repairs,self.escalations,self.tasks,self.cursor,self.parts))
                if self.phase=='inventory':self.phase='verify'
                else:
                    if self.phase=='verify':
                        for visual_id in list(self.parts):self._finish_report(visual_id,self._aggregate(visual_id))
                    self.phase='repair'
                self.tasks=[];self.cursor=0;self.parts={}
                try:self.save()
                except Exception:
                    self.phase,self.records,self.evaluations,self.pending,self.repairs,self.escalations,self.tasks,self.cursor,self.parts=transition
                    self.status='paused_persistence';raise
            elif self.phase=='repair':
                for v in self.artifacts:
                    if v in self.pending:continue
                    if v in self.escalations or assess(self.inventories[v],self.evaluations[v],self.policy)['accepted']:continue
                    if self.rounds[v]>=self.config.repair_rounds:
                        self.escalations[v]=dict(status='needs_regeneration',reason='Bounded semantic repair rounds exhausted');continue
                    previous=copy.deepcopy((self.pending,self.rounds,self.escalations))
                    if not self._repair(v):return self.status
                    try:self.save()
                    except Exception:
                        self.pending,self.rounds,self.escalations=previous;self.status='paused_persistence';raise
                if self.pending:self.phase='verify';self.tasks=[];self.save();continue
                self.phase='lecture';self.save()
            elif self.phase=='lecture':
                if self.consistency is None and not self._whole_lecture():return self.status
                all_pass=all(assess(self.inventories[v],self.evaluations[v],self.policy)['accepted'] and v not in self.escalations for v in self.artifacts)
                unresolved_generation=any(a['status']!='preserved_nonvisual' for a in self.skipped.values())
                consistent=self.consistency['status'] in {'consistent','no_flagged_semantic_reconciliation'}
                self.status='complete_accepted' if all_pass and not unresolved_generation and consistent else 'complete_unresolved'
                self.phase='done';self.save();return self.status
            else:raise ValueError('Unknown verification phase')

    def results(self):
        values=[]
        for visual_id,artifact in self.artifacts.items():
            semantic=self.evaluations.get(visual_id)
            if semantic is None:
                values.append(dict(visual_id=visual_id,acceptance=dict(accepted=False,reasons=['verification_incomplete']),generation_hash=self.original_hashes[artifact['optimized_segment_id']]));continue
            record=self.records[visual_id];revision_hash=digest(canonical(record).encode())
            values.append(dict(version=VERIFICATION_VERSION,visual_id=visual_id,generation_hash=self.original_hashes[artifact['optimized_segment_id']],
                revision_id='VR'+digest((visual_id+revision_hash).encode())[:24],revision_hash=revision_hash,source_id=self.index.snapshot.source_id,
                source_sha256=self.index.snapshot.sha256,template=record['type'],record=copy.deepcopy(record),
                adapter=convert(record,visual_id),fact_inventory=copy.deepcopy(self.inventories[visual_id]),report=copy.deepcopy(semantic),
                coverage_ledger=[dict(fact,coverage=next(r for r in semantic['coverage'] if r['fact_id']==fact['id']),
                    issues=[i['id'] for i in semantic['issues'] if fact['id'] in i['fact_ids']],
                    repair_rounds=self.rounds[visual_id],reverification='performed' if self.repairs[visual_id] else 'not_required_or_not_completed') for fact in self.inventories[visual_id]],
                metrics=coverage_metrics(self.inventories[visual_id],semantic),repairs=copy.deepcopy(self.repairs[visual_id]),
                density_diagnostics=dict(items=len(item_map(record))-len(record['support']),
                    longest_description=max((len(i.get('desc','')) for i in item_map(record).values()),default=0),
                    graph_relations=len(record['data'].get('relations',[])),identified_essential_facts=sum(f['priority'] in {'critical','essential'} for f in self.inventories[visual_id]),
                    registry_recommended_items=REGISTRY[record['type']].recommended_items,actual_browser_readability_verified=False),
                acceptance=assess(self.inventories[visual_id],semantic,self.policy) if visual_id not in self.escalations else dict(accepted=False,reasons=['escalation'],escalation=self.escalations[visual_id]),
                deterministic_validation='passed',semantic_verification='verifier_assessed_not_expert_validated',
                model=self.verifier.config.model,prompt_hashes=self.prompt_hashes,inventory_mode=self.config.mode))
        return values

    def metrics(self):
        results=self.results();facts={};priority={'critical':0,'essential':1,'supporting':2,'redundant':3}
        for rows in self.inventories.values():
            for fact in rows:
                if fact['id'] not in facts or priority[fact['priority']]<priority[facts[fact['id']]['priority']]:facts[fact['id']]=fact
        outcomes={}
        for semantic in self.evaluations.values():
            for row in semantic['coverage']:outcomes.setdefault(row['fact_id'],set()).add(row['status'])
        ratio=lambda values:sum(values)/len(values) if values else None
        scopes=[f for f in facts.values() if f['priority']!='redundant']
        visible=lambda f:any(s.startswith('visible_') for s in outcomes.get(f['id'],set()))
        supporting=lambda f:any(s.startswith('support_') for s in outcomes.get(f['id'],set()))
        preserved=lambda f:bool(outcomes.get(f['id'],set())&PRESERVED)
        referenced=set()
        def references(value,artifact):
            if isinstance(value,dict):
                for key,child in value.items():
                    if key=='refs' or key.endswith('_refs'):
                        referenced.update(artifact['source_aliases'][r]['id'] for r in child)
                    else:references(child,artifact)
            elif isinstance(value,list):
                for child in value:references(child,artifact)
        for v,record in self.records.items():references(record,self.artifacts[v])
        grounding=[row['status'] in SUPPORTED for semantic in self.evaluations.values() for row in semantic['grounding']]
        return dict(status=self.status,source_range_ownership=1,identified_distinct_facts=len(facts),inventory_exhaustiveness_guaranteed=False,
            lecture_visible_fact_coverage=ratio([visible(f) for f in scopes]),
            lecture_supporting_fact_coverage=ratio([supporting(f) for f in scopes]),
            lecture_essential_fact_coverage=ratio([preserved(f) for f in scopes if f['priority']=='essential']),
            lecture_critical_fact_coverage=ratio([preserved(f) for f in scopes if f['priority']=='critical']),
            lecture_generated_claim_grounding=ratio(grounding),source_reference_coverage=len(referenced)/max(1,len(self.index.units)),
            semantic_denominator='distinct identified fact IDs in evaluated generated visuals and their linked support; standalone N excluded',
            standalone_nonvisual=[dict(segment_id=g['id'],source_id=self.index.snapshot.source_id,source_hash=self.index.snapshot.sha256,
                start=g['start'],end=g['end'],source_start=g['source_start'],source_end=g['source_end'],
                supplementary_links=g['supplementary_links'],status='preserved_nonvisual',semantically_represented=False)
                for g in self.groups if self.skipped.get(g['id'],{}).get('status')=='preserved_nonvisual'],
            visuals=len(self.artifacts),accepted_visuals=sum(r['acceptance']['accepted'] for r in results),
            nonvisual_segments=sum(a['status']=='preserved_nonvisual' for a in self.skipped.values()),
            unresolved_generation_segments=sum(a['status']!='preserved_nonvisual' for a in self.skipped.values()),
            per_visual={r['visual_id']:r.get('metrics',{}) for r in results},lecture_consistency=self.consistency,
            requests=self.requests,usage=self.usage,duration_seconds=self.duration,cache_reuse=self.cache_reuse,
            repair_rounds=self.rounds,mode=self.config.mode,shared_model_reasoning_independence=False)

    def artifact(self):
        """Detached auditable lecture result; completion and acceptance are separate."""
        return json.loads(canonical(dict(version=VERIFICATION_VERSION,processing_status=self.status,
            source_id=self.index.snapshot.source_id,source_sha256=self.index.snapshot.sha256,index=self.index.fingerprint,
            optimized_manifest_hash=self.generation.optimized_hash,provisional_manifest_hash=self.generation.provisional_hash,
            generation_artifact_hashes=self.original_hashes,model=self.verifier.config.model,prompt_hashes=self.prompt_hashes,
            acceptance=dict(accepted=self.status=='complete_accepted',scope='identified_inventory_and_enumerated_claims',
                standalone_nonvisual_semantically_verified=False,inventory_exhaustiveness_guaranteed=False),
            visuals=self.results(),preserved_generation_outcomes=self.skipped,metrics=self.metrics())))

    @classmethod
    def resume(cls,generation,optimizer,verifier,metadata,**options):
        job=cls(generation,optimizer,verifier,metadata,**options)
        record=job.store.latest(job.run_id)
        if not isinstance(record,ReadingCheckpoint) or record.stage!='verification_v1' or record.schema_version!=1 or record.run_id!=job.run_id:raise ValueError('No compatible verification checkpoint')
        value=strict_json(record.state_json)
        if record.config_sha256!=job.config_hash or record.source_hashes!=((job.index.snapshot.source_id,job.index.snapshot.sha256),):raise ValueError('Verification source/configuration changed')
        for key in ('config_hash','source_hash','index','optimized_hash','original_hashes','prompt_hashes','inventory_version','verification_version'):
            if value[key]!=job._save_state()[key]:raise ValueError('Verification checkpoint binding mismatch: '+key)
        if set(value['records'])!=set(job.records) or set(value['inventories'])!=set(job.records):raise ValueError('Verification artifact set mismatch')
        def verify_facts(v,facts):
            checked,_=inventory(dict(visual_id=v,complete=True,facts=facts),v,job._source(v),job.index.fingerprint,max_facts=max(len(facts),job.config.max_facts_per_part))
            if canonical(checked)!=canonical(facts):raise ValueError('Persisted fact identity mismatch')
        for v,facts in value['inventories'].items():
            if facts:verify_facts(v,facts)
            job.inventories[v]=facts
        def verify_report(v,semantic,content):
            raw=copy.deepcopy(semantic);raw['issues']=[{k:x for k,x in i.items() if k!='id'} for i in raw['issues']]
            claim_list,items,support=claims(content,v,job._source(v))
            checked=report(raw,v,job.inventories[v],claim_list,items,support,job._source(v))
            if canonical(checked)!=canonical(semantic):raise ValueError('Persisted issue/report identity mismatch')
        def replay_patch(v,candidate,source_report):
            patches=[]
            for audit in candidate['audit']:
                operation=audit['operation'];after=audit['after'];before=audit['before']
                field={'replace_title':'title','replace_description':'desc','replace_label':'label','replace_value':'value','replace_support_text':'text','replace_refs':'refs'}.get(operation)
                replacement=after[field] if field else audit['added_support'] if operation=='add_support' else None
                evidence=audit['evidence_refs']
                patches.append(dict(issue_id=audit['issue_id'],operation=operation,item_id=audit['item_id'],value=replacement,refs=evidence))
            repaired,audit,escalation=apply_repairs(job.records[v],dict(visual_id=v,repairs=patches,escalation=None),v,source_report['issues'],job._source(v),job.artifacts[v]['category'],max_items=generation.config.max_items,max_depth=generation.config.max_depth)
            if canonical(audit)!=canonical(candidate['audit']) or canonical(repaired)!=canonical(candidate['record']):raise ValueError('Persisted repair patch replay mismatch')
        for v,audits in value['repairs'].items():
            if v not in job.records:raise ValueError('Unknown repaired visual')
            for audit in audits:
                verify_report(v,audit['source_report'],job.records[v])
                candidate=dict(audit=audit['patches'])
                # Reconstruct the candidate from its exact issue-scoped before/after
                # values. No accepted revision is trusted merely because it is saved.
                current=copy.deepcopy(job.records[v]);items=item_map(current);items['@title']=dict(title=current['title'])
                for patch in candidate['audit']:
                    target=items[patch['item_id']]
                    if canonical(target)!=canonical(patch['before']):raise ValueError('Repair before-value mismatch')
                    if patch['operation']=='replace_title':current['title']=patch['after']['title']
                    elif patch['operation']=='remove_relation':current['data']['relations']=[r for r in current['data']['relations'] if r['id']!=patch['item_id']]
                    elif patch['operation']=='add_support':current['support'].append(patch['added_support'])
                    else:target.clear();target.update(copy.deepcopy(patch['after']))
                    items=item_map(current);items['@title']=dict(title=current['title'])
                candidate['record']=current
                replay_patch(v,candidate,audit['source_report']);verify_report(v,audit['report'],current)
                job.evaluations[v]=audit['source_report'];job.pending[v]=candidate;job.rounds[v]=audit['round']
                job._finish_report(v,audit['report'])
                if canonical(job.repairs[v][-1])!=canonical(audit):raise ValueError('Repair acceptance/history mismatch')
            if canonical(job.records[v])!=canonical(value['records'][v]):raise ValueError('Repaired revision integrity mismatch')
        for v,content in value['records'].items():
            source=job._source(v)
            validate_record(content,job.artifacts[v]['record']['segment_id'],job.artifacts[v]['category'],source,max_items=generation.config.max_items,max_depth=generation.config.max_depth)
            if not value['repairs'].get(v) and canonical(content)!=canonical(job.artifacts[v]['record']):raise ValueError('Unproven modified generation content')
        for v,semantic in value['evaluations'].items():
            if v not in job.records:raise ValueError('Unknown evaluated visual')
            verify_report(v,semantic,value['records'][v])
        for v,candidate in value['pending'].items():
            if v not in job.records:raise ValueError('Unknown pending repair')
            replay_patch(v,candidate,value['evaluations'][v])
        for key in ('phase','status','records','inventories','inventory_cache','evaluations','pending','repairs','rounds','escalations','tasks','cursor','parts','history','inflight','consistency','requests','usage','duration'):
            setattr(job,key,value[key])
        if job.phase not in {'inventory','compact','verify','repair','lecture','done'}:raise ValueError('Unknown persisted verification phase')
        if not isinstance(job.status,str) or job.status not in {'ready','request_in_flight','unresolved_capacity','complete_accepted','complete_unresolved'} and not job.status.startswith('paused_'):raise ValueError('Unknown persisted verification status')
        if set(job.rounds)!=set(job.artifacts) or set(job.repairs)!=set(job.artifacts) or set(job.usage)!=set(asdict(verifier.accounting)):raise ValueError('Checkpoint accounting/repair set mismatch')
        if any(type(v) is not int or v<0 for v in job.usage.values()) or type(job.requests) is not int or job.requests<0:raise ValueError('Invalid verifier accounting')
        for v,escalation in job.escalations.items():
            from .visual_repair import ESCALATIONS
            from .generation_schema import text
            fields(escalation,('status','reason'))
            if v not in job.artifacts or escalation['status'] not in ESCALATIONS:raise ValueError('Unknown persisted escalation')
            text(escalation['reason'],240)
        if not 0<=job.cursor<=len(job.tasks):raise ValueError('Verification cursor mismatch')
        for v,count in job.rounds.items():
            if v not in job.artifacts or type(count) is not int or not 0<=count<=job.config.repair_rounds:raise ValueError('Invalid repair counter')
        if job.phase in {'inventory','compact','verify'} and job.tasks:
            expected=job._inventory_tasks() if job.phase=='inventory' else job._compact_tasks() if job.phase=='compact' else job._verification_tasks(list(job.pending) if job.pending else [v for v in job.artifacts if v not in job.evaluations])
            if canonical(expected)!=canonical(job.tasks):raise ValueError('Persisted verification task/evidence mismatch')
        # Revalidate completed parts against their exact request and complete IDs.
        seen_parts={}
        if job.phase=='verify':
            for data in job.tasks[:job.cursor]:
                for request in data:
                    v=request['visual_id'];i=seen_parts.get(v,0)
                    semantic=job.parts[v][i];seen_parts[v]=i+1
                    raw=copy.deepcopy(semantic);raw['issues']=[{k:x for k,x in issue.items() if k!='id'} for issue in raw['issues']]
                    checked=job._parse_reports(dict(records=[raw]),[request])[v]
                    if canonical(checked)!=canonical(semantic):raise ValueError('Persisted verification part mismatch')
            if any(len(parts)!=seen_parts.get(v,0) for v,parts in job.parts.items()):raise ValueError('Unexpected verification parts')
        for key,cached in job.inventory_cache.items():
            for v,facts in cached.items():
                if v not in job.artifacts:raise ValueError('Unknown cached inventory')
                verify_facts(v,facts)
        if job.config.mode=='strict':
            source_tasks=job._inventory_tasks()
            completed=source_tasks[:job.cursor] if job.phase=='inventory' else source_tasks
            reconstructed={v:{} for v in job.artifacts}
            expected_cache_keys=set()
            for data in completed:
                cache_key=digest(canonical([job.prompt_hashes['inventory'],data]).encode());expected_cache_keys.add(cache_key)
                if cache_key not in job.inventory_cache:raise ValueError('Missing completed source inventory checkpoint')
                cached=job.inventory_cache[cache_key]
                raw=dict(records=[dict(visual_id=v,complete=True,facts=facts) for v,facts in cached.items()])
                checked=job._parse_inventories(raw,data)
                if canonical(checked)!=canonical(cached):raise ValueError('Cached source inventory/evidence mismatch')
                for v,facts in cached.items():
                    for fact in facts:reconstructed[v][fact['id']]=fact
            if set(job.inventory_cache)!=expected_cache_keys:raise ValueError('Unexpected source inventory cache revision')
            if canonical({v:list(facts.values()) for v,facts in reconstructed.items()})!=canonical(job.inventories):raise ValueError('Source inventory lost or gained fact records')
        elif job.phase=='compact':
            completed={r['visual_id'] for data in job.tasks[:job.cursor] for r in data}
            if completed!={v for v,facts in job.inventories.items() if facts} or completed!=set(job.evaluations):raise ValueError('Compact verification progress mismatch')
        job.parent=record.checkpoint_id;job.revision=value['state']['revision']
        if job.status=='request_in_flight':job.status='paused_uncertain_request'
        if job.status in {'complete_accepted','complete_unresolved'}:
            if job.phase!='done' or set(job.evaluations)!=set(job.artifacts) or job.pending:raise ValueError('Incomplete finalized verification')
            accepted=all(assess(job.inventories[v],job.evaluations[v],job.policy)['accepted'] and v not in job.escalations for v in job.artifacts)
            accepted=accepted and not any(a['status']!='preserved_nonvisual' for a in job.skipped.values()) and job.consistency['status'] in {'consistent','no_flagged_semantic_reconciliation'}
            if (job.status=='complete_accepted')!=accepted:raise ValueError('Persisted acceptance mismatch')
            if value['final_result_hash']!=digest(canonical(job.results()).encode()):raise ValueError('Final verification artifact hash mismatch')
            job.cache_reuse=1
        return job


def prepare_verification(generation,optimizer,verifier,metadata,*,environment=None,**options):
    import os
    env=os.environ if environment is None else environment
    flag=env.get('NOETRA_INFOGRAPHIC_ENGINE_ENABLED','false').strip().lower()
    if flag=='false':return None
    if flag!='true':raise ValueError('NOETRA_INFOGRAPHIC_ENGINE_ENABLED must be true or false')
    return VerificationJob(generation,optimizer,verifier,metadata,**options)
