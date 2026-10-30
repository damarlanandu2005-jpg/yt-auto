# Runs ON KAGGLE (free GPU T4 x2), pushed by .github/workflows/scene-art-test.yml (engine = qwen).
# The workflow puts PROMPTS and REFS (base64 reference pictures from cartoon/character_refs/) above this file.
# Owner, 30 Oct: test Qwen-Image-Edit (20B, the edit version takes reference pictures, known for keeping a
# character the same) next to FLUX.2 [dev] 32B, on the same 8 Titanic scenes.
#   - model: the community 4-bit (NF4) build libaya/Qwen-Image-Edit-2511-4bit (whole pipeline, said to fit 16 GB)
#   - speed: try the Lightning LoRA (lightx2v/Qwen-Image-Edit-2511-Lightning, 8 steps, CFG 1); if it does not load
#     on the 4-bit model, fall back to 20 normal steps
#   - parts are moved to the GPU only while used (enable_model_cpu_offload)
# Hardware, versions, times and every error go to job.json; each picture is saved as soon as it is drawn.
# No keys or secrets are in this kernel.
import base64
import io
import json
import os
import shutil
import subprocess
import sys
import time
import traceback
from pathlib import Path

os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")
W = Path("/kaggle/working")
OUT = W / "scenes"
JOB = {"started": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "seconds": {}, "errors": [], "notes": []}
REPO = "libaya/Qwen-Image-Edit-2511-4bit"
LORA = "lightx2v/Qwen-Image-Edit-2511-Lightning"
SIZE = (576, 1024)
SEED = 30
BUDGET_S = 10.5 * 3600
T0 = time.time()


def save_job() -> None:
    JOB["pictures"] = sorted(p.name for p in OUT.glob("*.png")) if OUT.exists() else []
    W.mkdir(parents=True, exist_ok=True)
    (W / "job.json").write_text(json.dumps(JOB, indent=1))


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-U", "diffusers", "transformers", "accelerate",
                    "safetensors", "huggingface-hub", "bitsandbytes", "peft", "psutil"], check=True)
    import importlib.metadata as md
    JOB["versions"] = {p: md.version(p) for p in ("diffusers", "transformers", "huggingface-hub", "bitsandbytes",
                                                  "peft", "torch")}
    import psutil
    import torch
    from diffusers import QwenImageEditPlusPipeline
    from huggingface_hub import HfApi
    from PIL import Image
    JOB["hardware"] = {"gpus": [torch.cuda.get_device_name(i) for i in range(torch.cuda.device_count())],
                       "ram_gb": round(psutil.virtual_memory().total / 2**30, 1),
                       "disk_free_gb": round(shutil.disk_usage("/root").free / 2**30, 1)}

    t = time.time()
    pipe = QwenImageEditPlusPipeline.from_pretrained(REPO, torch_dtype=torch.bfloat16)
    JOB["load_s"] = round(time.time() - t)
    steps, cfg = 20, 4.0
    try:
        files = [f for f in HfApi().list_repo_files(LORA) if f.endswith(".safetensors")]
        JOB["lora_files"] = files
        pick = next((f for f in files if "8step" in f.lower() and "bf16" in f.lower()), None) or \
            next((f for f in files if "8step" in f.lower()), None) or (files[0] if files else None)
        pipe.load_lora_weights(LORA, weight_name=pick)
        steps, cfg = 8, 1.0
        JOB["notes"].append(f"Lightning LoRA loaded: {pick} -> 8 steps, CFG 1")
    except Exception as e:  # noqa: BLE001
        JOB["notes"].append(f"Lightning LoRA not used ({type(e).__name__}: {str(e)[:300]}) -> 20 steps, CFG 4")
    JOB["steps"], JOB["cfg"] = steps, cfg
    pipe.enable_model_cpu_offload()
    JOB["setup_s"] = round(time.time() - T0)
    print("setup", JOB["setup_s"], "s", JOB["notes"], flush=True)

    P = PROMPTS  # noqa: F821
    refs = {k: Image.open(io.BytesIO(base64.b64decode(v))).convert("RGB") for k, v in REFS.items()}  # noqa: F821
    for sc in P["scenes"]:
        if time.time() - T0 > BUDGET_S:
            JOB["notes"].append(f"stopped before scene {sc['id']}: time budget")
            break
        name = f"qwen_{sc['id']}.png"
        t = time.time()
        try:
            names = [r for r in sc.get("refs", ["stickman_front"]) if r in refs]
            ref_list = [refs[r] for r in names]
            which = " and ".join(f"picture {i + 1} ({'his costume' if 'costume' in n else 'our stickman'})"
                                 for i, n in enumerate(names))
            prompt = (f"Use {which} as the character reference: draw exactly this same stickman (same round white "
                      f"head, same eyes and eyebrows, same thin black stick body). New picture: {sc['prompt']}. "
                      f"{P['style']}")
            img = pipe(image=ref_list, prompt=prompt, negative_prompt=P["negative"], true_cfg_scale=cfg,
                       num_inference_steps=steps, width=SIZE[0], height=SIZE[1],
                       generator=torch.Generator("cpu").manual_seed(SEED)).images[0]
            img.save(OUT / name)
            JOB["peak_vram_gb"] = [round(torch.cuda.max_memory_allocated(i) / 2**30, 1)
                                   for i in range(torch.cuda.device_count())]
        except Exception as e:  # noqa: BLE001  one failed picture is recorded, the rest go on
            JOB["errors"].append(f"{name}: {traceback.format_exc()[-1500:]}")
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
