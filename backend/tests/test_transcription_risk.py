import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from transcription_risk import detect,run,RiskConfig


def fixture(texts):
    return dict(audio_duration=100,segments=[dict(id=10+i,start=i*5,end=i*5+4,text=t,words=[]) for i,t in enumerate(texts)])


class RiskTests(unittest.TestCase):
    def test_categories(self):
        examples={
            'CODE_VISUAL_DEPENDENCY':"Let's type this code in our method.",
            'FORMULA_VISUAL_DEPENDENCY':'Here is the formula. Divide by this expression here.',
            'SCREEN_OUTPUT_DEPENDENCY':"Let's run this program and look at the output.",
            'DIAGRAM_VISUAL_DEPENDENCY':'Look at this diagram and the arrows here.',
            'TABLE_CHART_VISUAL_DEPENDENCY':'As you can see this graph shows a trend.',
            'SLIDE_TEXT_DEPENDENCY':'Look at these bullet points on the slide.',
            'CORRECTION_OR_REVISION':'Sorry, I meant multiply this formula instead of dividing.',
        }
        for cat,text in examples.items():
            with self.subTest(cat=cat):
                self.assertIn(cat,detect(fixture([text]),'hash')['events'][0]['categories'])

    def test_conversation_and_acronyms_not_errors(self):
        for text in ['This one. Like this. Here is my friend.','I enjoyed dinner yesterday.','The JVM executes bytecode.']:
            self.assertFalse(detect(fixture([text]),'h')['events'])

    def test_context_and_split_phrase(self):
        r=detect(fixture(["Let's write a",'method like this.']),'h')
        self.assertTrue(any(h['method']=='adjacent_segment_pattern' for d in r['raw_detections'] for h in d['triggers']))
        self.assertIn('AMBIGUOUS_VISUAL_REFERENCE',r['events'][0]['categories'])
        self.assertEqual(r['events'][0]['source_segments'][0]['id'],10)

    def test_real_diagnostics_only(self):
        d=fixture(['The JVM uses bytecode.'])
        d['segments'][0]['words']=[dict(text='JVM',start=0,end=1,probability=.1)]
        r=detect(d,'h'); self.assertIn('TECHNICAL_ASR_RISK',r['events'][0]['categories'])
        d['segments'][0]['words'][0]['probability']=None
        self.assertFalse(detect(d,'h')['events'])

    def test_ranking_bounds_merge_and_stability(self):
        d=fixture(['Here is the formula.','Divide by this expression here.','Sorry, replace this formula.'])
        a=detect(d,'h'); b=detect(d,'h')
        self.assertEqual(a['events'],b['events'])
        self.assertEqual(len(a['events']),1)
        self.assertEqual(a['events'][0]['priority'],'HIGH')
        self.assertEqual(a['events'][0]['start'],0)
        self.assertEqual(len(a['raw_detections']),3)
        self.assertNotEqual(a['events'][0]['event_id'],detect(d,'changed')['events'][0]['event_id'])
        self.assertGreater(len(detect(d,'h',RiskConfig(max_merged_seconds=8))['events']),1)

    def test_context_is_bounded(self):
        d=fixture(['Here is the formula.','This one.'])
        d['segments'][1].update(start=80,end=84)
        self.assertEqual(len(detect(d,'h')['raw_detections']),1)

    def test_serialization_and_fingerprint(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]) as t:
            source=Path(t)/'source.json'; source.write_text(json.dumps(fixture(['Here is the formula.'])))
            before=source.read_bytes(); r=run(source,Path(t)/'out')
            self.assertEqual(r['source_sha256'],hashlib.sha256(before).hexdigest())
            self.assertEqual(before,source.read_bytes())
            self.assertEqual(json.loads((Path(t)/'out/risk_intervals.json').read_text())['events'],r['events'])
            self.assertEqual(len(list((Path(t)/'out').iterdir())),5)

    def test_invalid_timeline(self):
        d=fixture(['Here is the formula.']); d['segments'][0]['end']=101
        with self.assertRaises(ValueError): detect(d,'h')

    def test_revision_links_and_unrelated_events(self):
        d=fixture(['Here is the formula.','Sorry, replace this formula.'])
        r=detect(d,'h',RiskConfig(max_merged_seconds=8))
        self.assertTrue(r['events'][0]['linked_event_ids'])
        d=fixture(['Look at this diagram.','Here is the formula.'])
        self.assertEqual(len(detect(d,'h')['events']),2)


if __name__=='__main__': unittest.main()
