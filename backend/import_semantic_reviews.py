"""Validate exported offline reviews against current claim/source versions.

Writes a new audit directory; never edits knowledge, credentials or usage history.
"""
import argparse
import json
from hashlib import sha256
from pathlib import Path
from app.models.knowledge import KnowledgeDocument
from app.models.source import SourceDocument
from app.evaluation.semantic_review import build_review_inventory, append_decision, resolve_reviews
from app.evaluation.review_outputs import evidence_desk_html


def import_reviews(knowledge_path,source_path,decisions_path,output,history_path=None,relations_path=None,legacy_pin_path=None):
    def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))
    knowledge=KnowledgeDocument.model_validate(read(knowledge_path))
    source=SourceDocument.model_validate(read(source_path))
    workspace=build_review_inventory(knowledge,source,duplicate_relations=read(relations_path) if relations_path else ())
    history=read(history_path) if history_path else []
    pin=read(legacy_pin_path) if legacy_pin_path else None
    if pin:
        for field,expected in (('baseline_artifact','baseline_sha256'),('source_artifact','source_sha256')):
            if sha256(Path(pin[field]).read_bytes()).hexdigest()!=pin[expected]:
                raise ValueError('Legacy provenance artifact changed')
    decisions=read(decisions_path)
    if not isinstance(decisions,list):raise ValueError('Expected an explicit list of review decisions')
    for decision in decisions:history=append_decision(workspace,history,decision)
    resolved=resolve_reviews(workspace,history,legacy_pin=pin)
    target=Path(output);target.mkdir(exist_ok=False,parents=True)
    for name,value in [('decision_history.json',history),('resolved_workspace.json',resolved)]:
        (target/name).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
    (target/'evidence_desk.html').write_text(evidence_desk_html(resolved),encoding='utf-8')
    return resolved


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('knowledge','source','decisions','output'):parser.add_argument('--'+name,required=True)
    parser.add_argument('--history');parser.add_argument('--relations')
    parser.add_argument('--legacy-pin')
    args=parser.parse_args()
    result=import_reviews(args.knowledge,args.source,args.decisions,args.output,args.history,args.relations,args.legacy_pin)
    print(json.dumps(dict(records=len(result['review_history']),invalidated=len(result['invalidated_decisions']),
        whole_document_verified=False,api_requests=0)))
