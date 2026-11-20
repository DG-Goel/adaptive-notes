import sys
from pathlib import Path
import tempfile
import unittest
import av
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from visual_recovery import schedule,tasks,png,sha,save


class VisualTests(unittest.TestCase):
    def test_sampling(self):
        ts=schedule(10,20,3)
        self.assertEqual(ts,sorted(set(ts)))
        self.assertIn(15,ts)
        self.assertTrue(all(10<=t<20 for t in ts))

    def test_mixed_tasks(self):
        self.assertEqual(tasks({'categories':['CODE_VISUAL_DEPENDENCY','FORMULA_VISUAL_DEPENDENCY']}),['Text Recognition:','Formula Recognition:'])

    def test_png_and_checkpoint(self):
        frame=av.VideoFrame.from_ndarray(np.zeros((32,64,3),dtype=np.uint8),format='rgb24')
        blob=png(frame)
        self.assertEqual(blob[:8],b'\x89PNG\r\n\x1a\n')
        self.assertEqual(sha(blob),sha(png(frame)))
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]) as tmp:
            path=Path(tmp)/'state.json'; save(path,{'x':1}); save(path,{'x':2})
            self.assertIn('2',path.read_text())


if __name__=='__main__': unittest.main()
