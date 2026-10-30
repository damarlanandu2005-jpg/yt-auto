# Runs ON KAGGLE (free GPU T4 x2), pushed by .github/workflows/scene-art-test.yml (engine = flux2).
# The workflow puts lines above this file: PROMPTS (cartoon/scene_art_test/prompts.json) and REFS (a dict of
# base64 PNG reference pictures from cartoon/character_refs/).
# Owner's choice (30 Oct): FLUX.2 [dev] 32B, the big multi-reference model, squeezed to fit Kaggle:
#   - the 4-bit copy diffusers/FLUX.2-dev-bnb-4bit (transformer and Mistral text encoder in 4-bit, VAE bf16)
#   - each big part is split over both T4s (14.6 GiB usable each): the text encoder reads all prompts first and is
#     freed, then the transformer is loaded over both cards
# Every scene gets the stickman reference picture(s) so he stays the same; one picture per scene, saved at once,
# so a run that hits Kaggle's time limit still leaves the finished pictures. Hardware is printed first.
# No keys are in this kernel. If Hugging Face refuses the download (gated model), the kernel reads HF_TOKEN from
# Kaggle's own secrets store (Add-ons -> Secrets in the notebook), which the owner adds by hand.
import base64
import os as _os
_os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")
import gc
import io
import json
import os
import shutil
import subprocess
import sys
import time
import traceback
from pathlib import Path

W = Path("/kaggle/working")
OUT = W / "scenes"
JOB = {"started": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "seconds": {}, "errors": [], "notes": []}
REPO = "diffusers/FLUX.2-dev-bnb-4bit"
SIZE = (576, 1024)       # 9:16; small first, the T4 is slow (upscaling comes later if the look is right)
STEPS = 28
GUIDANCE = 4.0
SEED = 30
BUDGET_S = 10.5 * 3600   # Kaggle stops a run at 12 h; stop drawing before that so job.json is written
T0 = time.time()


def save_job() -> None:
    JOB["pictures"] = sorted(p.name for p in OUT.glob("*.png")) if OUT.exists() else []
    W.mkdir(parents=True, exist_ok=True)
    (W / "job.json").write_text(json.dumps(JOB, indent=1))


def hardware() -> None:
    import psutil
    import torch
    JOB["hardware"] = {
        "gpus": [f"{torch.cuda.get_device_name(i)} {torch.cuda.get_device_properties(i).total_memory / 2**30:.1f} GB"
                 for i in range(torch.cuda.device_count())],
        "ram_gb": round(psutil.virtual_memory().total / 2**30, 1),
        "disk_free_gb": {p: round(shutil.disk_usage(p).free / 2**30, 1) for p in ("/kaggle/working", "/root", "/tmp")
                         if os.path.exists(p)},
        "bf16_supported": torch.cuda.is_bf16_supported() if torch.cuda.is_available() else None,
    }
    print("hardware:", JOB["hardware"], flush=True)


def hf_login_if_needed() -> None:
    from huggingface_hub import hf_hub_download
    try:
        hf_hub_download(REPO, "model_index.json")
        JOB["notes"].append(f"{REPO}: downloads without login")
        return
    except Exception as e:  # noqa: BLE001
        JOB["notes"].append(f"{REPO} without login: {type(e).__name__}: {str(e)[:200]}")
    try:
        from kaggle_secrets import UserSecretsClient
        os.environ["HF_TOKEN"] = UserSecretsClient().get_secret("HF_TOKEN")
        hf_hub_download(REPO, "model_index.json")
        JOB["notes"].append(f"{REPO}: downloads with the owner's HF_TOKEN from Kaggle secrets")
    except Exception as e:  # noqa: BLE001
        raise RuntimeError("GATED: Hugging Face needs the owner's login for FLUX.2 [dev] "
                           f"(accept the licence on the model page, add HF_TOKEN in Kaggle secrets): {str(e)[:300]}")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    t = time.time()
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-U", "diffusers", "transformers", "accelerate",
                    "safetensors", "huggingface-hub", "bitsandbytes", "psutil"], check=True)
    import importlib.metadata as md
    JOB["versions"] = {p: md.version(p) for p in ("diffusers", "transformers", "huggingface-hub", "bitsandbytes",
                                                  "torch")}
    import torch
    from PIL import Image
    hardware()
    hf_login_if_needed()
    from diffusers import Flux2Pipeline

    # T4 has no native bf16; FLUX can overflow in fp16. Try bf16 first (emulated, slower), record what happened.
    dtype = torch.bfloat16
    P = PROMPTS  # noqa: F821
    refs = {k: Image.open(io.BytesIO(base64.b64decode(v))).convert("RGB") for k, v in REFS.items()}  # noqa: F821
    for im in refs.values():
        im.thumbnail((512, 512))

    # Run 1 (30 Oct): loading the whole pipeline put the 4-bit transformer on GPU 0 alone and needed 15.0 GiB of
    # its 14.6. So each big part is split over BOTH T4s (device_map auto, ~13 GiB cap each), one at a time:
    # 1) the text encoder reads every prompt, then is freed; 2) the transformer is loaded and draws.
    cap = {0: "13GiB", 1: "13GiB"}
    from diffusers import Flux2Transformer2DModel
    import transformers
    from huggingface_hub import hf_hub_download
    t = time.time()
    lib, cls = json.loads(Path(hf_hub_download(REPO, "model_index.json")).read_text())["text_encoder"]
    te = getattr(transformers, cls).from_pretrained(REPO, subfolder="text_encoder", torch_dtype=dtype, device_map="auto",
                                   max_memory=cap)
    JOB["text_encoder_class"] = type(te).__name__
    pipe = Flux2Pipeline.from_pretrained(REPO, text_encoder=te, transformer=None, torch_dtype=dtype)
    JOB["text_encoder_load_s"] = round(time.time() - t)
    print("text encoder loaded", JOB["text_encoder_load_s"], "s", flush=True)
    t = time.time()
    embeds = {}
    for sc in P["scenes"]:
        text = f"{sc['prompt']}. {P['character']}. {P['style']}"
        with torch.no_grad():
            out = pipe.encode_prompt(prompt=text, device=torch.device("cuda:0"))
        embeds[sc["id"]] = (out[0] if isinstance(out, (tuple, list)) else out).to("cpu")
    JOB["encode_s"] = round(time.time() - t)
    pipe.text_encoder = None
    del te
    gc.collect()
    torch.cuda.empty_cache()

    t = time.time()
    # Run 2: 'auto' filled GPU 0 (12.9 GiB) and left 4.2 on GPU 1, so drawing had 0.8 GiB free on GPU 0 and every
    # attention step (2-3 GiB) ran out. Cap each card lower so the ~17 GiB transformer is spread ~8.5 + 8.5.
    tr = Flux2Transformer2DModel.from_pretrained(REPO, subfolder="transformer", torch_dtype=dtype, device_map="auto",
                                                 max_memory={0: "8.5GiB", 1: "10GiB"})
    pipe.transformer = tr
    pipe.vae.to("cuda:0")
    JOB["transformer_load_s"] = round(time.time() - t)
    JOB["vram_after_load_gb"] = [round(torch.cuda.memory_allocated(i) / 2**30, 1) for i in range(2)]
    print("transformer loaded", JOB["transformer_load_s"], "s", JOB["vram_after_load_gb"], flush=True)
    JOB["setup_s"] = round(time.time() - T0)
    for sc in P["scenes"]:
        if time.time() - T0 > BUDGET_S:
            JOB["notes"].append(f"stopped before scene {sc['id']}: time budget")
            break
        name = f"flux2dev_{sc['id']}.png"
        t = time.time()
        try:
            ref_list = [refs[r] for r in sc.get("refs", ["stickman_front"]) if r in refs]
            img = pipe(prompt_embeds=embeds[sc["id"]].to("cuda:0"), image=ref_list or None,
                       width=SIZE[0], height=SIZE[1], num_inference_steps=STEPS, guidance_scale=GUIDANCE,
                       generator=torch.Generator("cuda:0").manual_seed(SEED)).images[0]
            img.save(OUT / name)
            JOB["peak_vram_gb"] = [round(torch.cuda.max_memory_allocated(i) / 2**30, 1) for i in range(2)]
        except Exception as e:  # noqa: BLE001  one failed picture is recorded, the rest go on
            JOB["errors"].append(f"{name}: {traceback.format_exc()[-1200:]}")
            if "out of memory" in str(e).lower():
                torch.cuda.empty_cache()
        JOB["seconds"][name] = round(time.time() - t, 1)
        print(name, JOB["seconds"][name], flush=True)
        save_job()


try:
    main()
except Exception:  # noqa: BLE001  the collect step reads job.json either way
    JOB["errors"].append(traceback.format_exc()[-3000:])
finally:
    JOB["total_s"] = round(time.time() - T0)
    save_job()
    print(json.dumps(JOB)[:3000], flush=True)
