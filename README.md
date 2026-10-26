# yt-auto

Low-cost automated pipeline for original explainer videos. The pipeline makes the video; a human reviews every video and uploads it manually through YouTube Studio.

Blueprint: see the "YouTube Automation Blueprint" doc.

## Status: Phase 0 (server benchmark)

Phase 0 checks that one complete ~6-minute video can be built on a free server, three times in a row, in under 25 minutes each.

| Step | Tool | Licence |
| --- | --- | --- |
| Narration | Kokoro via kokoro-onnx (CPU) | Apache-2.0 / MIT |
| Keyframes (charts, diagrams, cards) | matplotlib | PSF-based (BSD-style) |
| Motion and assembly | FFmpeg: slow zoom, fades, x264 | LGPL/GPL (run as a separate program) |
| Subtitles | faster-whisper `base.en`, int8 | MIT |

`phase0/sample_script.json` is a benchmark sample only. It has not been through fact-checking and is not for upload.

## Run it

**On GitHub (recommended):** Actions tab → "Phase 0 benchmark" → Run workflow. Results are saved to the `bench-results` branch; the full video of run 1 is attached to the workflow run as `phase0-video` for 7 days.

**Locally (light test only):**

```bash
pip install -r requirements.txt
bash scripts/download_models.sh models
python phase0/run_benchmark.py --models models --out out/test --scenes 2 --skip-subtitles
```

## Layout

```
yt_auto/        pipeline modules (tts, visuals, render, subtitles, bench)
phase0/         benchmark script and sample script
scripts/        model download
.github/        GitHub Actions workflow
```

## Secrets

Add API keys only as GitHub repository secrets (Settings → Secrets and variables → Actions). Never commit them. Phase 0 needs no keys; Phase 1 will use `GEMINI_API_KEY`.
