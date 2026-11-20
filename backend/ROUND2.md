# Round 2 notes refinement

For the local video library, run `.venv/Scripts/python.exe video_notes_jobs.py` from the backend directory and open `http://127.0.0.1:8765`. The page lists MP4 files directly in that directory. Start local Ollama with the installed `glm-ocr:q8_0` model available before submitting a job. The workflow also uses the existing transcription environment, cached Whisper model, React renderer bundle and Edge.

The page calls `POST /api/video-notes` with `{"video":"video3.mp4","allow_groq":true}`. Poll `GET /api/video-notes/{job_id}` for progress and retrieve `/study` or `/reference` under that job URL. The service binds to loopback and expects a same-origin page. Run one service instance per workspace. The active extraction pipeline retains RPM, RPD and TPM checks and usage accounting. Provider limits still apply.

Run these commands from the backend directory. The input directory contains Round 1's `partial_notes.md`, `extraction_results.json`, and `source_document.json`. The model receives the displayed note text and note IDs. Python reads the saved provenance for timing.

```powershell
cd notes-flowchart
npm.cmd exec --offline -- vite build --config vite.round2.config.js --outDir ../data/round2-renderer
cd ..
.venv/Scripts/python.exe run_round2.py data/output/multimodal_notes_category_full_20261110_135722_142723 data/output/round2_java_demo --demo
```

Use Edge or pass `--browser` with a Chromium executable. The demo uses a local fixture from two existing Java notes. Omitting the mode creates a notes-only request manifest and a preview with source gap annotations.

For live processing, supply an operator-reviewed inventory in the existing organization inventory format for slots 6–10, including key fingerprints, organization and project IDs, verification details and configured provider limits. Keep the actual keys in the environment file. Prepare the bundle with `--prepare-approvals <inventory.json>`, then use `--live <output/approvals.json>` with the same source and output directories. The live runner uses the existing shared quota ledgers, the configured 85% ceilings and the 6–10 rotation. A provider 429 stops the run. Subsequent runs reuse successful checkpoints.

The output includes Markdown with relative PNG references, renderer payloads, ordered notes with timestamp spans, teaching-unit proposals and a processing report. Keep the visuals directory alongside the Markdown when exporting. The original text remains available in the ordered notes even when a rendered table replaces a redundant note. A model-proposed rewrite is recorded for review. Exact timestamp resolution is limited to saved speech segment bounds, and broad source intervals are marked as needing alignment.

The operator-provided bindings for slots 6–10 are saved in `data/round2_organization_inventory.json`. Reuse this inventory when preparing approvals for a new notes manifest. The approvals for the existing 12-request Java manifest are in `data/output/round2_java_demo/approvals.json`.

After visual selection and rendering, use `run_round2.py NOTES.md OUTPUT --polish-notes` to prepare the text-only pass with the user’s textbook Markdown prompt. Pass `--prepare-approvals data/round2_organization_inventory.json` to prepare the bundle, then `--live OUTPUT/approvals.json` to run with the existing slots 6–10. Choose timestamped Markdown to keep timestamps or the reading copy for a metadata-free result. Tables and diagrams stay at their existing anchors. The polished Markdown is saved separately.
