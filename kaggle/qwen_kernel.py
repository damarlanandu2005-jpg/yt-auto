# Runs ON KAGGLE (free GPU T4 x2), pushed by .github/workflows/scene-art-test.yml (engine = qwen).
# The workflow puts PROMPTS and REFS (base64 reference pictures from cartoon/character_refs/) above this file.
# Owner, 30 Oct: test Qwen-Image-Edit (20B, the edit version takes reference pictures, known for keeping a
# character the same) next to FLUX.2 [dev] 32B, on the same 8 Titanic scenes.
#   - model: the community 4-bit (NF4) build libaya/Qwen-Image-Edit-2511-4bit (whole pipeline, said to fit 16 GB)
#   - speed: try the Lightning LoRA (lightx2v/Qwen-Image-Edit-2511-Lightning, 8 steps, CFG 1); if it does not load
#     on the 4-bit model, fall back to 20 normal steps
#   - text encoder on GPU 1, transformer spread over both T4s, VAE on GPU 0 (whole-pipeline loading ran out of memory)
# Hardware, versions, times and every error go to job.json; each picture is saved as soon as it is drawn.
# No keys or secrets are in this kernel.
import base64
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

os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")
W = Path("/kaggle/working")
OUT = W / "scenes"
JOB = {"started": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "seconds": {}, "errors": [], "notes": []}
REPO = "libaya/Qwen-Image-Edit-2511-4bit"
LORA = "lightx2v/Qwen-Image-Edit-2511-Lightning"
SIZE = (576, 1024)
SEED = 30
BUDGET_S = 10.5 * 3600
USE_LORA = False
T0 = time.time()


def set_compute(model, dtype) -> None:
    """Make the 4-bit (bitsandbytes) layers compute in `dtype` (T4: fp16 has tensor cores, bf16 does not)."""
    n = 0
    for m in model.modules():
        if hasattr(m, "compute_dtype") and m.__class__.__name__ == "Linear4bit":
            m.compute_dtype = dtype
            n += 1
    JOB.setdefault("compute_dtype", {})[str(dtype)] = f"{n} 4-bit layers"


def image_stats(img) -> dict:
    import numpy as np
    a = np.asarray(img.convert("L"), dtype="float32")
    st = {"mean": round(float(a.mean()), 1), "std": round(float(a.std()), 1)}
    st["looks_broken"] = st["std"] < 8 or st["mean"] < 6
    return st


def save_job() -> None:
    JOB["pictures"] = sorted(p.name for p in OUT.glob("*.png")) if OUT.exists() else []
    W.mkdir(parents=True, exist_ok=True)
    (W / "job.json").write_text(json.dumps(JOB, indent=1))


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-U", "diffusers", "transformers", "accelerate",
                    "safetensors", "huggingface-hub", "bitsandbytes", "peft", "psutil"], check=True)
    subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", "-q", "torchao"], check=False)
    # runs 4-6 (newer torchao + Lightning LoRA loaded) all failed with "Cannot copy out of meta tensor", even
    # after reloading the transformer; run 3 (neither) reached the last stage. So: no LoRA, no torchao upgrade.
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

    # Run 1 (30 Oct): from_pretrained put every 4-bit part on GPU 0 and ran out of memory while loading (needed
    # 4.6 GiB more, 3.7 free). So each part goes to its own place: the text encoder (Qwen2.5-VL, it also looks at
    # the reference pictures every call) on GPU 1, the transformer spread over both cards, the VAE on GPU 0.
    import diffusers
    import transformers
    from huggingface_hub import hf_hub_download
    t = time.time()
    index = json.loads(Path(hf_hub_download(REPO, "model_index.json")).read_text())
    JOB["model_index"] = {k: v for k, v in index.items() if isinstance(v, list)}
    te = getattr(transformers, index["text_encoder"][1]).from_pretrained(
        REPO, subfolder="text_encoder", torch_dtype=torch.bfloat16, device_map={"": "cuda:1"})
    # run 6: the pipeline works on GPU 0; this hook moves the text encoder's inputs to GPU 1 and its answer back
    from accelerate.hooks import AlignDevicesHook, add_hook_to_module
    add_hook_to_module(te, AlignDevicesHook(execution_device=torch.device("cuda:1"), io_same_device=True))
    JOB["text_encoder_gb"] = round(torch.cuda.memory_allocated(1) / 2**30, 1)
    print("text encoder on GPU 1:", JOB["text_encoder_gb"], "GiB", flush=True)
    def load_transformer(dtype=torch.bfloat16):
        if OPTIONS.get("single_gpu"):  # noqa: F821
            # Speed test 1 (30 Oct 19:53): the LoRA on the transformer split by accelerate (device_map) failed with
            # "Cannot copy out of meta tensor" even without torchao. Here: no device_map at all (no accelerate hooks),
            # the whole ~11 GiB 4-bit transformer on GPU 0; the reference pictures are 512x512 now, so attention
            # needs far less than run 8's 4.1 GiB.
            with torch.cuda.device(0):
                return getattr(diffusers, index["transformer"][1]).from_pretrained(
                    REPO, subfolder="transformer", torch_dtype=dtype)
        return getattr(diffusers, index["transformer"][1]).from_pretrained(
            REPO, subfolder="transformer", torch_dtype=dtype, device_map="auto",
            max_memory={0: "7.5GiB", 1: "9.5GiB"})  # run 9: 7+5 (and run 2: 8.5+3.5) failed the size check
        # runs 4-6 failed with meta tensors (cause: the Lightning LoRA / newer torchao, not the split); run 8 had the
        # whole ~11 GiB transformer on GPU 0 and attention needed 4.1 GiB with 2.6 free. Split it again ~7 + 4.
    tr = load_transformer()
    JOB["transformer_device"] = str(next(tr.parameters()).device)
    pipe = QwenImageEditPlusPipeline.from_pretrained(REPO, text_encoder=te, transformer=tr,
                                                     torch_dtype=torch.bfloat16)
    # run 3: the pipeline works on the text encoder's GPU (cuda:1) and the VAE on cuda:0 got the reference
    # pictures from cuda:1 ("Expected all tensors to be on the same device"): keep the VAE where the pipeline works
    type(pipe)._execution_device = property(lambda self: torch.device("cuda:0"))
    JOB["execution_device"] = str(pipe._execution_device)
    pipe.vae.to("cuda:0")
    # run 7: encoding the reference picture needed 5.1 GiB with only 2.0 free next to the 11 GiB transformer;
    # tiles and slices keep the VAE's working memory small
    # run 10: every step's attention needed 4.1 GiB (3.1 free) because the edit pipeline enlarges each reference
    # picture to ~1 megapixel (4096 extra tokens). 512x512 is plenty to show who the stickman is (~1024 tokens).
    import diffusers.pipelines.qwenimage.pipeline_qwenimage_edit_plus as qep
    JOB["vae_image_size_was"] = getattr(qep, "VAE_IMAGE_SIZE", None)
    if hasattr(qep, "VAE_IMAGE_SIZE"):
        qep.VAE_IMAGE_SIZE = 512 * 512
    pipe.vae.enable_tiling()
    pipe.vae.enable_slicing()
    JOB["load_s"] = round(time.time() - t)
    JOB["vram_after_load_gb"] = [round(torch.cuda.memory_allocated(i) / 2**30, 1) for i in range(2)]
    print("loaded", JOB["load_s"], "s", JOB["vram_after_load_gb"], flush=True)
    # Speed test (owner, 30 Oct): OPTIONS {"lora": true, "dtypes": ["bf16", "fp16"], "scenes": [...]}.
    # Runs 4-6 failed ("Cannot copy out of meta tensor") after the LoRA was loaded with a pip-upgraded torchao;
    # peft only wanted torchao because Kaggle has an old copy installed, so this run removes torchao instead.
    O = OPTIONS  # noqa: F821
    JOB["options"] = O
    P = dict(PROMPTS)  # noqa: F821
    if O.get("scenes"):
        P["scenes"] = [sc for sc in P["scenes"] if sc["id"] in O["scenes"]]
    refs = {k: Image.open(io.BytesIO(base64.b64decode(v))).convert("RGB") for k, v in REFS.items()}  # noqa: F821
    use_lora = bool(O.get("lora", USE_LORA))
    pick = None
    if use_lora:
        files = [f for f in HfApi().list_repo_files(LORA) if f.endswith(".safetensors")]
        JOB["lora_files"] = files
        pick = next((f for f in files if "8step" in f.lower() and "bf16" in f.lower()), None) or \
            next((f for f in files if "8step" in f.lower()), None)
    first = True
    for dname in O.get("dtypes", ["bf16"]):
        dtype = torch.float16 if dname == "fp16" else torch.bfloat16
        t = time.time()
        # a fresh transformer for every variant after the first (fp16 weights; no LoRA left from the last one)
        if not (first and dtype == torch.bfloat16):
            pipe.transformer = None
            gc.collect()
            torch.cuda.empty_cache()
            pipe.transformer = load_transformer(dtype)
        first = False
        set_compute(pipe.transformer, dtype)
        steps, cfg, prefix = 20, 4.0, f"qwen_{dname}_" if O.get("dtypes") else "qwen_"
        if use_lora:
            try:
                # speed tests 1-2: with the default low_cpu_mem_usage the LoRA layers start on the 'meta' device and
                # the 4-bit base layers' quant_state was left empty ("Cannot copy out of meta tensor"), split or not
                pipe.load_lora_weights(LORA, weight_name=pick, low_cpu_mem_usage=False)
                steps, cfg, prefix = 8, 1.0, f"qwen8_{dname}_"
                JOB["notes"].append(f"{dname}: Lightning LoRA loaded ({pick}) -> 8 steps, CFG 1")
            except Exception as e:  # noqa: BLE001
                JOB["notes"].append(f"{dname}: Lightning LoRA failed to load ({type(e).__name__}: {str(e)[:300]})")
                continue
        JOB.setdefault("variant_setup_s", {})[dname] = round(time.time() - t)
        print("variant", dname, "steps", steps, flush=True)
        for sc in P["scenes"]:
            if time.time() - T0 > BUDGET_S:
                JOB["notes"].append(f"stopped before {dname} scene {sc['id']}: time budget")
                break
            name = f"{prefix}{sc['id']}.png"
            t = time.time()
            try:
                names = [r for r in sc.get("refs", ["stickman_front"]) if r in refs]
                ref_list = [refs[r] for r in names]
                which = " and ".join(f"picture {k + 1} ({'his costume' if 'costume' in n else 'our stickman'})"
                                     for k, n in enumerate(names))
                prompt = (f"Use {which} as the character reference: draw exactly this same stickman (same round "
                          f"white head, same eyes and eyebrows, same thin black stick body). New picture: "
                          f"{sc['prompt']}. {P['style']}")
                img = pipe(image=ref_list, prompt=prompt, negative_prompt=P["negative"], true_cfg_scale=cfg,
                           num_inference_steps=steps, width=SIZE[0], height=SIZE[1],
                           generator=torch.Generator("cpu").manual_seed(SEED)).images[0]
                torch.cuda.synchronize()
                JOB.setdefault("gen_s", {})[name] = round(time.time() - t, 1)  # drawing only
                JOB.setdefault("image_stats", {})[name] = image_stats(img)
                img.save(OUT / name)
                JOB["peak_vram_gb"] = [round(torch.cuda.max_memory_allocated(k) / 2**30, 1)
                                       for k in range(torch.cuda.device_count())]
            except Exception as e:  # noqa: BLE001  one failed picture is recorded, the rest go on
                JOB["errors"].append(f"{name}: {traceback.format_exc()[-1500:]}")
                if "out of memory" in str(e).lower():
                    torch.cuda.empty_cache()
            JOB["seconds"][name] = round(time.time() - t, 1)
            print(name, JOB["seconds"][name], flush=True)
            save_job()
        if use_lora:
            try:
                pipe.unload_lora_weights()
            except Exception as e:  # noqa: BLE001
                JOB["notes"].append(f"unload LoRA: {type(e).__name__}")


try:
    main()
except Exception:  # noqa: BLE001  the collect step reads job.json either way
    JOB["errors"].append(traceback.format_exc()[-3000:])
finally:
    JOB["total_s"] = round(time.time() - T0)
    save_job()
    print(json.dumps(JOB)[:3000], flush=True)
