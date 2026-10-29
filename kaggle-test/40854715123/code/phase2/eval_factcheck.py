"""Phase 2: measure the fact-checker on planted errors.

Runs the AI fact-check (yt_auto.writer.check, the same call the video pipeline
uses) and the plain-code number/unit guard (yt_auto.factguard) on
phase2/factcheck_testset.json, then counts misses and false alarms per error type.
The AI check sends all cases in ONE request (free tier: 20 requests/day per model).

Usage:
    python phase2/eval_factcheck.py --out out/eval               # AI + guard (needs GEMINI_API_KEY)
    python phase2/eval_factcheck.py --out out/eval --guard-only  # no API call
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from yt_auto import factguard, llm, writer  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--testset", default=str(ROOT / "phase2" / "factcheck_testset.json"))
    ap.add_argument("--out", required=True)
    ap.add_argument("--guard-only", action="store_true")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    llm.LOG_DIR = out / "llm"

    data = json.loads(Path(args.testset).read_text(encoding="utf-8"))
    passages, cases, rule = data["passages"], data["cases"], data["pass_rule"]
    idx = {pid: {"text": p["text"]} for pid, p in passages.items()}

    ai = {}
    if not args.guard_only:
        sentences = [{"id": c["id"], "kind": c["kind"], "text": c["text"], "sources": c["sources"]} for c in cases]
        ai = writer.check(sentences, idx, "eval_factcheck")

    rows = []
    for c in cases:
        guard = factguard.check(c["text"], [passages[s]["text"] for s in c["sources"]]) if c["kind"] == "fact" else []
        r = ai.get(c["id"])
        ai_flag = None if args.guard_only else (r is None or r["verdict"] != "supported")
        flagged = bool(guard) or bool(ai_flag)
        rows.append({**c, "ai_verdict": r["verdict"] if r else ("skipped" if args.guard_only else "missing"),
                     "ai_problem": (r or {}).get("problem", ""), "guard": guard,
                     "ai_flag": ai_flag, "guard_flag": bool(guard), "flagged": flagged})

    def score(key):
        per = defaultdict(lambda: [0, 0])  # category -> [caught, total]
        false_alarms = []
        for x in rows:
            hit = bool(x[key])
            if x["expect"] == "error":
                per[x["category"]][0] += hit
                per[x["category"]][1] += 1
            elif hit:
                false_alarms.append(x["id"])
        caught = sum(v[0] for v in per.values())
        total = sum(v[1] for v in per.values())
        return {"caught": caught, "errors": total, "rate": round(caught / total, 3) if total else 0,
                "per_category": {k: f"{v[0]}/{v[1]}" for k, v in sorted(per.items())},
                "false_alarms": false_alarms,
                "controls": sum(1 for x in rows if x["expect"] == "ok")}

    results = {"guard_only": score("guard_flag"), "combined": score("flagged")}
    if not args.guard_only:
        results["ai_only"] = score("ai_flag")
    comb = results["combined"]
    per_ok = all(int(v.split("/")[0]) / int(v.split("/")[1]) >= rule["min_caught_per_category"]
                 for v in comb["per_category"].values())
    results["pass"] = (comb["rate"] >= rule["min_caught_overall"] and per_ok
                       and len(comb["false_alarms"]) <= rule["max_false_alarms"])
    results["rule"] = rule
    results["llm_calls"] = llm.LOG
    (out / "results.json").write_text(json.dumps({"summary": results, "cases": rows}, indent=1, ensure_ascii=False),
                                      encoding="utf-8")

    md = ["# Fact-check test (Phase 2)", "",
          f"Pass rule: catch at least {rule['min_caught_overall']:.0%} of errors overall and "
          f"{rule['min_caught_per_category']:.0%} in every type; at most {rule['max_false_alarms']} false alarm.", "",
          f"**Result: {'PASS' if results['pass'] else 'FAIL'}**", "",
          "| Checker | Caught | " + " | ".join(comb["per_category"]) + " | False alarms |",
          "| --- | --- | " + " | ".join("---" for _ in comb["per_category"]) + " | --- |"]
    for name in ("ai_only", "guard_only", "combined"):
        if name in results:
            s = results[name]
            md.append(f"| {name} | {s['caught']}/{s['errors']} | " + " | ".join(s["per_category"].values())
                      + f" | {len(s['false_alarms'])}/{s['controls']} {s['false_alarms'] or ''} |")
    md += ["", "## Misses and false alarms (combined)", ""]
    for x in rows:
        if (x["expect"] == "error") != x["flagged"]:
            what = "MISSED" if x["expect"] == "error" else "FALSE ALARM"
            md.append(f"- {what} `{x['id']}` ({x['category']}): {x['text']}  \n  AI: {x['ai_verdict']} "
                      f"{x['ai_problem']} · guard: {x['guard'] or '-'}")
    (out / "report.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md))


if __name__ == "__main__":
    main()
