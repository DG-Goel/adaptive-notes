"""Run the existing CLI unchanged and record external GPU observations."""
import datetime
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
if len(sys.argv) > 1:
    HERE = HERE.parent / sys.argv[1]
    HERE.mkdir(parents=True, exist_ok=False)
os.chdir(ROOT)
os.environ['HF_HUB_CACHE'] = str(ROOT / 'data' / 'transcriptions' / 'model-cache')
from faster_whisper.utils import download_model

begin = time.perf_counter()
print('Downloading/checking official Systran/faster-whisper-small.en only', flush=True)
model_path = download_model('small.en')
download_seconds = time.perf_counter() - begin
print(f'Model ready after {download_seconds:.2f}s: {model_path}', flush=True)
cmd = [sys.executable, 'transcribe_video.py', '--input', 'video.mp4', '--output',
       str(HERE / 'artifacts'), '--model', 'small.en', '--device', 'cuda',
       '--compute-type', 'int8_float16', '--beam-size', '3']
samples = []
started = time.perf_counter()
with (HERE / 'cli.log').open('w', encoding='utf-8') as log:
    proc = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT)
    while proc.poll() is None:
        r = subprocess.run(['nvidia-smi', '--query-gpu=timestamp,memory.used,utilization.gpu',
                            '--format=csv,noheader,nounits'], capture_output=True, text=True)
        samples.append({'elapsed_seconds': time.perf_counter()-started,
                        'sample': r.stdout.strip(), 'error': r.stderr.strip()})
        time.sleep(1)
elapsed = time.perf_counter()-started
peak = max((int(s['sample'].split(',')[1].strip()) for s in samples if s['sample']), default=None)
report = dict(command=cmd, exit_code=proc.returncode, cli_wall_seconds=elapsed,
              model_download_or_cache_seconds=download_seconds, official_model_path=model_path,
              gpu_peak_total_used_mib=peak, gpu_sampling_interval_seconds=1,
              gpu_memory_scope='Whole GPU, includes other processes; sampled peak, not exact allocation peak',
              gpu_samples=samples)
(HERE / 'runtime_observations.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k != 'gpu_samples'}, indent=2), flush=True)
raise SystemExit(proc.returncode)
