# CLAUDE.md — project memory for yt-auto

Read this first in every session. It records the goal, decisions and lessons so far.

## The owner

- Nandu, a creator in Andhra Pradesh, India. Writes basic English: reply in **plain, simple English**, short sentences, tables where helpful.
- Laptop: 16 GB RAM, RTX 3050, **GPU fan broken**. Never run heavy work (rendering, TTS, whisper) on it. Light tests only. All real runs happen on **GitHub Actions** (later maybe Oracle Cloud Always Free).
- Has ChatGPT Go, Gemini Pro and Claude Pro subscriptions. These are chat apps; the pipeline uses APIs, not these subscriptions.
- Budget: **₹0 recurring**. No paid APIs or billing accounts unless the owner explicitly approves after measured need.

## The goal

A low-cost automated pipeline that makes **original, fact-checked explainer videos** for a worldwide English audience. The system does everything up to an upload-ready package. **The owner reviews every video and uploads manually in YouTube Studio.** Auto-upload is out of scope until the YouTube API audit passes (unaudited API uploads are forced private).

Full plan: "YouTube Automation Blueprint" doc — https://claude.ai/artifact/XN7whLn8Zb58uT3u6SKKeA (version 2, revised after outside reviews by ChatGPT and Gemini).

## Ground rules (do not break)

- Every factual script line links to a saved source. No source, no claim.
- Every asset (image, font, music, voice, model) has a licence record: source URL, licence + version, attribution, download date. Allowed: public domain, CC0, CC BY, CC BY-SA. **Never CC BY-NC or ND.**
- Every video has its own question, structure and visuals. Never the same template with new numbers (YouTube "inauthentic content" rule, renamed 15 Jul 2025).
- No AI "expert" persona. No financial, legal or health advice. No corporate-fraud or named-company accusation topics (defamation risk in India).
- AI disclosure box in YouTube is needed only for realistic AI depictions of real people/places/events. AI script, TTS narration, charts and non-realistic illustrations do not need it.
- Never commit secrets. Keys live in GitHub repo secrets only. `GEMINI_API_KEY` is saved as a repo secret (confirmed by the Phase 1 API check run, 26 Oct 2026).

## Verified facts (checked against official pages, 26 Oct 2026)

- YPP India, lower tier: 500 subs + 3 uploads/90 days + 3,000 watch hours/12 months or 3M Shorts views/90 days. Unlocks fan funding and shopping only, not ads.
- Ad revenue: 1,000 subs + 4,000 hours or 10M Shorts views; **from 1 Feb 2027 new applicants need 8,000 hours or 20M Shorts views** (YouTube Blog, 10 Aug 2026).
- The "2 Dec 2025 rule banning text-to-speech videos" quoted by Gemini and some reviews is **not on YouTube's official page**. Ignore it. The real rule bans reading other people's text (articles, forums) regardless of voice.
- No official evidence found of an AI-voice + programmatic-visuals explainer channel succeeding. That is why the pilot tests Kokoro vs the owner's own voice.

## Status

| Phase | State |
| --- | --- |
| 0. Server benchmark | **PASSED** 27 Oct 2026: 3/3 runs on GitHub Actions (AMD EPYC, 4 cores), build 3 min 18 s to 3 min 26 s, ~4 min per job, peak ~690 MB, no hangs |
| 0b. Niche data test | Not started. Needs a YouTube Data API key (owner to create). Niches to test: how technology works, science and space, money and economics (education only) |
| 1. Production core | **In progress** (branch `claude/phase-1-production-core-ufulti`). Pipeline built; first full video under review |
| 2–6, auto-upload | Not started (see blueprint) |

Owner feedback on the Phase 0 video: **voice quality good**; pace was a bit fast (fixed: speed 0.9, longer pauses); **wants more pictures** (decided: real photos first, AI illustrations when none fits).

## Phase 1 facts (checked 26 Oct 2026 from a GitHub Actions run, not from blogs)

- Gemini free tier (pricing page): free text models are 3.8 Flash, 3.6 Flash, 3.5 Flash-Lite, 3.1 Flash-Lite, Gemma 4. `gemini-2.5-flash` and `2.5-flash-lite` return 404 "no longer available to new users". Exact RPM/RPD are shown only in AI Studio, not on the docs page. Free tier content may be used by Google to improve products.
- **Every Gemini image model has a free-tier limit of 0** (429 `limit: 0` for 2.5-flash-image, 3-pro-image, 3.1-flash-image). So no AI illustrations at ₹0; photos + charts/cards only.
- 3.8 Flash is often overloaded (503) and slow (script call 590 s). `llm()` falls back down a model list; quick jobs start on 3.6 Flash.
- NASA Image Library API and Wikimedia Commons API: free, no key. NASA: media generally not copyrighted, credit NASA, no endorsement, no NASA logo with AI imagery, don't attribute LLM text to NASA, third-party © images excluded. Wikimedia: User-Agent with contact, one request at a time.
- Commons descriptions can be vandalised (saw one); the vision check of chosen photos is the safety gate.

## Phase 1 to-do (production core)

1. Script from a topic with the Gemini API free tier (Flash-class model; no billing). One `llm()` function so the provider can be swapped. Target 900–1,000 words for ~6 minutes at speed 0.9 (the 630-word sample gave ~4.5 min).
2. Picture step:
   - Real photos first: NASA Image and Video Library API (no key), Wikimedia Commons API. Filter to allowed licences; save licence JSON next to each file.
   - AI illustrations only when no photo fits: Gemini image model, clearly non-realistic style; check free-tier limits in AI Studio first.
   - A new visual every ~4–5 seconds, mixing photos (Ken Burns via FFmpeg), charts and diagrams.
3. Subtitles: time **our own script text** (forced alignment) instead of whisper's transcription, which mishears words ("too" for "to").
4. Keep Phase 0 lessons below. Keep the benchmark/diagnostics code.
5. Done when: one 5–8 minute video, good enough to publish, renders end to end with no manual editing.

## Code layout

```
yt_auto/tts.py         Kokoro via kokoro-onnx (CPU). Speed 0.9, 0.4 s sentence pause, 1.0 s scene pause
yt_auto/visuals.py     matplotlib keyframes: title, stat, bullets, flow, bars, line, circles
yt_auto/render.py      FFmpeg: per-keyframe segment (zoompan + fades), concat, mux (loudnorm -16 LUFS), preview
yt_auto/subtitles.py   faster-whisper base.en int8; run as its own process: python -m yt_auto.subtitles in.wav out.srt
yt_auto/bench.py       timings, memory, CPU model, FFmpeg version
yt_auto/llm.py         one llm() for all text steps: Gemini free tier, model fallback, every call logged
yt_auto/research.py    Wikipedia articles -> numbered passages (sources.json, with revision ids)
yt_auto/writer.py      plan -> script (each sentence cites passage ids) -> separate fact-check -> fix or drop
yt_auto/shots.py       ~4.5 s visual slots, visual plan, photo pick + vision check, card-number guard
yt_auto/photos.py      NASA + Commons search, licence filter, licence JSON per file
yt_auto/align.py       subtitles from our own text: exact sentence times + whisper word times
yt_auto/package.py     description.txt, licences.json, review.md, contact sheet
phase1/make_video.py   topic -> package (stages cached in --out, so a rerun resumes)
phase1/check_apis.py   pre-flight: key present, which models answer, NASA/Commons up, saves official pages
.github/workflows/phase1-video.yml   manual (topic, scenes); also a 2-scene test when the workflow file changes on a phase-1 branch
.github/workflows/phase1-check.yml   manual; also runs when the check changes on a phase-1 branch
phase0/run_benchmark.py      end-to-end benchmark; phase0/sample_script.json (GPS sample, not fact-checked, not for upload)
.github/workflows/phase0-benchmark.yml   manual only (Actions -> Run workflow, 1 or 3 runs)
```

Results of each workflow run are committed to the **`bench-results`** branch: Phase 0 `<run_id>/run<n>/`, Phase 1 `phase1/<run_id>/` (report.json with every LLM call, review.md, script, factcheck, visuals, contact_sheet.jpg, preview, llm/ prompts+replies), checks `phase1-check/<run_id>/`. Full video is an Actions artifact (7 days).

A new workflow can't be started by hand from a branch (404) until it has run there once; that's why the Phase 1 workflows also have a narrow path-limited push trigger.

## Lessons from Phase 0 (7 attempts) — do not repeat

1. **FFmpeg: use the static release build `ffmpeg-n8.1-latest-linux64-gpl-8.1.tar.xz` from BtbN, cached.**
   - Ubuntu `apt-get install ffmpeg` hung twice on runners (12+ and 8+ min).
   - The daily **master** build looped forever (100% CPU, no progress at 32.6 s) when decoding on AMD EPYC runners, even with `-threads 1`.
2. **Run faster-whisper in a separate process.** It leaves threads behind; starting FFmpeg afterwards in the same process can freeze.
3. **faster-whisper: pass a 16 kHz numpy array**, not a file path. Newer PyAV breaks its file decoder (`metadata_errors` TypeError).
4. Every FFmpeg call: `-nostdin`, `stdin=DEVNULL`, a timeout, and its own log file. `faulthandler.dump_traceback_later` in the entry script. These made the real cause provable instead of guessed.
5. Pin `runs-on: ubuntu-24.04` and Python 3.13. Give every workflow step a `timeout-minutes`.
6. Diagnose with evidence before changing code. The owner explicitly asked for this.
7. Workflow logs on GitHub's log storage can't be read from Claude's cloud sessions (404, even live); that's why logs are saved to the `bench-results` branch.
8. Phase 1: `faulthandler` must fire before the workflow step timeout, or a hang leaves no stack.
9. Phase 1: Commons/NASA have photos of objects, not staged scenes: ask for simple subjects, pick leniently, verify by looking.

## Reused open-source parts

Used: Kokoro / kokoro-onnx (Apache-2.0 / MIT), matplotlib, FFmpeg 8.1 (run as a separate program), faster-whisper (MIT). To borrow ideas from: MoneyPrinterTurbo (MIT; FFmpeg/subtitle code), darkzOGx youtube-automation-agent (MIT; approval-before-upload, job resume). Study only: OpenMontage (AGPL — don't copy code). Not used: gemini-youtube-automation (auto-uploads with no review), ai-youtube-shorts-automation (no licence), TubeFlow (no video), Coqui XTTS-v2 (model licence), Remotion (paid licence above 3 people).

## Conventions

- Commit messages explain why. Push to `main`.
- Phase 1+ workflows: manual trigger or schedule, never on every push (saves free minutes; private repo has 2,000 min/month).
- Test small locally (1–2 scenes) before using GitHub minutes.
