"""Local media transcription CLI; downloads require an explicit opt-in."""
import argparse
import logging
from transcription import TranscriptionConfig, transcribe


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True, help="New or empty output directory")
    parser.add_argument("--model", default="small.en", help="Model name or local CTranslate2 model directory")
    parser.add_argument("--device", choices=("cuda", "cpu"), default="cuda")
    parser.add_argument("--compute-type", default="int8_float16")
    parser.add_argument("--beam-size", type=int, default=3)
    parser.add_argument("--cpu-threads", type=int, default=4)
    parser.add_argument("--min-silence-duration-ms", type=int, default=2000)
    parser.add_argument("--speech-pad-ms", type=int, default=400)
    parser.add_argument("--allow-model-download", action="store_true",
                        help="Explicitly authorize downloading the requested model weights")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    try:
        result = transcribe(args.input, args.output, TranscriptionConfig(
            model=args.model, device=args.device, compute_type=args.compute_type,
            beam_size=args.beam_size, cpu_threads=args.cpu_threads,
            min_silence_duration_ms=args.min_silence_duration_ms,
            speech_pad_ms=args.speech_pad_ms, allow_download=args.allow_model_download))
    except Exception as exc:
        logging.error("%s", exc)
        return 1
    logging.info("Saved %d segments; device=%s compute=%s elapsed=%.2fs RTF=%s",
                 result["metrics"]["segment_count"], result["device"], result["compute_type"],
                 result["processing_duration"], result["real_time_factor"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
