"""Quality gate (blueprint steps 9-11): checks a finished package before the owner sees it.

Each check returns PASS, FAIL (must be fixed before upload) or FLAG (owner decides).
Technical and most editorial checks are plain code and cost no API quota; the
editorial judgement (hook, title promise, visuals, sensitive topics) is ONE AI request.

    from yt_auto import gate
    result = gate.run(pkg_dir, library_dir, use_ai=True)
"""
from __future__ import annotations

import json
import math
import re
import subprocess
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path

PASS, FAIL, FLAG = "PASS", "FAIL", "FLAG"

# Limits (YouTube Studio: title 100 characters, description 5,000, tags 500; no < or > in either)
TITLE_MAX, DESC_MAX, TAGS_MAX = 100, 5000, 500
SILENCE_DB, SILENCE_MAX_S = -45, 2.0
LUFS_TARGET, LUFS_TOL, TRUE_PEAK_MAX = -16.0, 2.0, -1.0
BLACK_MIN_S = 1.0          # scene fades are 0.6 s of near-black: allowed
BLACK_PIX_TH = 0.05        # our dark card background (#0f1720) is above this, so cards don't count as black
LENGTH_TOL_S = 0.5
MINUTES = (5.0, 8.0)
# Originality thresholds (calibrated in phase3/eval_gate.py; see its report)
TOPIC_SIM_MAX = 0.45       # content-word cosine: unrelated 0.05, related space topic 0.29, same topic 0.57
TEMPLATE_SIM_MAX = 0.25    # share of sentences matching a past sentence once numbers are masked
COPY_SIM_MAX = 0.10        # 5-word phrase overlap with a past video


def check(name: str, status: str, detail: str = "", **data) -> dict:
    return {"check": name, "status": status, "detail": detail, **data}


# ---------- media (FFmpeg) ----------

def _ffmpeg(args: list[str], log: Path | None, timeout: int = 900) -> str:
    """Run FFmpeg with no stdin and a time limit; return its stderr (and keep it in a log file)."""
    r = subprocess.run(["ffmpeg", "-nostdin", "-hide_banner", *args], stdin=subprocess.DEVNULL,
                       capture_output=True, text=True, timeout=timeout)
    if log:
        log.write_text(r.stderr, encoding="utf-8")
    return r.stderr


def _duration(path: Path, stream: str) -> float | None:
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", stream, "-show_entries",
                        "stream=duration:format=duration", "-of", "json", str(path)],
                       stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=60)
    try:
        d = json.loads(r.stdout)
        vals = [float(s["duration"]) for s in d.get("streams", []) if s.get("duration")]
        return vals[0] if vals else float(d["format"]["duration"])
    except (ValueError, KeyError):
        return None


def media_checks(video: Path, logs: Path) -> list[dict]:
    out = []
    if not video.exists():
        return [check("video_file", FAIL, f"{video.name} is missing")]
    total = _duration(video, "v:0") or 0.0

    # Silence over 2 s in the middle (start/end pauses are fine)
    err = _ffmpeg(["-i", str(video), "-af", f"silencedetect=noise={SILENCE_DB}dB:d={SILENCE_MAX_S}",
                   "-vn", "-f", "null", "-"], logs / "gate_silence.log")
    starts = [float(x) for x in re.findall(r"silence_start: (-?[\d.]+)", err)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", err)] + [total]
    gaps = [(round(a, 1), round(b, 1)) for a, b in zip(starts, ends) if a > 1.0 and b < total - 1.0]
    out.append(check("audio_silence", FAIL if gaps else PASS,
                     f"silent gaps over {SILENCE_MAX_S:g} s at {gaps}" if gaps else "no long silent gaps", gaps=gaps))

    # Loudness (we normalise to -16 LUFS, true peak -1.5 dBTP)
    err = _ffmpeg(["-i", str(video), "-af", "ebur128=peak=true", "-vn", "-f", "null", "-"], logs / "gate_loudness.log")
    m_i = re.findall(r"I:\s+(-?[\d.]+) LUFS", err)
    m_p = re.findall(r"Peak:\s+(-?[\d.]+|-inf) dBFS", err)
    if not m_i:
        out.append(check("audio_loudness", FAIL, "could not measure loudness (no audio?)"))
    else:
        lufs = float(m_i[-1])
        peak = float(m_p[-1]) if m_p and m_p[-1] != "-inf" else -99.0
        bad = abs(lufs - LUFS_TARGET) > LUFS_TOL or peak > TRUE_PEAK_MAX + 0.5
        out.append(check("audio_loudness", FAIL if bad else PASS,
                         f"{lufs:.1f} LUFS (target {LUFS_TARGET:g} ± {LUFS_TOL:g}), true peak {peak:.1f} dBTP",
                         lufs=lufs, true_peak=peak))

    # Black frames longer than a scene fade
    err = _ffmpeg(["-i", str(video), "-vf", f"blackdetect=d={BLACK_MIN_S}:pix_th={BLACK_PIX_TH}", "-an", "-f", "null",
                   "-"], logs / "gate_black.log")
    blacks = [(round(float(a), 1), round(float(b), 1))
              for a, b in re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", err)]
    out.append(check("video_black", FAIL if blacks else PASS,
                     f"black frames at {blacks}" if blacks else "no black stretches", blacks=blacks))

    # Audio and video lengths match; overall length on target
    a_len, v_len = _duration(video, "a:0"), _duration(video, "v:0")
    if a_len is None or v_len is None:
        out.append(check("av_length", FAIL, f"audio {a_len}, video {v_len}: a stream is missing"))
    else:
        diff = abs(a_len - v_len)
        out.append(check("av_length", FAIL if diff > LENGTH_TOL_S else PASS,
                         f"audio {a_len:.1f} s, video {v_len:.1f} s (differ by {diff:.1f} s)"))
        mins = v_len / 60
        out.append(check("video_minutes", PASS if MINUTES[0] <= mins <= MINUTES[1] else FLAG,
                         f"{mins:.1f} min (target {MINUTES[0]:g}-{MINUTES[1]:g})"))
    return out


# ---------- package files ----------

def scene_checks(script: dict, visuals: list[dict], frames_dir: Path | None) -> list[dict]:
    covered = {v["scene"] for v in visuals}
    missing = [sc["id"] for sc in script["scenes"] if sc["id"] not in covered]
    no_frame = []
    if frames_dir is not None:
        no_frame = [v["id"] for v in visuals if not (frames_dir / f"{v['id']}.png").exists()]
    bad = missing or no_frame
    return [check("scenes_complete", FAIL if bad else PASS,
                  f"scenes with no visuals: {missing}; visuals with no frame: {no_frame[:10]}" if bad
                  else f"all {len(script['scenes'])} scenes have visuals")]


def rights_checks(visuals: list[dict], licences: list[dict]) -> list[dict]:
    from .photos import record_allowed

    problems = []
    by_file = {r.get("file"): r for r in licences if r.get("file")}
    kinds = {r.get("kind") for r in licences}
    for need in ("voice model", "font"):
        if need not in kinds:
            problems.append(f"no licence record for the {need}")
    for v in visuals:
        p = v.get("photo")
        if not p:
            continue
        r = by_file.get(p.get("file"))
        if r is None:
            problems.append(f"{v['id']}: picture {p.get('file')} has no licence record")
            continue
        missing = [k for k in ("source_page", "licence", "author", "attribution", "downloaded") if not r.get(k)]
        if missing:
            problems.append(f"{v['id']}: licence record missing {missing}")
        elif not record_allowed(r):
            problems.append(f"{v['id']}: licence {r['licence']!r} is not allowed")
    return [check("rights", FAIL if problems else PASS,
                  "; ".join(problems) if problems else f"{len(by_file)} pictures, voice and font all have allowed licences",
                  problems=problems)]


def metadata_checks(title: str, description: str, tags: list[str] | None = None) -> list[dict]:
    problems = []
    if not title.strip() or len(title) > TITLE_MAX:
        problems.append(f"title is {len(title)} characters (1-{TITLE_MAX} allowed)")
    if len(description) > DESC_MAX:
        problems.append(f"description is {len(description)} characters (max {DESC_MAX})")
    for name, text in (("title", title), ("description", description)):
        if "<" in text or ">" in text:
            problems.append(f"{name} contains < or >, which YouTube rejects")
    if tags and len(",".join(tags)) > TAGS_MAX:
        problems.append(f"tags are {len(','.join(tags))} characters (max {TAGS_MAX})")
    src = description.split("Sources", 1)[1] if "Sources" in description else ""
    if not re.search(r"https?://", src.split("Image credits", 1)[0]):
        problems.append("description lists no sources")
    return [check("metadata", FAIL if problems else PASS, "; ".join(problems) or
                  f"title {len(title)} chars, description {len(description)} chars, sources listed")]


VOICE_MATCH_MIN = 0.85  # share of script words heard in the owner's recording


def voice_checks(pkg: Path) -> list[dict]:
    """Own-voice videos: the recording must follow the fact-checked script."""
    f = pkg / "voice_match.json"
    if not f.exists():
        return []
    m = json.loads(f.read_text(encoding="utf-8"))
    share = m.get("script_words_heard")
    if share is None:
        return [check("voice_matches_script", FLAG, "could not check: no word timing from the recording")]
    missing = m.get("missing_sentences", [])
    status = FAIL if share < VOICE_MATCH_MIN else (FLAG if missing else PASS)
    detail = f"{share:.0%} of script words heard (need {VOICE_MATCH_MIN:.0%})"
    if missing:
        detail += f"; sentences skipped or changed: {[x['id'] for x in missing][:10]}"
    return [check("voice_matches_script", status, detail)]


def fact_checks(script: dict) -> list[dict]:
    bad = []
    for sc in script["scenes"]:
        for s in sc["sentences"]:
            if s["kind"] == "fact" and (not s.get("sources") or not str(s.get("check", "")).startswith("supported")):
                bad.append(f"{s['id']} ({s.get('check') or 'not checked'}, sources {s.get('sources')})")
    return [check("facts_linked", FAIL if bad else PASS,
                  f"unlinked or unsupported: {bad[:8]}" if bad else "every fact sentence has a checked source",
                  bad=bad)]


def brief_checks(plan: dict) -> list[dict]:
    need = ["question", "answer", "evidence", "unique_examples", "why_watch"]
    missing = [k for k in need if not str(plan.get(k, "")).strip()]
    return [check("editorial_brief", FAIL if missing else PASS,
                  f"brief is missing {missing}" if missing else "brief complete")]


def pronunciation_checks(script: dict, known: dict) -> list[dict]:
    """Acronyms and long rare words the voice may say wrongly, unless already in the list."""
    words = Counter()
    for sc in script["scenes"]:
        for s in sc["sentences"]:
            for w in re.findall(r"\b[A-Z][A-Z0-9-]{1,}\b|\b[A-Za-z]*\d[A-Za-z]+\b", s["text"]):
                words[w] += 1
    unknown = sorted(w for w in words if w not in known and w.lower() not in known)
    return [check("pronunciation", FLAG if unknown else PASS,
                  f"listen for: {unknown[:20]} (add them to pronunciation.json once checked)" if unknown
                  else "no new hard terms", terms=unknown)]


# ---------- originality: compare with past videos ----------

_STOP = set("""a an the and or but if then so of to in on at by for with from as is are was were be been being it its
this that these those there here you your we our they their he she his her them i me my not no yes do does did can
could will would should may might must just about into over under than more most less very also only even when
where why how what which who whom whose all any each every both few many much some such own same other another one
two three four five six seven eight nine ten first second""".split())


def _sentences(script: dict) -> list[str]:
    return [s["text"] for sc in script["scenes"] for s in sc["sentences"]]


def _content_words(text: str) -> Counter:
    return Counter(w for w in re.findall(r"[a-z]+", text.lower()) if w not in _STOP and len(w) > 2)


def _cosine(a: Counter, b: Counter) -> float:
    num = sum(a[k] * b[k] for k in a.keys() & b.keys())
    den = math.sqrt(sum(v * v for v in a.values())) * math.sqrt(sum(v * v for v in b.values()))
    return num / den if den else 0.0


def _masked(s: str) -> str:
    return re.sub(r"\d[\d,.]*", "#", s.lower())


def similarity(a: dict, b: dict) -> dict:
    sa, sb = _sentences(a), _sentences(b)
    topic = _cosine(_content_words(" ".join(sa)), _content_words(" ".join(sb)))
    # same template with new numbers: a sentence that matches a past one once numbers are masked
    mb = [_masked(x) for x in sb]
    hits = sum(1 for x in sa if any(SequenceMatcher(None, _masked(x), y).ratio() >= 0.8 for y in mb))
    template = hits / max(len(sa), 1)

    def grams(ss):
        w = re.findall(r"[a-z0-9]+", " ".join(ss).lower())
        return {" ".join(w[i:i + 5]) for i in range(len(w) - 4)}
    ga, gb = grams(sa), grams(sb)
    copy = len(ga & gb) / max(len(ga), 1)
    return {"topic": round(topic, 3), "template": round(template, 3), "copy": round(copy, 3)}


def originality_checks(script: dict, library: list[tuple[str, dict]]) -> list[dict]:
    if not library:
        return [check("originality", PASS, "no past videos to compare with yet")]
    rows = []
    for name, past in library:
        sim = similarity(script, past)
        rows.append({"past": name, **sim})
    worst = max(rows, key=lambda r: (r["topic"] >= TOPIC_SIM_MAX, r["template"], r["topic"]))
    reasons = []
    for r in rows:
        if r["topic"] >= TOPIC_SIM_MAX:
            reasons.append(f"same topic as {r['past']} (word similarity {r['topic']:.2f} ≥ {TOPIC_SIM_MAX})")
        if r["template"] >= TEMPLATE_SIM_MAX:
            reasons.append(f"{r['template']:.0%} of sentences follow {r['past']} with only numbers/words changed")
        if r["copy"] >= COPY_SIM_MAX:
            reasons.append(f"{r['copy']:.0%} of 5-word phrases copied from {r['past']}")
    return [check("originality", FAIL if reasons else PASS,
                  "; ".join(reasons) if reasons else
                  f"closest past video {worst['past']}: topic {worst['topic']:.2f}, template {worst['template']:.2f}, "
                  f"copy {worst['copy']:.2f}", compared=rows)]


def load_library(library_dir: Path | None, exclude_title: str = "") -> list[tuple[str, dict]]:
    if not library_dir or not library_dir.exists():
        return []
    out = []
    for f in sorted(library_dir.glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        script = d.get("script", d)
        if exclude_title and script.get("title") == exclude_title:
            continue
        out.append((f.stem, script))
    return out


# ---------- editorial judgement (one AI request) ----------

AI_SCHEMA = {"type": "object", "properties": {"checks": {"type": "array", "items": {
    "type": "object", "properties": {
        "check": {"type": "string", "enum": ["hook_question", "hook_why", "title_promise", "scene_relevance",
                                             "sensitive", "adds_value"]},
        "ok": {"type": "boolean"}, "reason": {"type": "string"}},
    "required": ["check", "ok", "reason"]}}}, "required": ["checks"]}


def ai_checks(title: str, plan: dict, script: dict, timing: dict, visuals: list[dict]) -> list[dict]:
    from .llm import LIGHT, LLMError, llm

    first30 = " ".join(s["text"] for s in timing["sentences"] if s["start"] < 30)
    body = "\n".join(f"## {sc['heading']}\n" + " ".join(s["text"] for s in sc["sentences"]) for sc in script["scenes"])
    cards = [v for v in visuals if not v.get("photo")]
    shown = "\n".join(f"{v['id']}: narration: {v['text'][:140]} | card: {json.dumps(v.get('card', {}), ensure_ascii=False)[:160]}"
                      for v in cards[:80])
    prompt = f"""You review a finished explainer video before a human checks it. Judge each item strictly,
using only what is given. Answer every check.

- hook_question: do the first 30 seconds clearly state the question the video answers?
- hook_why: do the first 30 seconds also say why the question matters to the viewer?
- title_promise: does the script actually deliver what the title promises (no promise the video doesn't keep,
  no claim the video contradicts)?
- scene_relevance: does each text card below show something the narration at that moment is saying? List any card
  ids that are generic or unrelated in the reason.
- sensitive: is there financial, legal or health ADVICE, or an accusation against a real named person or company?
  ok=true means none.
- adds_value: does the video explain and connect ideas (examples, comparisons, why), rather than only listing
  facts in a new order?

TITLE: {title}
QUESTION (from the brief): {plan.get('question', '')}
FIRST 30 SECONDS: {first30}

SCRIPT:
{body}

TEXT CARDS SHOWN:
{shown}"""
    try:
        res = llm(prompt, schema=AI_SCHEMA, name="gate_editorial", temperature=0.1, models=LIGHT)
    except LLMError as e:
        return [check("editorial_ai", FLAG, f"AI review not available: {e}")]
    out = []
    for c in res["checks"]:
        # Blueprint: the hook FAILS only with "no clear question up front"; the rest is the owner's call.
        status = PASS if c["ok"] else (FAIL if c["check"] in ("hook_question", "title_promise") else FLAG)
        out.append(check(c["check"], status, c["reason"]))
    for name in ("hook_question", "hook_why", "title_promise", "scene_relevance", "sensitive", "adds_value"):
        if name not in {c["check"] for c in out}:
            out.append(check(name, FLAG, "AI reviewer gave no answer"))
    return out


# ---------- run everything ----------

def run(pkg: Path, library_dir: Path | None = None, use_ai: bool = True, media: bool = True,
        pronunciation: dict | None = None, script: dict | None = None) -> dict:
    """pkg holds script.json, plan.json, timing.json, visuals.json, licences.json, description.txt
    (and video.mp4 + frames/ when media=True). `script` overrides script.json (e.g. a 2-scene test)."""
    script = script or json.loads((pkg / "script.json").read_text(encoding="utf-8"))
    plan = json.loads((pkg / "plan.json").read_text(encoding="utf-8"))
    visuals = json.loads((pkg / "visuals.json").read_text(encoding="utf-8"))
    licences = json.loads((pkg / "licences.json").read_text(encoding="utf-8"))
    desc = (pkg / "description.txt").read_text(encoding="utf-8")
    title = script["title"]
    logs = pkg / "gate_logs"
    logs.mkdir(exist_ok=True)

    results = []
    if media:
        results += media_checks(pkg / "video.mp4", logs)
    results += scene_checks(script, visuals, (pkg / "frames") if media else None)
    results += rights_checks(visuals, licences)
    results += metadata_checks(title, desc)
    if pronunciation is None:
        known = Path(__file__).resolve().parents[1] / "pronunciation.json"
        pronunciation = json.loads(known.read_text(encoding="utf-8")) if known.exists() else {}
    results += pronunciation_checks(script, pronunciation)
    results += voice_checks(pkg)
    results += fact_checks(script)
    results += brief_checks(plan)
    results += originality_checks(script, load_library(library_dir, exclude_title=title))
    if use_ai and (pkg / "timing.json").exists():
        timing = json.loads((pkg / "timing.json").read_text(encoding="utf-8"))
        results += ai_checks(title, plan, script, timing, visuals)
    verdict = FAIL if any(r["status"] == FAIL for r in results) else (
        FLAG if any(r["status"] == FLAG for r in results) else PASS)
    out = {"verdict": verdict, "checks": results}
    (pkg / "gate.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    return out


def markdown(result: dict) -> str:
    icon = {PASS: "✅", FAIL: "❌", FLAG: "⚠️"}
    head = {PASS: "READY for your review", FAIL: "NOT READY: fix the ❌ items first",
            FLAG: "READY, but decide on the ⚠️ items"}[result["verdict"]]
    lines = [f"## Quality gate: {head}", "", "| | Check | Result |", "| --- | --- | --- |"]
    order = {FAIL: 0, FLAG: 1, PASS: 2}
    for r in sorted(result["checks"], key=lambda r: order[r["status"]]):
        lines.append(f"| {icon[r['status']]} | {r['check']} | {r['detail'].replace('|', '/')} |")
    return "\n".join(lines) + "\n"
