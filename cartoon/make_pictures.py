"""Scene pictures for a Short with FLUX.2 [dev] 32B fp16 on Kaggle (owner decision 31 Oct 2026).

  python cartoon/make_pictures.py plan  --script meta/script.json --topic "..." --out pics        # prompts (1-2 AI requests)
  python cartoon/make_pictures.py pack  --out pics [--only step1,step3] [--level 1]                # k/run.py for Kaggle
  python cartoon/make_pictures.py check --out pics --pictures DIR [--level 0]                      # looks at every picture
  python cartoon/make_pictures.py selftest                                                         # plain code, no AI
  python cartoon/make_pictures.py checktest --pictures DIR                                         # the picture checker on labelled pictures

`plan` writes pics/pictures.json (the scenes with their detailed prompts, plain-code checked, one fix round).
`pack` writes pics/k/ (run.py + kernel-metadata.json) with the final composed prompts; the workflow pushes it.
`check` looks at the drawn pictures; the ones that fail get a stronger prompt in pics/redo_<level>.json
(pack --redo pics/redo_1.json draws only those again, a new seed each time). Kaggle holds no keys.
"""
from __future__ import annotations

import argparse
import base64
import io
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from yt_auto import scene_art  # noqa: E402

REFS = ROOT / "cartoon" / "character_refs"


def build_refs(names: set[str]) -> dict[str, str]:
    """base64 JPEGs: stickman_front, and costume_<name> = the costume picture alone, ONE reference
    (two references ran out of memory on the T4s, and stickman + costume side by side made FLUX draw two heroes, 31 Oct)."""
    from PIL import Image

    def enc(im) -> str:
        b = io.BytesIO()
        im.save(b, "JPEG", quality=92)
        return base64.b64encode(b.getvalue()).decode()

    front = Image.open(REFS / "stickman_front.png").convert("RGB")
    out = {}
    for n in sorted(names):
        if n == "stickman_front":
            im = front.copy()
            im.thumbnail((512, 512))
        else:
            # the costume picture ALONE (it already shows the hero's face): next to the plain stickman FLUX drew two heroes
            im = Image.open(REFS / "costumes" / f"{n}.png").convert("RGB")
            im.thumbnail((512, 512))
        out[n] = enc(im)
    return out


def plan(a) -> None:
    from yt_auto import cartoon
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    script = json.loads(Path(a.script).read_text())
    texts = cartoon.scene_texts(script)
    res = scene_art.plan_prompts(script, texts, a.topic)
    problems = scene_art.validate(res["scenes"], texts)
    log = {"first_problems": problems}
    if problems:  # one automatic fix round, like the scene writer
        again = scene_art.plan_prompts(script, texts, a.topic + "\n\nFIX THESE PROBLEMS of your first answer:\n- " + "\n- ".join(problems))
        p2 = scene_art.validate(again["scenes"], texts)
        if len(p2) <= len(problems):
            res, problems = again, p2
    log["problems"] = problems
    for s in res["scenes"]:
        s["narration"] = texts.get(s["id"], "")
    (out / "pictures.json").write_text(json.dumps({"topic": a.topic, "scenes": res["scenes"], "log": log}, indent=1, ensure_ascii=False))
    print(json.dumps(log, indent=1))
    for s in res["scenes"]:
        print(f"\n[{s['id']}] {s['shot']} costume={s['costume']} others={s['others']}\n  {scene_art.compose(s)[:300]}")


def pack(a) -> None:
    out = Path(a.out)
    data = json.loads((Path(a.redo) if a.redo else out / "pictures.json").read_text())
    scenes = data["scenes"]
    if a.only:
        scenes = [s for s in scenes if s["id"] in a.only.split(",")]
    assert scenes, "no scenes to draw"
    prompts = {"composed": True, "scenes": [{"id": s["id"], "prompt": scene_art.compose(s), "refs": scene_art.refs_for(s),
                                              "seed": s.get("seed", 30)} for s in scenes]}
    refs = build_refs({r for s in prompts["scenes"] for r in s["refs"]})
    opts = {"dtype": "fp16", "scenes": [s["id"] for s in scenes]}
    k = out / "k"
    k.mkdir(exist_ok=True)
    body = (ROOT / "kaggle" / "flux2_kernel.py").read_text()
    (k / "run.py").write_text(f"import json as _j\nPROMPTS = _j.loads({json.dumps(prompts)!r})\nREFS = {refs!r}\n"
                              f"OPTIONS = _j.loads({json.dumps(opts)!r})\n" + body)
    user = os.environ.get("KAGGLE_USERNAME", "USER")
    (k / "kernel-metadata.json").write_text(json.dumps({
        "id": f"{user}/yt-auto-flux2", "title": "yt-auto flux2", "code_file": "run.py", "language": "python",
        "kernel_type": "script", "is_private": "true", "enable_gpu": "true", "enable_internet": "true",
        "machine_shape": "NvidiaTeslaT4", "dataset_sources": [], "competition_sources": [], "kernel_sources": [],
        "model_sources": []}, indent=1))
    print("packed", len(scenes), "scenes;", (k / "run.py").stat().st_size, "bytes")


def check(a) -> None:
    out = Path(a.out)
    data = json.loads((out / "pictures.json").read_text())
    by_id = {s["id"]: s for s in data["scenes"]}
    if a.redo:  # a redraw round: only those scenes are looked at again
        by_id = {s["id"]: s for s in json.loads(Path(a.redo).read_text())["scenes"]}
    pics = {}
    for s in by_id:
        for pat in (f"flux2dev_fp16_{s}.*", f"flux2dev_{s}.*"):
            f = next(iter(sorted(Path(a.pictures).glob(pat))), None)
            if f:
                pics[s] = f
                break
    texts = {s["id"]: s.get("narration", "") for s in by_id.values()}
    res = scene_art.check_pictures(pics, by_id, texts)
    failed = {sid: p for sid, p in res.items() if p}
    missing = [s for s in by_id if s not in pics]
    (out / f"check_{a.level}.json").write_text(json.dumps({"problems": res, "missing": missing}, indent=1))
    redo = {"scenes": [scene_art.redo_prompt(by_id[sid], p, a.level + 1) for sid, p in failed.items()]}
    redo["scenes"] += [by_id[m] for m in missing]
    (out / f"redo_{a.level + 1}.json").write_text(json.dumps(redo, indent=1, ensure_ascii=False))
    print(f"passed {len(pics) - len(failed)} of {len(by_id)}; failed {sorted(failed)}; missing {missing}")
    for sid, p in failed.items():
        print(" ", sid, p)


def selftest(_a=None) -> None:
    """Plain-code test of compose / validate / redo (no AI). Written before the code, 31 Oct."""
    ok = {"id": "step1", "shot": "medium", "costume": "none", "others": "a small group of 6 stickmen",
          "prompt": "the tilted deck of a sinking 1912 ocean liner at night under bright stars, a small group of six passengers "
                    "waiting, our stickman in the front looking at two lifeboats with wide worried eyes and raised eyebrows, "
                    "cold blue moonlight on the dark sea behind him"}
    texts = {"step1": "The ship carries lifeboats for only one-third of the people."}
    t = scene_art.compose(ok)
    assert "NO real humans" in t and "no letters" in t and "round white head" in t, t
    assert scene_art.refs_for(ok) == ["stickman_front"]
    # a crowd word in the prompt adds the stickman crowd rule even when 'others' says nobody
    sneaky = dict(ok, others="nobody")
    assert "NO real humans" in scene_art.compose(sneaky)
    # no people at all: no crowd rule
    alone = dict(ok, others="nobody", prompt="the stickman stands alone on an empty dark beach at night looking up at the moon, "
                 "his arms hanging down and a small worried mouth, soft blue light, a calm sea and a few rocks behind him")
    assert "NO real humans" not in scene_art.compose(alone)
    # costume
    dv = dict(ok, costume="diver")
    assert scene_art.refs_for(dv) == ["costume_diver"] and "brass diving helmet" in scene_art.compose(dv)
    assert scene_art.validate([ok], texts) == [], scene_art.validate([ok], texts)
    bad = scene_art.validate([dict(ok, prompt="a photo of a ship with a sign saying TITANIC"), ], texts)
    assert any("photo" in p for p in bad) and any("text" in p for p in bad) and any("too short" in p for p in bad), bad
    assert scene_art.validate([dict(ok, costume="clown")], texts)
    two = scene_art.validate([ok, dict(ok, id="step2", costume="winter")], {"step1": "a", "step2": "b"})
    assert any("outfit" in p for p in two), two
    assert any("no prompt" in p for p in scene_art.validate([], texts))
    assert any("wide shots" in p for p in scene_art.validate([dict(ok, id=f"w{i}", shot="wide", prompt=ok["prompt"] + str(i) * 3 + f" x{i}" * 12) for i in range(3)], {f"w{i}": "t" for i in range(3)}))
    # redraw gets stronger
    r1 = scene_art.redo_prompt(ok, ["5 real-looking people are drawn; every person must be a stickman"], 1)
    assert "IMPORTANT" in scene_art.compose(r1) and r1["seed"] == 31
    r2 = scene_art.redo_prompt(r1, ["2 real-looking people are drawn"], 2)
    assert "at most 5" in r2["prompt"] and r2["seed"] == 32
    r3 = scene_art.redo_prompt(ok, ["text in the picture: SOS"], 1)
    assert "no writing of any kind" in scene_art.compose(r3)
    print("selftest: all checks passed")


# Labelled pictures for the checker test (31 Oct, written BEFORE the checker ran): the real-people crowds must fail,
# the stickman pictures must pass. Files are in bench-results scene-art-test/pictures/.
EXPECT = {"flux2dev_04": False, "flux2dev_fp16_04": False,  # crowds of real-looking people with a few stickmen
          "flux2dev_01": True, "flux2dev_fp16_01": True, "flux2dev_fp16_02": True, "flux2dev_fp16_07": True,
          "flux2dev_07": True}


def checktest(a) -> None:
    pics = {n: next(iter(sorted(Path(a.pictures).glob(f"{n}.*"))), None) for n in EXPECT}
    pics = {n: f for n, f in pics.items() if f}
    scenes = {n: {"id": n, "prompt": "the stickman in the scene described by the narration"} for n in pics}
    res = scene_art.check_pictures(pics, scenes, {n: "" for n in pics})
    right = {n: (not res[n]) == EXPECT[n] for n in pics}
    for n in pics:
        print(f"{n}: expected {'pass' if EXPECT[n] else 'FAIL'}; got {'pass' if not res[n] else 'FAIL'} {res[n]}")
    print(f"checker test: {sum(right.values())} of {len(right)} right")
    Path(a.out).mkdir(parents=True, exist_ok=True)
    (Path(a.out) / "checktest.json").write_text(json.dumps({"expect": EXPECT, "got": res, "right": right}, indent=1))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("action", choices=["plan", "pack", "check", "selftest", "checktest"])
    ap.add_argument("--script")
    ap.add_argument("--topic", default="")
    ap.add_argument("--out", default="out/pics")
    ap.add_argument("--only")
    ap.add_argument("--redo")
    ap.add_argument("--pictures")
    ap.add_argument("--level", type=int, default=0)
    a = ap.parse_args()
    {"plan": plan, "pack": pack, "check": check, "selftest": selftest, "checktest": checktest}[a.action](a)


if __name__ == "__main__":
    main()
