"""Download Ollama models straight from Ollama's registry (plain HTTP, our own code, nothing installed) into one
flat folder, ready to upload as a private Kaggle dataset.

Owner, 29 Oct: "save the models; later runs should start from the saved copy instead of downloading again".
Every Kaggle run starts on a fresh machine, so the only lasting copy is a dataset attached to the notebook.
It also freezes the exact model version that passed the Kaggle test (run 40865470880).

Folder layout (flat, because the Kaggle CLI uploads only top-level files):
  sha256-<hex>                 one file per blob (weights, template, licence, params), checked by SHA-256
  manifest__<name>__<tag>.json the model's manifest, as Ollama stores it under manifests/registry.ollama.ai/library/
kaggle/ollama_setup.py rebuilds Ollama's folder from these with links (no copying) on the Kaggle machine.

  python kaggle/save_models.py --out /mnt/models qwen3:32b gpt-oss:20b
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
import urllib.request
from pathlib import Path

REGISTRY = "https://registry.ollama.ai/v2/library"
ACCEPT = "application/vnd.docker.distribution.manifest.v2+json"


def get(url: str, timeout: int = 60):
    req = urllib.request.Request(url, headers={"Accept": ACCEPT, "User-Agent": "yt-auto-save-models"})
    return urllib.request.urlopen(req, timeout=timeout)


def blob(name: str, digest: str, size: int, out: Path) -> None:
    path = out / digest.replace(":", "-")
    if path.exists() and path.stat().st_size == size:
        print(f"  {path.name[:19]} already here", flush=True)
        return
    want = digest.split(":", 1)[1]
    for attempt in range(1, 4):
        h, done, t0 = hashlib.sha256(), 0, time.time()
        try:
            with get(f"{REGISTRY}/{name}/blobs/{digest}", timeout=120) as r, open(path, "wb") as f:
                while chunk := r.read(8 << 20):
                    f.write(chunk)
                    h.update(chunk)
                    done += len(chunk)
        except OSError as e:  # ConnectionResetError is not a URLError (CLAUDE.md lesson 10)
            print(f"  {path.name[:19]} attempt {attempt} failed: {e!r}", flush=True)
            continue
        if h.hexdigest() == want and done == size:
            print(f"  {path.name[:19]} {size / 1e9:.2f} GB in {time.time() - t0:.0f} s, SHA-256 ok", flush=True)
            return
        print(f"  {path.name[:19]} attempt {attempt}: wrong size or SHA-256", flush=True)
    path.unlink(missing_ok=True)
    sys.exit(f"could not download {name} {digest}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("models", nargs="+", help="name:tag, e.g. qwen3:32b")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    for model in args.models:
        name, tag = model.split(":", 1)
        with get(f"{REGISTRY}/{name}/manifests/{tag}") as r:
            raw = r.read()
        man = json.loads(raw)
        parts = [man["config"], *man["layers"]]
        print(f"{model}: {len(parts)} blobs, {sum(p['size'] for p in parts) / 1e9:.1f} GB", flush=True)
        for p in parts:
            blob(name, p["digest"], p["size"], out)
        (out / f"manifest__{name}__{tag}.json").write_bytes(raw)  # last, so a manifest means a complete model


if __name__ == "__main__":
    main()
