"""Synthetic, opt-in generator-only evaluation; normal invocation is a dry run."""
import argparse
from dataclasses import replace
import json
import os
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4
from .generation_fixtures import fixtures


def main(argv=None):
    parser=argparse.ArgumentParser()
    parser.add_argument('--live',action='store_true')
    parser.add_argument('--dry-run',action='store_true')
    parser.add_argument('--fixture',action='append',choices=[f['code'] for f in fixtures()])
    parser.add_argument('--category',choices=list('ABC'))
    parser.add_argument('--max-requests',type=int,default=3)
    parser.add_argument('--max-tokens',type=int,default=100000)
    parser.add_argument('--retry-paused',action='store_true')
    parser.add_argument('--output',type=Path,default=Path('data/infographics/generation-evaluation'))
    args=parser.parse_args(argv)
    if args.max_requests<1 or args.max_tokens<1:parser.error('Positive request/token budgets required')
    selected=[f for f in fixtures() if (not args.fixture or f['code'] in args.fixture) and (not args.category or f['code'][0]==args.category)]
    if not selected:parser.error('No fixtures selected')
    if args.dry_run or not args.live:
        result=dict(mode='dry_run',fixtures=[f['code'] for f in selected],requests=0,live_quality='pending',semantic_verification='pending')
        print(json.dumps(result));return result
    from .generator_init import initialize_generator
    from .clients import Accounting,LocalLimitError
    from .token_budget import TokenBudgetManager,ModelLimits
    from .optimization_evaluation import fragmented_job
    from .optimization import OptimizationJob
    from .generation import GenerationJob,GenerationConfig
    from .checkpoints import SQLiteCheckpointStore
    client,metadata=initialize_generator(dict(os.environ,NOETRA_INFOGRAPHIC_ENGINE_ENABLED='true',NOETRA_INFOGRAPHIC_GENERATOR_MAX_ATTEMPTS='1'))
    print(json.dumps(dict(model=metadata.name,input_limit=metadata.input_tokens,output_limit=metadata.output_tokens)))
    original=client.complete
    def limited(*a,**kw):
        if client.accounting.attempts>=args.max_requests or client.accounting.reserved_tokens+client.config.context_tokens>args.max_tokens:
            raise LocalLimitError('Evaluation invocation budget exhausted')
        return original(*a,**kw)
    client.complete=limited
    try:
        budget=TokenBudgetManager(ModelLimits.from_client(client.config,metadata))
        # Metadata-only local fixture stub, not a planner client or credential.
        # fragmented_job constructs annotated ranges without invoking any model.
        fixture_planner=SimpleNamespace(config=SimpleNamespace(role='planner',model=client.config.model),accounting=Accounting())
        for example in selected:
            store=SQLiteCheckpointStore(args.output/'checkpoints')
            source_fixture=dict(id=example['code'],blocks=[example['source']],acceptable_categories=[[example['code'][0]]])
            source=fragmented_job(source_fixture,fixture_planner,budget,store,example['code']+'-input')
            optimized=OptimizationJob(source,store=store,run_id=example['code']+'-optimization');optimized.run()
            options=dict(store=store,run_id=example['code']+'-generation',allow_skipped=True,config=GenerationConfig(max_requests=args.max_requests))
            job=GenerationJob.resume(optimized,client,metadata,**options) if store.latest(options['run_id']) else GenerationJob(optimized,client,metadata,**options)
            job.run(retry_paused=args.retry_paused)
            artifacts=job.artifacts()
            result=dict(fixture=example['code'],status=job.status,artifacts=artifacts,metrics=job.metrics(),
                diagnostics=dict(expected_template=example['code'],selected_templates=[a.get('type') for a in artifacts],
                    fixture_selection_match=bool(artifacts and artifacts[0].get('type')==example['code']),
                    output_truncation='not separately reported by existing transport; malformed/truncated JSON is rejected',
                    semantic_preservation='pending independent Phase 6 verification'))
            args.output.mkdir(parents=True,exist_ok=True)
            path=args.output/(example['code']+'-'+uuid4().hex[:12]+'.json')
            with path.open('x',encoding='utf-8') as handle:handle.write(json.dumps(result,indent=2,ensure_ascii=False).replace(client.config.api_key,'[REDACTED]'))
    finally:client.close()


if __name__=='__main__':main()
