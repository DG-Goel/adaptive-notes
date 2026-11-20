"""Offline, non-overwriting rebuild from saved knowledge plus explicit review annotations."""
import argparse,json
from pathlib import Path
from app.models.knowledge import KnowledgeDocument
from app.models.source import SourceDocument
from app.models.educational_review import EducationalReview
from app.evaluation.notes_pipeline import build_preview


def rebuild(knowledge_path,source_path,review_path,output):
    knowledge=KnowledgeDocument.model_validate_json(Path(knowledge_path).read_text(encoding='utf-8'))
    source=SourceDocument.model_validate_json(Path(source_path).read_text(encoding='utf-8'))
    reviews=json.loads(Path(review_path).read_text(encoding='utf-8'))
    items={i.knowledge_id:i for i in knowledge.get_all_items()}
    for key,value in reviews.items():
        if key not in items:raise ValueError('Review targets unknown knowledge')
        items[key].educational_review=EducationalReview.model_validate(value)
    result=build_preview(knowledge,source,required_chunks=[],completed_chunks=[])
    result['report']['gates']['extraction_completion']={'outcome':'NOT_EVALUATED',
        'reason':'Offline rebuild of saved accepted knowledge; no new extraction or reassessment of live completion.'}
    out=Path(output);out.mkdir(exist_ok=False)
    (out/'notes.md').write_text(result['markdown'],encoding='utf-8')
    for name,value in [('reviewed_knowledge.json',result['knowledge'].model_dump(mode='json')),
                       ('quality_report.json',result['report']),('representations.json',result['representations'].model_dump(mode='json')),
                       ('assembled.json',result['assembled'].model_dump(mode='json')),('render_manifest.json',result['rendered'].manifest.model_dump(mode='json'))]:
        (out/name).write_text(json.dumps(value,indent=2,ensure_ascii=False),encoding='utf-8')
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ('knowledge','source','reviews','output'):p.add_argument('--'+name,required=True)
    a=p.parse_args();result=rebuild(a.knowledge,a.source,a.reviews,a.output)
    print(json.dumps({'items':result['report']['after'],'sections':len(result['assembled'].sections),
                      'readiness':result['report']['educational_review']['readiness'],'live_requests':0}))
