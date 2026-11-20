"""Explicitly authorized full run: local TPD only excepted, all other checks retained."""
from datetime import datetime, timezone
from pathlib import Path
from app.extraction.quota_policy import daily_token_exception
from run_authorized_java import save
from run_full_multimodal_categories import main

PARENT = Path('data/output/multimodal_notes_category_full_20261110_135722_142723')
CONSENT = 'Current user: run the full etraction bypassing only the daily quota thing only keep still the reamining three'


if __name__ == '__main__':
    stamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S_%f')
    run_id = PARENT.name + ':tpd_exception:' + stamp
    save(PARENT/('tpd_exception_'+stamp+'.json'), dict(run_id=run_id, authorization=CONSENT,
        ignored_local_metric='TPD', enforced_metrics=['RPM','RPD','TPM'],
        accounting_preserved=True, provider_429_stops_run=True, persistent_defaults_changed=False))
    with daily_token_exception(authorization=CONSENT, run_id=run_id):
        main(resume=PARENT)
