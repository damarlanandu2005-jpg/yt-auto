"""Phase 5 pilot summary: cost, time and failure rate per video.

    python pilot/summary.py RESULTS     # RESULTS = a checkout of the bench-results branch

Reads pilot/pilot.json (which runs belong to which video) and each run's report.json.
Writes pilot/report.md.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    results = Path(sys.argv[1])
    pilot = json.loads((ROOT / "pilot" / "pilot.json").read_text(encoding="utf-8"))
    md = ["# Pilot report (Phase 5)", "",
          "| # | Voice | Topic | Runs (failed) | Gemini requests (OK / tried) | Server minutes | Video | Gate | "
          "Voice matched | Your minutes | Uploaded |",
          "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    totals = {"ok": 0, "tried": 0, "minutes": 0.0, "runs": 0, "failed": 0, "videos": 0}
    for v in pilot["videos"]:
        ok = tried = 0
        minutes, failed, length, gate, match = 0.0, 0, "-", "-", "-"
        for run in v["runs"]:
            rep_path = results / "phase1" / str(run) / "report.json"
            if not rep_path.exists():
                failed += 1
                continue
            rep = json.loads(rep_path.read_text(encoding="utf-8"))
            calls = rep.get("llm_calls", [])
            ok += sum(1 for c in calls if c.get("status") == 200)
            tried += len(calls)
            minutes += rep.get("total_seconds", 0) / 60
            if rep.get("video_seconds"):
                length = f"{rep['video_seconds'] / 60:.1f} min"
                gate = rep.get("gate", {}).get("verdict", "-")
                vm = rep.get("voice_match", {}).get("script_words_heard")
                match = f"{vm:.0%}" if vm is not None else ("Kokoro" if rep.get("voice") == "kokoro" else "-")
            elif not rep.get("stopped_after"):
                failed += 1
        totals.update(ok=totals["ok"] + ok, tried=totals["tried"] + tried, minutes=totals["minutes"] + minutes,
                      runs=totals["runs"] + len(v["runs"]), failed=totals["failed"] + failed,
                      videos=totals["videos"] + (length != "-"))
        md.append(f"| {v['n']} | {v['voice']} | {v['topic'][:60]} | {len(v['runs'])} ({failed}) | {ok} / {tried} | "
                  f"{minutes:.0f} | {length} | {gate} | {match} | {v['owner_minutes'] or '-'} | {v['uploaded'] or '-'} |")
    rate = totals["failed"] / totals["runs"] if totals["runs"] else 0
    md += ["", f"Videos made: {totals['videos']}/8 · runs {totals['runs']}, failed {totals['failed']} ({rate:.0%}) · "
               f"Gemini requests {totals['ok']} OK of {totals['tried']} tried · server time {totals['minutes']:.0f} min · "
               "money spent: ₹0"]
    (ROOT / "pilot" / "report.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md))


if __name__ == "__main__":
    main()
