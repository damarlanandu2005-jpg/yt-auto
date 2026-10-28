"""Visual plan: a new visual every ~4-5 seconds, real photos first.

1. slots(): cut the narration timeline into slots of about 3-6.5 seconds.
2. plan_visuals(): one model call gives each slot a photo request or a chart/diagram.
3. find_photos(): NASA + Commons search, one model call picks the best candidate
   per slot, then one call LOOKS at the chosen photos and rejects bad matches.
4. drawings: ink drawings from a free open model on the runner's CPU (Gemini image models have a
   free limit of 0) for ideas no photo can show, then for photo slots left without a photo; one call
   LOOKS at them and rejects bad ones. A slot with neither keeps its fallback card.
"""
from __future__ import annotations

import io
import json
import math
import re
from pathlib import Path

from . import footage, photos
from .llm import LIGHT, VISION, LLMError, llm

TARGET_S, MIN_S, MAX_S = 4.5, 3.0, 6.5


def slots(sentences: list[dict], total: float) -> list[dict]:
    """sentences: [{"id","scene","text","start","end"}] in order, times in the final video."""
    units = []
    for s in sentences:
        dur = s["end"] - s["start"]
        k = max(1, math.ceil(dur / MAX_S)) if dur > MAX_S else 1
        words = s["text"].split()
        for i in range(k):  # long sentence -> k parts, split by words
            a, b = round(i * len(words) / k), round((i + 1) * len(words) / k)
            units.append({"scene": s["scene"], "sentence": s["id"], "text": " ".join(words[a:b]),
                          "start": s["start"] + dur * a / len(words)})
    out, cur = [], None
    for i, u in enumerate(units):
        nxt = units[i + 1]["start"] if i + 1 < len(units) else total
        merge = (cur is not None and u["scene"] == cur["scene"] and u["start"] - cur["start"] < MIN_S
                 and nxt - cur["start"] <= MAX_S)
        if merge:
            cur["text"] += " " + u["text"]
            if u["sentence"] not in cur["sentences"]:
                cur["sentences"].append(u["sentence"])
        else:
            cur = {"scene": u["scene"], "start": u["start"], "text": u["text"], "sentences": [u["sentence"]]}
            out.append(cur)
    out = _merge_short(out, total)
    out[0]["start"] = 0.0
    for i, sl in enumerate(out):
        sl["id"] = f"v{i + 1:03}"
        sl["end"] = out[i + 1]["start"] if i + 1 < len(out) else total
        sl["seconds"] = round(sl["end"] - sl["start"], 2)
        sl["scene_start"] = i == 0 or out[i - 1]["scene"] != sl["scene"]
    return out


def _merge_short(out: list[dict], total: float, short: float = 2.2, limit: float = 8.0) -> list[dict]:
    """Fold any slot under `short` seconds into a neighbour in the same scene (a flash of a picture is tiring)."""
    def length(i):
        return (out[i + 1]["start"] if i + 1 < len(out) else total) - out[i]["start"]

    i = 0
    while i < len(out):
        if length(i) < short:
            prev_ok = i > 0 and out[i - 1]["scene"] == out[i]["scene"] and length(i - 1) + length(i) <= limit
            next_ok = (i + 1 < len(out) and out[i + 1]["scene"] == out[i]["scene"]
                       and length(i) + length(i + 1) <= limit)
            if prev_ok or next_ok:
                a, b = (i - 1, i) if prev_ok and (not next_ok or length(i - 1) <= length(i + 1)) else (i, i + 1)
                out[a]["text"] += " " + out[b]["text"]
                out[a]["sentences"] += [x for x in out[b]["sentences"] if x not in out[a]["sentences"]]
                del out[b]
                continue
        i += 1
    return out


_CARD = {
    "type": {"type": "string", "enum": ["title", "stat", "bullets", "flow", "bars", "timeline", "compare"]},
    "title": {"type": "string"}, "subtitle": {"type": "string"},
    "value": {"type": "string"}, "label": {"type": "string"}, "note": {"type": "string"},
    "items": {"type": "array", "items": {"type": "string"}, "maxItems": 4},
    "steps": {"type": "array", "items": {"type": "string"}, "maxItems": 5},
    "labels": {"type": "array", "items": {"type": "string"}, "maxItems": 6},
    "values": {"type": "array", "items": {"type": "number"}, "maxItems": 6},
    "unit": {"type": "string"},
    "events": {"type": "array", "maxItems": 5, "items": {"type": "object", "properties": {
        "when": {"type": "string"}, "label": {"type": "string"}}, "required": ["when", "label"]}},
    "left_title": {"type": "string"}, "left_points": {"type": "array", "items": {"type": "string"}, "maxItems": 3},
    "right_title": {"type": "string"}, "right_points": {"type": "array", "items": {"type": "string"}, "maxItems": 3},
}
PLAN_SCHEMA = {"type": "object", "properties": {"visuals": {"type": "array", "items": {
    "type": "object",
    "properties": {
        "id": {"type": "string"},
        "kind": {"type": "string", "enum": ["video", "photo", "drawing", "step", "card"]},
        "focus": {"type": "string", "enum": ["center", "left", "right", "top", "bottom"],
                  "description": "kind=step: which part of the previous picture to move closer to"},
        "photo_subject": {"type": "string", "description": "the ONE thing the photo shows, in a few plain words "
                                                            "(e.g. 'a GPS satellite', 'an atomic clock')"},
        "photo_queries": {"type": "array", "items": {"type": "string"}, "maxItems": 2,
                          "description": "2 search phrases of 1-3 common words, e.g. 'atomic clock', 'GPS receiver'"},
        "drawing_subject": {"type": "string", "description": "kind=drawing: one simple scene of objects in plain "
                                                              "words, e.g. 'a radio wave travelling from a satellite "
                                                              "down to a phone'"},
        "card": {"type": "object", "properties": _CARD, "required": ["type", "title"],
                 "description": "the card to show (kind=card), or the fallback if no photo or drawing works"},
    },
    "required": ["id", "kind", "card"],
}}}, "required": ["visuals"]}

CARD_HELP = """Card types (all text short; big and readable on a phone):
- title: title (+ subtitle). Use for scene openings.
- stat: value (a number with unit, e.g. "20,200 km") + label (+ note).
- bullets: title + 2-4 items (each under 6 words).
- flow: title + 2-5 steps (cause -> effect, process).
- bars: title + labels + values (+ unit). Compare 2-6 quantities.
- timeline: title + 2-5 events {when, label}.
- compare: title + left_title/left_points vs right_title/right_points."""


def plan_visuals(script_title: str, the_slots: list[dict], headings: dict[str, str], max_drawings: int = 12) -> list[dict]:
    lines = [f"{s['id']} [{s['seconds']:.1f}s] (scene: {headings[s['scene']]}{', SCENE START' if s['scene_start'] else ''}) "
             f"{s['text']}" for s in the_slots]
    prompt = f"""Video: {script_title}
Plan one visual for each slot of narration below. The viewer sees it while hearing that text.
Rules:
- Real photos first: use kind=photo for at least 65 per cent of slots, whenever a real photo could show the
  thing being talked about (objects, places, spacecraft, machines, nature, historical photos).
  Ask for SIMPLE subjects an archive surely has ("a handheld GPS receiver", "a rocket launch", "an atomic
  clock"), never a detailed scene ("a hiker with a GPS in remote mountains with no signal"). Never ask for a
  photo of a chart, graph, diagram or data: archive charts are about other things; use a card instead. A photo of the
  object being discussed is better than a text card.
- Moving footage first for the big moments: kind=video = real NASA footage or NASA animation (rocket launches,
  spacecraft, astronauts, Earth from orbit, the Sun, planets, galaxies, black hole or star animations). Use it
  for about 20 to 30 per cent of slots, like a documentary. Give photo_subject and photo_queries (simple words a
  NASA video archive has: "black hole animation", "galaxy flythrough", "rocket launch").
- Use kind=drawing (at most {max_drawings} in the whole video) for an idea no real photo can show: an invisible
  process, a view nobody photographed, a comparison of two things (e.g. "a radio wave travelling from a satellite
  down to a phone", "two clocks side by side, one in orbit and one on the ground"). drawing_subject: one simple
  scene of CONCRETE objects a viewer recognises at once ("a huge exploding star beside a small blue planet",
  "a DNA double helix with a broken rung"), never a process word ("composition changing", "errors"). No people, faces or hands, no logos, emblems or flags, no text, no numbers, no maps.
- Step by step (owner's rule): when the narration explains ONE object or scene in parts over several slots, use
  kind=step for the next 1 or 2 slots: they show the SAME picture as the slot before, moved closer to the part
  being explained (focus: center, left, right, top or bottom). Wide view first, then closer, then detail.
  Use steps for about 10 to 20 per cent of slots; never more than 2 steps in a row; a step needs a photo or
  drawing right before it.
- Use kind=card when a number, comparison, process or list is the point, or at scene starts (title card).
- The first slot is a title card with the video title.
- Every number on a card MUST appear in that slot's text or earlier in the same scene. Never invent data.
- Vary: never the same card type twice in a row; never more than 2 cards in a row.
- Text cards are the last choice: at most one bullets card per scene, and a bare title card only at scene starts.
  Prefer stat, bars, timeline, flow or compare when a card is needed.
- For kind=photo and kind=drawing still give a fallback card (used if no good picture is made).
{CARD_HELP}

SLOTS:
""" + "\n".join(lines)
    res = llm(prompt, schema=PLAN_SCHEMA, name="visual_plan", temperature=0.7, models=LIGHT, last_resort=True)
    by_id = {v["id"]: v for v in res["visuals"]}
    out = []
    for s in the_slots:
        v = by_id.get(s["id"]) or {"kind": "card", "card": {"type": "title", "title": headings[s["scene"]]}}
        out.append({**s, **v, "id": s["id"]})
    return out


_WORDS = {w: str(i) for i, w in enumerate(
    "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen "
    "seventeen eighteen nineteen twenty".split())}
_WORDS.update({"thirty": "30", "forty": "40", "fifty": "50", "sixty": "60", "seventy": "70", "eighty": "80",
               "ninety": "90", "hundred": "100", "thousand": "1000", "once": "1", "twice": "2", "half": "0.5",
               "ones": "1", "zeros": "0", "zeroes": "0", "first": "1", "second": "2", "third": "3", "fourth": "4",
               "fifth": "5", "sixth": "6"})


def _numbers(text: str, words: bool = False) -> set[str]:
    found = {n.replace(",", "") for n in re.findall(r"\d[\d,]*(?:\.\d+)?", text)}
    if words:  # the narration may say "two" where the card shows "2"
        found |= {_WORDS[w] for w in re.findall(r"[a-z]+", text.lower()) if w in _WORDS}
    return found


def check_card_numbers(visuals: list[dict], scene_text: dict[str, str]) -> list[str]:
    """Cards may only show numbers spoken in their scene. Bad cards become title cards."""
    problems = []
    for v in visuals:
        card = v["card"]
        # ensure_ascii=False: otherwise "°" becomes "\u00b0" and its digits look like numbers
        shown = _numbers(json.dumps({k: card.get(k) for k in ("value", "label", "note", "items", "steps", "values",
                                                                "events", "left_points", "right_points", "subtitle")},
                                    ensure_ascii=False))
        shown = {n.rstrip("0").rstrip(".") if "." in n else n for n in shown}
        spoken = {n.rstrip("0").rstrip(".") if "." in n else n for n in _numbers(scene_text[v["scene"]], words=True)}
        bad = shown - spoken
        if bad:
            problems.append(f"{v['id']}: numbers {sorted(bad)} not in narration; card replaced")
            v["card"] = {"type": "title", "title": card.get("title") or "", "subtitle": ""}
    return problems


PICK_SCHEMA = {"type": "object", "properties": {"picks": {"type": "array", "items": {
    "type": "object", "properties": {"id": {"type": "string"}, "choice": {"type": "string"}},
    "required": ["id", "choice"]}}}, "required": ["picks"]}
SEEN_SCHEMA = {"type": "object", "properties": {"images": {"type": "array", "items": {
    "type": "object", "properties": {"n": {"type": "integer"}, "seen": {"type": "string"}},
    "required": ["n", "seen"]}}}, "required": ["images"]}
VERIFY_SCHEMA = {"type": "object", "properties": {"checks": {"type": "array", "items": {
    "type": "object", "properties": {"n": {"type": "integer"}, "seen": {"type": "string"},
                                     "fits": {"type": "boolean"}, "reason": {"type": "string"}},
    "required": ["n", "seen", "fits", "reason"]}}}, "required": ["checks"]}


CHART_WORDS = re.compile(r"\b(chart|graph|plot|diagram|data|infographic|table)s?\b", re.I)


def find_photos(visuals: list[dict], photo_dir: Path, log: dict) -> None:
    """Fill v["photo"] (path + licence record) for photo slots; others keep their card."""
    for v in visuals:  # pilot video 1 v045: "scientific data graph" found a Mars density chart
        if v["kind"] == "photo" and CHART_WORDS.search(v.get("photo_subject", "") + " " +
                                                         " ".join(v.get("photo_queries") or [])):
            v["kind"] = "card"
            log.setdefault("chart_photos_to_cards", []).append(v["id"])
    want = [v for v in visuals if v["kind"] in ("photo", "video") and v.get("photo_queries")]
    cands: dict[str, list[dict]] = {}
    for v in want:
        if v["kind"] == "video":  # NASA footage first, photos as the fallback candidates
            vids = []
            for q in v["photo_queries"][:2]:
                try:
                    vids += [c for c in footage.search(q) if c["id"] not in {x["id"] for x in vids}]
                except Exception as e:  # noqa: BLE001
                    print(f"[footage] search {q!r} failed: {e!r}", flush=True)
            cands[v["id"]] = (vids[:8] + photos.search(v["photo_queries"][:2], per_source=4))[:12]
        else:
            cands[v["id"]] = photos.search(v["photo_queries"][:2], per_source=6)[:12]
    log["photo_slots"] = len(want)
    log["candidates"] = {k: len(c) for k, c in cands.items()}
    asks = [v for v in want if cands[v["id"]]]
    if not asks:
        return
    blocks = []
    for v in asks:
        opts = "\n".join(f"  {c['source'][:4]}{' VIDEO' if c.get('kind') == 'video' else ''}:{i}: {c['title'][:90]} | "
                         f"{c['description'][:160]}"
                         for i, c in enumerate(cands[v["id"]]))
        blocks.append(f"[{v['id']}] needs: {v.get('photo_subject', '')} | narration: {v['text']}\n{opts}")
    prompt = """Pick the best photo for each slot from its numbered candidates (title | description).
Choose a candidate if it shows the slot's subject or something closely related that fits the narration
(it does not need to match every detail: a photo of a real handheld GPS receiver fits "a hiker's GPS").
Answer "" only when no candidate is related, or the only related ones would mislead the viewer.
Prefer real photographs over diagrams with small text, logos, or maps with dense labels. Where the slot
needs video, prefer a VIDEO candidate that shows the subject (footage or animation, not a talking person or a
press conference). Avoid close-up
faces of private people. Do not use the same photo twice.
Answer choice = the candidate number as text, or "".

""" + "\n\n".join(blocks)
    try:
        picks = {p["id"]: p["choice"] for p in llm(prompt, schema=PICK_SCHEMA, name="photo_pick",
                                                     temperature=0.2, models=LIGHT, last_resort=True)["picks"]}
    except LLMError as e:
        log["pick_error"] = str(e)
        return

    used, chosen = set(), []
    for v in asks:
        # Accept "6" or "wiki:6" (run 40465984856: Flash-Lite copied the label, and every pick was lost).
        m = re.search(r"(\d+)\s*$", str(picks.get(v["id"], "")))
        if not m or int(m.group(1)) >= len(cands[v["id"]]):
            continue
        c = cands[v["id"]][int(m.group(1))]
        if c["id"] in used:
            continue
        try:
            path = _fetch(c, photo_dir, v["id"], v)
        except Exception as e:  # noqa: BLE001
            print(f"[photos] download failed for {v['id']}: {e!r}", flush=True)
            continue
        if path:
            used.add(c["id"])
            v["photo"] = {"path": str(path), **json.loads(path.with_suffix(".licence.json").read_text())}
            chosen.append(v)
    log["downloaded"] = len(chosen)
    _verify(chosen, log)
    # Second try: the next candidate for each rejected slot, looked at the same way (test run 40636347540:
    # 9 of 16 first picks were rejected and became cards).
    tried = {v["id"]: {c["id"] for c in cands[v["id"]] if c.get("title") == v["photo_rejected"].get("title")}
             for v in chosen if v.get("photo_rejected")}
    again = []
    for v in [v for v in chosen if v.get("photo_rejected")]:
        for c in cands[v["id"]]:
            if c["id"] in used or c["id"] in tried[v["id"]]:
                continue
            try:
                path = _fetch(c, photo_dir, v["id"] + "b", v)
            except Exception:  # noqa: BLE001
                continue
            if path:
                used.add(c["id"])
                v["photo"] = {"path": str(path), **json.loads(path.with_suffix(".licence.json").read_text())}
                again.append(v)
                break
    if again:
        second: dict = {}
        _verify(again, second)
        log["second_try"] = {"tried": len(again), "kept": sum(1 for v in again if v.get("photo")),
                             "seen": second.get("seen", {}),
                             "rejected": second.get("rejected_after_looking", []), "error": second.get("verify_error")}
        if second.get("verify_error"):  # not looked at: don't use them
            for v in again:
                v.pop("photo", None)


def _fetch(c: dict, photo_dir: Path, stem: str, v: dict) -> Path | None:
    if c.get("kind") == "video":
        return footage.fetch(c, photo_dir, stem, float(v.get("seconds") or 5))
    return photos.download(c, photo_dir, stem)


def _thumb(path: str, size: int = 384) -> bytes:
    from PIL import Image

    im = Image.open(path).convert("RGB")
    im.thumbnail((size, size))
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=80)
    return buf.getvalue()


# Never drawn: a drawn logo, emblem or flag imitates a real organisation's mark (run 40580636183 drew a
# fake "US Space Force logo" and the vision check passed it), and drawn people/brands could mislead.
NO_DRAW = re.compile(r"\b(logo|emblem|insignia|seal|badge|flag|crest|coat of arms|trademark|brand|mascot|"
                     r"portrait|face|person|people|man|woman|astronaut|scientist|president|map)s?\b", re.I)


PLANNED_MAX = 12


STEP_ZOOM = (1.0, 1.4, 1.8)  # wide, closer, detail (more would blur 1,000-pixel photos)


def apply_steps(visuals: list[dict], log: dict) -> None:
    """kind=step slots reuse the previous slot's picture, zoomed closer at its focus (after photos and drawings
    are final, so a rejected picture is never reused). A step with no picture before it keeps its card."""
    made, orphan = 0, []
    for i, v in enumerate(visuals):
        if v["kind"] != "step":
            continue
        prev = visuals[i - 1] if i else None
        if prev and prev.get("photo") and prev["scene"] == v["scene"] and prev.get("zoom", 1.0) < STEP_ZOOM[-1]:
            level = STEP_ZOOM.index(prev.get("zoom", 1.0)) + 1 if prev.get("zoom", 1.0) in STEP_ZOOM else 1
            v["photo"] = {k: x for k, x in prev["photo"].items() if k != "video_clip"}  # a still close-up
            v["zoom"] = STEP_ZOOM[min(level, len(STEP_ZOOM) - 1)]
            v["focus"] = v.get("focus") or prev.get("focus") or "center"
            v["step_of"] = prev.get("step_of", prev["id"])
            made += 1
        else:
            orphan.append(v["id"])
    log["steps"] = made
    log["steps_without_picture"] = orphan


def _card_number(v: dict) -> str | None:
    c = v.get("card") or {}
    if c.get("type") == "stat":
        m = re.search(r"\d[\d,.]*", str(c.get("value", "")))
        return m.group(0).replace(",", "") if m else None
    return None


def limit_cards(visuals: list[dict], log: dict) -> None:
    """Code rules (step 2 test run 40637860035 had 4 number cards in a row and '1.5 million years' twice):
    never more than 2 cards in a row, and no number card repeating a number already shown in its scene.
    An extra card becomes a closer look at the last picture of its scene (or stays a card if there is none)."""
    fixed, run, seen = [], 0, {}
    for i, v in enumerate(visuals):
        if v.get("photo"):
            run = 0
            continue
        run += 1
        num = _card_number(v)
        repeat = num is not None and num in seen.get(v["scene"], set())
        if num is not None:
            seen.setdefault(v["scene"], set()).add(num)
        if run <= 2 and not repeat:
            continue
        last = next((u for u in reversed(visuals[:i]) if u.get("photo") and u["scene"] == v["scene"]), None)
        if last is None:
            continue
        v["photo"] = {k: x for k, x in last["photo"].items() if k != "video_clip"}
        v["zoom"] = STEP_ZOOM[1] if last.get("zoom", 1.0) < STEP_ZOOM[1] else STEP_ZOOM[0]
        v["focus"] = {"center": "left", "left": "right", "right": "top"}.get(last.get("focus") or "center", "center")
        v["kind"], v["step_of"] = "step", last.get("step_of", last["id"])
        fixed.append(v["id"])
        run = 0
    log["cards_to_pictures"] = fixed


def drawing_jobs(visuals: list[dict], max_n: int) -> list[dict]:
    """Planned drawings first, then photo slots that ended without a photo (up to max_n in all)."""
    from .drawings import CLOUD_PLANNED_MAX, cloud_ready

    planned_max = CLOUD_PLANNED_MAX if cloud_ready() else PLANNED_MAX
    planned = [v for v in visuals if v["kind"] == "drawing" and v.get("drawing_subject")
               and not NO_DRAW.search(v["drawing_subject"])]
    no_photo = [v for v in visuals if v["kind"] in ("photo", "video") and not v.get("photo") and v.get("photo_subject")
                and not NO_DRAW.search(v["photo_subject"])]
    # Keep room for photo slots whose photo failed the check: pilot video 1 remake (run 40593105860) planned
    # 18 drawings (asked for at most 12), so the 12 rejected photos all became bare title cards.
    jobs = [{"id": v["id"], "subject": v["drawing_subject"]} for v in planned[:planned_max]]
    jobs += [{"id": v["id"], "subject": v["photo_subject"]} for v in no_photo]
    return jobs[:max_n]


def add_drawings(visuals: list[dict], drawn: dict[str, str], log: dict) -> None:
    """Attach finished drawings as pictures, then look at them and drop bad ones (fail closed)."""
    by_id = {v["id"]: v for v in visuals}
    chosen = []
    for vid, path in drawn.items():
        v = by_id[vid]
        rec = json.loads(Path(path).with_suffix(".licence.json").read_text())
        v["photo"] = {"path": path, **rec}
        v.setdefault("photo_subject", v.get("drawing_subject", ""))
        if v["kind"] == "drawing":
            v["photo_subject"] = v.get("drawing_subject") or v["photo_subject"]
        chosen.append(v)
    sub: dict = {}
    _verify(chosen, sub, drawings=True)
    log["drawings_seen"] = sub.get("seen", {})
    log["drawings_rejected"] = sub.get("rejected_after_looking", [])
    if "verify_error" in sub:
        log["drawings_verify_error"] = sub["verify_error"]
        for v in chosen:  # not looked at: don't use them (fail closed)
            v["drawing_rejected"] = v.pop("photo")
    log["drawings_used"] = sum(1 for v in chosen if v.get("photo"))


def _verify(chosen: list[dict], log: dict, drawings: bool = False) -> None:
    """Let the model look at each chosen picture; drop ones that don't show the subject.

    Each picture is sent with its own "Image n:" label, the model first says what it sees, and a
    picture it gives no verdict for is dropped (fail closed)."""
    if not chosen:
        return
    # Step 1, blind: describe each picture WITHOUT being told what it should show. When told, the model
    # copied the request as what it "saw" and passed all 18 drawings of pilot video 1 (run 40586668835),
    # including a red diamond for "a star near Earth" and a Mars density chart for a supernova.
    try:
        desc = llm(f"""Above are {len(chosen)} images, each right after its label "Image n:". For EVERY image, say in
one or two plain sentences what it literally shows, as if to someone who cannot see it. Be honest: if it is
abstract, unclear or just shapes, say so. Mention any text, labels, logo, emblem, chart axes, or deformed
hands, faces or bodies.""", images=[(f"Image {i + 1}:", _thumb(v["photo"]["path"])) for i, v in enumerate(chosen)],
                   schema=SEEN_SCHEMA, name="drawing_describe" if drawings else "photo_describe", temperature=0.1,
                   models=VISION, last_resort=True)
    except LLMError as e:
        log["verify_error"] = str(e)
        return
    seen_by_n = {x["n"]: x["seen"] for x in desc["images"]}
    if drawings:
        rules = """The pictures are ink drawings made by an AI image model, which often misses. A drawing fits if a
viewer hearing the narration would recognise its main object(s) (a star, a planet, a blast, molecules, DNA,
fish...). It does NOT need to show the action or process (collapsing, moving, changing): a still picture of
the right thing is enough. It does NOT fit if it is only shapes or texture with no recognisable object, shows
a different thing (a volcano or canyon for the atmosphere, a red diamond for a star), has text or labels, looks
like a logo/emblem/badge/flag, or has deformed bodies."""
    else:
        rules = """A photo fits only if the description shows it clearly depicts what it should show: not mostly text,
not a test target, not a different planet or object than the narration is about, no watermark, nothing
misleading. A diagram, infographic or poster with many labels or much text does NOT fit (too small to read
in a video, and made for another purpose). A chart or graph fits ONLY if its labels show it is about exactly what the narration says (a graph
of Mars data, or with unexplained labels like 'RHOS', does not fit a sentence about Earth or a star)."""
    listing = "\n".join(f"Image {i + 1}: described as: {seen_by_n.get(i + 1, '(no description)')}\n"
                        f"  should show: {v.get('photo_subject', '')}\n  narration: {v['text']}"
                        for i, v in enumerate(chosen))
    prompt = f"""Step 2 of a picture check for a science video. Someone looked at each picture WITHOUT knowing
what it should show and described it. Decide for each image whether the picture fits.
{rules}
When unsure, answer fits = false (a chart or plain card is shown instead, which is fine).
Copy the description into "seen".
{listing}"""
    try:
        res = llm(prompt, schema=VERIFY_SCHEMA, name="drawing_verify" if drawings else "photo_verify",
                  temperature=0.1, models=LIGHT, last_resort=True)
    except LLMError as e:
        log["verify_error"] = str(e)
        return
    verdicts = {c["n"]: c for c in res["checks"] if 1 <= c["n"] <= len(chosen)}
    rejected, seen = [], {}
    for i, v in enumerate(chosen, 1):
        c = verdicts.get(i) or {"fits": False, "reason": "no verdict returned", "seen": ""}
        seen[v["id"]] = c.get("seen", "")
        if not c["fits"]:
            rejected.append({"id": v["id"], "title": v["photo"]["title"], "seen": c.get("seen", ""),
                             "reason": c["reason"]})
            v["drawing_rejected" if drawings else "photo_rejected"] = v.pop("photo")
    log["seen"] = seen
    log["rejected_after_looking"] = rejected
