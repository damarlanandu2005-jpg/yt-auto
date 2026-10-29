"""Ollama on a Kaggle GPU machine: install, start, and use the saved models (owner, 29 Oct: no new download
every run). Shared by the Kaggle scripts; it travels inside their code bundle.

Saved models are the private dataset made by kaggle/save_models.py (kaggle-test.yml action=save-models). Their
files are linked into Ollama's folder, not copied. A model missing from the dataset is downloaded as before.
"""
from __future__ import annotations

import json
import os
import subprocess
import time
import urllib.request
from pathlib import Path

MODELS_DIR = Path("/root/.ollama/models")
INPUT = Path("/kaggle/input")


def sh(cmd: str, log: Path | None = None, timeout: int = 1800) -> int:
    print("$", cmd, flush=True)
    with open(log, "a") if log else open(os.devnull, "w") as f:
        r = subprocess.run(cmd, shell=True, stdout=f if log else None, stderr=subprocess.STDOUT if log else None,
                           timeout=timeout)
    return r.returncode


def install(log: Path) -> bool:
    # Ollama's installer needs zstd, which Kaggle's image lacks (first test run: "requires zstd for extraction")
    sh("apt-get install -y -q zstd || (apt-get update -q && apt-get install -y -q zstd)", log, 600)
    sh("curl -fsSL https://ollama.com/install.sh | sh", log, 900)
    return sh("command -v ollama", log, 30) == 0


def link_saved_models() -> list[str]:
    """Link every saved model found under /kaggle/input into Ollama's folder. Returns the models linked."""
    found = []
    for man in sorted(INPUT.rglob("manifest__*.json")):
        _, name, tag = man.stem.split("__", 2)
        m = json.loads(man.read_text())
        blobs = [man.parent / p["digest"].replace(":", "-") for p in [m["config"], *m["layers"]]]
        if not all(b.exists() for b in blobs):
            print(f"[models] saved {name}:{tag} is incomplete; it will be downloaded", flush=True)
            continue
        (MODELS_DIR / "blobs").mkdir(parents=True, exist_ok=True)
        for b in blobs:
            dst = MODELS_DIR / "blobs" / b.name
            if not (dst.exists() or dst.is_symlink()):
                dst.symlink_to(b.resolve())
        mdir = MODELS_DIR / "manifests" / "registry.ollama.ai" / "library" / name
        mdir.mkdir(parents=True, exist_ok=True)
        (mdir / tag).write_bytes(man.read_bytes())
        found.append(f"{name}:{tag}")
    print(f"[models] saved models linked: {found or 'none'}", flush=True)
    return found


def serve(log: Path, context: int = 32768) -> bool:
    env = {**os.environ, "OLLAMA_MODELS": str(MODELS_DIR), "OLLAMA_KEEP_ALIVE": "60m",
           "OLLAMA_CONTEXT_LENGTH": str(context), "OLLAMA_NOPRUNE": "1"}  # never delete the linked files
    subprocess.Popen(["ollama", "serve"], stdout=open(log, "w"), stderr=subprocess.STDOUT, env=env)
    for _ in range(120):
        try:
            with urllib.request.urlopen("http://127.0.0.1:11434/api/version", timeout=5) as r:
                return r.status == 200
        except OSError:
            time.sleep(1)
    return False


def ensure(model: str, log: Path) -> dict:
    """The model ready to answer: the saved copy if Ollama accepts it, else a download. Returns timings."""
    env = f"OLLAMA_MODELS={MODELS_DIR}"
    if sh(f"{env} ollama show {model} --modelfile > /dev/null", log, 120) == 0:
        return {"source": "saved", "seconds": 0}
    t = time.time()
    ok = sh(f"{env} ollama pull {model}", log, 2400) == 0
    return {"source": "downloaded" if ok else "failed", "seconds": round(time.time() - t)}
