"""Scene-picture test (owner 'go', 30 Oct 2026): helpers for .github/workflows/scene-art-test.yml.

    python cartoon/scene_art_test/run.py cloudflare --out OUT   # 8 FLUX schnell pictures (words only) + model list
    python cartoon/scene_art_test/run.py sheet --out OUT DIR... # one contact sheet: a row per way, a column per scene

Needs CLOUDFLARE_API_TOKEN / CLOUDFLARE_ACCOUNT_ID for `cloudflare` (8 pictures, about 640 of the free 10,000
neurons). The Kaggle way runs in kaggle/scene_art_kernel.py; the ChatGPT way is the owner's zip (CHATGPT.md).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))


def cloudflare(out: Path) -> None:
    from yt_auto import drawings

    P = json.loads((HERE / "prompts.json").read_text())
    out.mkdir(parents=True, exist_ok=True)
    log = {"model": drawings.CLOUD["model"], "seconds": {}, "errors": []}
    for sc in P["scenes"]:
        t = time.time()
        try:
            raw = drawings.cloud_draw(f"{sc['prompt']}. {P['character']}. {P['style']}")
            (out / f"flux_{sc['id']}.jpg").write_bytes(raw)
        except Exception as e:  # noqa: BLE001  one failed picture is recorded, the rest go on
            body = e.read().decode(errors="replace")[:400] if hasattr(e, "read") else ""
            log["errors"].append(f"{sc['id']}: {e!r} {body}"[:600])
            if "429" in str(e):  # first run 30 Oct: all 8 got 429; keep the reason, don't spend more
                break
        log["seconds"][sc["id"]] = round(time.time() - t, 1)
    # Which Cloudflare image models exist now: some may take a reference picture (the one we used takes words only)
    try:
        url = (f"https://api.cloudflare.com/client/v4/accounts/{os.environ['CLOUDFLARE_ACCOUNT_ID']}/ai/models/search?"
               + urllib.parse.urlencode({"task": "Text-to-Image"}))
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {os.environ['CLOUDFLARE_API_TOKEN']}"})
        with urllib.request.urlopen(req, timeout=60) as r:
            models = json.loads(r.read()).get("result", [])
        log["image_models"] = [{"name": m.get("name"), "description": (m.get("description") or "")[:300],
                                "properties": m.get("properties")} for m in models]
    except Exception as e:  # noqa: BLE001
        log["errors"].append(f"model list: {e!r}"[:300])
    # Input format of the FLUX.2 models that take reference pictures (their docs page is not reachable from
    # Claude's sandbox; the API describes itself)
    log["schemas"] = {}
    for m in ("@cf/black-forest-labs/flux-2-klein-4b", "@cf/black-forest-labs/flux-2-klein-9b",
              "@cf/black-forest-labs/flux-2-dev"):
        try:
            url = (f"https://api.cloudflare.com/client/v4/accounts/{os.environ['CLOUDFLARE_ACCOUNT_ID']}/ai/models/schema?"
                   + urllib.parse.urlencode({"model": m}))
            req = urllib.request.Request(url, headers={"Authorization": f"Bearer {os.environ['CLOUDFLARE_API_TOKEN']}"})
            with urllib.request.urlopen(req, timeout=60) as r:
                log["schemas"][m] = json.loads(r.read()).get("result")
        except Exception as e:  # noqa: BLE001
            log["schemas"][m] = f"error: {e!r}"[:300]
    (out / "cloudflare.json").write_text(json.dumps(log, indent=1))
    print(json.dumps({k: v for k, v in log.items() if k != "image_models"}, indent=1))
    print("image models:", [m["name"] for m in log.get("image_models", [])])


ROWS = [("flux_", "1. Cloudflare FLUX (words only)"), ("sdxl_ip0_", "2a. Kaggle SDXL (words only)"),
        ("sdxl_ip4_", "2b. Kaggle SDXL + logo 0.4"), ("sdxl_ip7_", "2c. Kaggle SDXL + logo 0.7"),
        ("sdxl_c5_", "2d. SDXL, logo character 0.5"), ("sdxl_c8_", "2e. SDXL, logo character 0.8"),
        ("sdxl_s10_", "2f. SDXL, logo style only"), ("flux2dev_", "4. FLUX.2 dev 32B + refs"),
        ("qwen_", "5. Qwen-Image-Edit 20B + refs"),
        ("flux2dev_fp16_", "A. FLUX.2 dev, 28 steps, fp16"), ("qwen8_bf16_", "B. Qwen 8-step (Lightning)"),
        ("qwen8_fp16_", "C. Qwen 8-step + fp16"),
        ("chatgpt_", "3. ChatGPT (owner)")]


def sheet(out: Path, dirs: list[Path]) -> None:
    from PIL import Image, ImageDraw, ImageFont

    P = json.loads((HERE / "prompts.json").read_text())
    ids = [s["id"] for s in P["scenes"]]
    files = {p.name: p for d in dirs if d.exists() for p in d.rglob("*") if p.suffix.lower() in (".png", ".jpg", ".jpeg")}
    rows = [(pre, label) for pre, label in ROWS if any(n.startswith(pre) for n in files)]
    tw, th, lab, top = 216, 384, 300, 40
    img = Image.new("RGB", (lab + tw * len(ids), top + th * len(rows)), "white")
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 20)
    except OSError:
        font = ImageFont.load_default()
    for j, i in enumerate(ids):
        d.text((lab + j * tw + 8, 10), f"scene {i}", fill="black", font=font)
    for r, (pre, label) in enumerate(rows):
        d.text((10, top + r * th + th // 2 - 10), label, fill="black", font=font)
        for j, i in enumerate(ids):
            f = next((files[n] for n in files if n.startswith(pre + i + ".")), None)
            if not f:
                continue
            p = Image.open(f).convert("RGB")
            # every way shown at 9:16: square pictures (FLUX) are centre-cropped, like the video would be
            want = 9 / 16
            if p.width / p.height > want:
                w = int(p.height * want)
                p = p.crop(((p.width - w) // 2, 0, (p.width + w) // 2, p.height))
            img.paste(p.resize((tw - 6, th - 6)), (lab + j * tw + 3, top + r * th + 3))
    out.mkdir(parents=True, exist_ok=True)
    img.save(out / "sheet.jpg", quality=88)
    print("sheet:", out / "sheet.jpg", img.size, [label for _, label in rows])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("action", choices=["cloudflare", "sheet"])
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("dirs", nargs="*", type=Path)
    a = ap.parse_args()
    cloudflare(a.out) if a.action == "cloudflare" else sheet(a.out, a.dirs)


if __name__ == "__main__":
    main()
