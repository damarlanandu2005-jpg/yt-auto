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
# First choice when the owner's Cloudflare secrets are set (added 28 Oct): FLUX.1 [schnell] on Workers AI.
# Official pricing page (28 Oct): free 10,000 neurons/day (reset 00:00 UTC); FLUX.1 schnell costs 4.8 neurons per
# 512x512 tile + 9.6 per step, about 58 per 1024x1024 drawing at 4 steps, so ~170 drawings/day stay free. Terms:
# the customer keeps all rights in inputs and outputs; Cloudflare doesn't train on them. Model licence Apache-2.0.
CLOUD = {"model": "@cf/black-forest-labs/flux-1-schnell", "name": "FLUX.1 [schnell] (Black Forest Labs) on Cloudflare "
         "Workers AI", "licence": "Apache-2.0", "page": "https://huggingface.co/black-forest-labs/FLUX.1-schnell",
         "steps": 4}
CLOUD_DAILY_MAX = 120  # stay well under the free 10,000 neurons (≈170 drawings) per day
MAX_DRAWINGS = 24  # 12 planned + room for photo slots whose photo failed the check (local model: ~80 s each)
CLOUD_MAX_DRAWINGS, CLOUD_PLANNED_MAX = 60, 40  # Workers AI: seconds each, ~170 free a day (2 videos fit)
BUDGET_S = 32 * 60
CACHE = Path.home() / "hf-draw"  # own model cache (the whisper cache has its own key in the workflow)


def record(path: Path, subject: str, cloud: bool = False) -> dict:
    """Licence record, same fields as a photo's. The model's licence (Apache-2.0) puts no limits on what
    it draws; the drawings are non-realistic, so YouTube's AI disclosure is not needed."""
    name = CLOUD["name"] if cloud else f"{MODEL['base']} + {MODEL['lora']}"
    short = "FLUX.1 schnell" if cloud else "Segmind-Vega"
    return {"file": path.name, "kind": "drawing", "source": "ai_drawing", "title": subject,
            "source_page": CLOUD["page"] if cloud else MODEL["page"],
            # not "no third-party rights": a model licence doesn't settle every output question (review, 28 Oct)
            "licence": "AI-generated drawing; model licence Apache-2.0"
                       + ("; Cloudflare terms (read 28 Oct 2026): customer keeps rights in inputs and outputs" if cloud else ""),
            "model_licence": CLOUD["licence"] if cloud else MODEL["licence"], "licence_url": MODEL["licence_url"],
            "author": f"AI-generated with {name}",
            "attribution": f"Illustration generated with {short} (Apache-2.0): {subject}",
            "downloaded": dt.date.today().isoformat(), "prompt": f"{subject}, {STYLE}"}


def cloud_ready() -> bool:
    return bool(os.environ.get("CLOUDFLARE_API_TOKEN") and os.environ.get("CLOUDFLARE_ACCOUNT_ID"))


def cloud_draw(prompt: str, seed: int = 0, timeout: int = 90) -> bytes:
    """One FLUX.1 schnell drawing (JPEG bytes, about 1024x1024) from Workers AI's REST API."""
    import base64
    import urllib.request

    url = (f"https://api.cloudflare.com/client/v4/accounts/{os.environ['CLOUDFLARE_ACCOUNT_ID']}/ai/run/"
           f"{CLOUD['model']}")
    # Only prompt and steps are accepted ('seed' -> 400 "unevaluated properties", drawing test 40644346087)
    body = json.dumps({"prompt": prompt, "steps": CLOUD["steps"]}).encode()
    req = urllib.request.Request(url, data=body, headers={"Authorization": f"Bearer {os.environ['CLOUDFLARE_API_TOKEN']}",
                                                          "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        d = json.loads(r.read())
    if not d.get("success", True) or not (d.get("result") or {}).get("image"):
        raise RuntimeError(f"Workers AI: {str(d.get('errors') or d)[:300]}")
    return base64.b64decode(d["result"]["image"])


def _to_frame(raw: bytes, out: Path) -> None:
    """Centre-crop the square drawing to our 16:9 size."""
    import io

    from PIL import Image

    im = Image.open(io.BytesIO(raw)).convert("RGB")
    s = max(WIDTH / im.width, HEIGHT / im.height)
    im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    x, y = (im.width - WIDTH) // 2, (im.height - HEIGHT) // 2
    im.crop((x, y, x + WIDTH, y + HEIGHT)).save(out)


def make_cloud(jobs: list[dict], out_dir: Path) -> tuple[dict, dict]:
    """Draw on Workers AI; stop at the first quota/limit error (the rest fall back to the local model)."""
    import time
    import urllib.error

    drawn, log = {}, {"backend": "cloudflare", "seconds": {}, "errors": []}
    for i, job in enumerate(jobs[:CLOUD_DAILY_MAX]):
        t = time.perf_counter()
        try:
            raw = cloud_draw(f"{job['subject']}, {STYLE}", 1000 + i)
        except urllib.error.HTTPError as e:
            log["errors"].append(f"{job['id']}: HTTP {e.code} {e.read()[:200]!r}")
            if e.code in (401, 403, 429):  # no access or the free allocation is used up: stop asking
                break
            continue
        except Exception as e:  # noqa: BLE001
            log["errors"].append(f"{job['id']}: {e!r}"[:300])
            continue
        p = out_dir / f"{job['id']}.png"
        _to_frame(raw, p)
        (out_dir / f"{job['id']}.licence.json").write_text(json.dumps(record(p, job["subject"], cloud=True), indent=2))
        drawn[job["id"]] = str(p)
        log["seconds"][job["id"]] = round(time.perf_counter() - t, 1)
    log["drawn"] = len(drawn)
    return drawn, log


def make(jobs: list[dict], out_dir: Path, root: Path, budget_s: int = BUDGET_S) -> dict:
    """jobs: [{"id", "subject"}]. Returns {"drawn": {id: path}, "log": {...}}."""
    out_dir.mkdir(parents=True, exist_ok=True)
    if not jobs:
        return {"drawn": {}, "log": {"asked": 0}}
    cloud_drawn, cloud_log = {}, None
    if cloud_ready():
        cloud_drawn, cloud_log = make_cloud(jobs, out_dir)
        jobs = [j for j in jobs if j["id"] not in cloud_drawn]
        if not jobs:
            return {"drawn": cloud_drawn, "log": {"asked": len(cloud_drawn), "drawn": len(cloud_drawn), "cloud": cloud_log}}
    try:
        import importlib.util

        local_ok = importlib.util.find_spec("diffusers") is not None
    except Exception:  # noqa: BLE001
        local_ok = False
    if not local_ok:
        return {"drawn": cloud_drawn, "log": {"asked": len(jobs) + len(cloud_drawn), "drawn": len(cloud_drawn),
                                              "cloud": cloud_log, "local": "not installed"}}
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
    return {"drawn": {**cloud_drawn, **drawn},
            "log": {**{k: v for k, v in res.items() if k != "drawn"}, "asked": len(jobs) + len(cloud_drawn),
                    "drawn": len(drawn) + len(cloud_drawn), "cloud": cloud_log, **({"error": err} if err else {})}}


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
