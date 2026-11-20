import json
from pathlib import Path
import pytest
from app.ingestion.multimodal_adapter import parse_multimodal
from app.extraction.chunker import ContentChunker
from app.extraction.source_context import bind_context
from app.extraction.quote_catalog import catalog

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'data/transcriptions/video_stage4/run_20261110/multimodal_transcript.json'


@pytest.fixture(scope='module')
def doc(): return parse_multimodal(SOURCE)


def test_all_evidence_and_verbatim_speech(doc):
    stage4=json.loads(SOURCE.read_text(encoding='utf-8'))
    speech=[u for u in doc.source_units if u.type=='speech']
    visuals=[u for u in doc.source_units if u.type=='visual_candidate']
    assert len(speech)<2181 and len(visuals)==501
    original=[s for u in speech for s in u.provenance['original_segments']]
    assert original==stage4['speech_segments']
    for u in speech:
        assert len(u.text.split())<=250
        for s,span in zip(u.provenance['original_segments'],u.provenance['segment_character_spans']):
            assert u.text[span['start']:span['end']]==s['text']
    assert all(u.text is None and u.representation_status=='awaiting_interpretation' for u in visuals)


def test_candidates_nonquotable_with_context_retained(doc):
    chunks=ContentChunker().chunk(doc.source_units,doc.document_id)
    chunk=next(c for c in chunks if c.uninterpreted_source_ids)
    chunk=bind_context(chunk,doc.source_units)
    quotes=catalog(chunk)
    assert all(not v['source_id'].startswith('V') for v in quotes.values())
    assert any('UNVERIFIED' in s for s in chunk.context_limitations)


def test_repeats_and_source_gaps_retained(doc):
    byid={u.provenance['evidence_id']:u for u in doc.source_units if u.type=='visual_candidate'}
    for u in byid.values():
        if u.provenance['duplicate_of']:
            assert byid[u.provenance['duplicate_of']].provenance['raw_output']==u.provenance['raw_output']
    assert any(g['kind']=='VISUAL_CONTEXT_REQUIRED' for g in doc.ingestion['unresolved_gaps'])
    assert all(not u.provenance['approved_for_canonical_integration'] for u in byid.values())


def test_lineage_rejected(tmp_path):
    path=tmp_path/'multimodal_transcript.json'; path.write_text(json.dumps({'schema_version':'1.0'}))
    (tmp_path/'visual_evidence_index.json').write_text(json.dumps({'source_paths':{'source':str(path)},'source_fingerprints':{'source':'0'*64}}))
    with pytest.raises(ValueError,match='hash mismatch'): parse_multimodal(path)


def test_prepared_exact_request_payloads_are_frozen():
    from app.extraction.organization_scheduler import digest
    pointer=ROOT/'data/output/latest_multimodal_run.txt'
    if not pointer.exists(): pytest.skip('No prepared live request inventory')
    manifest=json.loads((Path(pointer.read_text())/'manifest.json').read_text(encoding='utf-8'))
    assert all(e['request_sha256']==digest(e['payload']) for e in manifest['requests'])
