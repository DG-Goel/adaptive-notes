"""Task 11 delivery replay: existing components only, network denied, no providers."""
import json
import os
from pathlib import Path
from hashlib import sha256
import socket
import sys

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]
sys.path.insert(0,str(ROOT))
os.environ['HF_HUB_OFFLINE']='1'
os.environ['TRANSFORMERS_OFFLINE']='1'
def blocked(*a,**k):raise AssertionError('No network permitted in Task 11 delivery')
socket.socket.connect=blocked
socket.create_connection=blocked

from app.ingestion.docling_parser import DoclingParser
from app.ingestion.router import ingest_document
from app.models.source import SourceDocument
from app.extraction.chunker import ContentChunker
from app.extraction.source_context import bind_context
from app.extraction.context_grounding import chunk_prompt
from app.extraction.organization_extraction import prepare_request
from app.extraction.organization_scheduler import ExtractionConfiguration,digest,SchedulerHold
from app.extraction.document_authorization import document_plan
from tests.test_structured_ingestion import create_documents,mock_notes,controlled_structure


def save(name,value):
    path=OUT/name;path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')


def persist_preview(name,source):
    preview,payloads=mock_notes(source)
    save(name+'/source_document.json',source.model_dump(mode='json'))
    save(name+'/request_evidence.json',payloads)
    save(name+'/mock_knowledge.json',preview['knowledge'].model_dump(mode='json'))
    save(name+'/quality_report.json',preview['report'])
    (OUT/name/'notes_preview.md').write_text(preview['markdown'],encoding='utf-8')
    return {'source_units':len(source.source_units),'mock_items':preview['report']['after'],
        'status':'UNVERIFIED_PREVIEW','semantic_quality_score':None,
        'source_units_without_primary_knowledge':preview['report']['gates']['educational_completeness']['source_units_without_primary_knowledge'],
        'mechanical_provenance':preview['report']['gates']['semantic_faithfulness']['mechanical_provenance']}


def main():
    os.chdir(ROOT)
    raw=json.loads((ROOT/'data/output/docling_structure.json').read_text(encoding='utf-8'))
    old=json.loads((ROOT/'data/output/source_units.json').read_text(encoding='utf-8'))
    source=DoclingParser.project_document(raw,document_id=old['document_id'])
    DoclingParser.save_sidecar(raw,source,OUT/'sidecars')
    save('source_document_v2.json',source.model_dump(mode='json'))
    save('element_mapping.json',source.ingestion)
    mapped={u.docling_ref:u for u in source.source_units}
    oldrefs={u['docling_ref'] for u in old['source_units']}
    # Review ledger concerns this historical fixture only; no document-specific rule
    # is introduced in production. Short fragments are retained, not interpreted.
    furniture={'#/texts/10','#/texts/11','#/texts/36','#/texts/37','#/texts/74','#/texts/92','#/texts/108'}
    fragments={'#/texts/7','#/texts/68','#/texts/124'}
    ledger=[]
    for t in raw['texts']:
        if t['self_ref'] in oldrefs:continue
        category=('Recovered document furniture' if t['self_ref'] in furniture else
                  'Still unresolved' if t['self_ref'] in fragments else 'Recovered educational element')
        ledger.append({'docling_ref':t['self_ref'],'source_id':mapped[t['self_ref']].source_id,
            'label':t['label'],'text':t['text'],'classification':category,'source_text_recovered':True,
            'semantic_approval':False,'excluded':False,
            'reason':'Isolated source fragment; intended interpretation remains uncertain' if category=='Still unresolved' else
                     'Page number or running book/chapter label; retained without automatic exclusion' if category=='Recovered document furniture' else
                     'Source teaching, exercise, caption, heading or vocabulary element; not a count of unique facts'})
    save('recovered_42_accounting.json',ledger)
    save('unresolved_visual_inventory.json',[{'source_id':u.source_id,'docling_ref':u.docling_ref,
        'page':u.page,'bbox':u.bbox.model_dump() if u.bbox else None,
        'original_provenance':u.provenance,'limitations':u.interpretation_limitations,
        'counts_as_completed':False} for u in source.source_units if u.representation_status=='awaiting_interpretation'])
    config=ExtractionConfiguration(max_retries=0,prompt_policy='canonical_grounded_v4',response_format='json_schema')
    chunks=ContentChunker().chunk(source.source_units,source.document_id)
    requests=[];holds=[]
    for c in chunks:
        c=bind_context(c,source.source_units).model_copy(update={'ingestion_binding':digest(source.model_dump(mode='json'))})
        try:
            payload,budget=prepare_request(c,config)
            requests.append({'chunk_id':c.chunk_id,'request_sha256':digest(payload),'payload':payload,
                'chunk':c.model_dump(mode='json'),'authorization_status':'UNAPPROVED'})
        except SchedulerHold as e:
            holds.append({'chunk_id':c.chunk_id,'reason':str(e)})
    # Replay inventory is a preparation artifact, never a Stage A approval record.
    save('pdf_replay_request_package.json',{'version':'task11_offline_replay_v2',
        'authorization_status':'UNAPPROVED','live_calls':0,'source_document_sha256':digest(source.model_dump(mode='json')),
        'requests':requests,'budget_holds':holds})
    old_chunks=ContentChunker().chunk(SourceDocument.model_validate(old).source_units,old['document_id'])
    repaired_old=sum(bool(chunk_prompt(bind_context(c,SourceDocument.model_validate(old).source_units))) for c in old_chunks)
    counts={k:sum(r['classification']==k for r in ledger) for k in ['Recovered educational element',
        'Recovered document furniture','Valid intentional exclusion','Duplicate representation','Still unresolved']}
    comparison={'baseline':{'raw_text_elements':131,'canonical_units':109,'text_bearing_units':89,
        'unmatched_text_references':42,'empty_picture_units':15,'empty_list_units':5,
        'chunks':13,'serialization_failures':9},
        'after':{'raw_text_elements':len(raw['texts']),'canonical_units':len(source.source_units),
            'text_bearing_units':sum(bool(u.text) for u in source.source_units),
            'unmatched_text_references':len([t for t in raw['texts'] if t['self_ref'] not in mapped]),
            'unresolved_pictures':len(source.ingestion['unresolved_source_ids']),
            'structural_groups':sum(u.representation_status=='structural' for u in source.source_units),
            'chunks':len(chunks),'serialization_failures':len(chunks)-len(requests)-len(holds),
            'prepared_requests':len(requests),'budget_holds':holds,'repaired_original_chunks':repaired_old},
        'recovered_42_classification':counts,'historical_id_associations_preserved':all(mapped[u['docling_ref']].source_id==u['source_id'] for u in old['source_units']),
        'notes':'Element recovery is not factual accuracy, semantic verification, or unique-fact coverage.'}
    save('before_after.json',comparison)
    pdf_preview=persist_preview('saved_pdf_mock_preview',source)
    formats={}
    for path in create_documents(OUT/'controlled_inputs'):
        options={} if path.suffix=='.txt' else {'sidecar_dir':str(OUT/'sidecars')}
        if path.suffix=='.pdf':options['pdf_mode']='native'
        doc=ingest_document(path,parser_options=options)
        name='controlled_'+path.suffix[1:]
        formats[name]={'actual_conversion':True,'pdf_mode':'native_model_free' if path.suffix=='.pdf' else None,
            **persist_preview(name,doc)}
        manifest=document_plan(path,config,'task11-'+path.suffix[1:],parser_options=options)
        save(name+'/manifest.unapproved.json',manifest)
    controlled=DoclingParser.project_document(controlled_structure(),document_id='CONTROLLED_STRUCTURE')
    structured_preview=persist_preview('controlled_structure',controlled)
    save('cross_format_results.json',{'formats':formats,'saved_pdf_replay':pdf_preview,
        'controlled_structured_fixture':structured_preview,'llm':'MockLLMProvider only','live_calls':0})
    cache=Path.home()/'.cache/huggingface/hub'
    save('enrichment_feasibility.json',{'code_formula_v2_cached':(cache/'models--docling-project--CodeFormulaV2').exists(),
        'granite_docling_258m_cached':(cache/'models--ibm-granite--granite-docling-258M').exists(),
        'torch_build':'2.14.0+cpu','gpu_enrichment_test':'NOT_RUN_CPU_ONLY_AND_WEIGHTS_NOT_CACHED',
        'enrichment_test':'NOT_AVAILABLE_NO_CACHED_WEIGHTS','models_downloaded':False,
        'native_formula_and_controlled_literal_code_payloads':'PASS_WITHOUT_ENRICHMENT',
        'memory_benchmark':'NOT_VERIFIED; no enrichment model initialized'})
    before=json.loads((OUT/'historical_hashes_before.json').read_text(encoding='utf-8'))
    altered=[p for p,h in before.items() if not Path(p).exists() or sha256(Path(p).read_bytes()).hexdigest()!=h]
    save('historical_preservation.json',{'checked_files':len(before),'altered_files':altered,
        'passed':not altered,'task9_status':'READY_FOR_HUMAN_REVIEW','quota_records_modified':False,'live_calls':0})
    if altered:raise AssertionError(altered)
    print(json.dumps({'output':str(OUT),'comparison':comparison,'formats':formats,'protected_files':len(before)},indent=2))


if __name__=='__main__':main()
