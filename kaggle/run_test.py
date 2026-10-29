# Runs ON KAGGLE (free GPU notebook), pushed by .github/workflows/kaggle-test.yml. The workflow puts two lines
# above this file: BUNDLE (our code + test inputs, base64 tar.gz) and MODELS (Ollama model names).
# Owner's idea (29 Oct): run our own open AI model on Kaggle's free GPUs, so there is no daily request limit.
# The models must first pass the SAME tests as Gemini:
#   1. Phase 2 fact-check test: 30 planted errors + 16 clean controls (rule set before testing: >= 80 % caught,
#      >= 60 % per error type, <= 1 false alarm). Gemini Flash: 30/30, 0 false alarms (run 40466026336).
#   2. Short script: plan + Wikipedia sources of the Mariana Trench test (run 40843120092) -> script -> fact-check:
#      words left and sentences dropped (Gemini: 111 words, 1 dropped).
#   3. Scene writer: scenes.js for that script -> our plain-code checks (Gemini: 0 problems after one fix).
# No keys or secrets are in this kernel. Results go to /kaggle/working/results (fetched by the workflow).
import base64
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
    s = cartoon.write_short("What happens if you fall into the Mariana Trench?", plan, sources)
    rep = writer.fact_check(s, sources)
    res["script"] = {"words": writer.word_count(s), "dropped": len(rep["dropped"]), "fixed": len(rep["fixed"]),
                     "story_problems": cartoon.check_story(s), "seconds": round(time.time() - t0)}
    (out / "script.json").write_text(json.dumps(s, indent=1, ensure_ascii=False))
except Exception as e:
    res["script"] = {"error": repr(e)[:500]}
# scene writer on the GEMINI script of the same test, so both models get the same input
t0 = time.time()
try:
    g = json.loads((inp / "script.json").read_text())
    r = cartoon.write_scenes(g, cartoon.script_md(g, sources))
    problems = cartoon.validate_scenes(r["scenes_js"], g)
    res["scenes"] = {"problems": problems, "n_problems": len(problems), "seconds": round(time.time() - t0)}
    (out / "scenes.js").write_text(r["scenes_js"])
except Exception as e:
    res["scenes"] = {"error": repr(e)[:500]}
(out / "summary.json").write_text(json.dumps(res, indent=1))
print(json.dumps(res)[:1500])
'''


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    tarfile.open(fileobj=io.BytesIO(base64.b64decode(BUNDLE)), mode="r:gz").extractall(CODE)  # noqa: F821
    sh("nvidia-smi", OUT / "gpu.txt")
    t0 = time.time()
    # Ollama's installer needs zstd, which Kaggle's image lacks (first run: "requires zstd for extraction")
    sh("apt-get install -y -q zstd || (apt-get update -q && apt-get install -y -q zstd)", OUT / "ollama_install.log", 600)
    sh("curl -fsSL https://ollama.com/install.sh | sh", OUT / "ollama_install.log", 900)
    if sh("command -v ollama", OUT / "ollama_install.log", 30) != 0:
        (OUT / "summary.json").write_text(json.dumps({"error": "ollama did not install; see ollama_install.log"}))
        return
    env = {**os.environ, "OLLAMA_KEEP_ALIVE": "60m", "OLLAMA_CONTEXT_LENGTH": "32768"}
    subprocess.Popen(["ollama", "serve"], stdout=open(OUT / "ollama_server.log", "w"), stderr=subprocess.STDOUT, env=env)
    summary = {"install_s": round(time.time() - t0), "server": wait_server(), "models": {}}
    (CODE / "run_script_scenes.py").write_text(SCRIPT_AND_SCENES)
    for model in MODELS:  # noqa: F821
        slug = model.replace(":", "_").replace("/", "_")
        m = summary["models"][model] = {}
        try:
            t = time.time()
            m["pull_ok"] = sh(f"ollama pull {model}", OUT / f"{slug}_pull.log", 2400) == 0
            m["pull_s"] = round(time.time() - t)
            run_env = {**os.environ, "LLM_QUALITY_MODELS": f"local:{model}", "LLM_LIGHT_MODELS": f"local:{model}",
                       "PYTHONUNBUFFERED": "1"}
            t = time.time()
            r = subprocess.run([sys.executable, "phase2/eval_factcheck.py", "--out", str(OUT / slug / "factcheck")],
                               cwd=CODE, env=run_env, timeout=5400, capture_output=True, text=True)
            (OUT / f"{slug}_factcheck.log").write_text(r.stdout + r.stderr)
            m["factcheck_s"] = round(time.time() - t)
            fc = OUT / slug / "factcheck" / "results.json"
            if fc.exists():
                s = json.loads(fc.read_text())["summary"]
                m["factcheck"] = {k: v for k, v in s.items() if k != "llm_calls"}
            t = time.time()
            r = subprocess.run([sys.executable, "run_script_scenes.py", str(OUT / slug / "short")], cwd=CODE, env=run_env,
                               timeout=7200, capture_output=True, text=True)
            (OUT / f"{slug}_short.log").write_text(r.stdout + r.stderr)
            m["short_s"] = round(time.time() - t)
            sj = OUT / slug / "short" / "summary.json"
            if sj.exists():
                m["short"] = json.loads(sj.read_text())
        except Exception:  # noqa: BLE001  one model failing must not lose the others
            m["error"] = traceback.format_exc()[-1500:]
        sh(f"ollama rm {model}", None, 300)  # free the disk for the next model
        (OUT / "summary.json").write_text(json.dumps(summary, indent=1))
        print(model, json.dumps(m)[:1000], flush=True)
    (OUT / "summary.json").write_text(json.dumps(summary, indent=1))


main()
