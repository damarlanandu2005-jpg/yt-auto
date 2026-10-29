"""Phase 4 topic finding (blueprint steps 1 and 2).

Step 1, Topic Scout: gather MEASURED demand signals for a niche (no AI), then one Gemini request
proposes video questions that each cite at least one signal. Every idea is then measured again
with Wikipedia page views; an idea with no measured demand is dropped.

Step 2, Opportunity Scorer: drop ideas that repeat a past video (library/) or each other, one
Gemini request scores the rest on a fixed rubric, and a fixed formula (measured demand weighted
most) ranks them.

Signals (all free): videos beating their channel's normal (Phase 0b snapshots), YouTube's
most-popular charts (1 unit each), news RSS headlines, Wikipedia page views.
"""
from __future__ import annotations

import datetime as dt
import json
import math
import os
import re
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

from .photos import UA

WIKI_PV = "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/user"
YT = "https://youtube.googleapis.com/youtube/v3"

# Weights of the final score (each part is 1-5). v1 (27 Oct): demand 0.35, fit 0.20, visuals 0.20 (AI guess),
# originality 0.15, evergreen 0.10. v2 (28 Oct, fixed before its first run, after the 'what makes videos win'
# research): hits are one concrete famous subject with a twist or conflict, so 'hook' is scored; visuals are
# MEASURED (real NASA photos/videos of the main subject), since the two v1 pilot topics had little to show.
WEIGHTS = {"demand": 0.30, "hook": 0.20, "visuals": 0.20, "fit": 0.10, "originality": 0.10, "evergreen": 0.10}
REPEAT_TOPIC_SIM = 0.45      # idea vs past video question/title, content-word cosine
REPEAT_IDEA_SIM = 0.60       # idea vs a higher-ranked idea in the same batch


def _get(url: str, headers: dict | None = None, timeout: int = 30) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def _words(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def on_niche(text: str, niche: dict) -> bool:
    t = " " + " ".join(_words(text)) + " "
    if any(f" {w} " in t for w in niche.get("exclude_words", [])):
        return False
    return any(f" {w} " in t for w in niche["keywords"])


# ---------- step 1: signals ----------

def signals_outliers(niche_key: str, phase0b_dir: Path | None) -> list[dict]:
    """Videos that beat their channel's normal views/day (Phase 0b, latest snapshot)."""
    if not phase0b_dir or not (phase0b_dir / "channels.json").exists():
        return []
    import importlib.util
    spec = importlib.util.spec_from_file_location("niche_test", Path(__file__).resolve().parents[1] / "phase0b" / "niche_test.py")
    nt = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(nt)
    chosen = json.loads((phase0b_dir / "channels.json").read_text(encoding="utf-8"))["chosen"].get(niche_key, [])
    snaps = sorted((phase0b_dir / "snapshots").glob("*.json"))
    if not snaps:
        return []
    last = json.loads(snaps[-1].read_text(encoding="utf-8"))
    out = []
    for c in chosen:
        rows, med = nt.video_rows(last["channels"].get(c["id"], {}))
        for r in rows:
            if r["beats"]:
                out.append({"kind": "outlier_video", "title": r["title"], "channel": c["title"],
                            "subscribers": c["subscribers"], "ratio": round(r["vpd"] / med, 1),
                            "views": r["views"], "days": r["days"], "url": f"https://www.youtube.com/watch?v={r['id']}"})
    out.sort(key=lambda s: -s["ratio"])
    return out[:40]


def signals_trending(niche: dict, log: dict) -> list[dict]:
    """YouTube most-popular charts (1 unit per call), kept only if on-niche."""
    key = os.environ.get("YOUTUBE_API_KEY")
    if not key:
        log["trending"] = "YOUTUBE_API_KEY not set"
        return []
    out, units = [], 0
    for region in niche["youtube_regions"]:
        for cat in niche["youtube_categories"]:
            q = urllib.parse.urlencode({"part": "snippet,statistics", "chart": "mostPopular", "regionCode": region,
                                        "videoCategoryId": cat, "maxResults": 50})
            try:
                d = json.loads(_get(f"{YT}/videos?{q}", {"x-goog-api-key": key}))
                units += 1
            except (urllib.error.URLError, OSError) as e:
                log.setdefault("trending_errors", []).append(f"{region}/{cat}: {e}"[:160])
                continue
            for v in d.get("items", []):
                title = v["snippet"]["title"]
                if on_niche(title + " " + v["snippet"].get("description", "")[:200], niche):
                    out.append({"kind": "trending_video", "title": title, "region": region, "category": cat,
                                "views": int(v.get("statistics", {}).get("viewCount", 0)),
                                "url": f"https://www.youtube.com/watch?v={v['id']}"})
    log["trending_units"] = units
    seen, uniq = set(), []
    for s in sorted(out, key=lambda s: -s["views"]):
        if s["url"] not in seen:
            seen.add(s["url"])
            uniq.append(s)
    return uniq[:30]


def signals_news(niche: dict, log: dict) -> list[dict]:
    out = []
    for url in niche["rss_feeds"]:
        try:
            root = ET.fromstring(_get(url))
        except Exception as e:  # noqa: BLE001 — a dead feed is logged, not fatal
            log.setdefault("rss_errors", []).append(f"{url}: {e!r}"[:200])
            continue
        for item in root.iter("item"):
            title = (item.findtext("title") or "").strip()
            if title and on_niche(title, niche):
                out.append({"kind": "news", "title": title, "url": (item.findtext("link") or "").strip(),
                            "date": (item.findtext("pubDate") or "").strip()})
    return out[:40]


def pageviews(title: str, days: int = 60) -> dict | None:
    """Daily Wikipedia views (people, not bots) for the last `days` days."""
    end = dt.date.today() - dt.timedelta(days=1)
    start = end - dt.timedelta(days=days - 1)
    t = urllib.parse.quote(title.replace(" ", "_"), safe="")
    try:
        d = json.loads(_get(f"{WIKI_PV}/{t}/daily/{start:%Y%m%d}00/{end:%Y%m%d}00"))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise
    views = [i["views"] for i in d.get("items", [])]
    if not views:
        return None
    last30, prev30 = sum(views[-30:]), sum(views[:-30]) or 1
    return {"article": title, "last_30_days": last30, "trend": round(last30 / prev30, 2)}


# ---------- step 1: ideas from signals (1 Gemini request) ----------

IDEA_SCHEMA = {"type": "object", "properties": {"ideas": {"type": "array", "items": {
    "type": "object", "properties": {
        "question": {"type": "string", "description": "the one question the video answers, as a viewer would ask it"},
        "angle": {"type": "string"},
        "signals": {"type": "array", "items": {"type": "string"}, "description": "ids of the signals that show demand"},
        "wikipedia_articles": {"type": "array", "items": {"type": "string"}, "maxItems": 3,
                               "description": "exact English Wikipedia titles holding the facts"}},
    "required": ["question", "angle", "signals", "wikipedia_articles"]}}}, "required": ["ideas"]}


def propose(niche: dict, signals: list[dict], past: list[dict], n: int = 25) -> list[dict]:
    from .llm import QUALITY, llm

    lines = [f"{s['id']} [{s['kind']}] {s['title']}" + (f" ({s['ratio']}x its channel's normal)" if s.get("ratio") else "")
             for s in signals]
    past_txt = "\n".join(f"- {p['title']}" for p in past) or "- (none)"
    prompt = f"""Niche: {niche['label']}. Rules: {'; '.join(niche['rules'])}.
Below are measured demand signals: videos beating their channel's normal views, trending videos, and news.
Propose {n} different evergreen explainer video questions for this niche that real viewers are showing interest in.
- Each idea must cite the ids of the signals that show demand for it (at least one). Do not copy a video title;
  find the underlying question people want answered, and give an original angle.
- Explainers, not news reports: a news item can inspire a question that stays interesting for years.
- What wins (our research of 680 hit videos, 28 Oct): ONE concrete, famous subject people already know of,
  with a twist, a conflict or a surprising answer ("Why TON 618 is the scariest black hole", "We got T. rex
  wrong", "Why did humans start wearing clothes?"). Avoid vague or abstract questions ("why is the universe
  organised into webs") and "what if" ideas with nothing real to show: prefer subjects with real NASA photos
  and footage (missions, telescopes, planets, famous objects).
- Stay inside the niche. No advice, no accusations, no topics about one living person.
- Do NOT repeat these past videos:
{past_txt}
- For each, name 1-3 English Wikipedia articles (exact titles) that would hold the facts.

SIGNALS:
""" + "\n".join(lines)
    return llm(prompt, schema=IDEA_SCHEMA, name="topic_scout", temperature=0.9, models=QUALITY)["ideas"]


# ---------- step 2: repeats, scoring, ranking ----------

_STOP = set("a an the and or of to in on at by for with from is are was were be it its this that how why what "
            "when where who which does do can could would will you your we our there".split())


def _bag(text: str) -> Counter:
    return Counter(w for w in _words(text) if w not in _STOP and len(w) > 2)


def _cos(a: Counter, b: Counter) -> float:
    num = sum(a[k] * b[k] for k in a.keys() & b.keys())
    den = math.sqrt(sum(v * v for v in a.values())) * math.sqrt(sum(v * v for v in b.values()))
    return num / den if den else 0.0


def repeat_reason(idea: dict, past: list[dict]) -> str:
    q = _bag(idea["question"] + " " + idea.get("angle", ""))
    arts = {a.lower() for a in idea["wikipedia_articles"]}
    for p in past:
        sim = _cos(q, _bag(p["title"] + " " + p.get("question", "")))
        if sim >= REPEAT_TOPIC_SIM:
            return f"too close to past video '{p['title']}' (similarity {sim:.2f})"
        main = idea["wikipedia_articles"][0].lower() if idea["wikipedia_articles"] else ""
        if main and main in {a.lower() for a in p.get("articles", [])[:1]}:
            return f"same main subject ({idea['wikipedia_articles'][0]}) as past video '{p['title']}'"
        if arts and len(arts & {a.lower() for a in p.get("articles", [])}) >= 2:
            return f"uses the same sources as past video '{p['title']}'"
    return ""


def demand_score(idea: dict) -> float:
    """1-5 from measured numbers only (fixed rule)."""
    views = max([pv["last_30_days"] for pv in idea["pageviews"]] or [0])
    s = 1.0
    for floor, val in ((30_000, 2), (100_000, 3), (300_000, 4), (1_000_000, 5)):
        if views >= floor:
            s = val
    kinds = {sig["kind"] for sig in idea["evidence"]}
    if kinds & {"outlier_video", "trending_video"}:
        s += 1
    if any(pv["trend"] >= 1.3 for pv in idea["pageviews"]):
        s += 0.5
    return min(s, 5.0)


SCORE_SCHEMA = {"type": "object", "properties": {"scores": {"type": "array", "items": {
    "type": "object", "properties": {
        "n": {"type": "integer"},
        "fit": {"type": "integer", "description": "1-5: squarely inside the niche"},
        "hook": {"type": "integer", "description": "1-5: one concrete subject most people have heard of, with a "
                                                   "twist, conflict or surprising answer clear in one second "
                                                   "(5 = 'We got T. rex wrong'; 1 = abstract or vague)"},
        "originality": {"type": "integer", "description": "1-5: a fresh question/angle, not the obvious video"},
        "evergreen": {"type": "integer", "description": "1-5: still interesting in 2 years"},
        "safe": {"type": "boolean", "description": "false if it needs money/health/legal advice or accuses a "
                                                    "real named person or company"},
        "reason": {"type": "string"}},
    "required": ["n", "fit", "hook", "originality", "evergreen", "safe", "reason"]}}}, "required": ["scores"]}


NASA_SEARCH = "https://images-api.nasa.gov/search"


def visuals_score(idea: dict, log: dict) -> tuple[float, int]:
    """1-5 from a measured count: NASA Image and Video Library results (images + videos) for the main subject."""
    import urllib.parse

    subject = (idea["wikipedia_articles"] or [idea["question"]])[0]
    try:
        q = urllib.parse.urlencode({"q": subject, "media_type": "image,video", "page_size": 1})
        hits = int(json.loads(_get(f"{NASA_SEARCH}?{q}"))["collection"]["metadata"]["total_hits"])
    except Exception as e:  # noqa: BLE001
        log.setdefault("nasa_errors", []).append(f"{subject}: {e!r}"[:160])
        return 2.0, -1
    s = 1.0
    for floor, val in ((10, 2), (50, 3), (200, 4), (1000, 5)):
        if hits >= floor:
            s = val
    return s, hits


def score(niche: dict, ideas: list[dict], log: dict | None = None) -> None:
    from .llm import LIGHT, llm

    lines = [f"{i + 1}. {x['question']} — angle: {x['angle']} — sources: {', '.join(x['wikipedia_articles'])}"
             for i, x in enumerate(ideas)]
    prompt = f"""Score each video idea for a {niche['label']} explainer channel (worldwide English audience,
narration over real photos, simple ink drawings and charts; facts only from Wikipedia).
Use the rubric in the schema strictly; most ideas should NOT get 5s. Answer for every number.

""" + "\n".join(lines)
    res = llm(prompt, schema=SCORE_SCHEMA, name="topic_scorer", temperature=0.2, models=LIGHT)["scores"]
    by_n = {r["n"]: r for r in res}
    for i, x in enumerate(ideas, 1):
        r = by_n.get(i)
        if not r:
            x["scores"] = None
            continue
        parts = {k: max(1, min(5, int(r[k]))) for k in ("fit", "hook", "originality", "evergreen")}
        parts["demand"] = demand_score(x)
        parts["visuals"], x["nasa_hits"] = visuals_score(x, log if log is not None else {})
        x["scores"] = parts
        x["safe"] = r["safe"]
        x["score_reason"] = r["reason"]
        x["score"] = round(sum(WEIGHTS[k] * v for k, v in parts.items()), 2)


def load_past(library_dir: Path) -> list[dict]:
    out = []
    for f in sorted(library_dir.glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        out.append({"title": d.get("title") or d.get("script", {}).get("title", f.stem),
                    "question": d.get("question", ""), "articles": d.get("articles", [])})
    return out


def run(niche: dict, library_dir: Path, phase0b_dir: Path | None, out: Path, want: int = 10) -> dict:
    log: dict = {}
    past = load_past(library_dir)
    signals = signals_outliers(niche["key"], phase0b_dir) + signals_trending(niche, log) + signals_news(niche, log)
    for i, s in enumerate(signals, 1):
        s["id"] = f"S{i}"
    log["signals"] = Counter(s["kind"] for s in signals)
    (out / "signals.json").write_text(json.dumps(signals, indent=1, ensure_ascii=False), encoding="utf-8")
    if not signals:
        raise RuntimeError("no demand signals found for this niche")

    by_id = {s["id"]: s for s in signals}
    ideas = propose(niche, signals, past)
    kept, dropped = [], []
    for x in ideas:
        x["evidence"] = [by_id[s] for s in x.get("signals", []) if s in by_id]
        x["pageviews"] = []
        for a in x["wikipedia_articles"][:3]:
            try:
                pv = pageviews(a)
            except Exception as e:  # noqa: BLE001
                log.setdefault("pageview_errors", []).append(f"{a}: {e!r}"[:160])
                pv = None
            if pv:
                x["pageviews"].append(pv)
        why = ""
        if not x["evidence"] and not any(pv["last_30_days"] >= 30_000 for pv in x["pageviews"]):
            why = "no measured demand (no valid signal and under 30,000 Wikipedia views in 30 days)"
        elif not x["pageviews"]:
            why = "none of its Wikipedia articles exist, so no facts to build on"
        else:
            why = repeat_reason(x, past)
        (dropped if why else kept).append({**x, "dropped": why} if why else x)

    if kept:
        score(niche, kept, log)
    ranked = []
    for x in sorted((k for k in kept if k.get("scores")), key=lambda k: -k["score"]):
        if not x["safe"]:
            dropped.append({**x, "dropped": f"unsafe: {x['score_reason']}"})
            continue
        if x["scores"]["fit"] <= 2:  # blueprint: off-niche ideas dropped
            dropped.append({**x, "dropped": f"off-niche (fit {x['scores']['fit']}/5): {x['score_reason']}"})
            continue
        dup = next((r for r in ranked if _cos(_bag(x["question"]), _bag(r["question"])) >= REPEAT_IDEA_SIM
                    or (x["wikipedia_articles"][:1] == r["wikipedia_articles"][:1])), None)
        if dup:
            dropped.append({**x, "dropped": f"same as a higher-ranked idea: {dup['question']}"})
            continue
        ranked.append(x)
    chosen = ranked[:want]
    result = {"niche": niche["key"], "made": dt.datetime.now(dt.timezone.utc).isoformat(), "weights": WEIGHTS,
              "signals": dict(log.pop("signals")), "log": log, "proposed": len(ideas), "chosen": chosen,
              "reserve": ranked[want:], "dropped": dropped}
    (out / "ideas.json").write_text(json.dumps(result, indent=1, ensure_ascii=False), encoding="utf-8")
    (out / "ideas.md").write_text(markdown(result, niche), encoding="utf-8")
    return result


def markdown(r: dict, niche: dict) -> str:
    md = [f"# Topic ideas: {niche['label']}", "",
          f"Made {r['made'][:10]}. Signals: {r['signals']}. Ideas proposed {r['proposed']}, chosen {len(r['chosen'])}, "
          f"dropped {len(r['dropped'])}.", "",
          "Score (v2, 28 Oct) = 0.30 demand (measured) + 0.20 hook + 0.20 visuals (measured: NASA photos/videos) "
          "+ 0.10 fit + 0.10 originality + 0.10 evergreen (each 1-5).", "",
          "| # | Question | Score | Demand | Hook | NASA photos/videos | Evidence |",
          "| --- | --- | --- | --- | --- | --- | --- |"]
    for i, x in enumerate(r["chosen"], 1):
        pv = max(x["pageviews"], key=lambda p: p["last_30_days"])
        ev = "; ".join(f"{e['kind'].replace('_', ' ')}: {e['title'][:60]}" + (f" ({e['ratio']}x)" if e.get("ratio") else "")
                       for e in x["evidence"][:2])
        md.append(f"| {i} | {x['question']} | {x['score']} | {x['scores']['demand']:g} | {x['scores'].get('hook', '-')} | "
                  f"{x.get('nasa_hits', '-')} | Wikipedia "
                  f"'{pv['article']}' {pv['last_30_days']:,} views/30 days (trend {pv['trend']}x)"
                  + (f"; {ev}" if ev else "") + " |")
    md += ["", "## Dropped", ""]
    md += [f"- {x['question']} — {x['dropped']}" for x in r["dropped"]] or ["- none"]
    return "\n".join(md) + "\n"
