"""Phase 0b backward check (RULES.md, "Backward check"): an early niche answer from data that exists today.

    python phase0b/backward.py DATA      # DATA = bench-results phase0b folder; needs YOUTUBE_API_KEY
"""
from __future__ import annotations

import datetime as dt
import json
import statistics
import sys
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import niche_test as nt  # noqa: E402

CORE_ARTICLES = {  # fixed before running (RULES.md)
    "technology": ["Computer", "Smartphone", "Internet", "Electric battery", "Semiconductor",
                   "Artificial intelligence", "Electric car", "Engineering"],
    "science_space": ["Universe", "Black hole", "Solar System", "Mars", "Moon", "James Webb Space Telescope",
                      "Quantum mechanics", "Physics"],
    "money_economics": ["Inflation", "Economics", "Money", "Recession", "Gross domestic product", "Central bank",
                        "Interest rate", "Stock market"],
}
WIKI = "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/user"


def monthly_views(title: str) -> list[int]:
    end = dt.date.today().replace(day=1) - dt.timedelta(days=1)            # end of last full month
    start = (end.replace(day=1) - dt.timedelta(days=360)).replace(day=1)  # 12 full months
    t = urllib.parse.quote(title.replace(" ", "_"), safe="")
    req = nt.urllib.request.Request(f"{WIKI}/{t}/monthly/{start:%Y%m%d}00/{end:%Y%m%d}00",
                                    headers={"User-Agent": "yt-auto/0.1 (https://github.com/damarlanandu2005-jpg)"})
    with nt.urllib.request.urlopen(req, timeout=30) as r:
        return [i["views"] for i in json.loads(r.read())["items"]]


def median(xs):
    return round(statistics.median(xs), 3) if xs else None


def main() -> None:
    data = Path(sys.argv[1])
    sel = json.loads((data / "channels.json").read_text(encoding="utf-8"))
    snaps = sorted((data / "snapshots").glob("*.json"))
    last = json.loads(snaps[-1].read_text(encoding="utf-8"))
    elig = sel["eligible_all"]
    info = nt.channels_info([e["id"] for e in elig])            # for creation dates (1 unit per 50)
    missing = [e["id"] for e in elig if e["id"] not in last["channels"]]
    extra = {}
    for cid in missing:                                          # eligible but not chosen: fetch their videos
        ch = info.get(cid)
        if ch:
            vids = [nt.summarize_video(v) for v in nt.latest_videos(ch["contentDetails"]["relatedPlaylists"]["uploads"])]
            extra[cid] = {"latest_long": [v for v in vids if v["seconds"] >= 240 and not v["live"]][:10]}
    now = nt.now()
    res = {}
    for niche in nt.CFG["niches"]:
        growth, momentum, beats, recent, young = [], [], 0, 0, 0
        for e in (x for x in elig if x["niche"] == niche):
            ch = info.get(e["id"])
            if not ch:
                continue
            created = dt.datetime.fromisoformat(ch["snippet"]["publishedAt"].replace("Z", "+00:00"))
            months = (now - created).days / 30.44
            subs = int(ch["statistics"].get("subscriberCount", 0))
            if months <= 36:
                young += 1
                growth.append(subs / max(months, 1))
            snap = last["channels"].get(e["id"]) or extra.get(e["id"], {})
            rows, med = nt.video_rows(snap)
            usable = [r for r in rows if not r["too_new"]]
            if len(usable) >= 6:  # snapshots keep 10 long videos; some are under 7 days old
                h = len(usable) // 2
                new, old = usable[:h], usable[h:2 * h]
                a, b = statistics.median(r["vpd"] for r in new), statistics.median(r["vpd"] for r in old)
                if b > 0:
                    momentum.append(a / b)
            recent += len(usable)
            beats += sum(r["beats"] for r in usable)
        interest = {}
        for t in CORE_ARTICLES[niche]:
            try:
                m = monthly_views(t)
                interest[t] = {"last_6": sum(m[-6:]), "prev_6": sum(m[-12:-6]),
                               "change": round(sum(m[-6:]) / max(sum(m[-12:-6]), 1), 2)}
            except Exception as ex:  # noqa: BLE001
                interest[t] = {"error": repr(ex)[:120]}
        ch_ok = [v["change"] for v in interest.values() if "change" in v]
        res[niche] = {"eligible": sum(1 for x in elig if x["niche"] == niche), "young_channels": young,
                      "subs_per_month_median": median(growth), "momentum_median": median(momentum),
                      "breakout_rate": round(beats / recent, 3) if recent else None,
                      "wiki_last6_vs_prev6_median": median(ch_ok),
                      "wiki_last6_total": sum(v.get("last_6", 0) for v in interest.values()),
                      "too_little_data": young < 10, "interest": interest}
    ok = {n: r for n, r in res.items() if not r["too_little_data"] and r["subs_per_month_median"] is not None}
    order = sorted(ok, key=lambda n: -ok[n]["subs_per_month_median"])
    winner = None
    if order:
        winner = order[0]
        def rank_last(key):
            vals = {n: ok[n][key] for n in ok if ok[n][key] is not None}
            return vals and min(vals, key=vals.get) == winner and len(vals) > 1
        if len(order) > 1 and rank_last("momentum_median") and rank_last("breakout_rate"):
            winner = order[1]
    out = {"made": now.isoformat(), "units": nt.USED["units"], "niches": res, "ranking_by_main": order,
           "winner": winner}
    (data / "backward.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    lab = {n: nt.CFG["niches"][n]["label"] for n in res}
    md = ["# Niche backward check (early answer; the 4-week test confirms)", "",
          f"Made {now:%Y-%m-%d}. Method and winner rule: RULES.md 'Backward check' (written before running).", "",
          "| Niche | Eligible | Young (≤3 y) | Subs/month (median) | Momentum | Breakouts | Wikipedia interest (last 6 vs prev 6 months) |",
          "| --- | --- | --- | --- | --- | --- | --- |"]
    for n, r in res.items():
        md.append(f"| {lab[n]} | {r['eligible']} | {r['young_channels']}{' (too little data)' if r['too_little_data'] else ''} | "
                  f"{r['subs_per_month_median']} | {r['momentum_median']} | {r['breakout_rate']} | "
                  f"{r['wiki_last6_vs_prev6_median']}x ({r['wiki_last6_total']:,} views) |")
    md += ["", f"**Backward winner: {lab.get(winner, 'none')}**" + (f" (ranking on main measure: {', '.join(lab[n] for n in order)})" if order else "")]
    (data / "backward.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md))
    print(f"[quota] {nt.USED['units']} YouTube units")


if __name__ == "__main__":
    main()
