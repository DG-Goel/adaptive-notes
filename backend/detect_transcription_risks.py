"""Offline Stage 2 CLI; accepts existing timestamped transcript JSON only."""
import argparse
import json
from transcription_risk import RiskConfig, run

if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',required=True); p.add_argument('--output',required=True)
    p.add_argument('--config',help='JSON object overriding RiskConfig fields')
    a=p.parse_args()
    cfg=RiskConfig()
    if a.config:
        with open(a.config,encoding='utf-8') as f:
            cfg=RiskConfig(**json.load(f))
    print(json.dumps(run(a.input,a.output,cfg)['statistics'],indent=2))
