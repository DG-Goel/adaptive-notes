"""Offline diagnosis of actual saved provider evidence; no new requests."""
from pathlib import Path
from datetime import datetime, timezone
import json
from app.ingestion.transcript_parser import parse_transcript
from run_authorized_java import save


def main():
    root=Path(__file__).resolve().parent
    paths=[root/'data/output'/name for name in (
        'java_live_java-20261106_142907_743633','java_live_java-20261106_152613_552313')]
    out=root/'data/output'/('java_real_evaluation_'+datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S'))
    out.mkdir()
    source=parse_transcript(root.parent/'java.txt',min_segment_words=50,max_segment_words=500,detect_timestamps=True)
    sources={u.source_id:u.text for u in source.source_units}
    audits=[json.loads((p/'request_audit.json').read_text(encoding='utf-8')) for p in paths]
    attempts=[a for audit in audits for a in audit['attempts']]
    response=json.loads(next(paths[1].glob('*.response.json')).read_text(encoding='utf-8'))
    content=json.loads(response['choices'][0]['message']['content'])
    evidence=[]
    for category,items in content.items():
        for index,item in enumerate(items):
            for ei,entry in enumerate(item.get('source_evidence',[])):
                evidence.append(dict(category=category,item_index=index,evidence_index=ei,
                    source_id=entry['source_id'],quote=entry['quote'],fields=entry['fields'],
                    exact_match=entry['quote'] in sources.get(entry['source_id'],'')))
    save(out/'evidence_diagnostics.json',evidence)
    save(out/'request_audit.json',audits)
    summary=dict(classification='Partial live execution',real_requests_attempted=len(attempts),
        http_200=sum(a['http_status']==200 for a in attempts),http_400=sum(a['http_status']==400 for a in attempts),
        http_429=sum(a['http_status']==429 for a in attempts),accepted_chunks=0,
        initial_chunks=18,revised_chunks=36,source_units=len(sources),
        known_input_tokens=sum(a['input_actual'] or 0 for a in attempts),known_output_tokens=sum(a['output_actual'] or 0 for a in attempts),
        actual_total_tokens=None,missing_usage_requests=sum(a['input_actual'] is None for a in attempts),
        request_duration_seconds=sum(a['duration'] or 0 for a in attempts),retries_of_identical_request=0,
        raw_returned_items=sum(len(v) for v in content.values()),evidence_quotes=len(evidence),
        exact_quote_mismatches=sum(not e['exact_match'] for e in evidence),quality_score=None,
        generated_notes=None,run_directories=[str(p) for p in paths])
    save(out/'run_summary.json',summary)
    save(out/'source_coverage.json',{sid:{'validated_note_items':0,'raw_response_cites_source':any(sid in i['source_unit_ids'] for rows in content.values() for i in rows)} for sid in sources})
    categories={'Content completeness':30,'Factual accuracy':25,'Explanation quality':15,'Organization and readability':10,'Examples and code correctness':10,'Source traceability':10}
    save(out/'quality_scores.json',{'overall':None,'categories':{k:{'weight':v,'score':None,'reason':'No validated full-document notes exist'} for k,v in categories.items()}})
    (out/'quality_evaluation.md').write_text('''# Quality evaluation — incomplete real run

No accepted notes exist, so full-document scores are unavailable. This is an assistant review of saved model output, not human review or proof of Java correctness.

The second request returned 8 raw items: 4 concepts, 3 facts and 1 procedure, all citing T0001. Seven of ten evidence quotes are exact source substrings; three fail exact matching. This measures quotation mechanics only, not semantic entailment. Strict validation rejected the chunk, including otherwise plausible items, so validated source-to-notes coverage is 0/50.

The raw response includes the instructor's audience size and promises about learning speed among its facts. Those introductory statements offer limited Java study value. The compiler and runtime entries have minimal explanation (for example, “It has a compiler.”). The Java SE concept and one introductory fact have mismatching quotes; the installation procedure also has a mismatching step quote. Reformatting or valid JSON cannot repair these evidence defects.

No full Java syntax/code assessment, cross-chunk consistency assessment, completeness review, or student-usefulness score is possible from this one rejected introductory chunk. Do not extrapolate its quality to the rest of the transcript.

Recommended next improvement: preserve the exact source quotation contract and add an explicitly versioned, offline-tested evidence-correction stage or improved evidence instructions. Review any changed production prompt before generating fresh request approvals. Do not silently replace quotes, discard required fields, or count rejected output as accepted notes.
''',encoding='utf-8')
    (out/'error_report.md').write_text('''# Actual execution errors

1. Original chunk 1: HTTP 400, json_validate_failed. Groq reported “max completion tokens reached before generating a valid document.” Reserved input 3,678 and output 3,122 totaled 6,800. Actual token usage was not supplied. The entire reservation remains charged for its rolling windows. No identical retry occurred.
2. Source-boundary recovery: the production splitter created 36 chunks from the same 50 source units without omission or reordering. Revised chunk 1 returned HTTP 200, valid JSON and finish_reason stop. Reported tokens: 2,042 input, 2,940 output, 4,982 total. Output includes 2,227 reasoning tokens; these are already included in completion usage.
3. Revised chunk 1 failed strict source evidence validation. Offline replay reproduced the error. Three of ten quotes differ from the supplied source. This is a model evidence failure, not a credential, quota, browser or JSON syntax failure. It was not automatically corrected. The response and audit are preserved.

No rate-limit response, SQLite contention, timeout or network interruption was observed in these two calls. Those outcomes are not guarantees for future requests. No complete notes were generated.
''',encoding='utf-8')
    (out/'final_test_report.md').write_text('# Real Java test result\n\n**Partial live execution. Full-document generation did not complete.**\n\n'+json.dumps(summary,indent=2)+'\n\nSee error_report.md, quality_evaluation.md, quality_scores.json, evidence_diagnostics.json and source_coverage.json. Actual token total is unknown because the first request returned no usage. Known reported usage is 4,982 tokens. No fabricated notes or quality scores are provided.\n',encoding='utf-8')
    print(json.dumps({'report':str(out),**summary},indent=2))


if __name__=='__main__':
    main()
