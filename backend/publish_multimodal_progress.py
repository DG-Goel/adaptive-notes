"""Render validated real checkpoints only; never dispatch or mark a full run complete."""
import json
from pathlib import Path
import sqlite3
from app.models.source import SourceDocument
from app.models.knowledge import KnowledgeDocument
from app.extraction.knowledge_merge import CATEGORIES,normalize_knowledge_ids
from app.evaluation.notes_pipeline import build_preview


def publish(out):
    out=Path(out); manifest=json.loads((out/'manifest.json').read_bytes())
    document=SourceDocument.model_validate_json((out/'source_document.json').read_text(encoding='utf-8'))
    with sqlite3.connect('data/live_state/organization.sqlite') as db:
        passed={r[0] for r in db.execute('select id from operations where state=?',('success',))}
    parts=[]; completed=[]
    for e in manifest['requests']:
        p=out/(e['request_id']+'.json')
        if e['request_id'] in passed and p.exists():
            parts.append(KnowledgeDocument.model_validate_json(p.read_text(encoding='utf-8'))); completed.append(e['request_id'])
    if not parts: print('No validated checkpoints available yet'); return
    knowledge=KnowledgeDocument(document_id=document.document_id,source_filename=document.filename,extraction_timestamp='checkpoint-preview',
        **{c:[item for part in parts for item in getattr(part,c)] for c in CATEGORIES})
    knowledge.update_statistics(); knowledge=normalize_knowledge_ids(knowledge,artifact_id=manifest['run_id']).document
    preview=build_preview(knowledge,document,required_chunks=[e['request_id'] for e in manifest['requests'] if not e.get('parent_request_id')],completed_chunks=completed)
    target=out/f'progress_{len(completed):04d}'; target.mkdir(exist_ok=True)
    markdown='# Partial live notes — incomplete lecture\n\n'+preview['markdown']
    def clock(t):
        h,seconds=divmod(float(t),3600); m,seconds=divmod(seconds,60)
        return f'{int(h):02}:{int(m):02}:{seconds:06.3f}'
    times={u.source_id:dict(start=u.provenance['start'],end=u.provenance['end'],
        original_segment_ids=[s['id'] for s in u.provenance.get('original_segments',[])]) for u in document.source_units
        if u.provenance.get('modality')=='speech' and 'start' in u.provenance}
    for sid,timespan in times.items():
        markdown=markdown.replace('## Source '+sid+'\n','## Source '+sid+' — '+clock(timespan['start'])+'–'+clock(timespan['end'])+'\n')
    (target/'source_time_index.json').write_text(json.dumps(times,indent=2),encoding='utf-8')
    (target/'partial_notes.md').write_text(markdown,encoding='utf-8')
    (out/'live_partial_notes.md').write_text(markdown,encoding='utf-8')
    (target/'knowledge.json').write_text(knowledge.model_dump_json(indent=2),encoding='utf-8')
    (target/'quality_report.json').write_text(json.dumps(preview['report'],indent=2),encoding='utf-8')
    print(json.dumps(dict(output=str(target),validated_checkpoints=len(completed),knowledge_items=knowledge.total_items,complete=False)))


if __name__=='__main__':
    import sys
    publish(sys.argv[1] if len(sys.argv)>1 else Path('data/output/latest_multimodal_run.txt').read_text(encoding='utf-8'))
