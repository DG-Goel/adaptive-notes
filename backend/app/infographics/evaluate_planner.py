"""Opt-in CLI: python -m app.infographics.evaluate_planner --dry-run."""
import argparse
import json
import os
from pathlib import Path
from .source_index import build_index,digest
from .contracts import SourceSnapshot
from .segmentation_evaluation import evaluate


def main(argv=None):
    parser=argparse.ArgumentParser()
    parser.add_argument('--dry-run',action='store_true')
    parser.add_argument('--live',action='store_true')
    parser.add_argument('--fixture',action='append')
    parser.add_argument('--output',type=Path,default=Path('data/infographics/evaluation'))
    parser.add_argument('--max-requests',type=int,default=10)
    parser.add_argument('--max-tokens',type=int,default=100000)
    parser.add_argument('--repeat',action='store_true')
    parser.add_argument('--retry-paused',action='store_true')
    args=parser.parse_args(argv)
    if args.max_requests<=0 or args.max_tokens<=0: parser.error('Budgets must be positive')
    data=json.loads((Path(__file__).parent/'evaluation/fixtures_v1.json').read_text(encoding='utf-8'))
    fixtures=[f for f in data['fixtures'] if not args.fixture or f['id'] in args.fixture]
    if not fixtures: parser.error('No fixtures selected')
    if args.dry_run or not args.live:
        result=dict(mode='dry_run',fixtures=[f['id'] for f in fixtures],network_requests=0,
                    max_requests=args.max_requests,max_tokens=args.max_tokens,live_quality='pending')
        print(json.dumps(result)); return result
    from .planner_init import initialize_planner
    from .token_budget import TokenBudgetManager,ModelLimits
    from .checkpoints import SQLiteCheckpointStore
    from .segmentation import SegmentationJob
    from dataclasses import replace
    initialized=initialize_planner(dict(os.environ,NOETRA_INFOGRAPHIC_ENGINE_ENABLED='true'))
    client,metadata=initialized
    try:
        # Reserve each call's entire conservative RPM/TPM attempt envelope before
        # dispatch; set transport attempts to one to make the harness cap strict.
        client.config=replace(client.config,max_attempts=1)
        print(json.dumps(dict(model=metadata.name,input_limit=metadata.input_tokens,output_limit=metadata.output_tokens)))
        for fixture in fixtures:
            target=args.output/(fixture['id']+'.json')
            if target.exists() and not args.repeat and json.loads(target.read_text(encoding='utf-8')).get('status')=='complete': continue
            content='\n\n'.join(fixture['blocks']).encode()
            index=build_index(SourceSnapshot(fixture['id'],digest(content),content,'text/markdown'))
            store=SQLiteCheckpointStore(args.output/'checkpoints')
            run_id=fixture['id']+('-repeat-'+os.urandom(4).hex() if args.repeat else '')
            budget=TokenBudgetManager(ModelLimits.from_client(client.config,metadata))
            job=SegmentationJob.resume(type('Reader',(),{'snapshot':lambda self,_:index.snapshot})(),
                fixture['id'],client,budget,store,run_id) if store.latest(run_id) else SegmentationJob(index,client,budget,store,run_id)
            responses=[]
            original_complete=client.complete
            def capture(*a,**kw):
                response=original_complete(*a,**kw)
                import re
                safe=response.text.replace(client.config.api_key,'[REDACTED]')
                safe=re.sub(r'AIza[\w-]+','[REDACTED]',safe)
                responses.append(safe)
                return response
            client.complete=capture
            while job.status in {'ready','request_in_flight'} or (args.retry_paused and job.status.startswith('paused')):
                usage=client.accounting
                envelope=client.config.context_tokens
                if usage.attempts+2>args.max_requests or usage.reserved_tokens+2*envelope>args.max_tokens:
                    break
                prior=job.status
                job.step(retry_paused=args.retry_paused)
                if job.status.startswith('paused'): break
            client.complete=original_complete
            result=dict(fixture=fixture['id'],status=job.status,manifest=job.manifest,
                        responses=responses,metrics=evaluate(fixture,job.manifest),performance=job.metrics())
            args.output.mkdir(parents=True,exist_ok=True)
            # Fixture content is synthetic; exact credentials and Google key-like
            # strings are redacted from the response copies before persistence.
            target.write_text(json.dumps(result,indent=2),encoding='utf-8')
    finally: client.close()


if __name__=='__main__': main()
