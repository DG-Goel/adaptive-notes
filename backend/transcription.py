"""Independent Stage 1 ASR. No downstream ingestion or remote API calls."""
from dataclasses import asdict, dataclass
from pathlib import Path
import gc
import importlib.metadata
import json
import logging
import math
import os
import time

LOG = logging.getLogger(__name__)


def _cuda_libraries():
    """Keep Windows DLL directories registered for the model's lifetime."""
    handles = []
    if os.name == "nt":
        import ctypes
        for name in ("cublas64_12.dll", "cudnn64_9.dll", "cudnn_ops64_9.dll"):
            path = next((str(Path(directory.strip('"')) / name)
                         for directory in os.environ.get("PATH", "").split(os.pathsep)
                         if directory and (Path(directory.strip('"')) / name).is_file()), None)
            if not path:
                raise OSError(f"{name} missing from PATH; need CUDA 12 cuBLAS and cuDNN 9")
            handles.append(os.add_dll_directory(str(Path(path).parent)))
            handles.append(ctypes.WinDLL(path))
    return handles


@dataclass(frozen=True)
class TranscriptionConfig:
    model: str = "small.en"
    device: str = "cuda"
    compute_type: str = "int8_float16"
    beam_size: int = 3
    cpu_threads: int = 4
    min_silence_duration_ms: int = 2000
    speech_pad_ms: int = 400
    allow_download: bool = False

    def __post_init__(self):
        if self.device not in ("cpu", "cuda"):
            raise ValueError("device must be cpu or cuda")
        if self.beam_size < 1 or self.cpu_threads < 1:
            raise ValueError("beam_size and cpu_threads must be positive")
        if self.min_silence_duration_ms < 0 or self.speech_pad_ms < 0:
            raise ValueError("VAD durations must be nonnegative")


def timestamp(seconds, separator="."):
    milliseconds = round(seconds * 1000)
    hours, milliseconds = divmod(milliseconds, 3600000)
    minutes, milliseconds = divmod(milliseconds, 60000)
    sec, milliseconds = divmod(milliseconds, 1000)
    return f"{hours:02}:{minutes:02}:{sec:02}{separator}{milliseconds:03}"


def _time(value):
    if value is None:
        return None
    if not math.isfinite(value) or value < 0:
        raise ValueError(f"Invalid ASR timestamp: {value}")
    return value


def transcribe(input_path, output_dir, config=None):
    """Load one model, consume its lazy iterator once, and save authentic results.

    Fallback is limited to CUDA capability/initialization failures. Any decoding
    or iteration failure is reported with partial artifacts and never replayed.
    """
    config = config or TranscriptionConfig()
    source = Path(input_path).resolve(strict=True)
    if not source.is_file():
        raise ValueError("Input must be a local media file")
    target = Path(output_dir).resolve()
    if target.exists() and any(target.iterdir()):
        raise FileExistsError("Output directory must be empty (protects existing artifacts)")
    if source in [target / f"transcript.{ext}" for ext in ("json", "srt", "txt")]:
        raise ValueError("Output would overwrite input")
    from faster_whisper import WhisperModel
    import ctranslate2

    started = time.perf_counter()
    device = config.device
    compute = config.compute_type if device == "cuda" else "int8"
    warnings = []
    model = None
    dll_handles = []
    kwargs = dict(cpu_threads=config.cpu_threads, num_workers=1,
                  local_files_only=not config.allow_download)
    try:
        if device == "cuda":
            dll_handles = _cuda_libraries()
        if device == "cuda" and compute not in ctranslate2.get_supported_compute_types("cuda"):
            raise RuntimeError(f"CUDA compute type {compute} is unsupported")
        model = WhisperModel(config.model, device=device, compute_type=compute, **kwargs)
    except (RuntimeError, ValueError, OSError) as exc:
        if device != "cuda":
            raise
        reason = f"CUDA initialization failed: {exc}; falling back to CPU int8"
        warnings.append(reason)
        LOG.warning(reason)
        model = None
        gc.collect()
        device, compute = "cpu", "int8"
        model = WhisperModel(config.model, device=device, compute_type=compute, **kwargs)
    LOG.info("Transcribing on %s with %s", device, compute)
    vad = dict(min_silence_duration_ms=config.min_silence_duration_ms,
               speech_pad_ms=config.speech_pad_ms)
    stat = source.stat()
    result = dict(status="running", input=dict(path=str(source), filename=source.name,
                  size_bytes=stat.st_size, mtime_ns=stat.st_mtime_ns),
                  model=config.model, device=device, compute_type=compute,
                  configuration=asdict(config), vad=vad, language="en", task="transcribe",
                  word_timestamps=True, condition_on_previous_text=False, batched=False,
                  packages={p: importlib.metadata.version(p) for p in
                            ("faster-whisper", "ctranslate2", "av", "onnxruntime")},
                  model_path=str(getattr(model, "model_path", config.model)),
                  limitations=["Word alignment is approximate, not frame accurate.",
                               "ASR may misrecognize speech; no accuracy percentage established.",
                               "PyAV decodes audio into memory; memory grows with recording duration."],
                  warnings=warnings, segments=[])
    failure = None
    try:
        segments, info = model.transcribe(str(source), language="en", task="transcribe",
            beam_size=config.beam_size, word_timestamps=True, vad_filter=True,
            vad_parameters=vad, condition_on_previous_text=False, temperature=0.0)
        result.update(audio_duration=getattr(info, "duration", None),
                      duration_after_vad=getattr(info, "duration_after_vad", None),
                      language=info.language, language_probability=info.language_probability)
        previous = -1
        for segment in segments:
            start, end = _time(segment.start), _time(segment.end)
            if start is None or end is None or end < start or start < previous:
                raise ValueError("Nonchronological segment timestamps")
            previous = start
            words = []
            word_previous = -1
            for word in segment.words or []:
                ws, we = _time(word.start), _time(word.end)
                if ws is not None and (ws < word_previous or (we is not None and we < ws)):
                    raise ValueError("Nonchronological word timestamps")
                if ws is not None:
                    word_previous = ws
                words.append(dict(text=word.word, start=ws, end=we,
                                  probability=getattr(word, "probability", None)))
            result["segments"].append(dict(id=segment.id, start=start, end=end,
                text=segment.text, words=words,
                avg_logprob=getattr(segment, "avg_logprob", None),
                no_speech_prob=getattr(segment, "no_speech_prob", None)))
        result["status"] = "complete"
    except Exception as exc:
        failure = exc
        result.update(status="failed_partial", error=f"{type(exc).__name__}: {exc}")
        LOG.error("Transcription failed after %d segments; no retry: %s", len(result["segments"]), exc)
    result["processing_duration"] = time.perf_counter() - started
    duration = result.get("audio_duration")
    result["real_time_factor"] = result["processing_duration"] / duration if duration else None
    words = [w for s in result["segments"] for w in s["words"]]
    aligned = sum(w["start"] is not None and w["end"] is not None for w in words)
    result["metrics"] = dict(segment_count=len(result["segments"]), word_count=len(words),
        aligned_word_count=aligned, word_timestamp_coverage=aligned / len(words) if words else None)
    target.mkdir(parents=True, exist_ok=True)
    (target / "transcript.json").write_text(json.dumps(result, ensure_ascii=False, indent=2,
                                                     allow_nan=False), encoding="utf-8")
    srt, txt = [], []
    for index, s in enumerate(result["segments"], 1):
        srt.append(f"{index}\n{timestamp(s['start'], ',')} --> {timestamp(s['end'], ',')}\n{s['text'].strip()}\n")
        txt.append(f"[{timestamp(s['start'])} - {timestamp(s['end'])}] {s['text'].strip()}")
    (target / "transcript.srt").write_text("\n".join(srt), encoding="utf-8")
    (target / "transcript.txt").write_text("\n".join(txt), encoding="utf-8")
    if failure:
        raise RuntimeError(f"Partial results saved in {target}; recording was not retried") from failure
    return result
