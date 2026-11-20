"""Audited offline edits and rebuild; no authorization, provider or ledger writes."""
import json,argparse
from pathlib import Path
from app.models.knowledge import KnowledgeDocument
from app.models.source import SourceDocument
from app.models.educational_review import EducationalReview
from app.evaluation.citation_repair import add_reviewed_evidence,revise_reviewed_text
from app.evaluation.notes_pipeline import build_preview
from app.evaluation.field_faithfulness import leaves


def repair(run_dir,plan_path,output):
    root=Path(run_dir)
    knowledge=KnowledgeDocument.model_validate_json((root/'extraction_results.json').read_text(encoding='utf-8'))
    source=SourceDocument.model_validate_json((root/'source_document.json').read_text(encoding='utf-8'))
    audit=json.loads((root/'request_audit.json').read_text(encoding='utf-8'))
    plan=json.loads(Path(plan_path).read_text(encoding='utf-8'))
    items={i.knowledge_id:i for i in knowledge.get_all_items()};changes=[]
    for edit in plan.get('text_revisions',[]):
        changes.append(revise_reviewed_text(items[edit['item_id']],**{k:v for k,v in edit.items() if k!='item_id'},source=source))
    for edit in plan.get('citation_repairs',[]):
        changes.append(add_reviewed_evidence(items[edit['item_id']],**{k:v for k,v in edit.items() if k!='item_id'},source=source))
    for item_id,review in plan.get('reviews',{}).items():items[item_id].educational_review=EducationalReview.model_validate(review)
    required=plan['required_primary_requests']
    completed=[o['id'] for o in audit['operations'] if o['state']=='success']
    preview=build_preview(knowledge,source,required_chunks=required,completed_chunks=completed)
    output=Path(output);output.mkdir(exist_ok=False)
    (output/'notes.md').write_text(preview['markdown'],encoding='utf-8')
    for name,value in [('knowledge.json',preview['knowledge'].model_dump(mode='json')),('quality_report.json',preview['report']),
        ('changes.json',changes),('representations.json',preview['representations'].model_dump(mode='json')),
        ('assembled.json',preview['assembled'].model_dump(mode='json')),('render_manifest.json',preview['rendered'].manifest.model_dump(mode='json')),
        ('field_review_queue.json',preview['report']['educational_review']['field_review_queue'])]:
        (output/name).write_text(json.dumps(value,indent=2,ensure_ascii=False),encoding='utf-8')
    payloads=[]
    for rep in preview['representations'].representations:
        original=dict(leaves(items[rep.knowledge_id].model_dump(mode='json')))
        for path,value in leaves(rep.format_content):
            payloads.append(dict(item_id=rep.knowledge_id,path=path,output=value,matching_knowledge_paths=[p for p,t in original.items() if value==t],
                classification='presentation_mapping_not_semantic_verification'))
    (output/'presentation_mapping.json').write_text(json.dumps(payloads,indent=2,ensure_ascii=False),encoding='utf-8')
    return preview


if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ('run','plan','output'):p.add_argument('--'+name,required=True)
    a=p.parse_args();result=repair(a.run,a.plan,a.output)
    print(json.dumps({'items':result['report']['after'],'gates':{k:v['outcome'] for k,v in result['report']['gates'].items()},'live_calls':0}))
