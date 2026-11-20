"""Opt-in Phase 4 evaluation; defaults to network-free dry run."""
import argparse
from dataclasses import replace
import json
import os
from pathlib import Path
from .optimization_evaluation import fixture_set,fragmented_job,compare


def main(argv=None):
    parser=argparse.ArgumentParser()
    parser.add_argument('--live',action='store_true')
    parser.add_argument('--dry-run',action='store_true')
    parser.add_argument('--fixture',action='append')
    parser.add_argument('--max-requests',type=int,default=10)
    parser.add_argument('--max-tokens',type=int,default=100000)
    parser.add_argument('--retry-paused',action='store_true')
    parser.add_argument('--output',type=Path,default=Path('data/infographics/optimization-evaluation'))
    args=parser.parse_args(argv)
    if args.max_requests<1 or args.max_tokens<1: parser.error('Positive budgets required')
    fixtures=[f for f in fixture_set()['fixtures'] if not args.fixture or f['id'] in args.fixture]
    if not fixtures: parser.error('No fixtures selected')
    if not args.live or args.dry_run:
        result=dict(mode='dry_run',fixtures=[f['id'] for f in fixtures],requests=0,live_quality='pending',
                    input_provenance='deliberately fragmented fixture input, not model-generated segmentation')
        print(json.dumps(result)); return result
    from .planner_init import initialize_planner
    from .optimization import OptimizationJob
    from .optimization_model import OptimizationConfig
    from .token_budget import TokenBudgetManager,ModelLimits
    from .checkpoints import SQLiteCheckpointStore
    client,metadata=initialize_planner(dict(os.environ,NOETRA_INFOGRAPHIC_ENGINE_ENABLED='true',NOETRA_INFOGRAPHIC_PLANNER_MAX_ATTEMPTS='1'))
    client.config=replace(client.config,max_attempts=1)
    original_complete=client.complete
    try:
        print(json.dumps(dict(model=metadata.name,input_limit=metadata.input_tokens,output_limit=metadata.output_tokens)))
        budget=TokenBudgetManager(ModelLimits.from_client(client.config,metadata))
        def limited_complete(*a,**kw):
            usage=client.accounting
            if usage.attempts>=args.max_requests or usage.reserved_tokens+client.config.context_tokens>args.max_tokens:
                from .clients import LocalLimitError
                raise LocalLimitError('Evaluation invocation budget exhausted')
            return original_complete(*a,**kw)
        client.complete=limited_complete
        for fixture in fixtures:
            store=SQLiteCheckpointStore(args.output/'checkpoints')
            source=fragmented_job(fixture,client,budget,store,fixture['id']+'-input')
            options=dict(store=store,run_id=fixture['id']+'-optimization',config=OptimizationConfig(max_requests=args.max_requests))
            optimizer=OptimizationJob.resume(source,**options) if store.latest(options['run_id']) else OptimizationJob(source,**options)
            optimizer.run(retry_paused=args.retry_paused)
            result=dict(fixture=fixture['id'],status=optimizer.status,manifest=json.loads(optimizer.manifest) if optimizer.status in {'complete','optimization_skipped'} else None,
                metrics=optimizer.metrics(),comparison=compare(fixture,source.manifest,optimizer.groups),
                source_provenance='deliberately fragmented annotated fixture',live_quality='experimental')
            args.output.mkdir(parents=True,exist_ok=True)
            path=args.output/(fixture['id']+'.json')
            # Append a fresh review artifact; never overwrite a successful result.
            from uuid import uuid4
            path=path.with_name(path.stem+'-'+uuid4().hex[:12]+'.json')
            with path.open('x',encoding='utf-8') as handle:
                handle.write(json.dumps(result,ensure_ascii=False,indent=2).replace(client.config.api_key,'[REDACTED]'))
    finally: client.close()


if __name__=='__main__': main()
