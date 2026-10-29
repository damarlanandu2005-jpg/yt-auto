"""Strong-emotion topic finder for Stickman Thoughts (design cartoon/TOPIC_FINDER.md).

    python cartoon/find_topics.py find --out out/topics [--signals old/signals.json]
    python cartoon/find_topics.py test-safety            # test B, plain code, no network
    python cartoon/find_topics.py test-feeling --signals out/topics/signals.json --out out/topics   # test A

find: needs YOUTUBE_API_KEY (~600-900 units) and the AI (1 strong request for ideas + 2 for feeling scores).
--signals reuses measured signals of an earlier run (no YouTube units). Writes queue.json, report.md,
pictures_needed.md, signals.json, llm/.
test-feeling: the feeling scorer on competitor Shorts' titles, hits vs normal Shorts of the same channels.
Pass: AUC >= 0.65 (else the feeling weight drops to 0.10, rule in TOPIC_FINDER.md).
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from yt_auto import emotion_topics as et, llm  # noqa: E402


def test_feeling(signals: Path, out: Path, n: int = 120) -> dict:
    rows = json.loads(signals.read_text())["test_a"]
    hits = [r for r in rows if r["hit"]]
    norm = [r for r in rows if not r["hit"]]
    rnd = random.Random(29)
    k = min(n // 2, len(hits), len(norm))
    pick = rnd.sample(hits, k) + rnd.sample(norm, k)
    rnd.shuffle(pick)
    items = [{"question": r["title"], "situation": r["title"], "answer": "(not given)"} for r in pick]
    scores = {}
    for i in range(0, len(items), 60):
        part = et.feeling_scores(items[i:i + 60], llm.QUALITY, "emotion_test_a")
        scores.update({i + j: v for j, v in part.items()})
    pairs = [(scores[i + 1]["feeling"], r["hit"]) for i, r in enumerate(pick) if i + 1 in scores]
    res = {"pairs": len(pairs), "hits": k, "normal": k, "auc": et.auc(pairs), "rule": "AUC >= 0.65"}
    res["passed"] = res["auc"] >= 0.65
    (out / "test_a.json").write_text(json.dumps({**res, "rows": [
        {**r, "feeling": scores.get(i + 1, {}).get("feeling")} for i, r in enumerate(pick)]}, indent=1, ensure_ascii=False))
    return res


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("action", choices=["find", "test-safety", "test-feeling"])
    ap.add_argument("--out", default="out/topics")
    ap.add_argument("--signals", default="")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    llm.LOG_DIR = out / "llm"
    if args.action == "test-safety":
        r = et.eval_safety(ROOT / "cartoon" / "topic_safety_test.json")
        (out / "test_b.json").write_text(json.dumps(r, indent=1))
        print(json.dumps(r, indent=1))
        print(f"[topics] test B {'PASSED' if r['passed'] else 'FAILED'}: {r['caught']}/{r['of']} unsafe blocked, "
              f"{r['false_blocks']} safe wrongly blocked (rule: >= 24, <= 2)")
        sys.exit(0 if r["passed"] else 1)
    try:
        if args.action == "test-feeling":
            r = test_feeling(Path(args.signals), out)
            print(f"[topics] test A {'PASSED' if r['passed'] else 'FAILED'}: AUC {r['auc']} on {r['pairs']} Shorts")
            return
        r = et.run(out, ROOT / "library", Path(args.signals) if args.signals else None)
        print((out / "report.md").read_text())
        print(f"[topics] {len(r['queue'])}/{et.CFG['queue_size']} topics in the queue")
        if len(r["queue"]) < et.CFG["queue_size"]:
            sys.exit(1)
    finally:
        (out / "llm_calls.json").write_text(json.dumps(llm.LOG, indent=1))


if __name__ == "__main__":
    main()
