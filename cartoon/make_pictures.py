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
    problems = scene_art.validate(res, texts)
    log = {"first_problems": problems}
    if problems:  # one automatic fix round, like the scene writer
        again = scene_art.plan_prompts(script, texts, a.topic,
                                       "\nFIX THESE PROBLEMS of your first answer:\n- " + "\n- ".join(problems) + "\n")
        p2 = scene_art.validate(again, texts)
        if len(p2) <= len(problems):
            res, problems = again, p2
    log["problems"] = problems
    for s in res["scenes"]:
        s["narration"] = texts.get(s["id"], "")
    (out / "pictures.json").write_text(json.dumps({"topic": a.topic, **res, "log": log}, indent=1, ensure_ascii=False))
    print(json.dumps(log, indent=1))
    print("cast:", [(c["id"], c["role"], c["costume"]) for c in res["cast"]], "changes:", res["changes"])
    for s in res["scenes"]:
        print(f"\n[{s['id']}] {s['shot']} who={s['who']} outfit={scene_art.outfit(res, s['id'])}\n  {scene_art.compose(s, res)[:300]}")


def load_plan(path: Path) -> dict:
    return scene_art.upgrade(json.loads(path.read_text()))


def pack(a) -> None:
    out = Path(a.out)
    data = load_plan(Path(a.redo) if a.redo else out / "pictures.json")
    scenes = data["scenes"]
    if a.only:
        scenes = [s for s in scenes if s["id"] in a.only.split(",")]
    assert scenes, "no scenes to draw"
    prompts = {"composed": True, "scenes": [{"id": s["id"], "prompt": scene_art.compose(s, data),
                                              "refs": scene_art.refs_for(s, data), "seed": s.get("seed", 30)}
                                             for s in scenes]}
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
    plan_ = load_plan(out / "pictures.json")
    if a.redo:  # a redraw round: only those scenes are looked at again (the cast sheet stays the whole plan's)
        plan_ = {**plan_, "scenes": load_plan(Path(a.redo))["scenes"]}
    by_id = {s["id"]: s for s in plan_["scenes"]}
    pics = {}
    for s in by_id:
        for pat in (f"flux2dev_fp16_{s}.*", f"flux2dev_{s}.*"):
            f = next(iter(sorted(Path(a.pictures).glob(pat))), None)
            if f:
                pics[s] = f
                break
    texts = {s["id"]: s.get("narration", "") for s in by_id.values()}
    res = scene_art.check_pictures(pics, plan_, texts)
    failed = {sid: p for sid, p in res.items() if p}
    missing = [s for s in by_id if s not in pics]
    (out / f"check_{a.level}.json").write_text(json.dumps({"problems": res, "missing": missing}, indent=1))
    redo = {**{k: v for k, v in plan_.items() if k != "scenes"},
            "scenes": [scene_art.redo_prompt(by_id[sid], p, a.level + 1) for sid, p in failed.items()]
                      + [by_id[m] for m in missing]}
    (out / f"redo_{a.level + 1}.json").write_text(json.dumps(redo, indent=1, ensure_ascii=False))
    print(f"passed {len(pics) - len(failed)} of {len(by_id)}; failed {sorted(failed)}; missing {missing}")
    for sid, p in failed.items():
        print(" ", sid, p)


def _plan(cast, scenes, changes=()):
    return {"cast": cast, "changes": list(changes), "scenes": scenes}


HERO = {"id": "hero", "name": "the stickman", "role": "hero", "look": "the plain white-headed stickman", "costume": "none"}
LONG = ("at a dark quiet harbour at night under bright stars, cold blue moonlight on the calm water, wide worried eyes "
        "and raised eyebrows, small things around him on the ground and a tall lamp behind him")


def _sc(i, who, shot="medium", extra=""):
    return {"id": i, "shot": shot, "who": who, "prompt": f"Picture {i}: the stickman stands {LONG} {extra}"}


def selftest(_a=None) -> None:
    """Plain-code test of the plan rules for FIVE different story shapes (no AI): a lone hero with a crowd, two
    friends, a costume change, a battle with a crowd and a named leader, a hero with background extras."""
    S = scene_art
    crowd = {"id": "crowd", "name": "passengers", "role": "crowd", "look": "a small group of plain stickmen", "costume": "none"}
    friend = {"id": "friend", "name": "Mia", "role": "supporting", "costume": "none",
              "look": "a stickman with a red scarf and a green backpack"}
    leader = {"id": "gen", "name": "the general", "role": "supporting", "costume": "none",
              "look": "a stickman with a tall black hat and a long grey coat"}
    # 1 Titanic: hero + crowd. The crowd rule appears only in scenes with the crowd.
    p1 = _plan([HERO, crowd], [_sc("s1", ["hero"]), _sc("s2", ["hero", "crowd"], "medium", "with a group of passengers behind")])
    t1 = {"s1": "a", "s2": "b"}
    assert S.validate(p1, t1) == [], S.validate(p1, t1)
    assert "NO real humans" not in S.compose(p1["scenes"][0], p1) and "NO real humans" in S.compose(p1["scenes"][1], p1)
    assert S.refs_for(p1["scenes"][0], p1) == ["stickman_front"]
    # 2 two friends: both described word for word in every scene they share; only the hero has a reference
    p2 = _plan([HERO, friend], [_sc("s1", ["hero", "friend"]), _sc("s2", ["hero"]), _sc("s3", ["friend"], "close")])
    t2 = {"s1": "a", "s2": "b", "s3": "c"}
    assert S.validate(p2, t2) == [], S.validate(p2, t2)
    c1, c3 = S.compose(p2["scenes"][0], p2), S.compose(p2["scenes"][2], p2)
    assert "a red scarf and a green backpack" in c1 and "a red scarf and a green backpack" in c3
    assert "the same simple stickman" not in c3 and "hero is the same simple stickman" in c1  # no hero text without the hero
    assert S.refs_for(p2["scenes"][0], p2) == ["stickman_front"] and S.refs_for(p2["scenes"][2], p2) == []
    # 3 costume change: declared with a reason; scenes 3-4 use the astronaut picture, the others the plain stickman
    p3 = _plan([HERO], [_sc(f"s{i}", ["hero"]) for i in range(1, 6)] ,
               [{"scenes": ["s3", "s4"], "costume": "astronaut", "reason": "he flies to the Moon"}])
    t3 = {f"s{i}": "x" for i in range(1, 6)}
    assert S.validate(p3, t3) == [], S.validate(p3, t3)
    assert [S.outfit(p3, f"s{i}") for i in range(1, 6)] == ["none", "none", "astronaut", "astronaut", "none"]
    assert S.refs_for(p3["scenes"][2], p3) == ["costume_astronaut"] and "white space suit" in S.compose(p3["scenes"][2], p3)
    assert "white space suit" not in S.compose(p3["scenes"][0], p3)
    # 3b a change with no reason or an unknown scene is refused
    bad = _plan([HERO], p3["scenes"], [{"scenes": ["s9"], "costume": "astronaut", "reason": " "}])
    b = S.validate(bad, t3)
    assert any("no reason" in x for x in b) and any("unknown scene" in x for x in b), b
    # 4 battle: hero + named leader + crowd (several kinds of characters are fine)
    p4 = _plan([HERO, leader, crowd], [_sc("s1", ["hero", "gen", "crowd"]), _sc("s2", ["gen"], "close")])
    assert S.validate(p4, {"s1": "a", "s2": "b"}) == []
    # 5 hero + extras only in some scenes, costume chosen for the whole story
    p5 = _plan([dict(HERO, costume="diver"), crowd], [_sc("s1", ["hero"]), _sc("s2", ["hero", "crowd"])])
    assert S.refs_for(p5["scenes"][0], p5) == S.refs_for(p5["scenes"][1], p5) == ["costume_diver"]
    # the rules that must still refuse bad plans
    assert any("exactly one hero" in x for x in S.validate(_plan([HERO, dict(HERO, id="h2")], [_sc("s1", ["hero"])]), {"s1": "a"}))
    assert any("not in the cast" in x for x in S.validate(_plan([HERO], [_sc("s1", ["hero", "ghost"])]), {"s1": "a"}))
    assert any("only the hero uses a costume" in x for x in S.validate(_plan([HERO, dict(friend, costume="winter")], [_sc("s1", ["hero"])]), {"s1": "a"}))
    assert any("too short" in x for x in S.validate(_plan([HERO], [dict(_sc("s1", ["hero"]), prompt="a stickman")]), {"s1": "a"}))
    ph = S.validate(_plan([HERO], [dict(_sc("s1", ["hero"]), prompt="a photo of the stickman with a sign saying TITANIC " + LONG)]), {"s1": "a"})
    assert any("photo" in x for x in ph) and any("text" in x for x in ph), ph
    assert any("no prompt" in x for x in S.validate(_plan([HERO], []), {"s1": "a"}))
    assert any("wide shots" in x for x in S.validate(_plan([HERO], [dict(_sc(f"w{i}", ["hero"], "wide"), prompt=f"w{i} " * 3 + LONG + f" n{i} " * 4) for i in range(3)]), {f"w{i}": "t" for i in range(3)}))
    gore = S.validate(_plan([HERO], [dict(_sc("s1", ["hero"]), prompt="Picture s1: the stickman floats in space and blood sprays from his suit " + LONG)]), {"s1": "a"})
    assert any("blood or gore" in x for x in gore), gore
    r5 = S.redo_prompt(p1["scenes"][0], ["blood or gore is drawn; show danger without blood"], 1)
    assert "no blood" in S.compose(r5, p1)
    # old-format plans (Titanic first run) still load
    old = S.upgrade({"scenes": [{"id": "a", "shot": "wide", "costume": "winter", "others": "nobody", "prompt": "x"},
                                {"id": "b", "shot": "wide", "costume": "winter", "others": "5 stickmen", "prompt": "y"}]})
    assert old["cast"][0]["costume"] == "winter" and old["scenes"][1]["who"] == ["hero", "crowd"]
    # a redraw gets stronger, with a new seed
    r1 = S.redo_prompt(p1["scenes"][1], ["5 real-looking people are drawn; every person must be a stickman"], 1)
    assert "IMPORTANT" in S.compose(r1, p1) and r1["seed"] == 31
    r2 = S.redo_prompt(r1, ["2 real-looking people are drawn"], 2)
    assert "at most 5" in r2["prompt"] and r2["seed"] == 32
    r3 = S.redo_prompt(p1["scenes"][0], ["text in the picture: SOS"], 1)
    assert "no writing of any kind" in S.compose(r3, p1)
    r4 = S.redo_prompt(p2["scenes"][0], ["the character Mia is missing"], 1)
    assert "character descriptions exactly" in S.compose(r4, p2)
    print("selftest: all checks passed")


# Labelled pictures for the checker test (31 Oct, written BEFORE the checker ran): the real-people crowds must fail,
# the stickman pictures must pass. Files are in bench-results scene-art-test/pictures/.
EXPECT = {"flux2dev_04": False, "flux2dev_fp16_04": False,  # crowds of real-looking people with a few stickmen
          "flux2dev_fp16_02": True, "flux2dev_fp16_07": True, "flux2dev_01": True}


def checktest(a) -> None:
    pics = {n: next(iter(sorted(Path(a.pictures).glob(f"{n}.*"))), None) for n in EXPECT}
    pics = {n: f for n, f in pics.items() if f}
    plan_ = _plan([HERO, {"id": "crowd", "name": "extras", "role": "crowd", "look": "plain stickmen", "costume": "none"}],
                  [{"id": n, "shot": "medium", "who": ["hero"], "prompt": "the stickman in the scene described by the narration"}
                   for n in pics])
    res = scene_art.check_pictures(pics, plan_, {n: "" for n in pics})
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
