"""Before/after diagnostics using unchanged Phase 3 annotations."""
import json
from pathlib import Path
from .segmentation_evaluation import evaluate
from .contracts import SourceSnapshot
from .source_index import build_index,digest
from .segmentation import SegmentationJob
from .segmentation_schema import parse_response
from .reading_windows import BoundaryDecision
from dataclasses import asdict


def fixture_set():
    return json.loads((Path(__file__).parent/'evaluation/fixtures_v1.json').read_text(encoding='utf-8'))


def fragmented_job(fixture,planner,budget,store,run_id):
    """Deterministic deliberately fragmented input, never an LLM quality result."""
    content='\n\n'.join(fixture['blocks']).encode()
    job=SegmentationJob(build_index(SourceSnapshot(fixture['id'],digest(content),content,'text/markdown')),
        planner,budget,store,run_id)
    while job.reading.state.cursor<len(job.reading.index.units):
        window=job.reading.next_window().window
        if window is None: raise ValueError('Fixture source cannot fit segmentation window')
        rows=[]
        for block in window.source:
            position=block.position
            # Fixtures specify conceptual source blocks; exact index mapping is
            # checked rather than silently treating mismatched indices as labels.
            if len(job.reading.index.units)!=len(fixture['blocks']): raise ValueError('Fixture/index block mapping differs')
            category=fixture['acceptable_categories'][position][0]
            rows.append(dict(start=block.id,end=block.id,category=category,title=' '.join(fixture['blocks'][position].split()[:10])[:120],
                focus=' '.join(fixture['blocks'][position].split()[:15])[:240],density='medium',estimated_items=3,
                boundary_reason='document_end' if position==len(fixture['blocks'])-1 else 'objective_change'))
        decision=parse_response(json.dumps(dict(segments=rows,pending_from=None)),window)
        for segment in decision.segments:
            block=next(b for b in window.source if b.id==segment.start)
            row=asdict(segment)
            row.update(id='S'+digest((job.reading.index.fingerprint+block.id+block.id).encode())[:24],
                source_artifact_id=fixture['id'],source_sha256=job.reading.index.snapshot.sha256,
                source_start=block.source_start,source_end=block.source_end,start_position=block.position,end_position=block.position,
                continuation_group=None,source_tokens=block.token_count,source_token_kind='estimated',
                source_words=len(__import__('re').findall(r'\w+',block.text)))
            job.manifest.append(row)
        job.reading.apply(BoundaryDecision(window.id,window.source[-1].id))
    job.status='complete'
    return job


def compare(fixture,provisional,optimized):
    return dict(provisional=evaluate(fixture,provisional),optimized=evaluate(fixture,optimized),
                semantic_fact_coverage_verified=False)
