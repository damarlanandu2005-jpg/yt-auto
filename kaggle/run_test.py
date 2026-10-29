# Runs ON KAGGLE (free GPU notebook), pushed by .github/workflows/kaggle-test.yml. The workflow puts two lines
# above this file: BUNDLE (our code + test inputs, base64 tar.gz) and MODELS (Ollama model names).
# Owner's idea (29 Oct): run our own open AI model on Kaggle's free GPUs, so there is no daily request limit.
# Test 2 (29 Oct evening, owner dropped the model licence rule: "give the best model"): writers and coders for
# the two Short jobs, see SCRIPT_AND_SCENES. Test 1 (run 40865470880) also ran the Phase 2 fact-check test.
# The models must first pass the SAME tests as Gemini:
#   1. Phase 2 fact-check test: 30 planted errors + 16 clean controls (rule set before testing: >= 80 % caught,
#      >= 60 % per error type, <= 1 false alarm). Gemini Flash: 30/30, 0 false alarms (run 40466026336).
#   2. Short script: plan + Wikipedia sources of the Mariana Trench test (run 40843120092) -> script -> fact-check:
#      words left and sentences dropped (Gemini: 111 words, 1 dropped).
#   3. Scene writer: scenes.js for that script -> our plain-code checks (Gemini: 0 problems after one fix).
# No keys or secrets are in this kernel. Results go to /kaggle/working/results (fetched by the workflow).
import base64
import shutil
import io
import json
import os
import subprocess
import sys
import tarfile
import time
import traceback
import urllib.request
from pathlib import Path

W = Path("/kaggle/working")
CODE, OUT = W / "code", W / "results"


def sh(cmd: str, log: Path | None = None, timeout: int = 1800) -> int:
    print("$", cmd, flush=True)
    with open(log, "a") if log else open(os.devnull, "w") as f:
        r = subprocess.run(cmd, shell=True, stdout=f if log else None, stderr=subprocess.STDOUT if log else None,
                           timeout=timeout)
    return r.returncode


def wait_server(seconds: int = 120) -> bool:
    for _ in range(seconds):
        try:
            with urllib.request.urlopen("http://127.0.0.1:11434/api/version", timeout=5) as r:
                return r.status == 200
        except OSError:
            time.sleep(1)
    return False


SCRIPT_AND_SCENES = r'''
# Test 2 (29 Oct, owner: "give the best model"): the same two jobs a Short needs, with the same checks.
#   script: plan + Wikipedia sources of the Titanic test -> write_short -> fact-check (always gpt-oss:20b, so
#           every writer is judged by the same checker) -> story check, one rewrite like the real pipeline
#   scenes: the good, checked Titanic script (run 40903619735) -> write_scenes in the new library style ->
#           plain-code checks -> one fix round -> checks again (like make_short.scenes_with_checks)
import json, sys, time
from pathlib import Path
sys.path.insert(0, ".")
from yt_auto import cartoon, llm, writer
out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
llm.LOG_DIR = out / "llm"
inp = Path("test_inputs")
plan = json.loads((inp / "plan.json").read_text()); sources = json.loads((inp / "sources.json").read_text())
res = {}
t0 = time.time()
try:
    s = cartoon.write_short(plan["question"], plan, sources)
    rep = writer.fact_check(s, sources)
    problems = cartoon.check_story(s)
    first = {"words": writer.word_count(s), "dropped": len(rep["dropped"]), "problems": problems}
    if problems:
        s = cartoon.write_short(plan["question"], plan, sources, cartoon.rewrite_feedback(rep, problems))
        rep = writer.fact_check(s, sources)
        problems = cartoon.check_story(s)
    res["script"] = {"first_try": first, "words": writer.word_count(s), "dropped": len(rep["dropped"]),
                     "fixed": len(rep["fixed"]), "story_problems": problems, "seconds": round(time.time() - t0)}
    (out / "script.json").write_text(json.dumps(s, indent=1, ensure_ascii=False))
except Exception as e:
    res["script"] = {"error": repr(e)[:500]}
t0 = time.time()
try:
    g = json.loads((inp / "script.json").read_text())
    md = cartoon.script_md(g, sources)
    js = cartoon.fix_imports(cartoon.write_scenes(g, md)["scenes_js"])
    p1 = cartoon.validate_scenes(js, g)
    js2, p2 = js, p1
    if p1:
        js2 = cartoon.fix_imports(cartoon.write_scenes(g, md, "\n".join(f"- {p}" for p in p1), js)["scenes_js"])
        p2 = cartoon.validate_scenes(js2, g)
    res["scenes"] = {"problems_first": p1, "n_first": len(p1), "problems_after_fix": p2, "n_after_fix": len(p2),
                     "shots": len(__import__("re").findall(r"\bplace\(", js2)), "seconds": round(time.time() - t0)}
    (out / "scenes.js").write_text(js2)
except Exception as e:
    res["scenes"] = {"error": repr(e)[:500]}
(out / "summary.json").write_text(json.dumps(res, indent=1))
print(json.dumps(res)[:1500])
'''

CHECKER = "gpt-oss:20b"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    tarfile.open(fileobj=io.BytesIO(base64.b64decode(BUNDLE)), mode="r:gz").extractall(CODE)  # noqa: F821
    sys.path.insert(0, str(CODE / "kaggle"))
    import ollama_setup as ol
    sh("nvidia-smi", OUT / "gpu.txt")
    t0 = time.time()
    if not ol.install(OUT / "ollama_install.log"):
        (OUT / "summary.json").write_text(json.dumps({"error": "ollama did not install; see ollama_install.log"}))
        return
    saved = ol.link_saved_models()
    summary = {"install_s": round(time.time() - t0), "saved": saved, "server": ol.serve(OUT / "ollama_server.log"),
               "checker": CHECKER, "models": {}}
    summary["checker_model"] = ol.ensure(CHECKER, OUT / "models.log")
    (CODE / "run_script_scenes.py").write_text(SCRIPT_AND_SCENES)
    for model in MODELS:  # noqa: F821
        slug = model.replace(":", "_").replace("/", "_")
        m = summary["models"][model] = {}
        try:
            m["pull"] = ol.ensure(model, OUT / f"{slug}_pull.log")
            if m["pull"]["source"] == "failed":
                continue
            run_env = {**os.environ, "LLM_QUALITY_MODELS": f"local:{model}", "LLM_LIGHT_MODELS": f"local:{model}",
                       "LLM_CHECK_MODELS": f"local:{CHECKER}", "PYTHONUNBUFFERED": "1"}
            t = time.time()
            r = subprocess.run([sys.executable, "run_script_scenes.py", str(OUT / slug / "short")], cwd=CODE, env=run_env,
                               timeout=5400, capture_output=True, text=True)
            (OUT / f"{slug}_short.log").write_text(r.stdout + r.stderr)
            m["short_s"] = round(time.time() - t)
            sj = OUT / slug / "short" / "summary.json"
            if sj.exists():
                m["short"] = json.loads(sj.read_text())
        except Exception:  # noqa: BLE001  one model failing must not lose the others
            m["error"] = traceback.format_exc()[-1500:]
        if model not in saved and model != CHECKER:
            sh(f"ollama rm {model}", None, 300)  # free the disk for the next model
        (OUT / "summary.json").write_text(json.dumps(summary, indent=1))
        print(model, json.dumps(m)[:1000], flush=True)
    (OUT / "summary.json").write_text(json.dumps(summary, indent=1))
    shutil.rmtree(CODE, ignore_errors=True)


main()
