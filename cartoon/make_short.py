"""Make one Stickman Thoughts Short project (cartoon/TEMPLATE.md), ready for explainroo to render.

  python cartoon/make_short.py write --topic "What happens if you fall into the Mariana Trench?" --out out/short
  python cartoon/make_short.py fix --out out/short --log render_log.txt   # after an explainroo check with errors

`write`: plan -> Wikipedia sources -> 110-140 word script -> fact-check (the tested long-video checker)
-> scenes.js by the AI (one automatic fix round for plain-code problems). Stages are cached in --out/meta,
so a rerun resumes. Uses about 4-6 Gemini requests. `fix`: one request that repairs scenes.js from
explainroo's check errors. The project goes to --out/project; notes, sources and checks to --out/meta.
"""
from __future__ import annotations

import argparse
import faulthandler
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from yt_auto import cartoon, llm, research, writer  # noqa: E402


def cached(path: Path, make):
    if path.exists():
        return json.loads(path.read_text())
    data = make()
    path.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")
    return data


def scenes_with_checks(script: dict, md: str, meta: Path, feedback: str = "", previous: str = "") -> tuple[str, list[str]]:
    """AI writes scenes.js; plain-code checks; one automatic fix round if they find problems."""
    res = cartoon.write_scenes(script, md, feedback, previous)
    js = res["scenes_js"]
    problems = cartoon.validate_scenes(js, script)
    (meta / "scene_notes.txt").write_text(res.get("notes", ""), encoding="utf-8")
    if problems:
        print("[scenes] problems, one fix round:\n  " + "\n  ".join(problems), flush=True)
        res2 = cartoon.write_scenes(script, md, "\n".join(f"- {p}" for p in problems), js)
        js2 = res2["scenes_js"]
        problems2 = cartoon.validate_scenes(js2, script)
        if len(problems2) <= len(problems):
            js, problems = js2, problems2
    return js, problems


def write(args) -> None:
    out = Path(args.out)
    meta = out / "meta"
    meta.mkdir(parents=True, exist_ok=True)
    llm.LOG_DIR = meta / "llm"
    report: dict = {"topic": args.topic}
    plan = cached(meta / "plan.json", lambda: cartoon.plan_short(args.topic))
    print(f"[plan] {plan['question']} | feeling: {plan['emotion']}", flush=True)
    sources = (json.loads((meta / "sources.json").read_text()) if (meta / "sources.json").exists()
               else research.gather(plan["wikipedia_titles"], meta / "sources.json"))
    if not sources["articles"]:
        sys.exit("no Wikipedia article could be fetched for this plan")

    def make_script():
        s = cartoon.write_short(args.topic, plan, sources)
        (meta / "script_draft.json").write_text(json.dumps(s, indent=1, ensure_ascii=False), encoding="utf-8")
        rep = writer.fact_check(s, sources)
        (meta / "factcheck.json").write_text(json.dumps(rep, indent=1, ensure_ascii=False), encoding="utf-8")
        return s

    script = cached(meta / "script.json", make_script)
    fc = json.loads((meta / "factcheck.json").read_text()) if (meta / "factcheck.json").exists() else {}
    report["fact_check"] = {k: (len(v) if isinstance(v, list) else v) for k, v in fc.items()}
    report["story_problems"] = cartoon.check_story(script)
    report["words"] = writer.word_count(script)
    print(f"[script] {report['words']} words; fact-check {report['fact_check']}; story {report['story_problems'] or 'ok'}",
          flush=True)
    md = cartoon.script_md(script, sources)
    if (meta / "scenes.js").exists():
        js = (meta / "scenes.js").read_text()
        problems = cartoon.validate_scenes(js, script)
    else:
        js, problems = scenes_with_checks(script, md, meta)
        (meta / "scenes.js").write_text(js, encoding="utf-8")
    report["scene_problems"] = problems
    print(f"[scenes] {'ok' if not problems else problems}", flush=True)
    cartoon.write_project(out / "project", script, sources, js)
    (out / "description.txt").write_text(cartoon.description(script, sources), encoding="utf-8")
    report["llm_calls"] = len(llm.LOG)
    (meta / "report.json").write_text(json.dumps(report, indent=1, ensure_ascii=False), encoding="utf-8")


def fix(args) -> None:
    out = Path(args.out)
    meta = out / "meta"
    llm.LOG_DIR = meta / "llm"
    log = Path(args.log).read_text(errors="replace") if Path(args.log).exists() else ""
    errors = [l.strip() for l in log.splitlines() if re.match(r"\s*(ERROR|error)\b", l)]
    report = json.loads((meta / "report.json").read_text())
    if not errors:
        print("[fix] explainroo found no errors: nothing to fix", flush=True)
        report["render_errors"] = []
        (meta / "report.json").write_text(json.dumps(report, indent=1, ensure_ascii=False), encoding="utf-8")
        return
    script = json.loads((meta / "script.json").read_text())
    sources = json.loads((meta / "sources.json").read_text())
    md = cartoon.script_md(script, sources)
    js_old = (out / "project" / "scenes.js").read_text()
    js, problems = scenes_with_checks(script, md, meta, "\n".join(f"- explainroo check: {e}" for e in errors[:30]), js_old)
    if problems:
        print(f"[fix] new scenes.js still has plain-code problems, keeping the old one: {problems}", flush=True)
        js = js_old
    (out / "project" / "scenes.js").write_text(js, encoding="utf-8")
    report["render_errors_before_fix"] = errors
    report["fix_problems"] = problems
    (meta / "report.json").write_text(json.dumps(report, indent=1, ensure_ascii=False), encoding="utf-8")
    Path(out / "fixed").write_text("1")
    print(f"[fix] scenes.js rewritten for {len(errors)} explainroo error(s)", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    w = sub.add_parser("write")
    w.add_argument("--topic", required=True)
    w.add_argument("--out", required=True)
    f = sub.add_parser("fix")
    f.add_argument("--out", required=True)
    f.add_argument("--log", required=True)
    args = ap.parse_args()
    faulthandler.dump_traceback_later(40 * 60, exit=True)
    {"write": write, "fix": fix}[args.cmd](args)


if __name__ == "__main__":
    main()
