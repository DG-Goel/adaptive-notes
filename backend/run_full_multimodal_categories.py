"""Resumable full lecture extraction using native Task 12A category partitions."""
from datetime import datetime,timezone
import json
from pathlib import Path
import argparse
from prepare_multimodal_run import main as prepare
from run_authorized_java import run,save
from app.models.knowledge import KnowledgeDocument
from app.models.source import SourceDocument
from app.extraction.knowledge_merge import CATEGORIES,normalize_knowledge_ids
from app.evaluation.notes_pipeline import build_preview

ORDER=['facts','definitions','explanations','concepts','examples','procedures','relationships','formulas']


def must_stop(summary,roots,attempted):
    errors=' '.join(str(e.get('error','')) for e in summary.get('errors',[])).lower()
    if summary.get('http_429') or any(word in errors for word in ('quota_exhausted','uncertain','authorization','credential','active operation')):
        return True
    return not roots<=attempted


def publish(out,state):
    parts=[]; required=[]; completed=[]; total_input=0; total_output=0; unknown=0; attempted=0
    document=None
    for cat,record in state['categories'].items():
        folder=Path(record['output'])
        if not (folder/'run_summary.json').exists(): continue
        summary=json.loads((folder/'run_summary.json').read_bytes())
        total_input+=summary.get('input_tokens',0); total_output+=summary.get('output_tokens',0)
        unknown+=summary.get('unknown_usage_attempts',0); attempted+=summary.get('requests_attempted',0)
        if (folder/'extraction_results.json').exists(): parts.append(KnowledgeDocument.model_validate_json((folder/'extraction_results.json').read_text(encoding='utf-8')))
        manifest=json.loads((folder/'manifest.json').read_bytes()); required.extend(e['request_id'] for e in manifest['requests'] if not e.get('parent_request_id'))
        if (folder/'request_audit.json').exists():
            audit=json.loads((folder/'request_audit.json').read_bytes()); completed.extend(o['id'] for o in audit['operations'] if o['state']=='success')
        if document is None: document=SourceDocument.model_validate_json((folder/'source_document.json').read_text(encoding='utf-8'))
        record['summary']=summary
    full=all(c in state['categories'] and state['categories'][c].get('summary',{}).get('classification')=='Full live extraction completed' for c in ORDER)
    report=dict(classification='Full live extraction completed' if full else 'PARTIAL_OR_BLOCKED',categories_attempted=list(state['categories']),all_categories=ORDER,
        attempted_requests=attempted,input_tokens=total_input,output_tokens=total_output,unknown_usage_attempts=unknown,
        actual_total_tokens=None if unknown else total_input+total_output,source_grounding='Mechanical validation only; no human semantic verification',blocker=state.get('blocker'))
    if parts:
        knowledge=KnowledgeDocument(document_id=document.document_id,source_filename=document.filename,extraction_timestamp=datetime.now(timezone.utc).isoformat(),
            **{c:[item for p in parts for item in getattr(p,c)] for c in CATEGORIES})
        knowledge.update_statistics(); knowledge=normalize_knowledge_ids(knowledge,artifact_id=out.name).document
        save(out/'extraction_results.json',knowledge.model_dump(mode='json'))
        preview=build_preview(knowledge,document,required_chunks=required,completed_chunks=completed)
        (out/('generated_notes.md' if full else 'partial_notes.md')).write_text(preview['markdown'],encoding='utf-8')
        save(out/'structured_notes.json',preview['assembled'].model_dump(mode='json')); save(out/'quality_report.json',preview['report'])
        save(out/'source_document.json',document.model_dump(mode='json'))
        report.update(knowledge_items=knowledge.total_items,knowledge_counts={c:len(getattr(knowledge,c)) for c in CATEGORIES})
    save(out/'category_runs.json',state); save(out/'run_summary.json',report)
    (out/'execution_report.md').write_text('# Full multimodal category-partitioned run\n\n'+json.dumps(report,indent=2)+'\n\nPartial outputs are not complete lecture notes. Native per-field Task 12A claims and local validation retained. No images sent; no OCR candidates promoted. All quota/authorization gates remain mandatory.\n',encoding='utf-8')
    print(json.dumps(report),flush=True)


def main(resume=None, *, source=None):
    out=Path(resume) if resume else Path('data/output')/('multimodal_notes_category_full_'+datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S_%f'))
    out.mkdir(parents=True,exist_ok=True)
    state=json.loads((out/'category_runs.json').read_bytes()) if (out/'category_runs.json').exists() else dict(categories={})
    state.pop('blocker', None)
    for cat in ORDER:
        if cat not in state['categories']:
            folder=prepare(cat, source=source) if source else prepare(cat)
            state['categories'][cat]=dict(output=str(folder)); save(out/'category_runs.json',state)
        folder=Path(state['categories'][cat]['output'])
        manifest=json.loads((folder/'manifest.json').read_bytes())
        binding={k:manifest[k] for k in ('source_sha256','source_document_sha256')}
        if 'source_binding' not in state: state['source_binding']=binding
        if state['source_binding']!=binding:
            state['blocker']='Source or canonical adapter changed between category passes; dispatch refused'
            publish(out,state); break
        summary=run(folder,live=True,max_wait=65,continue_validation_failures=True,output_dir=folder)
        state['categories'][cat]['summary']=summary; publish(out,state)
        manifest=json.loads((folder/'manifest.json').read_bytes()); audit=json.loads((folder/'request_audit.json').read_bytes())
        attempted={r['request_id'] for r in audit['attempts'] if r['dispatched'] is not None}
        roots={e['request_id'] for e in manifest['requests'] if not e.get('parent_request_id')}
        if must_stop(summary,roots,attempted):
            state['blocker']=dict(category=cat,errors=summary['errors'],remaining_primary_requests=len(roots-attempted))
            publish(out,state); break
    print('FULL_RUN_OUTPUT',out,flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--resume'); main(p.parse_args().resume)
