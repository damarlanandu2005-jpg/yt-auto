"""Drawing test: can a free open image model on a GitHub runner (CPU only) make good drawings for our videos?

Records for each model: its licence (from Hugging Face, before we rely on it), seconds per drawing,
memory, and saves the drawings plus one contact sheet. No Gemini quota: the prompts are written here.

    python phase5/drawing_test.py OUT [--model segmind-vega] [--n 10]
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import resource
import time
import urllib.request
from pathlib import Path

STYLE = ("detailed ink illustration, white and grey pen linework on a pure black background, "
         "one bright red accent, high contrast, clean composition, no text, no letters")
PROMPTS = [  # one GPS scene, ten shots
    "satellites orbiting planet Earth, thin signal lines reaching down to a phone on the ground",
    "a hand holding a smartphone showing a map with a location pin",
    "cutaway of a navigation satellite with a glowing atomic clock inside",
    "three overlapping circles on a map meeting at one point, a location pin where they cross",
    "a radio wave travelling from a satellite in space down to a city, speed lines",
    "a sailing ship on the ocean at night, a satellite high above it",
    "two clocks side by side, one in orbit and one on the ground, showing slightly different times",
    "a ground control station with large dish antennas pointing at the sky",
    "a car dashboard with a navigation screen on a winding mountain road",
    "a ring of many satellites around planet Earth, seen from far away",
]
MODELS = {
    # SDXL distilled to 745M + LCM LoRA (4 steps). Licences checked from the model cards below.
    "segmind-vega": {"base": "segmind/Segmind-Vega", "lora": "segmind/Segmind-VegaRT", "steps": 4, "guidance": 0.0},
}


def card(repo: str) -> dict:
    req = urllib.request.Request(f"https://huggingface.co/api/models/{repo}", headers={"User-Agent": "yt-auto drawing test"})
    with urllib.request.urlopen(req, timeout=30) as r:
        d = json.loads(r.read())
    return {"repo": repo, "license": (d.get("cardData") or {}).get("license"), "gated": d.get("gated"),
            "tags": [t for t in d.get("tags", []) if t.startswith("license")], "sha": d.get("sha"),
            "last_modified": d.get("lastModified")}


def peak_mb() -> int:
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss // 1024


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--model", default="segmind-vega")
    ap.add_argument("--n", type=int, default=10)
    ap.add_argument("--width", type=int, default=1024)
    ap.add_argument("--height", type=int, default=576)
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    cfg = MODELS[a.model]
    res: dict = {"model": a.model, "config": cfg, "style": STYLE, "size": [a.width, a.height],
                 "cpu": platform.processor() or platform.machine(), "cores": os.cpu_count(),
                 "ram_gb": round(os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES") / 2**30, 1)}
    res["licences"] = [card(cfg["base"])] + ([card(cfg["lora"])] if cfg.get("lora") else [])
    (out / "result.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(res["licences"], indent=1), flush=True)

    import torch
    from diffusers import LCMScheduler, StableDiffusionXLPipeline

    torch.set_num_threads(os.cpu_count() or 4)
    t0 = time.perf_counter()
    pipe = StableDiffusionXLPipeline.from_pretrained(cfg["base"], torch_dtype=torch.float32)
    if cfg.get("lora"):
        pipe.load_lora_weights(cfg["lora"])
        pipe.fuse_lora()
        pipe.scheduler = LCMScheduler.from_config(pipe.scheduler.config)
    res["load_s"] = round(time.perf_counter() - t0, 1)
    print(f"loaded in {res['load_s']} s, peak {peak_mb()} MB", flush=True)
    rows, files = [], []
    for i, p in enumerate(PROMPTS[: a.n], 1):
        t = time.perf_counter()
        img = pipe(prompt=f"{p}, {STYLE}", num_inference_steps=cfg["steps"], guidance_scale=cfg["guidance"],
                   width=a.width, height=a.height, generator=torch.Generator().manual_seed(i)).images[0]
        f = out / f"d{i:02}.jpg"
        img.save(f, quality=90)
        files.append(f)
        rows.append({"file": f.name, "prompt": p, "seconds": round(time.perf_counter() - t, 1)})
        print(f"{f.name}: {rows[-1]['seconds']} s", flush=True)
        res.update(drawings=rows, peak_mb=peak_mb())
        (out / "result.json").write_text(json.dumps(res, indent=1))
    secs = [r["seconds"] for r in rows]
    res["avg_seconds"] = round(sum(secs) / len(secs), 1)
    res["peak_mb"] = peak_mb()
    (out / "result.json").write_text(json.dumps(res, indent=1))

    from PIL import Image
    w, h = 512, 288
    sheet = Image.new("RGB", (2 * w, ((len(files) + 1) // 2) * h))
    for i, f in enumerate(files):
        sheet.paste(Image.open(f).resize((w, h)), ((i % 2) * w, (i // 2) * h))
    sheet.save(out / "sheet.jpg", quality=85)
    print(f"average {res['avg_seconds']} s per drawing, peak {res['peak_mb']} MB", flush=True)


if __name__ == "__main__":
    main()
