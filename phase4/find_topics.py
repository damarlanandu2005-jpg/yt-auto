"""Phase 4: find and score video topics for a niche.

    python phase4/find_topics.py --niche science_space --out out/topics [--phase0b DATA]

Needs GEMINI_API_KEY (2 requests) and YOUTUBE_API_KEY (6 units for trending charts).
--phase0b points at the niche test data (bench-results/phase0b) for "beats its channel's normal" videos.
Writes ideas.json, ideas.md, signals.json and the AI prompts/replies (llm/).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from yt_auto import llm, topics  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--niche", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--phase0b", default="")
    ap.add_argument("--want", type=int, default=10)
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    llm.LOG_DIR = out / "llm"
    niche = json.loads((ROOT / "niches" / f"{args.niche}.json").read_text(encoding="utf-8"))
    try:
        r = topics.run(niche, ROOT / "library", Path(args.phase0b) if args.phase0b else None, out, args.want)
        print((out / "ideas.md").read_text(encoding="utf-8"))
        ok = len(r["chosen"]) >= args.want
        print(f"[phase4] {'DONE' if ok else 'NOT ENOUGH'}: {len(r['chosen'])}/{args.want} scored ideas with evidence")
    finally:
        (out / "llm_calls.json").write_text(json.dumps(llm.LOG, indent=1))


if __name__ == "__main__":
    main()
