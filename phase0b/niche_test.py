"""Phase 0b niche data test (rules: phase0b/RULES.md, settings: phase0b/niches.json).

Commands (DATA is a folder kept on the bench-results branch under phase0b/):
    python phase0b/niche_test.py check    DATA   # is YOUTUBE_API_KEY there and working? (1 unit)
    python phase0b/niche_test.py select   DATA   # find + choose channels -> DATA/channels.json (once)
    python phase0b/niche_test.py snapshot DATA   # stats for chosen channels -> DATA/snapshots/<date>.json
    python phase0b/niche_test.py report   DATA   # compare snapshots -> DATA/report.md

The key is sent in a header and never printed. Every call's quota cost is counted.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import statistics
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CFG = json.loads((ROOT / "phase0b" / "niches.json").read_text(encoding="utf-8"))
API = "https://youtube.googleapis.com/youtube/v3"
UNITS = {"search": 100}  # everything else we use costs 1 unit per call
USED = {"units": 0, "calls": 0}


class QuotaStop(RuntimeError):
    pass


def yt(endpoint: str, **params) -> dict:
    cost = UNITS.get(endpoint, 1)
    if USED["units"] + cost > CFG["quota"]["stop_at_units"]:
        raise QuotaStop(f"stopping at {USED['units']} units (limit {CFG['quota']['stop_at_units']})")
    key = os.environ.get("YOUTUBE_API_KEY")
    if not key:
        raise SystemExit("YOUTUBE_API_KEY is not set")
    url = f"{API}/{endpoint}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"x-goog-api-key": key, "Accept": "application/json"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                USED["units"] += cost
                USED["calls"] += 1
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            body = e.read().decode(errors="replace")[:800]
            if e.code in (500, 503) and attempt < 2:
                time.sleep(5 * (attempt + 1))
                continue
            raise RuntimeError(f"YouTube API {endpoint}: HTTP {e.code}: {body}") from None
        except OSError:
            if attempt < 2:
                time.sleep(5 * (attempt + 1))
                continue
            raise
    return {}


def _chunks(items, n=50):
    for i in range(0, len(items), n):
        yield items[i:i + n]


def iso_seconds(d: str) -> int:
    m = re.match(r"P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", d or "")
    if not m:
        return 0
    days, h, mi, s = (int(x or 0) for x in m.groups())
    return days * 86400 + h * 3600 + mi * 60 + s


def now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def age_days(published: str) -> float:
    return max((now() - dt.datetime.fromisoformat(published.replace("Z", "+00:00"))).total_seconds() / 86400, 0.01)


# ---------- data fetch ----------

def channels_info(ids: list[str]) -> dict[str, dict]:
    out = {}
    for chunk in _chunks(ids):
        d = yt("channels", part="snippet,statistics,contentDetails,status", id=",".join(chunk), maxResults=50)
        for c in d.get("items", []):
            out[c["id"]] = c
    return out


def latest_videos(uploads_playlist: str, n_items: int = 50) -> list[dict]:
    d = yt("playlistItems", part="contentDetails", playlistId=uploads_playlist, maxResults=n_items)
    ids = [it["contentDetails"]["videoId"] for it in d.get("items", [])]
    return videos_info(ids)


def videos_info(ids: list[str]) -> list[dict]:
    out = []
    for chunk in _chunks(ids):
        d = yt("videos", part="snippet,statistics,contentDetails,status,liveStreamingDetails", id=",".join(chunk))
        out += d.get("items", [])
    out.sort(key=lambda v: v["snippet"]["publishedAt"], reverse=True)
    return out


def summarize_video(v: dict) -> dict:
    st = v.get("statistics", {})
    return {"id": v["id"], "title": v["snippet"]["title"], "published": v["snippet"]["publishedAt"],
            "seconds": iso_seconds(v["contentDetails"].get("duration", "")),
            "views": int(st.get("viewCount", 0)), "likes": int(st.get("likeCount", 0) or 0),
            "comments": int(st.get("commentCount", 0) or 0),
            "live": "liveStreamingDetails" in v, "kids": v.get("status", {}).get("madeForKids", False)}


# ---------- commands ----------

def cmd_check(data: Path) -> None:
    d = yt("i18nLanguages", part="snippet", hl="en")
    ok = bool(d.get("items"))
    (data / "key_check.json").write_text(json.dumps({"ok": ok, "languages": len(d.get("items", [])),
                                                     "checked": now().isoformat(), "units": USED["units"]}))
    print(f"YOUTUBE_API_KEY works: {ok} ({len(d.get('items', []))} languages listed, {USED['units']} unit)")


def _english(texts: list[str], ch: dict) -> bool:
    lang = (ch["snippet"].get("defaultLanguage") or "").lower()
    if lang.startswith("en"):
        return True
    chars = "".join(texts)
    letters = [c for c in chars if c.isalpha()]
    return bool(letters) and sum(c.isascii() for c in letters) / len(letters) >= CFG["selection"]["english_ascii_min"]


def _fit(titles: list[str], words: list[str]) -> int:
    return sum(1 for t in titles if any(re.search(rf"\b{re.escape(w)}\b", t.lower()) for w in words))


def cmd_select(data: Path) -> None:
    """Version 1: choose channels once. Version 2 (RULES.md change log): top up with queries_v2,
    keeping every channel already chosen."""
    prev = None
    if (data / "channels.json").exists():
        prev = json.loads((data / "channels.json").read_text(encoding="utf-8"))
        if prev["rules_version"] >= CFG["version"]:
            print("channels.json already made with these rules: selection is never redone")
            return
    sel = CFG["selection"]
    after = (now() - dt.timedelta(days=sel["search"]["published_within_days"])).strftime("%Y-%m-%dT%H:%M:%SZ")
    found: dict[str, set[str]] = {}  # channel id -> niches whose search found it
    key = "queries_v2" if prev else "queries"
    for niche, nc in CFG["niches"].items():
        for q in nc[key]:
            d = yt("search", part="snippet", q=q, type=sel["search"]["type"], videoDuration=sel["search"]["videoDuration"],
                   relevanceLanguage=sel["search"]["relevanceLanguage"], publishedAfter=after,
                   maxResults=sel["search"]["maxResults"])
            for it in d.get("items", []):
                found.setdefault(it["snippet"]["channelId"], set()).add(niche)
    print(f"[select] {len(found)} candidate channels from {sum(len(n[key]) for n in CFG['niches'].values())} "
          f"searches ({USED['units']} units)", flush=True)

    if prev:  # screen only channels the first pull hasn't already screened
        found = {c: n for c, n in found.items() if c not in prev["screening_log"]}
    info = channels_info(sorted(found))
    log, eligible = {}, []
    for cid in sorted(found):
        ch = info.get(cid)
        if not ch:
            log[cid] = "channel not returned"
            continue
        st = ch.get("statistics", {})
        if st.get("hiddenSubscriberCount"):
            log[cid] = "hidden subscriber count"
            continue
        subs = int(st.get("subscriberCount", 0))
        if not sel["subscribers_min"] <= subs <= sel["subscribers_max"]:
            log[cid] = f"subscribers {subs} outside {sel['subscribers_min']}-{sel['subscribers_max']}"
            continue
        if ch.get("status", {}).get("madeForKids"):
            log[cid] = "made for kids"
            continue
        try:
            vids = [summarize_video(v) for v in latest_videos(ch["contentDetails"]["relatedPlaylists"]["uploads"])]
        except QuotaStop:
            raise
        except Exception as e:  # noqa: BLE001 — one broken channel shouldn't stop the test
            log[cid] = f"could not read uploads: {e}"[:200]
            continue
        long_v = [v for v in vids if v["seconds"] >= sel["long_video_min_seconds"] and not v["live"]]
        if len(long_v) < sel["long_videos_min"]:
            log[cid] = f"only {len(long_v)} long videos in its latest 50 uploads"
            continue
        if age_days(long_v[0]["published"]) > sel["last_long_upload_within_days"]:
            log[cid] = "no long upload in the last 60 days"
            continue
        if sum(v["live"] for v in vids) > len(vids) / 2:
            log[cid] = "mainly live streams"
            continue
        titles = [v["title"] for v in long_v[:sel["fit_out_of"]]]
        if not _english(titles + [ch["snippet"]["title"]], ch):
            log[cid] = "not English"
            continue
        fits = {n: _fit(titles, CFG["niches"][n]["keywords"]) for n in CFG["niches"]}
        bad = [t for t in titles if any(w in t.lower() for w in CFG["niches"]["money_economics"]["exclude_title_words"])]
        if bad:
            fits["money_economics"] = 0  # advice/trading channel: never in the money niche
        best = max(fits, key=lambda n: (fits[n], n in found[cid]))
        if fits[best] < sel["fit_min_titles"]:
            log[cid] = f"fit too low {fits}"
            continue
        eligible.append({"id": cid, "title": ch["snippet"]["title"], "subscribers": subs, "niche": best,
                         "fit": fits[best], "found_by": sorted(found[cid]),
                         "sample_titles": titles[:5]})
        log[cid] = f"eligible for {best} (fit {fits[best]}/10)"
    chosen = {}
    for niche in CFG["niches"]:
        keep = prev["chosen"][niche] if prev else []
        pool = sorted((e for e in eligible if e["niche"] == niche), key=lambda e: (-e["fit"], e["subscribers"], e["id"]))
        chosen[niche] = keep + [dict(e, added_in_version=CFG["version"]) for e in pool][:max(0, sel["channels_per_niche"] - len(keep))]
    out = {"created": prev["created"] if prev else now().isoformat(), "rules_version": CFG["version"],
           "candidates": len(found) + (prev["candidates"] if prev else 0),
           "eligible": len(eligible) + (prev["eligible"] if prev else 0), "units": USED["units"],
           "chosen": chosen, "eligible_all": (prev["eligible_all"] if prev else []) + eligible,
           "screening_log": {**(prev["screening_log"] if prev else {}), **log},
           "history": (prev.get("history", []) if prev else []) + [
               {"version": CFG["version"], "at": now().isoformat(), "new_candidates": len(found),
                "new_eligible": len(eligible), "units": USED["units"]}]}
    (data / "channels.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    for n, c in chosen.items():
        print(f"[select] {n}: {len(c)} chosen ({sum(e['niche'] == n for e in eligible)} newly eligible)")
    print(f"[select] units used: {USED['units']}")


def cmd_snapshot(data: Path) -> None:
    chosen = json.loads((data / "channels.json").read_text(encoding="utf-8"))["chosen"]
    ids = [c["id"] for cs in chosen.values() for c in cs]
    info = channels_info(ids)
    snap = {"taken": now().isoformat(), "channels": {}}
    n_latest = CFG["metrics"]["latest_long_videos"]
    for cid in ids:
        ch = info.get(cid)
        if not ch:
            snap["channels"][cid] = {"missing": True}
            continue
        st = ch["statistics"]
        try:
            vids = [summarize_video(v) for v in latest_videos(ch["contentDetails"]["relatedPlaylists"]["uploads"])]
        except QuotaStop:
            raise
        except Exception as e:  # noqa: BLE001
            vids, err = [], str(e)[:200]
        else:
            err = ""
        long_v = [v for v in vids if v["seconds"] >= CFG["selection"]["long_video_min_seconds"] and not v["live"]][:n_latest]
        snap["channels"][cid] = {"subscribers": int(st.get("subscriberCount", 0)), "views": int(st.get("viewCount", 0)),
                                 "videos": int(st.get("videoCount", 0)), "latest_long": long_v, "error": err}
    snap["units"] = USED["units"]
    (data / "snapshots").mkdir(exist_ok=True)
    name = now().strftime("%Y-%m-%d") + ".json"
    (data / "snapshots" / name).write_text(json.dumps(snap, ensure_ascii=False), encoding="utf-8")
    print(f"[snapshot] {name}: {len(ids)} channels, {USED['units']} units")


def video_rows(ch_snap: dict) -> tuple[list[dict], float | None]:
    rows = []
    for v in ch_snap.get("latest_long", []):
        days = age_days(v["published"])
        rows.append({**v, "days": round(days, 1), "vpd": v["views"] / days, "too_new": days < CFG["metrics"]["too_new_days"]})
    usable = [r["vpd"] for r in rows if not r["too_new"]]
    med = statistics.median(usable) if usable else None
    for r in rows:
        r["beats"] = bool(med) and not r["too_new"] and r["vpd"] >= CFG["metrics"]["outlier_ratio"] * med
    return rows, med


def cmd_report(data: Path) -> None:
    sel = json.loads((data / "channels.json").read_text(encoding="utf-8"))
    snaps = sorted((data / "snapshots").glob("*.json"))
    if not snaps:
        raise SystemExit("no snapshots yet")
    all_snaps = [json.loads(p.read_text(encoding="utf-8")) for p in snaps]
    first, last = all_snaps[0], all_snaps[-1]
    weeks = max((dt.datetime.fromisoformat(last["taken"]) - dt.datetime.fromisoformat(first["taken"])).days / 7, 0)

    def first_seen(cid):  # channels added in rules v2 start later: measure from their own first snapshot
        for sn in all_snaps:
            if sn["channels"].get(cid, {}).get("views"):
                return sn
        return first
    md = [f"# Niche data test — report ({len(snaps)} snapshot{'s' if len(snaps) > 1 else ''}, "
          f"{weeks:.1f} weeks of change)", "",
          f"Rules: phase0b/RULES.md (version {sel['rules_version']}). Channels chosen {sel['created'][:10]} from "
          f"{sel['candidates']} candidates ({sel['eligible']} eligible).", ""]
    summary = {}
    for niche, chans in sel["chosen"].items():
        growth, sub_up, beats, recent = [], [], 0, 0
        outliers = []
        for c in chans:
            f = first_seen(c["id"])
            a, b = f["channels"].get(c["id"], {}), last["channels"].get(c["id"], {})
            w = (dt.datetime.fromisoformat(last["taken"]) - dt.datetime.fromisoformat(f["taken"])).days / 7
            if w >= 1 and a.get("views") and b.get("views"):
                growth.append(((b["views"] / a["views"]) ** (1 / w) - 1) * 100)
                sub_up.append(b["subscribers"] > a["subscribers"])
            rows, med = video_rows(b)
            for r in rows:
                if not r["too_new"]:
                    recent += 1
                    beats += r["beats"]
                if r["beats"]:
                    outliers.append((r["vpd"] / med, c["title"], r["title"], c["subscribers"]))
        summary[niche] = {
            "channels": len(chans),
            "median_weekly_view_growth_pct": round(statistics.median(growth), 2) if growth else None,
            "share_subs_grew": round(sum(sub_up) / len(sub_up), 2) if sub_up else None,
            "share_videos_beat_normal": round(beats / recent, 3) if recent else None,
            "top_outliers": [f"{x:.1f}x · {t} — {ch} ({s:,} subs)" for x, ch, t, s in sorted(outliers, reverse=True)[:8]],
        }
    md += ["| Niche | Channels | Weekly view growth (median) | Subs grew | Videos beating normal |",
           "| --- | --- | --- | --- | --- |"]
    for n, s in summary.items():
        g = "needs 2+ snapshots" if s["median_weekly_view_growth_pct"] is None else f"{s['median_weekly_view_growth_pct']:.2f} %"
        sg = "-" if s["share_subs_grew"] is None else f"{s['share_subs_grew']:.0%}"
        sb = "-" if s["share_videos_beat_normal"] is None else f"{s['share_videos_beat_normal']:.0%}"
        md.append(f"| {CFG['niches'][n]['label']} | {s['channels']} | {g} | {sg} | {sb} |")
    for n, s in summary.items():
        md += ["", f"## {CFG['niches'][n]['label']}: videos beating their channel's normal", ""]
        md += [f"- {x}" for x in s["top_outliers"]] or ["- none yet"]
    md += ["", "Final choice: after 5 snapshots (4 weeks), by the rule in RULES.md. Owner confirms."]
    (data / "report.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    (data / "report.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False), encoding="utf-8")
    print("\n".join(md))


def main() -> None:
    cmd, data = sys.argv[1], Path(sys.argv[2])
    data.mkdir(parents=True, exist_ok=True)
    try:
        {"check": cmd_check, "select": cmd_select, "snapshot": cmd_snapshot, "report": cmd_report}[cmd](data)
    finally:
        print(f"[quota] {USED['calls']} calls, {USED['units']} units")


if __name__ == "__main__":
    main()
