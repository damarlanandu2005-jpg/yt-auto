"""Picture prompts for the FLUX.2 [dev] scene pictures (owner decision 31 Oct 2026: FLUX.2 [dev] 32B fp16 on Kaggle).

Story-driven, not rule-driven (owner, 31 Oct: rules that fit the Titanic must not control other Shorts). One AI call
writes a PLAN for the Short: a CAST SHEET (every character with a permanent id, role, look and costume), the
declared costume CHANGES with their reason, and per scene who is in it, the camera and a detailed prompt. Our code
then builds each FLUX prompt from that structured data (so a character's words are identical in every scene), picks
the reference picture, and checks consistency rules that fit any story (a character looks the same in every scene
unless the plan declares a change; every person in a scene is in the cast; every non-hero person is a stickman).
After the pictures are drawn, check_pictures() looks at every one (blind description first, then a judge that sees the
cast sheet and the scene plan) and says which must be redrawn; redo_prompt() makes a stronger prompt for a redraw.

plan = {"cast": [{id, name, role: hero|supporting|crowd, look, costume}], "changes": [{scenes, costume, reason}],
        "scenes": [{id, shot, who: [cast ids], prompt, narration}]}.   Only the hero has a reference picture
(the plain stickman, or a costume picture); other characters are kept by identical words in every scene.
"""
from __future__ import annotations

import io
import re
from pathlib import Path

from .llm import LIGHT, QUALITY, VISION, llm

COSTUMES = ["ancient_egypt", "astronaut", "diver", "doctor", "explorer", "sailor", "soldier", "winter"]
# what the costume pictures in cartoon/character_refs/costumes/ show (given to the plan writer)
COSTUME_LOOK = {"ancient_egypt": "ancient Egyptian clothes", "astronaut": "a white space suit with a helmet",
                "diver": "an old brass diving helmet and suit", "doctor": "a doctor's white coat",
                "explorer": "an explorer's hat and jacket", "sailor": "a sailor's cap and shirt",
                "soldier": "a soldier's helmet and uniform", "winter": "a thick winter coat, hat and scarf"}

CHARACTER = ("the hero is the same simple stickman in every picture: a big round white head with a thick black outline, "
             "two small black oval eyes, expressive black eyebrows, a small mouth, thin black stick arms and legs")
STYLE = ("flat 2D cartoon illustration, clean thick dark outlines, soft muted colours with simple flat shading, detailed "
         "full background, modern animated explainer style, vertical 9:16 portrait, no text, no letters, no numbers, "
         "no logos")
CROWD_RULE = ("EVERY other person in the picture is also a stickman: a round white head with a black outline, two dot "
              "eyes, thin black stick body (simple flat clothes only where described). NO real humans, no skin, no hair, "
              "no faces with noses, no realistic bodies")
CROWD_WORDS = re.compile(r"\b(crowd|passengers?|people|persons?|men|women|children|kids|workers|soldiers|villagers|"
                         r"audience|everyone|others?|survivors|sailors|crew|passers)\b", re.I)
BAD_WORDS = re.compile(r"\b(photo|photograph|photorealistic|realistic|3d|render|hyperreal\w*)\b", re.I)
TEXT_WORDS = re.compile(r"\b(sign|banner|poster|caption|label|title|text|letters?|words?|numbers?|logo|newspaper)\b", re.I)

PLAN_SCHEMA = {"type": "object", "properties": {
    "cast": {"type": "array", "minItems": 1, "maxItems": 5, "items": {"type": "object", "properties": {
        "id": {"type": "string", "description": "short permanent id, e.g. hero, friend, crowd"},
        "name": {"type": "string"},
        "role": {"type": "string", "enum": ["hero", "supporting", "crowd"]},
        "look": {"type": "string", "description": "fixed words for how this character looks (a stickman: head, face, "
                                                   "clothes, colours). Used word for word in every scene."},
        "costume": {"type": "string", "enum": ["none"] + COSTUMES,
                    "description": "hero only: his normal costume, usually none"}},
        "required": ["id", "name", "role", "look", "costume"]}},
    "changes": {"type": "array", "items": {"type": "object", "properties": {
        "scenes": {"type": "array", "items": {"type": "string"}},
        "costume": {"type": "string", "enum": COSTUMES},
        "reason": {"type": "string", "description": "why the story needs the hero to change clothes here"}},
        "required": ["scenes", "costume", "reason"]}},
    "scenes": {"type": "array", "items": {"type": "object", "properties": {
        "id": {"type": "string", "description": "the scene id given in the list"},
        "shot": {"type": "string", "enum": ["wide", "medium", "close"]},
        "who": {"type": "array", "items": {"type": "string"}, "description": "cast ids in this picture (can be empty)"},
        "prompt": {"type": "string", "description": "the detailed picture: where, the light, the camera, what each "
                                                    "character does and feels (face and body), the props, the one thing "
                                                    "the picture must show. Do not repeat the cast looks."}},
        "required": ["id", "shot", "who", "prompt"]}}},
    "required": ["cast", "changes", "scenes"]}


def plan_prompts(script: dict, texts: dict[str, str], topic: str, feedback: str = "") -> dict:
    listing = "\n".join(f'- scene "{sid}": narration: "{t}"' for sid, t in texts.items())
    costumes = "\n".join(f"  {k}: {v}" for k, v in COSTUME_LOOK.items())
    prompt = f"""You plan the pictures of a YouTube Short called "{topic}". A picture model will draw ONE vertical picture per
scene. The channel's hero is a plain stickman (a round white head, thin black stick body) who lives through the story.

STEP 1, THE CAST SHEET. List every character the story needs, each with a permanent id:
- exactly one "hero" (the plain stickman; look = his face and feeling-free base look; costume "none" unless the whole
  story is in a costume, e.g. a diving or space story);
- "supporting" characters only if the story really has a second or third named person (a friend, a guide...): give each
  fixed words for how he/she looks (still a stickman, with a clearly different hat, clothes or colour);
- "crowd" for groups of extras (plain stickmen, never real humans).
Never invent characters the narration does not need.
STEP 2, COSTUME CHANGES. The hero keeps the same look in every scene. Only if the story itself needs him to change
(for example normal clothes, then a space suit) list the scenes, the new costume and the reason in "changes".
Costumes the hero can wear:
{costumes}
STEP 3, THE SCENES. For EVERY scene below give: the shot (wide / medium / close), who is in it (cast ids), and a DETAILED
prompt, pin to pin, so nothing is left to chance:
- WHERE it is (the exact place, time of day, weather), the LIGHT and colours, the CAMERA.
- WHAT EACH CHARACTER DOES: pose, where he stands in the picture, face (eyes, eyebrows, mouth) and the feeling.
- The PROPS and the BIG THING the narration names, with their size next to the stickman.
- Show, don't write: no word, sign or number in the picture. Never ask for text.
- Say how many extras (a small group of 6, not "a huge crowd") and what they do.
- The pictures must differ: different camera, place or pose. The hero must be easy to see: at least a third of the
  picture height in "medium" and "close" shots.
- Say only what the narration says or clearly implies. 40 to 90 words per prompt, plain words, no style words
  (our code adds the style and the cast looks).
{feedback}
SCENES:
{listing}"""
    return llm(prompt, schema=PLAN_SCHEMA, name="picture_prompts", temperature=0.6, models=QUALITY)


def upgrade(data: dict) -> dict:
    """Old pictures.json (one costume + 'others' per scene, 31 Oct morning) -> the cast format."""
    if "cast" in data:
        return data
    sc = data["scenes"]
    costume = next((s.get("costume", "none") for s in sc), "none")
    cast = [{"id": "hero", "name": "the stickman", "role": "hero", "look": "the plain stickman", "costume": costume}]
    scenes = []
    for s in sc:
        who = ["hero"]
        if s.get("others", "nobody").lower() not in ("", "nobody", "none"):
            if not any(c["id"] == "crowd" for c in cast):
                cast.append({"id": "crowd", "name": "extras", "role": "crowd", "look": "plain stickmen", "costume": "none"})
            who.append("crowd")
        scenes.append({k: v for k, v in s.items() if k not in ("costume", "others")} | {"who": who})
    return {**data, "cast": cast, "changes": [], "scenes": scenes}


def _hero(plan: dict) -> dict | None:
    return next((c for c in plan["cast"] if c["role"] == "hero"), None)


def outfit(plan: dict, scene_id: str) -> str:
    """The hero's costume in one scene: his normal one, or a declared change."""
    h = _hero(plan)
    out = h.get("costume", "none") if h else "none"
    for ch in plan.get("changes", []):
        if scene_id in ch["scenes"]:
            out = ch["costume"]
    return out


def refs_for(scene: dict, plan: dict) -> list[str]:
    """Reference picture(s): the hero's (plain or costume) when he is in the scene. Only one: two ran out of memory."""
    h = _hero(plan)
    if h and h["id"] in scene.get("who", []):
        o = outfit(plan, scene["id"])
        return ["stickman_front"] if o == "none" else [f"costume_{o}"]
    return []


def compose(scene: dict, plan: dict) -> str:
    """The final text given to FLUX, built from the cast sheet + the scene prompt + our fixed rules."""
    by = {c["id"]: c for c in plan["cast"]}
    who = [by[i] for i in scene.get("who", []) if i in by]
    parts = [scene["prompt"].strip().rstrip(".")]
    for c in who:
        if c["role"] == "hero":
            parts.append(CHARACTER)
            o = outfit(plan, scene["id"])
            if o != "none":
                parts.append(f"the hero wears {COSTUME_LOOK[o]}, drawn like the costume reference picture, but he is "
                             "still the same hero with the same round white head and face")
        elif c["role"] == "supporting":
            parts.append(f"{c['name']} is a second main character, NOT the hero: {c['look']}")
        else:
            parts.append(f"{c['name']}: {c['look']}")
    if any(c["role"] != "hero" for c in who) or CROWD_WORDS.search(scene["prompt"]):
        parts.append(CROWD_RULE)
    parts.append(STYLE)
    parts += scene.get("redo", [])  # only a redraw has these (redo_prompt)
    return ". ".join(parts)


def validate(plan: dict, texts: dict[str, str]) -> list[str]:
    """Plain-code checks that fit any story. Empty list = fine."""
    problems = []
    cast, scenes = plan["cast"], plan["scenes"]
    ids = [c["id"] for c in cast]
    if len(set(ids)) != len(ids):
        problems.append("cast ids are not unique")
    if sum(c["role"] == "hero" for c in cast) != 1:
        problems.append("the cast needs exactly one hero")
    if len([c for c in cast if c["role"] != "crowd"]) > 4:
        problems.append("more than 4 named characters: too many to keep consistent")
    for c in cast:
        if len(c["look"].split()) < 3:
            problems.append(f"cast {c['id']}: look is too short to keep the character the same")
        if c["role"] != "hero" and c.get("costume", "none") != "none":
            problems.append(f"cast {c['id']}: only the hero uses a costume picture; describe clothes in 'look'")
        if c["role"] == "hero" and c.get("costume", "none") not in ["none"] + COSTUMES:
            problems.append(f"hero: unknown costume {c.get('costume')}")
    got = {s["id"] for s in scenes}
    for sid in texts:
        if sid not in got:
            problems.append(f"scene {sid}: no prompt written")
    for ch in plan.get("changes", []):
        if not ch.get("reason", "").strip():
            problems.append("a costume change has no reason")
        if ch["costume"] not in COSTUMES:
            problems.append(f"change to unknown costume {ch['costume']}")
        for sid in ch["scenes"]:
            if sid not in got:
                problems.append(f"costume change names unknown scene {sid}")
    for s in scenes:
        sid, p = s["id"], s["prompt"]
        if sid not in texts:
            problems.append(f"{sid}: not a scene of the script")
        for w in s.get("who", []):
            if w not in ids:
                problems.append(f"{sid}: who has '{w}', which is not in the cast")
        if len(p.split()) < 25:
            problems.append(f"{sid}: prompt too short ({len(p.split())} words), details are left to chance")
        if BAD_WORDS.search(p):
            problems.append(f"{sid}: asks for a photo/realistic/3d look (the style is flat 2D cartoon)")
        if TEXT_WORDS.search(p):
            problems.append(f"{sid}: asks for text in the picture ({TEXT_WORDS.search(p).group(0)}): show, don't write")
        named = [w for w in s.get("who", []) if w in ids and next(c for c in cast if c["id"] == w)["role"] != "crowd"]
        if not named and re.search(r"stickman|hero", p, re.I) and s.get("shot") != "wide":
            problems.append(f"{sid}: the prompt shows a stickman but 'who' lists no main character")
    shots = [s["id"] for s in scenes if s.get("shot") == "wide"]
    if scenes and len(shots) > max(2, len(scenes) // 3):
        problems.append(f"too many wide shots ({len(shots)} of {len(scenes)}): the characters get tiny")
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
    "realistic_people_count": {"type": "integer", "description": "how many BACKGROUND people with skin-coloured faces, "
                               "hair or noses (the main hero, even in a costume with a white round head, does not count)"},
    "main_figures": {"type": "string", "description": "each main figure and what it wears (head, clothes, colours)"},
    "text_seen": {"type": "string", "description": "every letter, number or word in the picture, or 'none'"}},
    "required": ["n", "seen", "stickmen_count", "realistic_people_count", "main_figures", "text_seen"]}}},
    "required": ["images"]}
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


def check_pictures(pics: dict[str, Path], plan: dict, texts: dict[str, str]) -> dict[str, list[str]]:
    """{scene id: [problems]}; an empty list = the picture passes. Plain code judges the counts from the blind
    description (any real-looking background person = fail); the judge sees the cast sheet and the scene plan and
    also compares the scenes with each other (does a character keep the same look?)."""
    ids = list(pics)
    by_scene = {s["id"]: s for s in plan["scenes"]}
    by_cast = {c["id"]: c for c in plan["cast"]}
    seen = llm(f"""Above are {len(ids)} cartoon pictures, each right after its label "Image n:". For EVERY image: say plainly
what is drawn (the place, the big objects, what each main figure does and feels). Count the stick figures
(a plain round white head with a black outline and thin stick body, with or without clothes). Count any REAL-LOOKING
people: skin-coloured faces, hair, noses and realistic bodies. The main hero (a white round head, even when he wears a
costume) is NOT one. Describe what each main figure wears. Quote every letter, number or word drawn (or say none).
Mention any deformed face, hand or body.""", images=[(f"Image {i}:", _thumb(pics[s])) for i, s in enumerate(ids, 1)],
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
        if by_scene.get(sid, {}).get("who") and x["stickmen_count"] < 1:
            out[sid].append("no stickman is visible")
        if x["text_seen"].strip().lower() not in ("none", "", "no text", "n/a"):
            out[sid].append(f"text in the picture: {x['text_seen'][:60]}")
    lines = []
    for i, sid in enumerate(ids, 1):
        sc = by_scene.get(sid, {"who": [], "prompt": ""})
        cast_txt = "; ".join(
            f"{by_cast[w]['name']} ({by_cast[w]['role']}): {by_cast[w]['look']}"
            + (f", wearing {COSTUME_LOOK[outfit(plan, sid)]}" if by_cast[w]["role"] == "hero" and outfit(plan, sid) != "none" else "")
            for w in sc.get("who", []) if w in by_cast) or "nobody in particular"
        x = by_n.get(i) or {}
        lines.append(f'Scene {sid} (Image {i}): narration: "{texts.get(sid, "")}"\n  should show: {cast_txt}\n'
                     f'  prompt asked for: {sc["prompt"][:400]}\n  described as: {x.get("seen", "(none)")}\n'
                     f'  main figures wear: {x.get("main_figures", "?")}')
    res = llm(f"""Someone described each cartoon picture WITHOUT knowing the story. Judge each scene against the plan. A scene has
a problem when: a character who should be there is missing, or an extra MAIN character is there that the plan does not
list; a character does not look like his cast description (head, clothes, colours); the hero wears something else than
planned or than in the other scenes (outfits may differ ONLY where the plan says so); the picture does not show what the
narration or the prompt asked for; the hero is tiny or hard to see; a face/hand/body is deformed; it looks the same as
another scene. Crowds, several heroes and costumes are fine when the plan lists them. Be concrete (say what to change).
If a scene is fine: ok = true and no problems.

{chr(10).join(lines)}""", schema=PIC_JUDGE, name="art_judge", temperature=0.1, models=LIGHT, last_resort=True)
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
    if "text" in text:
        redo.append("There is absolutely no writing of any kind: no letters, numbers, signs or labels anywhere")
    if "tiny" in text or "hard to see" in text:
        redo.append("The main character is large in the picture, filling at least a third of its height")
    if "missing" in text or "does not look like" in text or "wears" in text or "extra" in text:
        redo.append("Follow the character descriptions exactly: the right characters, each with his own look and clothes, no extra main character")
    if not redo:
        redo.append("Follow the scene description exactly: " + "; ".join(problems)[:300])
    new["redo"] = redo
    new["seed"] = 30 + level  # the kernel default seed is 30; every redraw level is a new picture
    return new
