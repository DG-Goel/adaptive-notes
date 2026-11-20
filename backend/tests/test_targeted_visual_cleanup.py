import json
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from targeted_visual_cleanup import OUT,sha


class CleanupEvidenceTests(unittest.TestCase):
    def test_original_sources_unchanged(self):
        m=json.loads((OUT/'manifest.json').read_text(encoding='utf-8'))
        for path,digest in m['source_hashes'].items(): self.assertEqual(sha(Path(path).read_bytes()),digest)

    def test_bounded_source_frames(self):
        m=json.loads((OUT/'manifest.json').read_text(encoding='utf-8'))
        for event in m['events']:
            low,high=m['windows'][event['event_id']]
            for frame in event['selected']: self.assertTrue(low<=frame['timestamp']<=high)

    def test_crop_provenance_and_bounded_retry(self):
        d=json.loads((OUT/'ocr_records.json').read_text(encoding='utf-8'))
        for r in d['records']:
            self.assertEqual(sha(Path(r['original_frame']).read_bytes()),r['original_frame_sha256'])
            self.assertEqual(sha(Path(r['crop_filename']).read_bytes()),r['crop_sha256'])
            self.assertEqual(r['options']['num_predict'],512)
        retry=[r for r in d['records'] if r['case']=='failed_task']
        self.assertEqual(len(retry),1)
        self.assertEqual(retry[0]['recognition_task'],'Text Recognition:')


if __name__=='__main__': unittest.main()
