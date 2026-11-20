"""Offline software tests: synthetic ASR objects, never accuracy evidence."""
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from transcription import TranscriptionConfig, timestamp, transcribe


class TranscriptionTests(unittest.TestCase):
    def run_asr(self, *, gpu_failure=False, partial=False, empty=False):
        calls = []
        segment = NS(id=0, start=134.20123, end=138.90123, text=" Original words.",
                     words=[NS(word=" Original", start=134.20123, end=135.2, probability=.9),
                            NS(word=" words.", start=None, end=None, probability=None)])

        class Model:
            def __init__(self, name, **kwargs):
                calls.append(kwargs)
                if gpu_failure and kwargs["device"] == "cuda":
                    raise RuntimeError("missing CUDA DLL")

            def transcribe(self, source, **kwargs):
                self_options.update(kwargs)
                def generate():
                    if not empty:
                        yield segment
                    if partial:
                        raise RuntimeError("device failed during inference")
                return generate(), NS(duration=200., duration_after_vad=4.7,
                                      language="en", language_probability=1.)

        self_options = {}
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]) as tmp:
            source = Path(tmp) / "lecture.mkv"
            source.write_bytes(b"mock media")
            output = Path(tmp) / "out"
            with patch.dict(sys.modules, {"faster_whisper": NS(WhisperModel=Model),
                     "ctranslate2": NS(get_supported_compute_types=lambda _: {"int8_float16"})}), \
                 patch("transcription.importlib.metadata.version", return_value="mock"), \
                 patch("transcription._cuda_libraries", return_value=[]):
                if partial:
                    with self.assertRaisesRegex(RuntimeError, "not retried"):
                        transcribe(source, output)
                else:
                    transcribe(source, output)
                data = json.loads((output / "transcript.json").read_text())
                self.assertEqual(source.read_bytes(), b"mock media")
                self.assertTrue(all(c["local_files_only"] for c in calls))
                self.assertTrue(self_options["vad_filter"])
                self.assertFalse(self_options["condition_on_previous_text"])
                self.assertEqual(self_options["vad_parameters"]["min_silence_duration_ms"], 2000)
                with self.assertRaises(FileExistsError):
                    transcribe(source, output)
            if not empty:
                self.assertEqual(data["segments"][0]["start"], 134.20123)
                self.assertEqual(data["segments"][0]["text"], " Original words.")
                self.assertIsNone(data["segments"][0]["words"][1]["start"])
                self.assertEqual(data["metrics"]["word_timestamp_coverage"], .5)
                self.assertIn("00:02:14,201", (output / "transcript.srt").read_text())
            return data, calls

    def test_gpu_outputs_and_original_timeline(self):
        data, calls = self.run_asr()
        self.assertEqual(data["device"], "cuda")
        self.assertEqual(len(calls), 1)

    def test_initialization_fallback(self):
        data, calls = self.run_asr(gpu_failure=True)
        self.assertEqual((data["device"], data["compute_type"]), ("cpu", "int8"))
        self.assertEqual(len(calls), 2)
        self.assertTrue(data["warnings"])

    def test_partial_failure_does_not_replay(self):
        data, calls = self.run_asr(partial=True)
        self.assertEqual(data["status"], "failed_partial")
        self.assertEqual(len(calls), 1)

    def test_silence_has_no_invented_segments(self):
        data, _ = self.run_asr(empty=True)
        self.assertEqual(data["segments"], [])

    def test_timestamp_carry_and_validation(self):
        self.assertEqual(timestamp(59.9999), "00:01:00.000")
        with self.assertRaises(ValueError):
            TranscriptionConfig(beam_size=0)


if __name__ == "__main__":
    unittest.main()
