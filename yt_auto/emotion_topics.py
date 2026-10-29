"""Strong-emotion topic finder for Stickman Thoughts Shorts (design: cartoon/TOPIC_FINDER.md, settings:
cartoon/topic_finder.json).

Steps (fixed before the first run, 29 Oct 2026):
  1. signals, measured, no AI: S1 Shorts that beat their own channel's normal (watch list + channels found by the
     searches), S2 Shorts with many views for "what happens if you..." searches (last 60 days).
  2. ideas: 1 strong-model request proposes ~40 situations across all subjects, each naming its signal, feeling,
     answer, Wikipedia articles and library places/things.
  3. gates: safety (plain code here, then the AI flag in step 5), form, repeat (library/ and competitor titles).
  4. sources, measured: the named Wikipedia articles are fetched; passages that talk about the answer are counted
     (T3), and the main article's page views are read (S3).
  5. score: feeling rubric by two different model lists (never shown view counts), formula from the settings.
  6. queue: the top 14, at most 3 per subject area, each with an evidence card; plus the pictures we still need.
"""
from __future__ import annotations

import datetime as dt
import json
import math
import os
import re
import statistics
import urllib.error
import urllib.parse
from pathlib import Path

from . import research, topics
from .topics import _bag, _cos, _get

ROOT = Path(__file__).resolve().parents[1]
CFG = json.loads((ROOT / "cartoon" / "topic_finder.json").read_text(encoding="utf-8"))
YT = topics.YT
USED = {"units": 0, "calls": 0}


# ---------- safety (T5), plain code; the AI flag comes on top in score() ----------

# Each rule: (kind, pattern). Patterns match whole words of the lower-cased question/situation/answer.
SAFETY_RULES = [
    ("dangerous act", r"\bchallenge\b|\btry (?:it|this)\b|\bat home\b|\bin your (?:bathtub|kitchen|room)\b|"
                      r"\bhow to (?:make|build|cook)\b|\bmake your own\b|\bfireworks? at home\b|\btide pods?\b|"
                      r"\bmix(?:ing)? bleach\b|\bbomb out of\b|\bhomemade (?:bomb|explosive|weapon)s?\b"),
    ("self-harm", r"\bsuicide\b|\bown life\b|\bkill (?:yourself|myself|himself|herself)\b|\bself[- ]harm\b|"
                  r"\bcut (?:yourself|myself)\b|\boverdos\w*\b|\bto feel better\b"),
    ("advice", r"\bshould you (?:invest|buy|take|stop|eat)\b|\binvest(?:ing|ment|ments)?\b|\bcrypto\w*\b|\bstocks?\b|\bbitcoin\b|"
               r"\bcures?\b|\bdiet\b|\blose weight\b|\bmedicine\b|\bmedication\b|\bpills?\b|\bdoctors? (?:hate|won't)\b|"
               r"\bhow to sue\b|\bsue\b|\blegal advice\b|\btax(?:es)?\b"),
    ("politics or religion", r"\belections?\b|\bpresident (?:again|now)\b|\bprime minister\b|\bmodi\b|\btrump\b|"
                             r"\bbiden\b|\bputin\b|\bpolitical party\b|\breligions?\b|\btrue god\b|\bhindu\w*\b|\bmuslims?\b|"
                             r"\bislam\w*\b|\bchristian\w*\b|\bcaste\b|\bmosque\b|\btemple dispute\b"),
    ("accusation", r"\blied\b|\bscam\w*\b|\bfraud\w*\b|\bcover[- ]?up\b|\bcorrupt\w*\b|\bhid from you\b|"
                   r"\bexposed (?:the|how)\b|\bguilty\b|\bcriminal company\b"),
    ("gore", r"\bbehead\w*\b|\bdecapitat\w*\b|\btortur\w*\b|\bdismember\w*\b|\bmutilat\w*\b|\bgore\b|\bgory\b"),
    ("recent tragedy", r"\b9/11\b|\btwin towers\b|\btitan submersible\b|\bcovid\w*\b|\bpandemic\b|\bgaza\b|"
                       r"\bukraine war\b|\bschool shooting\b|\bterror\w*\b"),
]


def safety_block(text: str, today: dt.date | None = None) -> str:
    """'' if safe, else the reason. A year within the last `recent_years` counts as a recent tragedy when the
    text also names a disaster word (an old year is fine: 1906 earthquake, 1912 Titanic)."""
    t = " " + text.lower() + " "
    for kind, pat in SAFETY_RULES:
        m = re.search(pat, t)
        if m:
            return f"{kind} ('{m.group(0).strip()}')"
    year_now = (today or dt.date.today()).year
    for y in re.findall(r"\b(1[89]\d\d|20\d\d)\b", t):
        if int(y) > year_now - CFG["recent_years"] and re.search(
                r"crash\w*|collaps\w*|implod\w*|disaster|killed|died|attack\w*|shoot\w*|sank|sinking|fire|flood\w*|"
                r"quake|earthquake|tsunami|stampede|bomb\w*|war\b|explo\w*", t):
            return f"recent tragedy (year {y}, less than {CFG['recent_years']} years ago)"
    return ""


# ---------- form (T1) ----------

FORM_START = re.compile(r"^(what (?:if|happens|would|was it like|does it feel|it feels)|why|how (?:does|do|would|did|"
                        r"long|far|deep|hot|cold|fast|big|it feels)|could you|can you)\b", re.I)


def form_problem(idea: dict) -> str:
    q = idea.get("question", "").strip()
    if not FORM_START.match(q):
        return "the question is not a 'what if / what happens / why / how' question"
    if len(q) > 90:
        return f"the question is too long for a Short title ({len(q)} characters)"
    if len(topics._words(idea.get("situation", ""))) < 4:
        return "no concrete situation the viewer can picture"
    if not idea.get("answer", "").strip():
        return "no known answer"
    return ""


# ---------- step 1: signals (YouTube Data API, measured) ----------

def yt(endpoint: str, **params) -> dict:
    cost = 100 if endpoint == "search" else 1
    if USED["units"] + cost > CFG["youtube_stop_at_units"]:
        raise RuntimeError(f"stopping at {USED['units']} YouTube units (limit {CFG['youtube_stop_at_units']})")
    key = os.environ.get("YOUTUBE_API_KEY")
    if not key:
        raise RuntimeError("YOUTUBE_API_KEY is not set")
    d = json.loads(_get(f"{YT}/{endpoint}?{urllib.parse.urlencode(params)}", {"x-goog-api-key": key}, timeout=60))
    USED["units"] += cost
    USED["calls"] += 1
    return d


def seconds(iso: str) -> int:
    m = re.fullmatch(r"P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso or "")
    if not m:
        return 0
    d, h, mi, s = (int(x or 0) for x in m.groups())
    return ((d * 24 + h) * 60 + mi) * 60 + s


def video_details(ids: list[str]) -> list[dict]:
    out = []
    for i in range(0, len(ids), 50):
        d = yt("videos", part="snippet,contentDetails,statistics", id=",".join(ids[i:i + 50]), maxResults=50)
        for v in d.get("items", []):
            st = v.get("statistics", {})
            out.append({"id": v["id"], "title": v["snippet"]["title"], "channel_id": v["snippet"]["channelId"],
                        "channel": v["snippet"]["channelTitle"], "published": v["snippet"]["publishedAt"][:10],
                        "seconds": seconds(v["contentDetails"].get("duration", "")),
                        "views": int(st.get("viewCount", 0)), "likes": int(st.get("likeCount", 0) or 0)})
    return out


def channel_shorts(channel: dict, log: dict) -> dict | None:
    """The channel's recent Shorts and which ones beat its normal (median) views."""
    try:
        if channel.get("id"):
            d = yt("channels", part="snippet,contentDetails,statistics", id=channel["id"])
        else:
            d = yt("channels", part="snippet,contentDetails,statistics", forHandle=channel["handle"])
        if not d.get("items"):
            log.setdefault("channel_errors", []).append(f"{channel.get('handle') or channel.get('id')}: not found")
            return None
        c = d["items"][0]
        uploads = c["contentDetails"]["relatedPlaylists"]["uploads"]
        ids, token = [], None
        while len(ids) < CFG["videos_per_channel"]:
            p = {"part": "contentDetails", "playlistId": uploads, "maxResults": 50}
            if token:
                p["pageToken"] = token
            page = yt("playlistItems", **p)
            ids += [i["contentDetails"]["videoId"] for i in page.get("items", [])]
            token = page.get("nextPageToken")
            if not token:
                break
        vids = video_details(ids[:CFG["videos_per_channel"]])
    except (urllib.error.URLError, OSError, KeyError, RuntimeError) as e:
        log.setdefault("channel_errors", []).append(f"{channel.get('handle') or channel.get('id')}: {e!r}"[:200])
        return None
    today = dt.date.today()
    shorts = [v for v in vids if 0 < v["seconds"] <= CFG["shorts_max_seconds"]
              and (today - dt.date.fromisoformat(v["published"])).days >= CFG["min_age_days"]]
    if len(shorts) < 5:
        return {"name": c["snippet"]["title"], "id": c["id"], "shorts": len(shorts), "median": 0, "hits": [], "normal": []}
    med = statistics.median(v["views"] for v in shorts) or 1
    for v in shorts:
        v["ratio"] = round(v["views"] / med, 1)
    hits = [v for v in shorts if v["ratio"] >= CFG["hit_ratio"] and v["views"] >= CFG["hit_min_views"]]
    normal = [v for v in shorts if 0.5 <= v["ratio"] <= 1.5]
    return {"name": c["snippet"]["title"], "id": c["id"], "handle": channel.get("handle", ""),
            "subscribers": int(c.get("statistics", {}).get("subscriberCount", 0) or 0), "shorts": len(shorts),
            "median": int(med), "hits": sorted(hits, key=lambda v: -v["ratio"]), "normal": normal}


def search_shorts(query: str, log: dict) -> list[dict]:
    after = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=CFG["search_days"])).strftime("%Y-%m-%dT%H:%M:%SZ")
    try:
        d = yt("search", part="snippet", q=query, type="video", videoDuration="short", order="viewCount",
               publishedAfter=after, relevanceLanguage="en", maxResults=50)
        vids = video_details([i["id"]["videoId"] for i in d.get("items", []) if i.get("id", {}).get("videoId")])
    except (urllib.error.URLError, OSError, RuntimeError) as e:
        log.setdefault("search_errors", []).append(f"{query}: {e!r}"[:200])
        return []
    return [{**v, "query": query} for v in vids
            if 0 < v["seconds"] <= CFG["shorts_max_seconds"] and v["views"] >= CFG["search_min_views"]]


def collect_signals(log: dict) -> dict:
    found = []
    for q in CFG["searches"]:
        found += search_shorts(q, log)
    # channels that show up most in the searches join the watch list for this run (discovery)
    count: dict[str, int] = {}
    for v in found:
        count[v["channel_id"]] = count.get(v["channel_id"], 0) + 1
    channels = [dict(c) for c in CFG["watch_channels"]]
    for cid, _ in sorted(count.items(), key=lambda kv: -kv[1])[:CFG["discover_channels_from_searches"]]:
        channels.append({"id": cid, "found_by": "searches"})
    seen, chans = set(), []
    for c in channels:
        r = channel_shorts(c, log)
        if r and r["id"] not in seen:
            seen.add(r["id"])
            r["found_by"] = c.get("found_by", "watch list")
            chans.append(r)
    signals = []
    for c in chans:
        for v in c["hits"][:12]:
            signals.append({"kind": "beats_channel", "title": v["title"], "channel": c["name"], "ratio": v["ratio"],
                            "views": v["views"], "url": f"https://www.youtube.com/shorts/{v['id']}"})
    hit_urls = {s["url"] for s in signals}
    for v in sorted(found, key=lambda v: -v["views"])[:40]:
        url = f"https://www.youtube.com/shorts/{v['id']}"
        if url not in hit_urls:
            signals.append({"kind": "search", "title": v["title"], "channel": v["channel"], "views": v["views"],
                            "query": v["query"], "url": url})
    for i, s in enumerate(signals, 1):
        s["id"] = f"S{i}"
    log["youtube_units"] = USED["units"]
    return {"channels": [{k: c[k] for k in ("name", "id", "found_by", "shorts", "median")} | {"hits": len(c["hits"])}
                         for c in chans],
            "signals": signals,
            # hits vs normal Shorts of the same channels: the set for test A (feeling scorer, AUC >= 0.65)
            "test_a": [{"channel": c["name"], "title": v["title"], "hit": v in c["hits"], "ratio": v["ratio"]}
                       for c in chans for v in c["hits"] + c["normal"]]}


# ---------- step 2: ideas (1 strong-model request) ----------

def library_names() -> tuple[set[str], set[str]]:
    lib = json.loads((ROOT / "cartoon" / "art" / "library.json").read_text(encoding="utf-8"))
    return set(lib["places"]), set(lib["things"])


IDEA_SCHEMA = {"type": "object", "properties": {"ideas": {"type": "array", "items": {
    "type": "object", "properties": {
        "question": {"type": "string", "description": "the Short's title question, as a curious viewer asks it"},
        "situation": {"type": "string", "description": "the one concrete moment the stickman lives through"},
        "feeling": {"type": "string", "enum": ["fear", "awe", "disgust", "wonder", "sadness", "surprise"]},
        "answer": {"type": "string", "description": "the true, documented answer in one sentence"},
        "area": {"type": "string"},
        "wikipedia_articles": {"type": "array", "items": {"type": "string"}, "minItems": 2, "maxItems": 4},
        "places": {"type": "array", "items": {"type": "string"}},
        "things": {"type": "array", "items": {"type": "string"}},
        "signals": {"type": "array", "items": {"type": "string"}}},
    "required": ["question", "situation", "feeling", "answer", "area", "wikipedia_articles", "places", "things",
                 "signals"]}}}, "required": ["ideas"]}


def propose(signals: list[dict], past: list[dict], n: int) -> list[dict]:
    from .cartoon import SAFETY
    from .llm import QUALITY, llm

    places, things = library_names()
    lines = [f"{s['id']} [{s['kind']}] {s['title']}" + (f" ({s['ratio']}x its channel's normal)" if s.get("ratio")
                                                         else f" ({s['views']:,} views)") for s in signals]
    past_txt = "\n".join(f"- {p['title']}" for p in past) or "- (none)"
    prompt = f"""Channel "Stickman Thoughts" (YouTube Shorts, 40-60 s, worldwide English): "The stickman wonders
'what if...?' He goes there. He feels it. He finds out the truth." Every fact comes from Wikipedia.

Below are MEASURED signals: Shorts that beat their own channel's normal views, and Shorts with many views for
"what happens if you..." searches. Propose {n} different Short ideas that real viewers are showing interest in.
- Each idea is ONE vivid situation a viewer can imagine being in, with a strong feeling that the true facts
  really carry (no fake drama), and an answer that is known and written down (a real event or a documented effect).
- What wins: one famous subject + a concrete situation + a twist ("What if you fell into the Mariana Trench?").
- Cite the ids of the signals that show interest (at least one). Never copy a signal's title: find the subject and
  the kind of situation people want, then give our own question.
- Spread the ideas over these areas (at most 5 per area): {', '.join(CFG['areas'])}.
- wikipedia_articles: 2-4 exact English Wikipedia titles that state the answer; for "what happens to you" ideas
  include the article about the effect itself (e.g. "Barotrauma", "Hypothermia").
- places: 1-2 names from OUR picture library where the story happens: {', '.join(sorted(places))}; or "space" for
  outer space. If none fits, write the place you would need (it goes on a list of pictures to make).
- things: 0-3 objects from the library ({', '.join(sorted(things))}) or the object you would need.
{SAFETY}
- No dangerous acts a viewer could copy, no self-harm, no politics or religion, no tragedy with living victims or
  families (less than {CFG['recent_years']} years ago), no gore beyond a cartoon.
- Do NOT repeat these past Shorts:
{past_txt}

SIGNALS:
""" + "\n".join(lines)
    return llm(prompt, schema=IDEA_SCHEMA, name="emotion_ideas", temperature=0.9, models=QUALITY)["ideas"]


# ---------- step 3: gates ----------

def gate(ideas: list[dict], signals: list[dict], past: list[dict]) -> tuple[list[dict], list[dict]]:
    sig_ids = {s["id"] for s in signals}
    kept, dropped, seen = [], [], []
    for x in ideas:
        x["signals"] = [s for s in x.get("signals", []) if s in sig_ids]
        x.setdefault("angle", x.get("situation", ""))
        text = x.get("question", "") + " " + x.get("situation", "")  # not the answer: "there was no cure" is history
        why = (safety_block(text) and f"safety: {safety_block(text)}") or form_problem(x)
        if not why and not x["signals"]:
            why = "cites no measured signal"
        if not why:
            why = topics.repeat_reason(x, past)
        if not why:
            q = _bag(x["question"])
            for s in signals:
                if _cos(q, _bag(s["title"])) >= CFG["competitor_copy_sim"]:
                    why = f"too close to the competitor title '{s['title']}'"
                    break
        if not why:
            for y in seen:
                if _cos(_bag(x["question"] + " " + x["situation"]), _bag(y["question"] + " " + y["situation"])) >= 0.6:
                    why = f"same idea as '{y['question']}'"
                    break
        if why:
            dropped.append({**x, "dropped": why})
        else:
            kept.append(x)
            seen.append(x)
    return kept, dropped


def drawable(idea: dict) -> tuple[float, list[str]]:
    """1-5 and the pictures we would still need (places and things not in the library)."""
    places, things = library_names()
    need_p = [p for p in idea.get("places", []) if p.lower() != "space" and p not in places]
    have_p = [p for p in idea.get("places", []) if p.lower() == "space" or p in places]
    need_t = [t for t in idea.get("things", []) if t not in things]
    need = [f"place: {p}" for p in need_p] + [f"thing: {t}" for t in need_t]
    if not have_p:
        return 2.0, need
    return (5.0 if not need_t else 4.0 if len(need_t) == 1 else 3.0), need


# ---------- step 4: sources and page views (measured) ----------

def source_check(idea: dict, cache: dict, log: dict) -> None:
    words = {w for w in _bag(idea["answer"] + " " + idea["situation"]) if len(w) > 3}
    found, hits, total = [], 0, 0
    for t in idea["wikipedia_articles"][:4]:
        if t not in cache:
            try:
                art = research.fetch_article(t)
                cache[t] = None if not art else {"title": art["title"], "url": art["url"],
                                                 "passages": [p["text"] for p in research.passages(art["text"])]}
            except Exception as e:  # noqa: BLE001  one failed article is logged, not fatal
                log.setdefault("wiki_errors", []).append(f"{t}: {e!r}"[:160])
                cache[t] = None
        art = cache[t]
        if not art:
            continue
        n = sum(1 for p in art["passages"] if len(words & set(topics._words(p))) >= 2)
        found.append({"title": art["title"], "url": art["url"], "passages": len(art["passages"]), "about_answer": n})
        hits += n
        total += len(art["passages"])
    idea["sources"] = found
    idea["source_hits"] = hits
    pv = None
    for a in found:
        try:
            pv = topics.pageviews(a["title"], days=60)
        except Exception as e:  # noqa: BLE001
            log.setdefault("pageview_errors", []).append(f"{a['title']}: {e!r}"[:160])
        if pv:
            break
    idea["pageviews"] = pv


# ---------- step 5: score (formula fixed in cartoon/topic_finder.json) ----------

FEEL_SCHEMA = {"type": "object", "properties": {"scores": {"type": "array", "items": {
    "type": "object", "properties": {
        "n": {"type": "integer"},
        "stakes": {"type": "integer", "description": "1-5: how much it matters to YOU, the viewer, in the story"},
        "vivid": {"type": "integer", "description": "1-5: can you picture the moment in one second?"},
        "twist": {"type": "integer", "description": "1-5: is the true answer surprising?"},
        "true_feeling": {"type": "integer", "description": "1-5: do the real facts carry the feeling, without drama "
                                                           "added by the writer?"},
        "safe": {"type": "boolean", "description": "false if dangerous to copy, self-harm, advice, politics, religion, "
                                                   "a living person, an accusation, a recent tragedy or gore"},
        "reason": {"type": "string"}},
    "required": ["n", "stakes", "vivid", "twist", "true_feeling", "safe", "reason"]}}}, "required": ["scores"]}


def feeling_scores(items: list[dict], models: list[str], name: str) -> dict[int, dict]:
    """Rubric scores by one model list. Gets only the idea text, never view counts (no bias from demand)."""
    from .llm import llm

    lines = [f"{i}. {x['question']} - situation: {x['situation']} - true answer: {x['answer']}"
             for i, x in enumerate(items, 1)]
    prompt = """Score each YouTube Short idea for a cartoon channel where a stickman lives through the situation and
finds out the true answer. Use the rubric in the schema strictly; most ideas should NOT get 5s. Answer for every
number.

""" + "\n".join(lines)
    res = llm(prompt, schema=FEEL_SCHEMA, name=name, temperature=0.2, models=models)["scores"]
    out = {}
    for r in res:
        try:
            parts = [max(1, min(5, int(r[k]))) for k in ("stakes", "vivid", "twist", "true_feeling")]
        except (KeyError, TypeError, ValueError):
            continue
        out[int(r["n"])] = {"feeling": round(sum(parts) / 4, 2), "safe": bool(r.get("safe", True)),
                            "reason": r.get("reason", "")}
    return out


def demand_score(idea: dict, by_id: dict) -> float:
    """1-5 from measured numbers only."""
    sig = [by_id[s] for s in idea["signals"] if s in by_id]
    ratio = max([s.get("ratio", 0) for s in sig if s["kind"] == "beats_channel"] or [0])
    views = max([s.get("views", 0) for s in sig if s["kind"] == "search"] or [0])
    yt_part = 1.0
    for ok, val in ((ratio >= 3 or views >= 200_000, 3), (ratio >= 5 or views >= 1_000_000, 4),
                    (ratio >= 10 or views >= 5_000_000, 5)):
        if ok:
            yt_part = val
    wv = (idea.get("pageviews") or {}).get("last_30_days", 0)
    wiki = 1.0
    for floor, val in ((10_000, 2), (30_000, 3), (100_000, 4), (300_000, 5)):
        if wv >= floor:
            wiki = val
    return round(0.6 * yt_part + 0.4 * wiki, 2)


def sources_score(hits: int) -> float:
    s = 1.0
    for floor, val in ((3, 2), (5, 3), (8, 4), (12, 5)):
        if hits >= floor:
            s = val
    return s


def variety_score(idea: dict, past: list[dict]) -> float:
    recent = past[-3:]
    sim = max([_cos(_bag(idea["question"] + " " + idea["situation"]), _bag(p["title"] + " " + p.get("question", "")))
               for p in recent] or [0])
    return 5.0 if sim < 0.15 else 3.0 if sim < 0.30 else 1.0


def run(out: Path, library_dir: Path, signals_file: Path | None = None, second_models: list[str] | None = None) -> dict:
    from .llm import LIGHT, QUALITY

    log: dict = {"date": dt.date.today().isoformat()}
    past = [p for p in topics.load_past(library_dir)]
    sig = json.loads(signals_file.read_text()) if signals_file else collect_signals(log)
    (out / "signals.json").write_text(json.dumps(sig, indent=1, ensure_ascii=False))
    print(f"[topics] {len(sig['signals'])} signals from {len(sig['channels'])} channels, {USED['units']} YouTube units",
          flush=True)
    if not sig["signals"]:
        raise RuntimeError(f"no measured signals; see the log: {log}")
    ideas = propose(sig["signals"], past, CFG["ideas"])
    kept, dropped = gate(ideas, sig["signals"], past)
    print(f"[topics] {len(ideas)} ideas, {len(kept)} past the gates", flush=True)
    cache: dict = {}
    for x in kept:
        source_check(x, cache, log)
        if x["source_hits"] < CFG["min_source_hits"] or len(x["sources"]) < 2:
            x["dropped"] = f"too few sources about the answer ({x['source_hits']} passages, {len(x['sources'])} articles)"
    dropped += [x for x in kept if x.get("dropped")]
    kept = [x for x in kept if not x.get("dropped")]
    # two different model lists score the feeling; a gap of 2+ points is flagged for the owner
    a = feeling_scores(kept, QUALITY, "emotion_feeling_a")
    b = feeling_scores(kept, second_models or LIGHT, "emotion_feeling_b")
    by_id = {s["id"]: s for s in sig["signals"]}
    W = CFG["weights"]
    for i, x in enumerate(kept, 1):
        ra, rb = a.get(i), b.get(i)
        got = [r for r in (ra, rb) if r]
        if not got:
            x["dropped"] = "no feeling score"
            continue
        if not all(r["safe"] for r in got):
            x["dropped"] = "safety (AI): " + "; ".join(r["reason"] for r in got if not r["safe"])[:300]
            continue
        x["feeling_models"] = [r["feeling"] for r in got]
        x["flag"] = "the two feeling scores differ by 2+ points" if len(got) == 2 and abs(
            got[0]["feeling"] - got[1]["feeling"]) >= 2 else ""
        x["feeling_reason"] = got[0]["reason"]
        d, x["pictures_needed"] = drawable(x)
        x["parts"] = {"demand": demand_score(x, by_id), "feeling": round(sum(x["feeling_models"]) / len(got), 2),
                      "sources": sources_score(x["source_hits"]), "drawable": d, "variety": variety_score(x, past)}
        x["score"] = round(sum(W[k] * v for k, v in x["parts"].items()), 2)
    dropped += [x for x in kept if x.get("dropped")]
    kept = sorted([x for x in kept if not x.get("dropped")], key=lambda x: -x["score"])
    queue, per_area = [], {}
    for x in kept:
        area = x["area"].lower().strip()
        if per_area.get(area, 0) >= CFG["max_per_area"]:
            x["reserve"] = f"area '{area}' already has {CFG['max_per_area']} in the queue"
            continue
        per_area[area] = per_area.get(area, 0) + 1
        queue.append(x)
        if len(queue) == CFG["queue_size"]:
            break
    for i, x in enumerate(queue, 1):
        x["rank"] = i
        x["evidence"] = [by_id[s] for s in x["signals"] if s in by_id]
    reserve = [x for x in kept if x not in queue]
    result = {"made": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "settings": CFG,
              "queue": queue, "reserve": reserve, "dropped": dropped, "log": log | {"youtube_units": USED["units"]},
              "channels": sig["channels"]}
    (out / "queue.json").write_text(json.dumps(result, indent=1, ensure_ascii=False))
    (out / "report.md").write_text(markdown(result))
    (out / "pictures_needed.md").write_text(pictures_md(queue + reserve))
    return result


def _num(n: int) -> str:
    return f"{n / 1e6:.1f}M" if n >= 1e6 else f"{n / 1e3:.0f}k" if n >= 1e3 else str(n)


def markdown(r: dict) -> str:
    L = [f"# Stickman topic queue ({r['made'][:10]})", "",
         f"{len(r['queue'])} in the queue, {len(r['reserve'])} in reserve, {len(r['dropped'])} dropped. "
         f"YouTube units used: {r['log'].get('youtube_units', 0)}. Score = demand 0.35 + feeling 0.25 + sources 0.20 "
         "+ drawable 0.10 + variety 0.10 (each 1-5).", "",
         "| # | Question | Feeling | Score | Demand | Feeling | Sources | Draw | Variety |",
         "|---|---|---|---|---|---|---|---|---|"]
    for x in r["queue"]:
        p = x["parts"]
        L.append(f"| {x['rank']} | {x['question']} | {x['feeling']} | **{x['score']}** | {p['demand']} | {p['feeling']} | "
                 f"{p['sources']} | {p['drawable']} | {p['variety']} |")
    L += ["", "## Evidence cards", ""]
    for x in r["queue"]:
        L += [f"### {x['rank']}. {x['question']}", "",
              f"- Situation: {x['situation']}", f"- True answer: {x['answer']}", f"- Area: {x['area']}",
              f"- Places / things: {', '.join(x['places'])} / {', '.join(x['things']) or '-'}"]
        for s in x["evidence"]:
            how = f"{s['ratio']}x its channel's normal" if s.get("ratio") else f"{_num(s['views'])} views, search '{s['query']}'"
            L.append(f"- Signal {s['id']}: [{s['title']}]({s['url']}) ({s['channel']}, {how})")
        pv = x.get("pageviews") or {}
        L.append("- Wikipedia: " + ", ".join(f"[{a['title']}]({a['url']}) {a['about_answer']}/{a['passages']} passages"
                                              for a in x["sources"])
                 + (f"; {_num(pv['last_30_days'])} readers in 30 days" if pv else ""))
        L.append(f"- Feeling (two models): {x['feeling_models']} - {x['feeling_reason']}")
        if x.get("flag"):
            L.append(f"- FLAG: {x['flag']}")
        if x["pictures_needed"]:
            L.append(f"- Pictures still needed: {', '.join(x['pictures_needed'])}")
        L.append("")
    L += ["## Reserve", ""] + [f"- {x['question']} ({x['score']}){' - ' + x['reserve'] if x.get('reserve') else ''}"
                               for x in r["reserve"]]
    L += ["", "## Dropped", ""] + [f"- {x.get('question', '?')}: {x['dropped']}" for x in r["dropped"]]
    L += ["", "## Channels measured", "", "| Channel | Found by | Shorts | Median views | Hits |", "|---|---|---|---|---|"]
    L += [f"| {c['name']} | {c['found_by']} | {c['shorts']} | {_num(c['median'])} | {c['hits']} |" for c in r["channels"]]
    if r["log"].get("channel_errors") or r["log"].get("search_errors"):
        L += ["", "Errors: " + "; ".join(r["log"].get("channel_errors", []) + r["log"].get("search_errors", []))]
    return "\n".join(L) + "\n"


def pictures_md(items: list[dict]) -> str:
    need: dict[str, list[str]] = {}
    for x in items:
        for p in x.get("pictures_needed", []):
            need.setdefault(p, []).append(x["question"])
    L = ["# Pictures still needed for the queued topics", "",
         "Make these with ChatGPT (style in cartoon/art/BATCHES.md), most-needed first.", "",
         "| Picture | Needed by |", "|---|---|"]
    L += [f"| {p} | {len(qs)}: {'; '.join(qs[:3])} |" for p, qs in sorted(need.items(), key=lambda kv: -len(kv[1]))]
    return "\n".join(L) + "\n"


def eval_safety(test_file: Path) -> dict:
    """Test B (plain-code part): blocked unsafe and wrongly blocked safe topics."""
    t = json.loads(test_file.read_text())
    missed = [x["q"] for x in t["unsafe"] if not safety_block(x["q"])]
    false = [(x["q"], safety_block(x["q"])) for x in t["safe"] if safety_block(x["q"])]
    caught = len(t["unsafe"]) - len(missed)
    return {"caught": caught, "of": len(t["unsafe"]), "false_blocks": len(false), "missed": missed,
            "false": false, "passed": caught >= 24 and len(false) <= 2}


def auc(pairs: list[tuple[float, bool]]) -> float:
    """Share of (hit, normal) pairs where the hit scored higher (ties count half)."""
    hits = [s for s, h in pairs if h]
    norm = [s for s, h in pairs if not h]
    if not hits or not norm:
        return math.nan
    win = sum(1.0 if a > b else 0.5 if a == b else 0.0 for a in hits for b in norm)
    return round(win / (len(hits) * len(norm)), 3)
