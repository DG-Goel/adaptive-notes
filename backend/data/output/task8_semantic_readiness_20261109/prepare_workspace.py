"""Freeze Task 7 provenance and prepare an offline review population before sampling."""
import json
from pathlib import Path
from hashlib import sha256
from datetime import datetime,timezone
from app.models.knowledge import KnowledgeDocument
from app.models.source import SourceDocument
from app.evaluation.semantic_review import build_review_inventory,resolve_reviews,plan_sample

P=Path('data/output/task8_semantic_readiness_20261109')
B=Path('data/output/task7_educational_completeness_20261109')
R=Path('data/output/java_live_java-20261109_022409_842270')
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(name,value):(P/name).write_text(json.dumps(value,indent=2,ensure_ascii=False),encoding='utf-8')
def digest(p):return sha256(p.read_bytes()).hexdigest()

paths={Path(p) for p in read(B/'preservation_before.json')}
paths|={p for p in B.rglob('*') if p.is_file()}
for folder in ('data/stage_a','data/authorization','data/credentials'):
    root=Path(folder)
    if root.exists():paths|={p for p in root.rglob('*') if p.is_file()}
before={str(p):digest(p) for p in sorted(paths)}
if not (P/'preservation_before.json').exists():write('preservation_before.json',before)
baseline_manifest=read(B/'artifact_manifest.json')['artifacts']
assert digest(B/'knowledge_v7.json')==baseline_manifest['knowledge_v7.json']
source_hash=read(B/'preservation_before.json')[str(R/'source_document.json')]
assert digest(R/'source_document.json')==source_hash
knowledge=KnowledgeDocument.model_validate(read(B/'knowledge_v7.json'))
source=SourceDocument.model_validate(read(R/'source_document.json'))
relations=read(B/'duplicate_decisions.json')
w=build_review_inventory(knowledge,source,duplicate_relations=relations,coverage_priority_ids=['T0004','T0045'])
pin=dict(source_version=w['source_version'],baseline_artifact=str(B/'knowledge_v7.json'),
    baseline_sha256=digest(B/'knowledge_v7.json'),source_artifact=str(R/'source_document.json'),source_sha256=source_hash,
    imported_at=datetime.now(timezone.utc).isoformat(),historical_review_times_unknown=True,
    field_bindings={r['key']:r['binding'] for r in w['inventory'] if r['legacy_review']['status']!='NOT_REVIEWED'})
write('legacy_provenance_pin.json',pin)
w=resolve_reviews(w,[],legacy_pin=pin)
write('initial_workspace.json',w)
sample=plan_sample(w,seed='Task8-20261109-precommitted-v1',risk_count=8,random_count=16)
if not (P/'sampling_plan.json').exists():write('sampling_plan.json',sample)
else:assert read(P/'sampling_plan.json')==sample
by_packet={p['packet_id']:p for p in w['packets']}
selected=[by_packet[p] for p in sample['risk_sample']+sample['random_sample']]
write('sample_evidence_packets.json',selected)
for n,p in enumerate(selected,1):
    print(json.dumps(dict(number=n,kind='RISK' if n<=8 else 'RANDOM',id=p['packet_id'],members=p['members'],
        claim=p['claim'],evidence=p['evidence']),ensure_ascii=True))
print(json.dumps(w['counts']))
