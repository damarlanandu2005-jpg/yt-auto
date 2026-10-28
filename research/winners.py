"""Research: what is different about a young channel's hit videos vs its normal videos?

Method and thresholds are fixed in research/RULES.md (written before any data was pulled).

    python research/winners.py OUT            # pull data, AI labels, report
    python research/winners.py OUT --no-ai    # code-only features (no Gemini)
"""
from __future__ import annotations

import argparse
import datetime as dt
import io
import json
import random
import re
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "study"))
from study_video import get, yt  # noqa: E402
from yt_auto import llm  # noqa: E402

NICHES = {
    "space": ["space documentary", "universe explained"],
    "science": ["science explained", "physics explained"],
    "history": ["history documentary", "ancient history explained"],
    "geography": ["geography explained", "why this country"],
    "psychology": ["psychology explained", "human behavior explained"],
    "mysteries": ["unsolved mystery documentary", "true story documentary"],
    "nature": ["animal documentary", "nature explained"],
    "engineering": ["how it works engineering", "megaprojects explained"],
    "illustrated": ["animated explainer", "illustrated story explained"],
}
YOUNG_DAYS, SEARCH_DAYS, MIN_VIDEOS = 730, 120, 8
HIT_X, HIT_MIN, NORMAL = 5.0, 10_000, (0.5, 2.0)
STRUGGLING = (20, 100)
WIN_POINTS, MIN_HITS = 10, 30
AI_MODELS = ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite"]  # never the strong models (RULES.md)
TEXT_MODELS = ["gemma-4-31b-it"] + AI_MODELS
NOW = dt.datetime.now(dt.timezone.utc)


def secs(d: str) -> int:
    m = re.fullmatch(r"P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", d or "")
    if not m:
        return 0
    dd, h, mi, s = (int(x or 0) for x in m.groups())
    return dd * 86400 + h * 3600 + mi * 60 + s


def when(s: str) -> dt.datetime:
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))


def chunks(xs, n):
    for i in range(0, len(xs), n):
        yield xs[i:i + n]


def pull(out: Path) -> dict:
    units = 0
    after = (NOW - dt.timedelta(days=SEARCH_DAYS)).strftime("%Y-%m-%dT%H:%M:%SZ")
    found: dict[str, set] = {}
    for niche, queries in NICHES.items():
        for q in queries:
            r = yt("search", part="snippet", q=q, type="video", order="viewCount", publishedAfter=after,
                   relevanceLanguage="en", videoDuration="medium", maxResults=50)
            units += 100
            for it in r.get("items", []):
                found.setdefault(it["snippet"]["channelId"], set()).add(niche)
    chans = {}
    for ids in chunks(sorted(found), 50):
        r = yt("channels", part="snippet,statistics,contentDetails", id=",".join(ids))
        units += 1
        for c in r.get("items", []):
            age = (NOW - when(c["snippet"]["publishedAt"])).days
            chans[c["id"]] = {"id": c["id"], "title": c["snippet"]["title"], "age_days": age,
                              "subs": int(c["statistics"].get("subscriberCount", 0)),
                              "niches": sorted(found[c["id"]]),
                              "uploads": c["contentDetails"]["relatedPlaylists"]["uploads"]}
    young = [c for c in chans.values() if c["age_days"] <= YOUNG_DAYS]
    videos = []
    for c in young:
        try:
            items = yt("playlistItems", part="contentDetails", playlistId=c["uploads"], maxResults=50)["items"]
            units += 1
            vids = yt("videos", part="snippet,contentDetails,statistics",
                      id=",".join(x["contentDetails"]["videoId"] for x in items))["items"] if items else []
            units += 1
        except Exception as e:  # noqa: BLE001
            c["error"] = repr(e)[:200]
            continue
        rows = []
        for v in vids:
            d, pub = secs(v["contentDetails"]["duration"]), when(v["snippet"]["publishedAt"])
            if d <= 180 or (NOW - pub).days < 7:
                continue
            rows.append({"id": v["id"], "channel": c["id"], "title": v["snippet"]["title"], "seconds": d,
                         "published": v["snippet"]["publishedAt"], "views": int(v["statistics"].get("viewCount", 0)),
                         "likes": int(v["statistics"].get("likeCount", 0)),
                         "comments": int(v["statistics"].get("commentCount", 0))})
        c["long_videos"] = len(rows)
        if rows:
            c["median_views"] = statistics.median(r["views"] for r in rows)
            dates = sorted(when(r["published"]) for r in rows)
            c["days_between_uploads"] = round((dates[-1] - dates[0]).days / max(len(dates) - 1, 1), 1)
        videos += rows
    data = {"pulled": NOW.isoformat(), "youtube_units": units, "channels_found": len(chans),
            "young_channels": young, "videos": videos}
    (out / "data.json").write_text(json.dumps(data, indent=1, ensure_ascii=False))
    return data


def label(data: dict) -> tuple[list[dict], list[dict]]:
    """Hits and normal videos of the same channels (RULES.md)."""
    rng = random.Random(42)
    by_ch: dict[str, list[dict]] = {}
    for v in data["videos"]:
        by_ch.setdefault(v["channel"], []).append(v)
    hits, normal = [], []
    for ch, vs in by_ch.items():
        if len(vs) < MIN_VIDEOS:
            continue
        med = statistics.median(v["views"] for v in vs) or 1
        h = [v for v in vs if v["views"] >= HIT_X * med and v["views"] >= HIT_MIN]
        n = [v for v in vs if NORMAL[0] * med <= v["views"] <= NORMAL[1] * med]
        if not h:
            continue
        rng.shuffle(n)
        for v in h:
            hits.append({**v, "x_median": round(v["views"] / med, 1)})
        normal += [{**v, "x_median": round(v["views"] / med, 1)} for v in n[:len(h)]]
    return hits, normal


EMO = ["curiosity", "awe", "fear", "surprise", "personal_stakes", "nostalgia", "humour", "anger", "none"]
TITLE_SCHEMA = {"type": "object", "properties": {"titles": {"type": "array", "items": {"type": "object", "properties": {
    "n": {"type": "integer"}, "emotion": {"type": "string", "enum": EMO},
    "promise": {"type": "string", "enum": ["answer", "list", "story", "warning", "challenge", "other"]}},
    "required": ["n", "emotion", "promise"]}}}, "required": ["titles"]}
THUMB_SCHEMA = {"type": "object", "properties": {"thumbs": {"type": "array", "items": {"type": "object", "properties": {
    "n": {"type": "integer"}, "words": {"type": "integer"},
    "face": {"type": "string", "enum": ["human", "drawn_character", "animal", "none"]},
    "subjects": {"type": "integer"},
    "style": {"type": "string", "enum": ["photo", "drawing", "3d_render", "screenshot_or_chart", "mixed"]},
    "mood": {"type": "string", "enum": ["dark", "bright", "mixed"]},
    "highlight": {"type": "boolean", "description": "an arrow, circle or box drawn to point at something"},
    "emotion": {"type": "string", "enum": EMO}},
    "required": ["n", "words", "face", "subjects", "style", "mood", "highlight", "emotion"]}}}, "required": ["thumbs"]}


def ai_titles(vs: list[dict]) -> None:
    for part in chunks(vs, 80):
        lines = "\n".join(f"{i + 1}. {v['title']}" for i, v in enumerate(part))
        try:
            r = llm.llm("For each YouTube title, give the MAIN emotion it uses to make people click, and the kind of "
                        "promise it makes.\n" + lines, schema=TITLE_SCHEMA, name="research_titles",
                        temperature=0.1, models=TEXT_MODELS)
        except llm.LLMError as e:
            print(f"[titles] {e}", flush=True)
            continue
        for t in r["titles"]:
            if 1 <= t["n"] <= len(part):
                part[t["n"] - 1]["ai_title"] = {"emotion": t["emotion"], "promise": t["promise"]}


def ai_thumbs(vs: list[dict], thumb_dir: Path) -> None:
    from PIL import Image

    for v in vs:
        f = thumb_dir / f"{v['id']}.jpg"
        if not f.exists():
            try:
                f.write_bytes(get(f"https://i.ytimg.com/vi/{v['id']}/mqdefault.jpg"))
            except Exception:  # noqa: BLE001
                continue
            time.sleep(0.1)
    have = [v for v in vs if (thumb_dir / f"{v['id']}.jpg").exists()]
    for part in chunks(have, 16):
        imgs = []
        for i, v in enumerate(part):
            buf = io.BytesIO()
            Image.open(thumb_dir / f"{v['id']}.jpg").convert("RGB").save(buf, "JPEG", quality=80)
            imgs.append((f"Image {i + 1}:", buf.getvalue()))
        try:
            r = llm.llm(f"""Above are {len(part)} YouTube thumbnails, each right after "Image n:". For EVERY one,
describe it: how many words of text are on it, any face, how many main subjects, its style, mood,
whether an arrow/circle/box points at something, and the main emotion it shows.""", images=imgs,
                        schema=THUMB_SCHEMA, name="research_thumbs", temperature=0.1, models=AI_MODELS)
        except llm.LLMError as e:
            print(f"[thumbs] {e}", flush=True)
            continue
        for t in r["thumbs"]:
            if 1 <= t["n"] <= len(part):
                part[t["n"] - 1]["ai_thumb"] = {k: t[k] for k in t if k != "n"}


CURIOUS = re.compile(r"\b(why|how|what|secret|hidden|mystery|strange|weird|nobody|never|truth|really|actually)\b", re.I)


def features(v: dict) -> dict[str, bool]:
    t = v["title"]
    words = t.split()
    caps = sum(1 for w in words if len(w) > 2 and w.isupper()) / max(len(words), 1)
    f = {
        "title: question mark": "?" in t,
        "title: has a number": bool(re.search(r"\d", t)),
        "title: says you/your": bool(re.search(r"\byou(r|'re)?\b", t, re.I)),
        "title: mostly CAPITALS": caps > 0.5,
        "title: some CAPITAL words": 0 < caps <= 0.5,
        "title: dash or colon": bool(re.search(r"[:—–|]| - ", t)),
        "title: curiosity word (why/how/secret/...)": bool(CURIOUS.search(t)),
        "title: short (8 words or less)": len(words) <= 8,
        "length: over 15 min": v["seconds"] > 900,
        "length: 8 to 15 min": 480 <= v["seconds"] <= 900,
    }
    a = v.get("ai_title")
    if a:
        for e in EMO:
            f[f"title emotion: {e}"] = a["emotion"] == e
        for p in ("answer", "list", "story", "warning", "challenge"):
            f[f"title promise: {p}"] = a["promise"] == p
    th = v.get("ai_thumb")
    if th:
        f.update({
            "thumb: no text": th["words"] == 0, "thumb: 1-3 words": 1 <= th["words"] <= 3,
            "thumb: 4+ words": th["words"] >= 4,
            "thumb: human face": th["face"] == "human", "thumb: drawn character": th["face"] == "drawn_character",
            "thumb: no face": th["face"] == "none", "thumb: one main subject": th["subjects"] == 1,
            "thumb: 3+ subjects": th["subjects"] >= 3,
            "thumb: photo": th["style"] == "photo", "thumb: drawing": th["style"] == "drawing",
            "thumb: 3D render": th["style"] == "3d_render", "thumb: dark mood": th["mood"] == "dark",
            "thumb: arrow/circle highlight": bool(th["highlight"]),
        })
        for e in ("curiosity", "awe", "fear", "surprise"):
            f[f"thumb emotion: {e}"] = th["emotion"] == e
    return f


def compare(hits, normal) -> list[dict]:
    rows = []
    names = sorted({k for v in hits + normal for k in features(v)})
    for k in names:
        h = [features(v).get(k) for v in hits if k in features(v)]
        n = [features(v).get(k) for v in normal if k in features(v)]
        if not h or not n:
            continue
        sh, sn = 100 * sum(h) / len(h), 100 * sum(n) / len(n)
        diff = sh - sn
        verdict = ("WINNING" if diff >= WIN_POINTS else "LOSING" if diff <= -WIN_POINTS else "no clear difference") \
            if len(h) >= MIN_HITS else f"too few hits ({len(h)})"
        rows.append({"feature": k, "hits_pct": round(sh), "normal_pct": round(sn), "diff": round(diff),
                     "n_hits": len(h), "n_normal": len(n), "verdict": verdict})
    return sorted(rows, key=lambda r: -r["diff"])


def sheet(vs: list[dict], thumb_dir: Path, path: Path, cols: int = 4) -> None:
    from PIL import Image, ImageDraw

    vs = [v for v in vs if (thumb_dir / f"{v['id']}.jpg").exists()]
    if not vs:
        return
    w, h = 320, 210
    im = Image.new("RGB", (cols * w, ((len(vs) + cols - 1) // cols) * h), (20, 20, 20))
    d = ImageDraw.Draw(im)
    for i, v in enumerate(vs):
        x, y = (i % cols) * w, (i // cols) * h
        im.paste(Image.open(thumb_dir / f"{v['id']}.jpg").convert("RGB").resize((320, 180)), (x, y))
        d.text((x + 4, y + 182), f"{v['x_median']}x · {v['views']:,} · {v['title'][:44]}", fill=(230, 230, 230))
    im.save(path, quality=85)


def report(data, hits, normal, rows, out: Path) -> None:
    young = data["young_channels"]
    chans = {c["id"]: c for c in young}
    struggling = [c for c in young if c.get("long_videos", 0) >= STRUGGLING[0] and c.get("median_views", 1e9) < STRUGGLING[1]]
    md = ["# What makes videos win: hits vs normal videos of the same young channels", "",
          f"Pulled {data['pulled'][:16]} UTC · rules: research/RULES.md (fixed before the data) · "
          f"YouTube units: {data['youtube_units']}", "",
          f"- Channels found: {data['channels_found']}; young (≤ 2 years): {len(young)}",
          f"- Long videos measured: {len(data['videos'])}",
          f"- **Hits** (≥ {HIT_X:g}× channel median and ≥ {HIT_MIN:,} views): {len(hits)} from "
          f"{len({v['channel'] for v in hits})} channels; normal videos compared: {len(normal)}",
          f"- Struggling young channels (≥ {STRUGGLING[0]} long videos, median < {STRUGGLING[1]} views): {len(struggling)}",
          "", f"A **winning signal** is ≥ {WIN_POINTS} points more common in hits, with ≥ {MIN_HITS} hits measured.", "",
          "## Signals", "", "| Feature | Hits | Normal | Diff | Verdict |", "| --- | --- | --- | --- | --- |"]
    for r in rows:
        md.append(f"| {r['feature']} | {r['hits_pct']}% | {r['normal_pct']}% | {r['diff']:+d} | {r['verdict']} |")
    md += ["", "## Biggest hits per niche (examples, not rules)", ""]
    for niche in NICHES:
        hs = sorted([v for v in hits if niche in chans[v["channel"]]["niches"]], key=lambda v: -v["x_median"])[:4]
        if not hs:
            continue
        md.append(f"### {niche}")
        for v in hs:
            c = chans[v["channel"]]
            md.append(f"- {v['x_median']}× normal, {v['views']:,} views, {v['seconds'] // 60} min: "
                      f"[{v['title']}](https://www.youtube.com/watch?v={v['id']}) — {c['title']} "
                      f"({c['subs']:,} subs, channel {c['age_days'] // 30} months old)"
                      + (f" · title: {v['ai_title']['emotion']}/{v['ai_title']['promise']}" if v.get("ai_title") else ""))
        md.append("")
    md += ["## Upload pace", "",
           f"- Hit channels: median {statistics.median([chans[c]['days_between_uploads'] for c in {v['channel'] for v in hits}] or [0])} days between long uploads",
           f"- Struggling channels: median {statistics.median([c['days_between_uploads'] for c in struggling] or [0])} days",
           "", "## Limits", "", "- Correlation, not proof: hits can also come from timing, topic or luck.",
           "- Video editing and the first 30 seconds are not measured (YouTube blocks server downloads): the owner's "
           "watch form covers that (watch_list.md)."]
    (out / "report.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    top = sorted(hits, key=lambda v: -v["x_median"])
    picks, seen = [], set()
    for v in top:  # one per channel, across niches
        if v["channel"] not in seen:
            picks.append(v)
            seen.add(v["channel"])
        if len(picks) == 10:
            break
    form = ["# Watch list: 10 hit videos (one per channel)", "",
            "For each video, watch the first 60 seconds (and skim the rest). Note in a few words:", "",
            "1. First 5 seconds: what do you see and hear? (a question, a shocking fact, a story, a face?)",
            "2. What emotion do you feel in the first 30 seconds? (curious, scared, amazed, sad...)",
            "3. Visuals: real footage, drawings, 3D, stock clips, text? How often does the picture change?",
            "4. Voice: human or AI? Music? Sound effects?",
            "5. What made you want to keep watching (or stop)?", ""]
    for i, v in enumerate(picks, 1):
        form.append(f"{i}. [{v['title']}](https://www.youtube.com/watch?v={v['id']}) — {v['x_median']}× its channel's normal")
    (out / "watch_list.md").write_text("\n".join(form) + "\n", encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--no-ai", action="store_true")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "thumbs").mkdir(exist_ok=True)
    llm.LOG_DIR = out / "llm"
    data = json.loads((out / "data.json").read_text()) if (out / "data.json").exists() else pull(out)
    hits, normal = label(data)
    print(f"[research] young channels {len(data['young_channels'])}, videos {len(data['videos'])}, "
          f"hits {len(hits)}, normal {len(normal)}", flush=True)
    if not a.no_ai:
        ai_titles(hits + normal)
        ai_thumbs(hits + normal, out / "thumbs")
    else:
        for v in hits + normal:
            try:
                (out / "thumbs" / f"{v['id']}.jpg").write_bytes(get(f"https://i.ytimg.com/vi/{v['id']}/mqdefault.jpg"))
            except Exception:  # noqa: BLE001
                pass
    (out / "labelled.json").write_text(json.dumps({"hits": hits, "normal": normal}, indent=1, ensure_ascii=False))
    rows = compare(hits, normal)
    report(data, hits, normal, rows, out)
    sheet(sorted(hits, key=lambda v: -v["x_median"])[:24], out / "thumbs", out / "hits_sheet.jpg")
    sheet(normal[:24], out / "thumbs", out / "normal_sheet.jpg")
    (out / "llm_calls.json").write_text(json.dumps([{k: e.get(k) for k in ("name", "model", "status")} for e in llm.LOG], indent=1))
    print((out / "report.md").read_text()[:3000], flush=True)


if __name__ == "__main__":
    main()
