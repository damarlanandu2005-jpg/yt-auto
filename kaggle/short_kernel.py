# Runs ON KAGGLE (free GPU T4 x2), pushed by .github/workflows/cartoon-short.yml (writer = kaggle-start).
# The workflow puts lines above this file: JOB_ID (the GitHub run that started it), TOPIC, WRITE_MODELS,
# CHECK_MODELS and BUNDLE (our code, base64 tar.gz).
# It does the text half of a Stickman Short with open models instead of Gemini (owner, 29 Oct): plan ->
# Wikipedia -> script -> fact-check -> scenes.js, i.e. `cartoon/make_short.py write`, the same code and checks
# as on GitHub. Kaggle test run 40865470880 chose the models: qwen3:32b writes (its Short script matched
# Gemini's: 112 words, 1 dropped), gpt-oss:20b fact-checks (30/30 planted errors, 0 false alarms).
# The models come from the private dataset <user>/ollama-models (no new download, owner 29 Oct).
# No keys or secrets are in this kernel. Results: /kaggle/working/short (fetched by the workflow's collect step).
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
CODE, SHORT, LOGS = W / "code", W / "short", W / "logs"


JOB = {"job_id": JOB_ID, "topic": TOPIC, "write_models": WRITE_MODELS, "check_models": CHECK_MODELS,  # noqa: F821
       "started": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}


def main() -> None:
    LOGS.mkdir(parents=True, exist_ok=True)
    tarfile.open(fileobj=io.BytesIO(base64.b64decode(BUNDLE)), mode="r:gz").extractall(CODE)  # noqa: F821
    sys.path.insert(0, str(CODE / "kaggle"))
    import ollama_setup as ol

    t0 = time.time()
    if not ol.install(LOGS / "ollama_install.log"):
        JOB["error"] = "ollama did not install; see logs/ollama_install.log"
        return
    JOB["saved_models"] = ol.link_saved_models()
    JOB["server"] = ol.serve(LOGS / "ollama_server.log")
    JOB["models"] = {m: ol.ensure(m, LOGS / "models.log") for m in dict.fromkeys(WRITE_MODELS + CHECK_MODELS)}  # noqa: F821
    JOB["setup_s"] = round(time.time() - t0)
    local = lambda ms: ",".join(f"local:{m}" for m in ms)  # noqa: E731
    env = {**os.environ, "PYTHONUNBUFFERED": "1", "MAKE_SHORT_TIMEOUT_MIN": "150", "SCRIPT_REWRITES": "3",
           "LLM_QUALITY_MODELS": local(WRITE_MODELS), "LLM_CHECK_MODELS": local(CHECK_MODELS),  # noqa: F821
           "LLM_LIGHT_MODELS": local(CHECK_MODELS + WRITE_MODELS)}  # noqa: F821
    t = time.time()
    with open(LOGS / "write.log", "w") as log:
        r = subprocess.run([sys.executable, "cartoon/make_short.py", "write", "--topic", TOPIC,  # noqa: F821
                            "--out", str(SHORT)], cwd=CODE, env=env, stdout=log, stderr=subprocess.STDOUT,
                           timeout=160 * 60)
    JOB["write_s"], JOB["write_exit"] = round(time.time() - t), r.returncode


try:
    main()
except Exception:  # noqa: BLE001  the collect step reads job.json either way
    JOB["error"] = traceback.format_exc()[-2000:]
finally:
    JOB["complete"] = (SHORT / "meta" / "report.json").exists()
    W.mkdir(parents=True, exist_ok=True)
    (W / "job.json").write_text(json.dumps(JOB, indent=1))
    print(json.dumps(JOB)[:2000], flush=True)
    shutil.rmtree(CODE, ignore_errors=True)  # our own code: already in the repo, keep the output small
