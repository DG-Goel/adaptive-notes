import json
import difflib
from pathlib import Path
from app.ingestion.transcript_parser import parse_transcript

doc=parse_transcript(Path('../java.txt'),min_segment_words=50,max_segment_words=500,detect_timestamps=True)
sources={u.source_id:u.text for u in doc.source_units}
response=json.loads(Path('data/output/java_live_java-20261106_152613_552313/java-20261106_152613_552313-0000.response.json').read_text())
rows=json.loads(response['choices'][0]['message']['content'])
for category,items in rows.items():
    for item in items:
        for evidence in item['source_evidence']:
            quote=evidence['quote']
            source=sources[evidence['source_id']]
            if quote not in source:
                match=difflib.SequenceMatcher(None,quote.lower(),source.lower(),autojunk=False).find_longest_match()
                start=max(0,match.b-match.a-20)
                print(json.dumps({'quote':quote,'nearby_source':source[start:start+len(quote)+80]}))
