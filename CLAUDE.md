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
- Never commit secrets. Keys live in GitHub repo secrets only. `GEMINI_API_KEY` is saved as a repo secret (confirmed 26-27 Oct 2026). **Use only `GEMINI_API_KEY`** (owner, 27 Oct). On 27 Oct the owner replaced it with a key from another project after the old project hit its daily limit; Claude explained the terms risk twice, the owner confirmed free tier and decided to go ahead. From then on: this one key only, no further switching to reset limits. Don't ask about other keys; never use extra keys or projects to get more free quota (Google APIs Terms: "will not attempt to circumvent" limits).
- Never pass `toJSON(secrets)` in a workflow: GitHub held those runs as 'action required'.
- **Upload rules (owner approved 28 Oct 2026):**
  - **R1** A video is "ready for review" only if every automatic check passes. Checks: every line sourced (facts_linked), quality gate has no FAIL, every photo/drawing was looked at by the AI and rejected ones are not used (pictures_checked), plain text cards (title/bullets) ≤ 25 % (plain_cards), a thumbnail exists and matches (thumbnail), the title promise is kept (title_promise). Otherwise the GitHub release is titled "DRAFT - do not upload". Then the owner watches it and ticks the checklist.
  - **R2** Honest emotion: the hook must be true and answered in the video; no fake urgency ("scientists are terrified") unless a source says it; thumbnail text matches the content.
  - **R3** Quality over volume: at most 1 video a day, each with its own question and structure. Never mass-upload (counter-example studied 28 Oct: @Jack-j4p8p, 174 AI space videos in 8 months, 6 subscribers, 2,276 total views).

## Verified facts (checked against official pages, 26 Oct 2026)

- YPP India, lower tier: 500 subs + 3 uploads/90 days + 3,000 watch hours/12 months or 3M Shorts views/90 days. Unlocks fan funding and shopping only, not ads.
- Ad revenue: 1,000 subs + 4,000 hours or 10M Shorts views; **from 1 Feb 2027 new applicants need 8,000 hours or 20M Shorts views** (YouTube Blog, 10 Aug 2026).
- The "2 Dec 2025 rule banning text-to-speech videos" quoted by Gemini and some reviews is **not on YouTube's official page**. Ignore it. The real rule bans reading other people's text (articles, forums) regardless of voice.
- No official evidence found of an AI-voice + programmatic-visuals explainer channel succeeding. That is why the pilot tests Kokoro vs the owner's own voice.

## Status

| Phase | State |
| --- | --- |
| 0. Server benchmark | **PASSED** 27 Oct 2026: 3/3 runs on GitHub Actions (AMD EPYC, 4 cores), build 3 min 18 s to 3 min 26 s, ~4 min per job, peak ~690 MB, no hangs |
| 0b. Niche data test | **Running** (week 0 = 27 Oct 2026). Rules frozen first (phase0b/RULES.md); v2 approved by owner after the first pull, before any growth data: 20 searches per niche (2,356 candidates, 80 eligible). Chosen: science 20, technology 12, money 11 (rule: under 15 cannot win, so far only science qualifies; all 43 are still measured). Weekly snapshots Mondays 03:17 UTC from `main` (2, 9, 16, 23 Nov); final report and owner's niche choice after 23 Nov. ~7,000 YouTube units used on day 1; ~90 per weekly snapshot. **Backward check** (owner asked for a faster answer; method written first in RULES.md) 27 Oct: science 57 eligible / 32 young channels, 611 subs/month, momentum 1.9, breakouts 24 %, Wikipedia 5.0 M views/6 mo (0.97x); technology and money only 4-5 young channels (too little data), money interest falling (0.82x). Backward winner: **science and space** (agrees with the forward rule). **Owner chose science and space on 27 Oct** (niche: niches/science_space.json); the 4-week test keeps running as a check and the choice can change if it disagrees strongly by 23 Nov. Results bench-results/phase0b/backward.md |
| 1. Production core | **DONE**, owner approved the video 27 Oct 2026. Run 40469284296: 7.4 min GPS video, 900 words fact-checked, 99 visuals (44 real photos, each checked by looking), subtitles from our own text, ~11 min on Actions. Owner liked the earlier 3.9 min version; quality work moves to later phases. Known weak spots: some title-only cards, one off-topic diagram (geostationary, v031) |
| 2. Research and facts | **Test PASSED** 27 Oct 2026 (run 40466026336): 30/30 planted errors caught, 0/16 false alarms (rule set before testing: ≥80% overall, ≥60% per type, ≤1 false alarm). First run 28/30 (missed 2 conflicting-source cases) → one prompt rule added. Also: number/unit guard, facts.csv, rights gate, junk-passage filter. Caveat: test set written by the same author as the checker; add independent cases later |
| 3. Quality gate | **Test PASSED** 27 Oct 2026 (run 40477248640): all 6 blueprint faults caught (silent gap, unlicensed image, wrong title promise, 3 kinds of near-duplicate), 17/17 planted faults overall, 0/5 false blocks on clean controls. First AI run blocked the approved video on 'hook'; split per blueprint (no question = FAIL, no 'why it matters' = FLAG). The gate also found a real bug: GPS description 9,850 chars (YouTube max 5,000) → credits shortened |
| 4. Topic finding | **DONE (done-when met)** 27 Oct 2026, run 40533636460 (science_space, provisional until the 0b result): 25 ideas proposed from 84 measured signals (40 'beats its channel's normal' videos, 4 trending, 40 news), 10 chosen with evidence, 15 in reserve, none repeating library/. Re-run for the winning niche after 23 Nov. Uses 2 Gemini requests + 3 YouTube units. Ideas in bench-results/phase4/<niche>/<run_id>/ideas.md |
| 5. Pilot and voice test | **In progress** (27 Oct). 8 science-and-space videos from the top 8 Phase 4 ideas (pilot/pilot.json). **Owner decided 27 Oct: no own-voice recordings for now, all 8 use Kokoro**; the voice test is postponed, own-voice tools stay ready. Own-voice flow: run 1 with stop_after_script → owner records from recording_script.md and uploads to voice/<folder>/ → run 2 with resume_from + owner_voice_folder. Gate checks the recording follows the checked script (≥85 % of words). Videos also published as GitHub pre-releases (plain mp4). pilot/summary.py builds the cost/time/failure table. Max ~2 videos/day (Gemini 20/day per model) |
| 6, auto-upload | Not started (see blueprint) |

Owner feedback on the Phase 0 video: **voice quality good**; pace was a bit fast (fixed: speed 0.9, longer pauses); **wants more pictures** (decided: real photos first, AI illustrations when none fits).

Owner feedback on the first Phase 1 video (27 Oct): quite good; full-length video approved ("ok for the current step"); wants more quality changes, to be done in later phases. Known weak spots: a few off-topic or misleading photos (e.g. a geostationary diagram for GPS), some bare title cards, video shorter than target when Flash-Lite wrote the script.

## Phase 1 facts (checked 26 Oct 2026 from a GitHub Actions run, not from blogs)

- Gemini free tier (pricing page): free text models are 3.8 Flash, 3.6 Flash, 3.5 Flash-Lite, 3.1 Flash-Lite, Gemma 4. `gemini-2.5-flash` and `2.5-flash-lite` return 404 "no longer available to new users". Exact RPM/RPD are shown only in AI Studio, not on the docs page. Free tier content may be used by Google to improve products.
- **Every Gemini image model has a free-tier limit of 0** (429 `limit: 0` for 2.5-flash-image, 3-pro-image, 3.1-flash-image). So no AI illustrations at ₹0; photos + charts/cards only.
- **Free tier = 20 requests/day per model** for 3.8 Flash, 3.6 Flash and 3.5 Flash (from the 429 replies: `GenerateRequestsPerDayPerProjectPerModel-FreeTier`, quotaValue 20; resets midnight Pacific = 12:30 pm IST). Failed 503 attempts seem to count. One video needs ~8-9 calls, so about 2-3 videos a day. Test runs spend the same quota: use `resume_from`.
- 3.8 Flash is often overloaded (503) and slow (script call 590 s). `llm()` falls back down a model list; quick jobs start on 3.6 Flash; script and fact-check never use Flash-Lite (it copied source wording).
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
yt_auto/llm.py         one llm() for all text steps, every call logged. QUALITY (3.8/3.6/3.5 Flash) for plan, script,
                       fact-check, topic ideas; LIGHT (Gemma 4 31B -> Flash-Lite -> GitHub Models gpt-4.1-mini -> Flash)
                       for visual plan, photo pick/check, gate, topic scores. Busy (503) model skipped at once, not retried
phase5/check_models.py live check of the LIGHT/VISION models (JSON, pictures in order, GitHub raw replies);
                       .github/workflows/ai-models-check.yml manual, results bench-results/phase5/models-check/<run_id>/
yt_auto/research.py    Wikipedia articles -> numbered passages (sources.json, with revision ids)
yt_auto/writer.py      plan -> script (each sentence cites passage ids) -> separate fact-check -> fix or drop
yt_auto/shots.py       ~4.5 s visual slots, visual plan, photo pick + vision check, card-number guard
yt_auto/photos.py      NASA + Commons search, licence filter, licence JSON per file
yt_auto/drawings.py    AI ink drawings (Segmind-Vega + VegaRT, Apache-2.0) on the runner CPU, own process, max 24 (12 planned) / 32 min;
                       for ideas no photo shows, then photo slots with no photo; shots.add_drawings looks at each (VISION) and drops bad ones
yt_auto/align.py       subtitles from our own text: exact sentence times + whisper word times
yt_auto/package.py     description.txt, licences.json, review.md, contact sheet
phase1/make_video.py   topic -> package (stages cached in --out, so a rerun resumes)
yt_auto/factguard.py   plain-code number/unit check beside the AI fact-check (no quota)
phase2/factcheck_testset.json  planted errors + controls (real Wikipedia passages; X* passages are synthetic)
phase2/eval_factcheck.py       counts misses/false alarms per error type (1 Gemini request); --guard-only needs none
.github/workflows/phase2-factcheck-eval.yml  manual; results in bench-results/phase2/<run_id>/
yt_auto/gate.py        quality gate: FFmpeg silence/loudness/black/length, scenes, rights, metadata, pronunciation, facts, brief, originality vs library/, 1 AI request (hook, title promise, cards, sensitive, value). PASS/FAIL/FLAG; results lead review.md
library/               approved videos (script JSON) that new videos must not duplicate. Add each video the owner approves
pronunciation.json     terms checked by listening; others get flagged
phase3/eval_gate.py    planted-fault test (2 Gemini requests; --no-ai needs none); fixtures in phase3/fixtures/
.github/workflows/phase3-gate-eval.yml  manual; results in bench-results/phase3/<run_id>/
phase0b/niche_test.py  niche test: check, select (once), snapshot (weekly), report; settings phase0b/niches.json, rules phase0b/RULES.md
.github/workflows/phase0b-niche.yml  manual (start/snapshot/report) + Mondays 03:17 UTC (only from main)
yt_auto/topics.py      Phase 4: signals (0b outliers, YouTube chart cat 28, RSS, Wikipedia views) -> 1 Gemini call ideas -> repeat filter vs library/ -> 1 Gemini call scores -> fixed formula (demand 0.35)
niches/<niche>.json    per-niche settings (blueprint's niche.yaml, JSON to avoid a dependency)
phase4/find_topics.py  entry; .github/workflows/phase4-topics.yml manual (niche choice)
yt_auto/owner_voice.py own-voice: recording_script.md; phone files → cleaned (highpass, afftdn, numpy pause shortening: FFmpeg silenceremove misbehaved on 6.1) → whisper word times → sentence times from our text → voice_match.json
voice/                 owner's recordings, one folder per video (see voice/README.md)
pilot/pilot.json       Phase 5 tracker; pilot/summary.py → pilot/report.md
study/study_video.py   learn from another video (facts, captions, frames, shot changes); .github/workflows/study-video.yml manual, results bench-results/study/<id>/<run_id>/ (video not kept)
phase5/drawing_test.py free open image model on the runner CPU: licence, seconds per drawing, memory, sample sheet; .github/workflows/drawing-test.yml manual, results bench-results/phase5/drawing-test/<run_id>/
phase1/check_apis.py   pre-flight: key present, which models answer, NASA/Commons up, saves official pages
.github/workflows/phase1-video.yml   manual only (topic, scenes, resume_from, new_visual_plan, stop_after_script, owner_voice_folder); publishes video-<run_id> pre-release with plain mp4
.github/workflows/phase1-check.yml   manual; also runs when the check changes on a phase-1 branch
phase0/run_benchmark.py      end-to-end benchmark; phase0/sample_script.json (GPS sample, not fact-checked, not for upload)
.github/workflows/phase0-benchmark.yml   manual only (Actions -> Run workflow, 1 or 3 runs)
```

Results of each workflow run are committed to the **`bench-results`** branch: Phase 0 `<run_id>/run<n>/`, Phase 1 `phase1/<run_id>/` (report.json with every LLM call, review.md, script, factcheck, visuals, contact_sheet.jpg, preview, llm/ prompts+replies), checks `phase1-check/<run_id>/`. Full video is an Actions artifact (7 days).

A new workflow can't be started by hand from a branch (404) until it has run there once. Fix: give it a narrow path-limited push trigger for one run, then remove it (done for phase1-video; phase1-check still has it).

A failed run is not always a bug: run 40404179356 failed only because all strong Gemini models had used their 20 requests/day. Check report.json for 429 before changing code.

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
10. Network: `ConnectionResetError` while reading a reply is not a `URLError`; catch `OSError` (crashed a run once).
11. Parse model answers loosely: Flash-Lite answered `wiki:6` where `6` was asked, and every photo pick was lost.
9. Phase 1: Commons/NASA have photos of objects, not staged scenes: ask for simple subjects, pick leniently, verify by looking.

## Reused open-source parts

Used: Kokoro / kokoro-onnx (Apache-2.0 / MIT), matplotlib, FFmpeg 8.1 (run as a separate program), faster-whisper (MIT). To borrow ideas from: MoneyPrinterTurbo (MIT; FFmpeg/subtitle code), darkzOGx youtube-automation-agent (MIT; approval-before-upload, job resume). Study only: OpenMontage (AGPL — don't copy code). Not used: gemini-youtube-automation (auto-uploads with no review), ai-youtube-shorts-automation (no licence), TubeFlow (no video), Coqui XTTS-v2 (model licence), Remotion (paid licence above 3 people).

## Conventions

- Commit messages explain why. Push to `main` (owner approved merging on 27 Oct; work branch `claude/phase-1-production-core-ufulti` was fast-forwarded into `main` at 744ebce).
- Gemini quota (27 Oct, owner said 'build it'): strong Flash only for plan/script/fact-check (~3-4 calls a video); light jobs on Gemma 4 (same key, free, separate limit) and GitHub Models (free, uses the workflow's own token, `permissions: models: read`). Models check results (27 Oct, runs 40557681397, 40559021860, 40560587143, 40560953772): 3.5 Flash-Lite JSON + pictures OK; 3.1 Flash-Lite OK but often 503; Gemma 4 text JSON OK once, then 500/503, and **HTTP 500 to every request with pictures** (so the photo check uses the VISION list, no Gemma); GitHub Models answers a bare 'OK' (text/plain, from GitHub's own IP) to catalog and chat: most likely Models is not enabled in repo Settings -> Models (owner asked). Until then it is skipped cleanly (non-JSON reply = next model). GitHub Models limits are third-party figures until a call works.
- Drawing test 27 Oct (run 40576992038): Segmind-Vega + VegaRT (both Apache-2.0, not gated) on the 4-core runner, 1024x576, 4 steps: 76 s per drawing, peak 9.2 GB RAM, model load 52 s. Ink style mostly holds; about 5 of 10 match their idea (ship, road, satellite cutaway, city, ground station), others miss (no Earth/satellite ring, garbled clock text, distorted hand, three circles not drawn), backgrounds switch black/white. Too slow for every shot (~2 h for 99); fits ~15-20 drawings per video for ideas photos can't show. Below the quality of the fitness channel the owner studied.
- Mixed visuals (owner chose A, 27 Oct): real photos first, then up to 24 AI ink drawings (12 planned + photo slots whose photo failed) (black background, red accent), then cards. Drawings are non-realistic (no YouTube AI disclosure), credited in the description, licence record source `ai_drawing` allowed only if the model licence is Apache-2.0 or MIT (photos.record_allowed). Workflow input max_drawings (0 = off).
- Quota note 27 Oct: at 21:00 UTC 3.5/3.6/3.8 Flash all answered 429 'daily free quota used up'; at 21:22 UTC (check run 40586113978) 3.5 and 3.6 answered 200. Owner confirmed the key was NOT changed. So the free daily quota is not strictly a midnight-Pacific reset; check with phase1-check (full) before assuming it is used up.
- Picture check (27 Oct): when the vision model is told what a picture should show, it copies that as what it 'saw' (passed all 18 drawings of pilot video 1). Now: blind describe (VISION) then a text judge (LIGHT). Test on pilot video 1 frames (phase5/check_pictures.py, picture-check.yml, run 40592925859): drawings 5 of 6 bad caught, 3 abstract ones also rejected; photos: wrong-object photos rejected, Mars chart still passed the AI, so chart/graph/diagram photo requests become cards in code (shots.CHART_WORDS).
- Phase 1+ workflows: manual trigger or schedule, never on every push (saves free minutes; private repo has 2,000 min/month).
- Test small locally (1–2 scenes) before using GitHub minutes.

- Chrome may block GitHub artifact zips as "dangerous download"; the owner keeps them via chrome://downloads. Consider GitHub Releases for plain mp4 downloads.
