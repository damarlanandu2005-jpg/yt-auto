# Runs ON KAGGLE (free GPU T4), pushed by .github/workflows/scene-art-test.yml (action = start).
# The workflow puts two lines above this file: PROMPTS (cartoon/scene_art_test/prompts.json) and REF (the channel
# logo's stickman, base64 PNG).
# Scene-picture test (owner, 30 Oct): can an open image model draw a WHOLE scene with OUR stickman inside it?
# SDXL base 1.0 + IP-Adapter (the reference picture guides the character), 8 scenes at 3 reference strengths
# (0 = words only, 0.4, 0.7), the same seed for every scene. Results: /kaggle/working/scenes/*.png + job.json.
# No keys or secrets are in this kernel; models come from Hugging Face (public, no login).
# Licences: SDXL base 1.0 = CreativeML Open RAIL++-M (outputs may be used commercially, with use limits);
# IP-Adapter (h94) = Apache-2.0.
import base64
import io
import json
import subprocess
import sys
import time
import traceback
from pathlib import Path

W = Path("/kaggle/working")
OUT = W / "scenes"
JOB = {"started": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "seconds": {}, "errors": []}
SCALES = [0.0, 0.4, 0.7]
SEED = 30
SIZE = (768, 1344)  # SDXL's own 9:16-like size
STEPS = 30


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    t = time.time()
    # Upgrade these together so pip picks versions that fit each other: upgrading diffusers alone pulled
    # huggingface-hub 2.4, which Kaggle's transformers refused (first run, 30 Oct)
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-U", "diffusers", "transformers", "accelerate",
                    "safetensors", "huggingface-hub"], check=True)
    import importlib.metadata as md
    JOB["versions"] = {p: md.version(p) for p in ("diffusers", "transformers", "huggingface-hub", "torch")}
    import torch
    from diffusers import StableDiffusionXLPipeline
    from PIL import Image
    from transformers import CLIPVisionModelWithProjection

    JOB["gpu"] = torch.cuda.get_device_name(0) if torch.cuda.is_available() else "none"
    enc = CLIPVisionModelWithProjection.from_pretrained("h94/IP-Adapter", subfolder="models/image_encoder",
                                                        torch_dtype=torch.float16)
    pipe = StableDiffusionXLPipeline.from_pretrained("stabilityai/stable-diffusion-xl-base-1.0", image_encoder=enc,
                                                     torch_dtype=torch.float16, variant="fp16",
                                                     use_safetensors=True).to("cuda")
    pipe.load_ip_adapter("h94/IP-Adapter", subfolder="sdxl_models", weight_name="ip-adapter_sdxl_vit-h.safetensors")
    JOB["setup_s"] = round(time.time() - t)
    ref = Image.open(io.BytesIO(base64.b64decode(REF))).convert("RGB")  # noqa: F821
    P = PROMPTS  # noqa: F821
    for scale in SCALES:
        pipe.set_ip_adapter_scale(scale)
        for sc in P["scenes"]:
            name = f"sdxl_ip{int(scale * 10)}_{sc['id']}.png"
            t = time.time()
            try:
                img = pipe(prompt=f"{sc['prompt']}. {P['character']}. {P['style']}", negative_prompt=P["negative"],
                           ip_adapter_image=ref, width=SIZE[0], height=SIZE[1], num_inference_steps=STEPS,
                           guidance_scale=6.0, generator=torch.Generator("cuda").manual_seed(SEED)).images[0]
                img.save(OUT / name)
            except Exception as e:  # noqa: BLE001  one failed picture is recorded, the rest go on
                JOB["errors"].append(f"{name}: {e!r}"[:300])
            JOB["seconds"][name] = round(time.time() - t, 1)
            print(name, JOB["seconds"][name], flush=True)


try:
    main()
except Exception:  # noqa: BLE001  the collect step reads job.json either way
    JOB["errors"].append(traceback.format_exc()[-2000:])
finally:
    JOB["pictures"] = sorted(p.name for p in OUT.glob("*.png")) if OUT.exists() else []
    W.mkdir(parents=True, exist_ok=True)
    (W / "job.json").write_text(json.dumps(JOB, indent=1))
    print(json.dumps(JOB)[:2000], flush=True)
