"""Make 1-3 vertical "zoom journey" Shorts from a finished long video's checked script.

  python phase5/make_shorts.py --long out/long --count 1 --models models --out out/shorts

--long holds script.json, sources.json (and delivery.json, keywords.json if there) of the long video,
as saved in bench-results/phase1/<run_id>/. The facts are reused exactly; only the hook question,
the drawings and the closing line are new. Uses 1 light AI request for the plan, 2 per Short for the
picture check, and 6-8 Cloudflare drawings per Short.
"""
from __future__ import annotations

import argparse
import faulthandler
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from yt_auto import drawings, llm, music, render, shorts  # noqa: E402
from yt_auto.sound import SFX_RECORD  # noqa: E402
from yt_auto.tts import Narrator  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--long", required=True, help="folder with the long video's script.json and sources.json")
    ap.add_argument("--count", type=int, default=1, help="Shorts to make (1-3)")
    ap.add_argument("--models", default="models")
    ap.add_argument("--out", required=True)
    ap.add_argument("--no-music", action="store_true")
    args = ap.parse_args()
    faulthandler.dump_traceback_later(50 * 60, exit=True)  # before the workflow step's time limit

    long_dir, out = Path(args.long), Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    render.LOG_DIR = out / "ffmpeg_logs"
    render.LOG_DIR.mkdir(exist_ok=True)
    llm.LOG_DIR = out / "llm"
    script = json.loads((long_dir / "script.json").read_text())
    sources = json.loads((long_dir / "sources.json").read_text())
    load = lambda name: json.loads((long_dir / name).read_text()) if (long_dir / name).exists() else {}  # noqa: E731
    delivery, key = load("delivery.json"), load("keywords.json")
    if not drawings.cloud_ready():
        sys.exit("Shorts need the Cloudflare drawing secrets (CLOUDFLARE_API_TOKEN, CLOUDFLARE_ACCOUNT_ID)")

    report: dict = {"long_title": script["title"], "started": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())}
    plan_file = out / "shorts_plan.json"
    plans = json.loads(plan_file.read_text()) if plan_file.exists() else shorts.plan(script, max(1, min(args.count, 3)))
    plan_file.write_text(json.dumps(plans, indent=1, ensure_ascii=False))
    print(f"[plan] {len(plans)} Short(s): " + "; ".join(p["title"] for p in plans), flush=True)

    narrator = Narrator(Path(args.models) / "kokoro-v1.0.int8.onnx", Path(args.models) / "voices-v1.0.bin")
    track, music_log = None, {}
    if not args.no_music:
        track = music.find(out / "music", script["title"] + " short", music_log)
    report["music"] = {k: track[k] for k in ("title", "author", "licence", "source_page")} if track else None
    report["shorts"] = []
    for n, p in enumerate(plans[:args.count], 1):
        t0 = time.perf_counter()
        try:
            r = shorts.make(p, n, script, sources, delivery, key, narrator, track, ROOT, out / f"short{n}")
        except Exception as e:  # noqa: BLE001  one bad Short must not lose the others
            r = {"title": p.get("title"), "error": repr(e)[:500]}
        r["build_s"] = round(time.perf_counter() - t0, 1)
        report["shorts"].append(r)
        print(f"[short {n}] {json.dumps(r, ensure_ascii=False)[:600]}", flush=True)
    report["llm_calls"] = llm.LOG
    report["sfx"] = SFX_RECORD
    report["music_record"] = track
    (out / "report.json").write_text(json.dumps(report, indent=1, ensure_ascii=False, default=str))
    if not any(s.get("video") for s in report["shorts"]):
        sys.exit("no Short was made (see report.json)")


if __name__ == "__main__":
    main()
