"""Picture prompts for the FLUX.2 [dev] scene pictures (owner decision 31 Oct 2026: FLUX.2 [dev] 32B fp16 on Kaggle).

One AI call writes a detailed picture prompt per scene of a checked Short script. Our own code then adds the fixed
rules the model must never forget (the stickman, the style, the stickman crowd, no text), picks the reference
picture, and checks the plain-code rules. After the pictures are drawn, check_pictures() looks at every one
(blind description first, then a text judge) and says which must be redrawn; redo_prompt() makes a stronger prompt
for a redraw. Scene 04 of the Titanic test showed why: a crowd of "passengers" was drawn as real people.
"""
from __future__ import annotations

import io
import re
from pathlib import Path

from .llm import LIGHT, QUALITY, VISION, llm

COSTUMES = ["ancient_egypt", "astronaut", "diver", "doctor", "explorer", "sailor", "soldier", "winter"]
# what the costume pictures in cartoon/character_refs/costumes/ show (given to the prompt writer)
COSTUME_LOOK = {"ancient_egypt": "ancient Egyptian clothes", "astronaut": "a white space suit with a helmet",
                "diver": "an old brass diving helmet and suit", "doctor": "a doctor's white coat",
                "explorer": "an explorer's hat and jacket", "sailor": "a sailor's cap and shirt",
                "soldier": "a soldier's helmet and uniform", "winter": "a thick winter coat, hat and scarf"}

CHARACTER = ("the same simple stickman in every picture: a big round white head with a thick black outline, two small "
             "black oval eyes, expressive black eyebrows, a small mouth, thin black stick arms and legs")
STYLE = ("flat 2D cartoon illustration, clean thick dark outlines, soft muted colours with simple flat shading, detailed "
         "full background, modern animated explainer style, vertical 9:16 portrait, no text, no letters, no numbers, "
         "no logos")
CROWD_RULE = ("EVERY other person in the picture is also a plain stickman exactly like him: a round white head with a "
              "black outline, two dot eyes, thin black stick body. NO real humans, no skin, no hair, no faces with "
              "noses, no realistic clothes on people")
CROWD_WORDS = re.compile(r"\b(crowd|passengers?|people|persons?|men|women|children|kids|workers|soldiers|villagers|"
                         r"audience|everyone|others?|survivors|sailors|crew|passers)\b", re.I)
BAD_WORDS = re.compile(r"\b(photo|photograph|photorealistic|realistic|3d|render|hyperreal\w*)\b", re.I)
TEXT_WORDS = re.compile(r"\b(sign|banner|poster|caption|label|title|text|letters?|words?|numbers?|logo|newspaper)\b", re.I)

SCHEMA = {"type": "object", "properties": {"scenes": {"type": "array", "items": {"type": "object", "properties": {
    "id": {"type": "string", "description": "the scene id given in the list"},
    "shot": {"type": "string", "enum": ["wide", "medium", "close"]},
    "costume": {"type": "string", "enum": ["none"] + COSTUMES},
    "others": {"type": "string", "description": "who else is in the picture, or 'nobody'. Other people are stickmen."},
    "prompt": {"type": "string", "description": "the detailed picture: where, the light, the camera, what the stickman "
                                                "does and feels (face and body), the props, the one thing the picture must show"}},
    "required": ["id", "shot", "costume", "others", "prompt"]}}}, "required": ["scenes"]}


def plan_prompts(script: dict, texts: dict[str, str], topic: str) -> dict:
    listing = "\n".join(f'- scene "{sid}": narration: "{t}"' for sid, t in texts.items())
    costumes = "\n".join(f"  {k}: {v}" for k, v in COSTUME_LOOK.items())
    prompt = f"""You write the picture prompts for a YouTube Short called "{topic}". A picture model will draw ONE vertical
picture per scene, from your prompt only. The hero is a plain stickman (a round white head, thin black stick body)
who lives through the story. Write a DETAILED prompt for every scene below, pin to pin, so nothing is left to chance:
- WHERE it is (the exact place, time of day, the weather), the LIGHT and colours, the CAMERA (wide / medium / close).
- WHAT THE STICKMAN DOES: his pose, where he stands in the picture, his face (eyes, eyebrows, mouth) and the feeling.
- The PROPS and the BIG THING the narration names (the iceberg, the ship...), with their size next to the stickman.
- Show, don't write: the picture tells the narration without any word, sign or number in it. Never ask for text.
- Other people are ALWAYS stickmen too, never real humans. Say how many (a small group of 6, not "a huge crowd") and
  what they do. If nobody else is there, say "nobody".
- COSTUME: the SAME choice in EVERY scene (the hero must look the same all through the Short). Default "none": the plain
  stickman is the channel's face. Choose one costume for ALL scenes only if the story physically needs it (a diving or
  space Short). A cold or night story does NOT need a winter coat. Costumes:
{costumes}
- The pictures must differ from each other: different camera, place or pose. The stickman must be easy to see: at
  least a third of the picture height in "medium" and "close" shots.
- Say only what the narration says or clearly implies. 40 to 90 words per prompt, plain words, no style words
  (the style is added by our code).

SCENES:
{listing}"""
    return llm(prompt, schema=SCHEMA, name="picture_prompts", temperature=0.6, models=QUALITY)


def refs_for(scene: dict) -> list[str]:
    return ["stickman_front"] if scene.get("costume", "none") == "none" else [f"costume_{scene['costume']}"]


def compose(scene: dict) -> str:
    """The final text given to FLUX: the model's scene prompt + our fixed rules (+ the hard sentences of a redraw)."""
    parts = [scene["prompt"].strip().rstrip(".")]
    others = scene.get("others", "nobody")
    people = others.lower() not in ("", "nobody", "none") or bool(CROWD_WORDS.search(scene["prompt"]))
    if people:
        parts.append(CROWD_RULE)
    parts.append(CHARACTER)
    if scene.get("costume", "none") != "none":
        parts.append(f"the stickman wears {COSTUME_LOOK[scene['costume']]}, drawn like the costume reference picture, "
                     "but he is still the same stickman with the same round white head and face")
    parts.append(STYLE)
    parts += scene.get("redo", [])  # only a redraw has these (redo_prompt)
    return ". ".join(parts)


def validate(scenes: list[dict], texts: dict[str, str]) -> list[str]:
    """Plain-code checks of the written prompts. Empty list = fine."""
    problems = []
    got = {s["id"] for s in scenes}
    for sid in texts:
        if sid not in got:
            problems.append(f"scene {sid}: no prompt written")
    for s in scenes:
        sid, p = s["id"], s["prompt"]
        if sid not in texts:
            problems.append(f"{sid}: not a scene of the script")
        if len(p.split()) < 25:
            problems.append(f"{sid}: prompt too short ({len(p.split())} words), details are left to chance")
        if BAD_WORDS.search(p):
            problems.append(f"{sid}: asks for a photo/realistic/3d look (the style is flat 2D cartoon)")
        if TEXT_WORDS.search(p):
            problems.append(f"{sid}: asks for text in the picture ({TEXT_WORDS.search(p).group(0)}): show, don't write")
        if s.get("costume", "none") not in ["none"] + COSTUMES:
            problems.append(f"{sid}: unknown costume {s.get('costume')}")
        if not re.search(r"stick", p, re.I) and s.get("shot") != "wide":
            problems.append(f"{sid}: the stickman is not mentioned")
    used = {s.get("costume", "none") for s in scenes}
    if len(used) > 1:
        problems.append(f"the hero changes outfit between scenes ({sorted(used)}): one costume (or none) for the whole Short")
    shots = [s["id"] for s in scenes if s.get("shot") == "wide"]
    if scenes and len(shots) > max(2, len(scenes) // 3):
        problems.append(f"too many wide shots ({len(shots)} of {len(scenes)}): the stickman gets tiny")
    seen = {}
    for s in scenes:
        key = " ".join(s["prompt"].lower().split()[:12])
        if key in seen:
            problems.append(f"{s['id']}: starts like {seen[key]} (pictures must differ)")
        seen[key] = s["id"]
    return problems


PIC_SEEN = {"type": "object", "properties": {"images": {"type": "array", "items": {"type": "object", "properties": {
    "n": {"type": "integer"}, "seen": {"type": "string"},
    "stickmen_count": {"type": "integer", "description": "how many stick figures with a plain round white head"},
    "realistic_people_count": {"type": "integer",
                               "description": "how many BACKGROUND people with skin-coloured faces, hair or noses (the main hero, even in a costume with a white round head, does not count)"},
    "text_seen": {"type": "string", "description": "every letter, number or word in the picture, or 'none'"}},
    "required": ["n", "seen", "stickmen_count", "realistic_people_count", "text_seen"]}}}, "required": ["images"]}
PIC_JUDGE = {"type": "object", "properties": {"scenes": {"type": "array", "items": {"type": "object", "properties": {
    "scene": {"type": "string"}, "ok": {"type": "boolean"},
    "problems": {"type": "array", "items": {"type": "string"}}}, "required": ["scene", "ok", "problems"]}}},
    "required": ["scenes"]}


def _thumb(path: Path) -> bytes:
    from PIL import Image
    im = Image.open(path).convert("RGB")
    im.thumbnail((432, 768))
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=85)
    return buf.getvalue()


def check_pictures(pics: dict[str, Path], scenes: dict[str, dict], texts: dict[str, str]) -> dict[str, list[str]]:
    """{scene id: [problems]}; an empty list = the picture passes. Counts come from the blind description, so the
    crowd rule is judged in plain code (any realistic person = fail), not by the text judge."""
    ids = list(pics)
    seen = llm(f"""Above are {len(ids)} cartoon pictures, each right after its label "Image n:". For EVERY image: say plainly
what is drawn (the place, the big objects, what the main stick figure does and feels). Count the stick figures
(a plain round white head with a black outline and thin stick body). Count any REAL-LOOKING people: skin-coloured
faces, hair, noses and realistic bodies. The main hero (a white round head, even when he wears a costume) is NOT one. Quote every letter, number or word drawn (or say none). Mention any
deformed face, hand or body.""", images=[(f"Image {i}:", _thumb(pics[s])) for i, s in enumerate(ids, 1)],
               schema=PIC_SEEN, name="art_seen", temperature=0.1, models=VISION, last_resort=True)
    by_n = {x["n"]: x for x in seen["images"]}
    out = {s: [] for s in ids}
    for i, sid in enumerate(ids, 1):
        x = by_n.get(i)
        if not x:
            out[sid].append("the picture was not described (fail closed)")
            continue
        if x["realistic_people_count"] > 0:
            out[sid].append(f"{x['realistic_people_count']} real-looking people are drawn; every person must be a stickman")
        if x["stickmen_count"] < 1:
            out[sid].append("no stickman is visible")
        if x["text_seen"].strip().lower() not in ("none", "", "no text", "n/a"):
            out[sid].append(f"text in the picture: {x['text_seen'][:60]}")
    listing = "\n".join(
        f'Scene {sid} (Image {i}): narration: "{texts.get(sid, "")}"\n  prompt asked for: {scenes[sid]["prompt"][:400]}\n'
        f'  described as: {(by_n.get(i) or {}).get("seen", "(none)")}' for i, sid in enumerate(ids, 1))
    res = llm(f"""Someone described each cartoon picture WITHOUT knowing the story. Judge each scene: a scene has a problem when the
picture does not show the thing the narration names or the prompt asked for, the stickman is tiny or hard to see, his
face does not show the feeling asked, a face/hand/body is deformed, or it looks the same as another scene. Be
concrete (say what to change). If a scene is fine: ok = true and no problems.

{listing}""", schema=PIC_JUDGE, name="art_judge", temperature=0.1, models=LIGHT, last_resort=True)
    for r in res["scenes"]:
        if r["scene"] in out and not r["ok"]:
            out[r["scene"]] += r["problems"] or ["judged not ok"]
    return out


def redo_prompt(scene: dict, problems: list[str], level: int) -> dict:
    """A stronger version of a scene for a redraw: adds hard sentences for the problems found. Returns a new scene."""
    new = dict(scene)
    redo = list(scene.get("redo", []))
    text = " ".join(problems).lower()
    if "real-looking" in text or "real people" in text:
        redo.append("IMPORTANT: draw only STICKMEN. Every single person, near or far, has a perfectly plain white circle "
                    "head, two dots for eyes and thin black line arms and legs. Not one person has hair, skin or a nose")
        if level >= 2:
            new["prompt"] = scene["prompt"] + " Only a few stickmen are in the picture (at most 5), and the picture is mostly the place."
            new["others"] = "at most 5 plain stickmen"
    if "text" in text:
        redo.append("There is absolutely no writing of any kind: no letters, numbers, signs or labels anywhere")
    if "tiny" in text or "hard to see" in text:
        redo.append("The stickman is large in the picture, filling at least a third of its height")
    if not redo:
        redo.append("Follow the scene description exactly: " + "; ".join(problems)[:300])
    new["redo"] = redo
    new["seed"] = 30 + level  # the kernel default seed is 30; every redraw level is a new picture
    return new
