# Runs ON KAGGLE (free GPU T4 x2), pushed by .github/workflows/cartoon-brain.yml. The workflow puts lines above this file:
# JOB_ID, TOPIC, SCRIPT_TEXT (the owner's own script or ''), WRITE_MODELS, CHECK_MODELS, VISION_MODEL and BUNDLE (our
# code + small character reference pictures, base64 tar.gz).
# Owner decision 31 Oct: no Gemini. ONE kernel makes the whole picture side of a Short with open models, one stage after the other
# (the two T4s hold one big model at a time):
#   A. Ollama: plan -> Wikipedia -> script -> fact-check            (qwen3:32b writes, gpt-oss:20b checks: make_short.py write --script-only)
#   B. Ollama: the picture plan = cast sheet + scene prompts        (make_pictures.py plan, same writer)
#   C. Ollama stopped, FLUX.2 [dev] 32B fp16 draws every scene       (make_pictures.py pack -> kaggle/flux2_kernel.py, ~6.5 min a picture)
#   D. Ollama again: a picture-reading model + gpt-oss judge look at every picture (make_pictures.py check)
#   E. failed pictures are redrawn with a stronger prompt and a new seed (back to C), at most REDRAWS times
# The outcome per scene (passed or not) is in /kaggle/working/out/summary.json; a Short whose pictures still fail is a DRAFT.
# No keys or secrets are in this kernel. Results: /kaggle/working/out.
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
CODE, OUT = W / "code", W / "out"
SHORT, PICS, LOGS = OUT / "short", OUT / "pics", OUT / "logs"
REDRAWS = 2
JOB = {"job_id": JOB_ID, "topic": TOPIC, "write_models": WRITE_MODELS, "check_models": CHECK_MODELS,  # noqa: F821
       "vision_model": VISION_MODEL, "owner_script": bool(SCRIPT_TEXT),  # noqa: F821
       "started": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "stages": {}}


def save() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "summary.json").write_text(json.dumps(JOB, indent=1))


def stage(name: str, t0: float) -> None:
    JOB["stages"][name] = round(time.time() - t0)
    print(f"[stage] {name} {JOB['stages'][name]} s", flush=True)
    save()


def local(ms) -> str:
    return ",".join(f"local:{m}" for m in ms)


def run_py(args: list[str], env: dict, log: Path, timeout: int, cwd: Path = CODE) -> int:
    with open(log, "a") as f:
        return subprocess.run([sys.executable, *args], cwd=cwd, env=env, stdout=f, stderr=subprocess.STDOUT,
                              timeout=timeout).returncode


def stop_ollama() -> None:
    subprocess.run("pkill -f 'ollama' || true", shell=True)
    time.sleep(8)  # the GPUs must be empty before FLUX loads
    subprocess.run("nvidia-smi --query-gpu=memory.used --format=csv", shell=True, stdout=open(LOGS / "gpu_after_ollama.txt", "a"))


def main() -> None:
    for d in (LOGS, PICS):
        d.mkdir(parents=True, exist_ok=True)
    tarfile.open(fileobj=io.BytesIO(base64.b64decode(BUNDLE)), mode="r:gz").extractall(CODE)  # noqa: F821
    sys.path.insert(0, str(CODE / "kaggle"))
    import ollama_setup as ol

    t0 = time.time()
    if not ol.install(LOGS / "ollama_install.log"):
        JOB["error"] = "ollama did not install; see logs/ollama_install.log"
        return
    JOB["saved_models"] = ol.link_saved_models()
    models = list(dict.fromkeys(WRITE_MODELS + CHECK_MODELS + [VISION_MODEL]))  # noqa: F821
    JOB["server"] = ol.serve(LOGS / "ollama_server.log", 32768, 1)
    JOB["models"] = {m: ol.ensure(m, LOGS / "models.log") for m in models}
    stage("setup", t0)
    base = {**os.environ, "PYTHONUNBUFFERED": "1", "MAKE_SHORT_TIMEOUT_MIN": "150", "SCRIPT_REWRITES": "3",
            "LLM_QUALITY_MODELS": local(WRITE_MODELS), "LLM_CHECK_MODELS": local(CHECK_MODELS),  # noqa: F821
            "LLM_LIGHT_MODELS": local(CHECK_MODELS + WRITE_MODELS)}  # noqa: F821

    # A. the checked script (RESUME_FILES: plan, sources and script of an earlier run: the script stage is then skipped,
    # 86 min in the first run; no rewrites on a resume)
    resume = RESUME_FILES  # noqa: F821
    if resume:
        (SHORT / "meta").mkdir(parents=True, exist_ok=True)
        for name, text in resume.items():
            (SHORT / "meta" / name).write_text(text)
        base["SCRIPT_REWRITES"] = "0"
        JOB["resumed_files"] = sorted(resume)
    t = time.time()
    args = ["cartoon/make_short.py", "write", "--topic", TOPIC, "--out", str(SHORT), "--script-only"]  # noqa: F821
    if SCRIPT_TEXT:  # noqa: F821
        (W / "owner_script.txt").write_text(SCRIPT_TEXT)  # noqa: F821
        args += ["--script-file", str(W / "owner_script.txt")]
    JOB["script_exit"] = run_py(args, base, LOGS / "script.log", 160 * 60)
    stage("script", t)
    script = SHORT / "meta" / "script.json"
    if not script.exists():
        JOB["error"] = "no checked script (see logs/script.log)"
        return

    # B. the picture plan (cast sheet + scene prompts)
    t = time.time()
    JOB["plan_exit"] = run_py(["cartoon/make_pictures.py", "plan", "--script", str(script), "--topic", TOPIC, "--out", str(PICS)],  # noqa: F821
                              base, LOGS / "plan.log", 60 * 60)
    stage("plan", t)
    if not (PICS / "pictures.json").exists():
        JOB["error"] = "no picture plan (see logs/plan.log)"
        return
    plan = json.loads((PICS / "pictures.json").read_text())
    JOB["plan_problems"] = plan.get("log", {}).get("problems", [])

    # C-E. draw, look, redraw
    eyes = {**base, "OLLAMA_UNLOAD_OTHERS": "1", "LLM_VISION_MODELS": local([VISION_MODEL]), "LLM_LIGHT_MODELS": local(CHECK_MODELS)}  # noqa: F821
    flux_dir = W / "scenes"  # where kaggle/flux2_kernel.py saves
    level, redo = 0, ""
    JOB["rounds"] = []
    while True:
        stop_ollama()
        t = time.time()
        pack = ["cartoon/make_pictures.py", "pack", "--out", str(PICS)] + (["--redo", redo] if redo else [])
        run_py(pack, base, LOGS / "pack.log", 600)
        code = subprocess.run([sys.executable, "run.py"], cwd=PICS / "k", env={**os.environ, "PYTHONUNBUFFERED": "1"},
                              stdout=open(LOGS / f"flux_{level}.log", "w"), stderr=subprocess.STDOUT, timeout=5 * 3600).returncode
        if (W / "job.json").exists():  # the FLUX script's own record (drawing seconds, errors, sizes)
            shutil.copy(W / "job.json", PICS / f"flux_job_{level}.json")
        stage(f"draw_{level}", t)
        if flux_dir.exists():
            shutil.copytree(flux_dir, PICS / f"drawn_{level}", dirs_exist_ok=True)
        # D. look
        t = time.time()
        JOB["server"] = ol.serve(LOGS / f"ollama_server_{level}.log", 32768, 1)
        ol.ensure(VISION_MODEL, LOGS / "models.log")  # noqa: F821
        ck = ["cartoon/make_pictures.py", "check", "--out", str(PICS), "--pictures", str(flux_dir), "--level", str(level)]
        if redo:
            ck += ["--redo", redo]
        run_py(ck, eyes, LOGS / f"check_{level}.log", 90 * 60)
        stage(f"check_{level}", t)
        res_f = PICS / f"check_{level}.json"
        res = json.loads(res_f.read_text()) if res_f.exists() else {"problems": {}, "missing": ["check failed"]}
        failed = {k: v for k, v in res["problems"].items() if v}
        JOB["rounds"].append({"level": level, "flux_exit": code, "failed": failed, "missing": res.get("missing", [])})
        save()
        nxt = PICS / f"redo_{level + 1}.json"
        if (not failed and not res.get("missing")) or level >= REDRAWS or not nxt.exists():
            break
        level += 1
        redo = str(nxt)
    last = JOB["rounds"][-1]
    JOB["final_failed"] = sorted(set(last["failed"]) | set(last["missing"]))
    JOB["pictures_ok"] = not JOB["final_failed"]
    # the final pictures, one per scene: the BEST drawing of each scene, not the newest (a redraw can be worse).
    # Best = the first round in which the scene passed, else the round with the fewest problems.
    final = OUT / "pictures"
    final.mkdir(exist_ok=True)
    JOB["picked_round"] = {}
    for p in sorted(PICS.glob("drawn_*/flux2dev_*.png")) or sorted(flux_dir.glob("flux2dev_*.png")):
        pass
    names = {q.name for q in flux_dir.glob("flux2dev_*.png")}
    for name in names:
        sid = name.removeprefix("flux2dev_fp16_").removeprefix("flux2dev_").rsplit(".", 1)[0]
        best, best_n = None, None
        for r in JOB["rounds"]:
            if sid not in r["failed"] and sid not in r["missing"]:
                n = 0  # passed in this round
            elif sid in r["failed"]:
                n = len(r["failed"][sid])
            else:
                continue
            src = PICS / f"drawn_{r['level']}" / name
            if src.exists() and (best_n is None or n < best_n):
                best, best_n = (src, r["level"]), n
                if n == 0:
                    break
        src = best[0] if best else flux_dir / name
        JOB["picked_round"][sid] = best[1] if best else "latest"
        shutil.copy(src, final / name)


try:
    main()
except Exception:  # noqa: BLE001  the collect step reads summary.json either way
    JOB["error"] = traceback.format_exc()[-2500:]
finally:
    JOB["finished"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    JOB["complete"] = "error" not in JOB and "pictures_ok" in JOB
    save()
    print(json.dumps(JOB)[:3000], flush=True)
    shutil.rmtree(CODE, ignore_errors=True)  # our own code: already in the repo
    shutil.rmtree(W / "scenes", ignore_errors=True)
