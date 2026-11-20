"""Task 13 wrapper around the unchanged admission/extraction/rendering mechanisms."""
import argparse
import json
from pathlib import Path
import sqlite3
import time
from run_authorized_java import run,save


def main(live=False):
    root=Path(__file__).resolve().parent
    out=Path((root/'data/output/latest_multimodal_run.txt').read_text(encoding='utf-8'))
    pre=json.loads((out/'preflight.json').read_text(encoding='utf-8'))
    ledger={}
    dbpath=root/'data/live_state/organization.sqlite'
    if dbpath.exists():
        with sqlite3.connect(dbpath) as db:
            db.row_factory=sqlite3.Row
            ledger['scheduler']=dict(db.execute('select * from scheduler').fetchone())
            ledger['organizations']=[{k:r[k] for k in ['slot','blocked','cooldown']} for r in db.execute('select * from organizations')]
            ledger['daily_usage']=[dict(r) for r in db.execute('select o.slot,count(*) attempts,sum(a.charged) charged from attempts a join operations o on o.id=a.request_id where a.completed is null or a.completed>? group by o.slot',(time.time()-86400,))]
            ledger['unresolved_operations']=[dict(r) for r in db.execute('select id,state from operations where completed is null')]
    save(out/'preflight_ledger_snapshot.json',ledger)
    try:
        summary=run(out,live=live,max_wait=65,continue_validation_failures=True,output_dir=out)
        summary.setdefault('classification','Offline preflight passed; no provider requests')
    except Exception as exc:
        summary=dict(classification='Blocked before live execution',blocker_type=type(exc).__name__,blocker=str(exc),requests_attempted=0,input_tokens=0,output_tokens=0)
        save(out/'run_summary.json',summary)
        print(json.dumps(summary),flush=True)
    old=root/'data/output/java_live_java-20261109_022409_842270'
    previous=json.loads((old/'run_summary.json').read_text(encoding='utf-8'))
    comparison=dict(old_artifact=str(old),old_classification=previous['classification'],old_completed_chunks=previous['completed_chunks'],old_total_chunks=previous['total_chunks'],old_items=previous.get('items'),
        new_classification=summary['classification'],new_items=summary.get('items'),new_completed_chunks=summary.get('completed_chunks',0),
        limitation='A blocked or partial new extraction is not a completeness improvement. No benchmark precision/recall or human readability score inferred.')
    save(out/'old_vs_new_comparison.json',comparison)
    report=['# Task 13 execution report','',json.dumps(summary,indent=2),'','## Source inventory','',json.dumps(pre,indent=2),
        '', 'All 501 visual records are retained as nonquotable, unverified candidates. Their raw readings are in the OCR review supplement and canonical provenance; unique primary candidate readings are supplied as nonquotable context limitations, never as permitted excerpts.',
        '', 'Mortgage stays VISUAL_CONTEXT_REQUIRED; conflicting path literals remain ambiguous; clipped retry output is not complete code. No topic is excluded because a visual literal is unavailable.',
        '', '## Historical comparison','',json.dumps(comparison,indent=2),'',
        'Full lecture notes/comparison are NOT complete unless every primary/recovery leaf is successful. Candidate availability is not verified content. Existing nine-representation rendering is used only for actual extracted knowledge.',
        '', '## Resume','',f'Run `.venv/Scripts/python.exe run_multimodal_notes.py --live` from backend after the exact reported admission blocker is resolved. Do not clear reservations, rotate to evade HOLD, or modify the approved manifest.',
        '', '## Modified files','', 'Added app/ingestion/multimodal_adapter.py, prepare_multimodal_run.py, run_multimodal_notes.py, tests/test_multimodal_adapter.py and this versioned run folder. Opt-in JSON branch added to app/ingestion/router.py; multimodal-only nonquotable split-leaf inventory handling added to document_authorization.py; optional output_dir added to run_authorized_java.py. Historical parsing, Task 12A schema/policy, ceilings and Stage A/B authorization checks remain in place.']
    (out/'full_execution_report.md').write_text('\n'.join(report),encoding='utf-8')
    print(json.dumps({'output':str(out),'classification':summary['classification']}),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--live',action='store_true'); main(p.parse_args().live)
