# Runs ON KAGGLE (free GPU T4 x2), pushed by .github/workflows/kaggle-vision-test.yml. Above this file the workflow puts
# BUNDLE (our code + the labelled test pictures, base64 tar.gz) and MODELS (Ollama picture-reading model names).
# Owner decision 31 Oct: remove Gemini from the project. The picture check (yt_auto/scene_art.check_pictures) needs a model
# that LOOKS at pictures, and only Gemini was ever tested. Same labelled pictures as the Gemini checker test (it scored
# 5 of 7, the 2 misses came from duplicate scenes in that batch). Rule set BEFORE running: a model passes when it
# catches BOTH real-people crowds and wrongly blocks at most 1 of the 3 clean pictures (4 of 5 right, crowds 2/2).
# The text judge is always gpt-oss:20b. No keys are in this kernel. Results: /kaggle/working/results.
import base64
import io
import json
import os
import shutil
import subprocess
import sys
import tarfile
import time
import traceback
from pathlib import Path

W = Path("/kaggle/working")
CODE, OUT = W / "code", W / "results"
JUDGE = "gpt-oss:20b"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    tarfile.open(fileobj=io.BytesIO(base64.b64decode(BUNDLE)), mode="r:gz").extractall(CODE)  # noqa: F821
    sys.path.insert(0, str(CODE / "kaggle"))
    import ollama_setup as ol
    ol.sh("nvidia-smi", OUT / "gpu.txt")
    t0 = time.time()
    if not ol.install(OUT / "ollama_install.log"):
        (OUT / "summary.json").write_text(json.dumps({"error": "ollama did not install"}))
        return
    saved = ol.link_saved_models()
    summary = {"install_s": round(time.time() - t0), "saved": saved, "server": ol.serve(OUT / "ollama_server.log", 16384, 1),
               "judge": JUDGE, "models": {}}
    summary["judge_model"] = ol.ensure(JUDGE, OUT / "models.log")
    for model in MODELS:  # noqa: F821
        slug = model.replace(":", "_").replace("/", "_")
        m = summary["models"][model] = {}
        try:
            m["pull"] = ol.ensure(model, OUT / f"{slug}_pull.log")
            if m["pull"]["source"] == "failed":
                continue
            env = {**os.environ, "LLM_VISION_MODELS": f"local:{model}", "LLM_LIGHT_MODELS": f"local:{JUDGE}",
                   "LLM_QUALITY_MODELS": f"local:{JUDGE}", "PYTHONUNBUFFERED": "1"}
            t = time.time()
            r = subprocess.run([sys.executable, "cartoon/make_pictures.py", "checktest", "--pictures", "test_inputs/pics",
                                "--out", str(OUT / slug)], cwd=CODE, env=env, timeout=3000, capture_output=True, text=True)
            (OUT / f"{slug}.log").write_text(r.stdout + r.stderr)
            m["seconds"] = round(time.time() - t)
            f = OUT / slug / "checktest.json"
            if f.exists():
                d = json.loads(f.read_text())
                right = d["right"]
                crowds = [k for k, v in d["expect"].items() if not v and k in right]
                m.update({"right": sum(right.values()), "of": len(right), "crowds_caught": sum(right[k] for k in crowds),
                          "crowds": len(crowds), "wrong": {k: d["got"][k] for k, v in right.items() if not v}})
                m["passes"] = m["crowds_caught"] == len(crowds) and m["right"] >= len(right) - 1
            else:
                m["error"] = (r.stdout + r.stderr)[-1200:]
        except Exception:  # noqa: BLE001  one model failing must not lose the others
            m["error"] = traceback.format_exc()[-1500:]
        if model not in saved and model != JUDGE:
            ol.sh(f"ollama rm {model}", None, 300)
        (OUT / "summary.json").write_text(json.dumps(summary, indent=1))
        print(model, json.dumps(m)[:800], flush=True)
    (OUT / "summary.json").write_text(json.dumps(summary, indent=1))
    shutil.rmtree(CODE, ignore_errors=True)


main()
