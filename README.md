# yt-auto

Low-cost automated pipeline for original explainer videos. The pipeline makes the video; a human reviews every video and uploads it manually through YouTube Studio.

Blueprint: see the "YouTube Automation Blueprint" doc.

## Status: Phase 1 (production core)

Phase 0 (server benchmark) passed on 27 Oct 2026. Phase 1 makes a full, fact-checked video from a topic.

| Step | Tool | Cost / licence |
| --- | --- | --- |
| Plan, script, fact-check, visual plan | Gemini API free tier (`yt_auto/llm.py`, falls back across free Flash models) | free tier, no billing |
| Sources | English Wikipedia (passages saved with revision ids) | free; CC BY-SA text, facts only |
| Photos | NASA Image and Video Library, Wikimedia Commons | free, no key; PD / CC0 / CC BY / CC BY-SA only |
| Charts and cards | matplotlib | PSF-based |
| Narration | Kokoro via kokoro-onnx (CPU), speed 0.9 | Apache-2.0 / MIT |
| Motion and assembly | FFmpeg 8.1: Ken Burns pans/zooms, x264 | run as a separate program |
| Subtitles | our own script text, timed by sentence (exact) + faster-whisper word times | MIT |

AI illustrations are not used yet: every Gemini image model has a free-tier limit of 0 (checked 26 Oct 2026).

## Run it

**On GitHub (recommended):** Actions tab → "Phase 1 video" → Run workflow → enter a topic (use `scenes = 2` for a quick test). Results go to the `bench-results` branch under `phase1/<run_id>/` (review sheet, script with sources, contact sheet, 480p preview, logs). The full video, subtitles and description are attached to the run as `phase1-package` for 7 days.

Needs the repo secret `GEMINI_API_KEY`. "Phase 1 API check" confirms the key works and which free models answer.

**Locally (light test only):** the Phase 0 benchmark still works:

```bash
pip install -r requirements.txt
bash scripts/download_models.sh models
python phase0/run_benchmark.py --models models --out out/test --scenes 2 --skip-subtitles
```

## Layout

```
yt_auto/        pipeline modules (llm, research, writer, shots, photos, tts, visuals, render, align, subtitles, package, bench)
phase1/         make_video.py (topic -> package), check_apis.py (pre-flight)
phase0/         benchmark script and sample script
scripts/        model download
.github/        GitHub Actions workflows (all manual)
```

## Secrets

Add API keys only as GitHub repository secrets (Settings → Secrets and variables → Actions). Never commit them. Phase 0 needs no keys; Phase 1 uses `GEMINI_API_KEY`.
