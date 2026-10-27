"""AI drawings: for ideas a real photo can't show, and for photo slots left without a good photo.

Free open model on the runner's CPU. Drawing test run 40576992038: Segmind-Vega + VegaRT LCM LoRA
(both Apache-2.0, not gated), 76 s per 1024x576 drawing, 9.2 GB peak, about half the drawings on
target, so every drawing is looked at by a vision model afterwards (shots.verify_drawings).
Runs in its own process (torch leaves threads behind, like whisper: CLAUDE.md lesson 2) with a
time budget; slots it doesn't reach keep their fallback card.

    python -m yt_auto.drawings jobs.json OUT_DIR BUDGET_SECONDS
"""
from __future__ import annotations

import datetime as dt
import json
import os
import subprocess
import sys
import time
from pathlib import Path

MODEL = {"base": "segmind/Segmind-Vega", "lora": "segmind/Segmind-VegaRT", "steps": 4, "guidance": 0.0,
         "licence": "Apache-2.0", "page": "https://huggingface.co/segmind/Segmind-Vega",
         "licence_url": "https://www.apache.org/licenses/LICENSE-2.0"}
# Subject first: SDXL's text encoders read only the first 77 tokens.
STYLE = ("pure black background, detailed ink illustration, white and grey pen linework, one bright red accent, "
         "high contrast, simple clear composition, no text, no letters, no numbers")
WIDTH, HEIGHT = 1024, 576
MAX_DRAWINGS = 18
BUDGET_S = 25 * 60
CACHE = Path.home() / "hf-draw"  # own model cache (the whisper cache has its own key in the workflow)


def record(path: Path, subject: str) -> dict:
    """Licence record, same fields as a photo's. The model's licence (Apache-2.0) puts no limits on what
    it draws; the drawings are non-realistic, so YouTube's AI disclosure is not needed."""
    return {"file": path.name, "kind": "drawing", "source": "ai_drawing", "title": subject,
            "source_page": MODEL["page"], "licence": "AI-generated drawing (no third-party rights)",
            "model_licence": MODEL["licence"], "licence_url": MODEL["licence_url"],
            "author": f"AI-generated with {MODEL['base']} + {MODEL['lora']}",
            "attribution": f"Illustration generated with Segmind-Vega ({MODEL['licence']}): {subject}",
            "downloaded": dt.date.today().isoformat(), "prompt": f"{subject}, {STYLE}"}


def make(jobs: list[dict], out_dir: Path, root: Path, budget_s: int = BUDGET_S) -> dict:
    """jobs: [{"id", "subject"}]. Returns {"drawn": {id: path}, "log": {...}}."""
    out_dir.mkdir(parents=True, exist_ok=True)
    if not jobs:
        return {"drawn": {}, "log": {"asked": 0}}
    (out_dir / "jobs.json").write_text(json.dumps(jobs, indent=1, ensure_ascii=False))
    env = {**os.environ, "HF_HUB_CACHE": str(CACHE), "HF_HUB_DISABLE_PROGRESS_BARS": "1"}
    try:
        r = subprocess.run([sys.executable, "-m", "yt_auto.drawings", str(out_dir / "jobs.json"), str(out_dir),
                            str(budget_s)], cwd=root, env=env, stdin=subprocess.DEVNULL, capture_output=True,
                           text=True, timeout=budget_s + 15 * 60)
        (out_dir / "drawings.log").write_text(r.stdout[-20000:] + "\n" + r.stderr[-20000:])
        err = f"exit {r.returncode}: {r.stderr[-600:]}" if r.returncode else ""
    except subprocess.TimeoutExpired:
        err = "timed out"
    res = json.loads((out_dir / "result.json").read_text()) if (out_dir / "result.json").exists() else {"drawn": {}}
    drawn = {k: str(out_dir / v) for k, v in res.get("drawn", {}).items() if (out_dir / v).exists()}
    return {"drawn": drawn, "log": {**{k: v for k, v in res.items() if k != "drawn"}, "asked": len(jobs),
                                    "drawn": len(drawn), **({"error": err} if err else {})}}


def _main() -> None:
    jobs = json.loads(Path(sys.argv[1]).read_text())
    out, budget = Path(sys.argv[2]), float(sys.argv[3])
    t0 = time.perf_counter()
    import diffusers
    import torch
    from diffusers import LCMScheduler, StableDiffusionXLPipeline

    torch.set_num_threads(os.cpu_count() or 4)
    pipe = StableDiffusionXLPipeline.from_pretrained(MODEL["base"], torch_dtype=torch.float32)
    pipe.load_lora_weights(MODEL["lora"])
    pipe.fuse_lora()
    pipe.scheduler = LCMScheduler.from_config(pipe.scheduler.config)
    pipe.set_progress_bar_config(disable=True)
    res = {"load_s": round(time.perf_counter() - t0, 1), "torch": torch.__version__,
           "diffusers": diffusers.__version__, "drawn": {}, "seconds": {}, "skipped_for_time": []}
    per = 80.0
    for i, job in enumerate(jobs):
        if time.perf_counter() - t0 + per > budget:
            res["skipped_for_time"] = [j["id"] for j in jobs[i:]]
            break
        t = time.perf_counter()
        img = pipe(prompt=f"{job['subject']}, {STYLE}", num_inference_steps=MODEL["steps"],
                   guidance_scale=MODEL["guidance"], width=WIDTH, height=HEIGHT,
                   generator=torch.Generator().manual_seed(1000 + i)).images[0]
        name = f"{job['id']}.png"
        img.save(out / name)
        (out / f"{job['id']}.licence.json").write_text(json.dumps(record(out / name, job["subject"]), indent=2))
        per = time.perf_counter() - t
        res["drawn"][job["id"]] = name
        res["seconds"][job["id"]] = round(per, 1)
        print(f"[drawings] {job['id']}: {per:.0f} s  {job['subject']}", flush=True)
        (out / "result.json").write_text(json.dumps(res, indent=1))
    res["total_s"] = round(time.perf_counter() - t0, 1)
    (out / "result.json").write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    import faulthandler

    faulthandler.dump_traceback_later(float(sys.argv[3]) + 10 * 60, exit=True)
    _main()
