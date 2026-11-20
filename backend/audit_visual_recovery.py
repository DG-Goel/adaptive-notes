"""Offline evidence audit; no inference and no edits to source artifacts."""
import difflib
import json
from pathlib import Path
import sys
from visual_recovery import sha,save


def audit(folder):
    out=Path(folder); state=json.loads((out/'visual_ocr_results.json').read_text(encoding='utf-8'))
    manifest=json.loads((out/'frame_manifest.json').read_text(encoding='utf-8'))
    issues=[]; changes=[]
    for m in manifest['events']:
        for f in m['selected']:
            for field,checksum in [('filename','sha256'),('inference_filename','inference_sha256')]:
                if sha(Path(f[field]).read_bytes())!=f[checksum]: issues.append('Frame hash mismatch: '+f[field])
        records=[r for r in state['records'] if r['event_id']==m['event_id'] and r['task']=='Text Recognition:']
        records.sort(key=lambda r:r['timestamp'])
        for a,b in zip(records,records[1:]):
            if a.get('raw_output')!=b.get('raw_output'):
                changes.append(dict(event_id=m['event_id'],from_timestamp=a['timestamp'],to_timestamp=b['timestamp'],
                    difference='\n'.join(difflib.unified_diff(a.get('raw_output','').splitlines(),b.get('raw_output','').splitlines(),lineterm='')),
                    limitation='Differences may be OCR instability as well as actual visual edits. Verify the two source frames.'))
    for field,key in [('transcript','transcript_sha256'),('risks','risks_sha256')]:
        path=state['identity']['configuration'][field]
        if sha(Path(path).read_bytes())!=state['identity'][key]: issues.append('Source hash mismatch: '+path)
    digest=state.get('model_info',{}).get('digest')
    placements=[m for p in state['gpu_observations'] for m in p.get('models',[]) if m['name']=='glm-ocr:q8_0']
    save(out/'evidence_audit.json',dict(issues=issues,ocr_state_differences=changes,
         original_sources_unchanged=not issues,model_digest=digest,
         all_observed_model_sizes_equal_vram=bool(placements) and all(m.get('size')==m.get('size_vram') for m in placements),
         placement_interpretation='Equal loaded size/VRAM is Ollama evidence of full GPU placement, not a claim about all CPU preprocessing.',
         model_output_limitations='OCR snippets are candidates; code fences, missing characters and descriptions are not independently verified.'))
    print('Audit issues:',issues,'; OCR state differences:',len(changes))


if __name__=='__main__': audit(sys.argv[1])
