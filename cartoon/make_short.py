"""Make one Stickman Thoughts Short project (cartoon/TEMPLATE.md), ready for explainroo to render.

  python cartoon/make_short.py write --topic "What happens if you fall into the Mariana Trench?" --out out/short
  python cartoon/make_short.py fix --out out/short --log render/log.txt --stills render/render/stills
  python cartoon/make_short.py review --out out/short --stills render2/render/stills

`write`: plan -> Wikipedia sources -> 110-140 word script -> fact-check (the tested long-video checker)
-> scenes.js by the AI (one automatic fix round for plain-code problems). Stages are cached in --out/meta,
so a rerun resumes. Uses about 4-6 Gemini requests. `fix`: one request that repairs scenes.js from
explainroo's check errors. The project goes to --out/project; notes, sources and checks to --out/meta.
"""
from __future__ import annotations

import argparse
import faulthandler
import json
import os
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
    # Rewrites from what the passages really say: 1 on GitHub (Gemini quota), more on Kaggle where they are free
    # (SCRIPT_REWRITES; Titanic run 40877631750 lost its answer after Kaggle's single rewrite).
    for i in range(int(os.environ.get("SCRIPT_REWRITES", "1"))):
        problems0 = cartoon.check_story(script)
        name = "script_retry.json" if i == 0 else f"script_retry{i + 1}.json"
        if not problems0 or (meta / name).exists():
            continue
        print(f"[script] {problems0}: rewrite {i + 1}", flush=True)
        s2 = cartoon.write_short(args.topic, plan, sources, cartoon.rewrite_feedback(fc, problems0))
        rep2 = writer.fact_check(s2, sources)
        (meta / name).write_text(json.dumps(s2, indent=1, ensure_ascii=False), encoding="utf-8")
        if len(cartoon.check_story(s2)) < len(problems0) or (not cartoon.check_story(s2)):
            script, fc = s2, rep2
            (meta / "script.json").write_text(json.dumps(s2, indent=1, ensure_ascii=False), encoding="utf-8")
            (meta / "factcheck.json").write_text(json.dumps(rep2, indent=1, ensure_ascii=False), encoding="utf-8")
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
    (out / "description.txt").write_text(cartoon.description(script, sources, js), encoding="utf-8")
    report["llm_calls"] = len(llm.LOG)
    old = json.loads((meta / "report.json").read_text()) if (meta / "report.json").exists() else {}
    # a rerun resumes from cached stages (e.g. after Kaggle): keep the models that wrote them
    report["models_used"] = sorted({e["model"] for e in llm.LOG if not e.get("error")} | set(old.get("models_used", [])))
    (meta / "report.json").write_text(json.dumps(report, indent=1, ensure_ascii=False), encoding="utf-8")


def review(args) -> dict:
    """Picture review of a render (blind description + judge). Saves meta/<name>.json."""
    out = Path(args.out)
    meta = out / "meta"
    llm.LOG_DIR = meta / "llm"
    script = json.loads((meta / "script.json").read_text())
    try:
        rev = cartoon.review_pictures(Path(args.stills), script)
    except Exception as e:  # noqa: BLE001  no review = not reviewed (the label says DRAFT)
        rev = {"error": repr(e)[:400]}
    (meta / f"{args.name}.json").write_text(json.dumps(rev, indent=1, ensure_ascii=False), encoding="utf-8")
    bad = {k: v for k, v in rev.get("problems", {}).items() if v}
    print(f"[review] {rev.get('error') or (str(len(bad)) + ' scene(s) with picture problems')}", flush=True)
    for k, v in bad.items():
        print(f"  {k}: {v}", flush=True)
    return rev


def fix(args) -> None:
    out = Path(args.out)
    meta = out / "meta"
    llm.LOG_DIR = meta / "llm"
    log = Path(args.log).read_text(errors="replace") if Path(args.log).exists() else ""
    errors = [l.strip() for l in log.splitlines() if re.match(r"\s*(ERROR|error)\b", l)]
    args.name = "picture_review1"
    rev = review(args) if args.stills else {}
    pictures = [f"{k}: {p}" for k, v in rev.get("problems", {}).items() for p in v]
    report = json.loads((meta / "report.json").read_text())
    report["render_errors_first"] = errors
    report["picture_problems_first"] = pictures
    if not errors and not pictures:
        print("[fix] no layout errors and no picture problems: nothing to fix", flush=True)
        (meta / "report.json").write_text(json.dumps(report, indent=1, ensure_ascii=False), encoding="utf-8")
        return
    script = json.loads((meta / "script.json").read_text())
    sources = json.loads((meta / "sources.json").read_text())
    md = cartoon.script_md(script, sources)
    js_old = (out / "project" / "scenes.js").read_text()
    feedback = ([f"- explainroo layout check: {e}" for e in errors[:30]]
                + [f"- picture review (an AI looked at the last frame of each scene): {p}" for p in pictures[:30]])
    js, problems = scenes_with_checks(script, md, meta, "\n".join(feedback), js_old)
    if problems:
        print(f"[fix] new scenes.js still has plain-code problems, keeping the old one: {problems}", flush=True)
        js = js_old
    else:
        Path(out / "fixed").write_text("1")
    (out / "project" / "scenes.js").write_text(js, encoding="utf-8")
    cartoon.copy_emoji(js, out / "project")  # the fixed scenes may use other emoji and pictures
    cartoon.copy_art(js, out / "project")
    (out / "description.txt").write_text(cartoon.description(script, sources, js), encoding="utf-8")
    report["fix_problems"] = problems
    (meta / "report.json").write_text(json.dumps(report, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"[fix] {len(errors)} layout error(s), {len(pictures)} picture problem(s) sent back to the scene writer", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    w = sub.add_parser("write")
    w.add_argument("--topic", required=True)
    w.add_argument("--out", required=True)
    f = sub.add_parser("fix")
    f.add_argument("--out", required=True)
    f.add_argument("--log", required=True)
    f.add_argument("--stills", default="", help="explainroo stills folder of the first render (picture review)")
    r = sub.add_parser("review")
    r.add_argument("--out", required=True)
    r.add_argument("--stills", required=True)
    r.add_argument("--name", default="picture_review2")
    args = ap.parse_args()
    # 40 min on GitHub; longer on Kaggle, where qwen3:32b took 12 min for one script (run 40865470880)
    faulthandler.dump_traceback_later(int(os.environ.get("MAKE_SHORT_TIMEOUT_MIN", "40")) * 60, exit=True)
    {"write": write, "fix": fix, "review": review}[args.cmd](args)


if __name__ == "__main__":
    main()
