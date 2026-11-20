import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from multimodal_transcript import align,build,digest,DEFAULTS


def speech():
    return dict(audio_duration=9000,segments=[dict(id=1,start=0,end=2,text=' Original speech.',words=[]),dict(id=2,start=3,end=5,text=' Correction.',words=[])])


def visual(t,text,frame='framehash'):
    return dict(timestamp=t,filename='image.png',sha256=frame,task='Text Recognition:',status='success',raw_output=text,event_id='e',model='local',model_version={'digest':'abc'})


class MultimodalTests(unittest.TestCase):
    def build(self,records):
        return build(speech(),dict(source_sha256='speechhash',events=[dict(event_id='e',start=0,end=5,priority='HIGH',categories=['CORRECTION_OR_REVISION'],linked_event_ids=['earlier'])]),dict(records=records),dict(records=[]),dict(speech='speechhash',stage3='s3hash',cleanup='cleanuphash'),False)

    def test_half_open_alignment_and_gaps(self):
        self.assertEqual(align(speech()['segments'],[0,1.9,2,2.5,3,5]),[0,0,None,None,1,None])

    def test_verbatim_and_dedup_changes(self):
        a=visual(1,'a=1;'); b=visual(3,'a=1;'); c=visual(4,'a=2;','newframe')
        r=self.build([a,b,c])
        self.assertEqual(r['speech_segments'],speech()['segments'])
        self.assertIsNotNone(r['visual_evidence'][1]['duplicate_of'])
        self.assertIsNone(r['visual_evidence'][2]['duplicate_of'])
        self.assertEqual([x['raw_output'] for x in r['visual_evidence']],['a=1;','a=1;','a=2;'])
        self.assertEqual(r['high_risk_events'][0]['linked_correction_event_ids'],['earlier'])

    def test_conflicting_characters_remain_unresolved(self):
        r=self.build([visual(1,'String message = "c:\\Windows";'),visual(1,'String message = "c:\\\\Windows";')])
        self.assertTrue(any(g['kind']=='CONFLICTING_CHARACTERS' for g in r['unresolved_gaps']))
        self.assertTrue(all(v['reading_status']=='AMBIGUOUS_READING' for v in r['visual_evidence']))
        self.assertTrue(all(not v['approved_for_canonical_integration'] for v in r['visual_evidence']))

    def test_missing_formula_and_retry_history(self):
        failed=visual(1,None); failed.update(status='failed',error='token repeat limit reached')
        r=self.build([failed,visual(1,'partial / M')])
        self.assertEqual(len(r['visual_evidence']),2)
        self.assertTrue(any(g['kind']=='VISUAL_CONTEXT_REQUIRED' for g in r['unresolved_gaps']))
        self.assertTrue(any(g['kind']=='UNRESOLVED_CLIPPED_CHARACTERS' for g in r['unresolved_gaps']))

    def test_provenance_and_image_integrity_failure(self):
        r=self.build([visual(1,'test')]); v=r['visual_evidence'][0]
        self.assertEqual(v['source_record_index'],0); self.assertEqual(v['frame_sha256'],'framehash')
        with self.assertRaises((FileNotFoundError,ValueError)):
            build(speech(),{'source_sha256':'h','events':[]},{'records':[visual(1,'test')]},{'records':[]},{'speech':'h','stage3':'x','cleanup':'y'},True)

    def test_fingerprint_rejection(self):
        with self.assertRaises(ValueError): build(speech(),{'source_sha256':'wrong'},{},{},{'speech':'actual'})


if __name__=='__main__': unittest.main()
