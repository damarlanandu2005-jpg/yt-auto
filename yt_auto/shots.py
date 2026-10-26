"""Visual plan: a new visual every ~4-5 seconds, real photos first.

1. slots(): cut the narration timeline into slots of about 3-6.5 seconds.
2. plan_visuals(): one model call gives each slot a photo request or a chart/diagram.
3. find_photos(): NASA + Commons search, one model call picks the best candidate
   per slot, then one call LOOKS at the chosen photos and rejects bad matches.
   A slot without a good photo uses its non-photo fallback (AI illustrations are
   not on the Gemini free tier: limit 0, checked 26 Oct 2026).
"""
from __future__ import annotations

import io
import json
import math
import re
from pathlib import Path

from . import photos
from .llm import FAST, LLMError, llm

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
        "kind": {"type": "string", "enum": ["photo", "card"]},
        "photo_subject": {"type": "string", "description": "the ONE thing the photo shows, in a few plain words "
                                                            "(e.g. 'a GPS satellite', 'an atomic clock')"},
        "photo_queries": {"type": "array", "items": {"type": "string"}, "maxItems": 2,
                          "description": "2 search phrases of 1-3 common words, e.g. 'atomic clock', 'GPS receiver'"},
        "card": {"type": "object", "properties": _CARD, "required": ["type", "title"],
                 "description": "the card to show (kind=card), or the fallback if no photo is found (kind=photo)"},
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


def plan_visuals(script_title: str, the_slots: list[dict], headings: dict[str, str]) -> list[dict]:
    lines = [f"{s['id']} [{s['seconds']:.1f}s] (scene: {headings[s['scene']]}{', SCENE START' if s['scene_start'] else ''}) "
             f"{s['text']}" for s in the_slots]
    prompt = f"""Video: {script_title}
Plan one visual for each slot of narration below. The viewer sees it while hearing that text.
Rules:
- Real photos first: use kind=photo for at least 65 per cent of slots, whenever a real photo could show the
  thing being talked about (objects, places, spacecraft, machines, nature, historical photos).
  Ask for SIMPLE subjects an archive surely has ("a handheld GPS receiver", "a rocket launch", "an atomic
  clock"), never a detailed scene ("a hiker with a GPS in remote mountains with no signal"). A photo of the
  object being discussed is better than a text card.
- Use kind=card when a number, comparison, process or list is the point, or at scene starts (title card).
- The first slot is a title card with the video title.
- Every number on a card MUST appear in that slot's text or earlier in the same scene. Never invent data.
- Vary: never the same card type twice in a row; never more than 2 cards in a row.
- Text cards are the last choice: at most one bullets card per scene, and a bare title card only at scene starts.
  Prefer stat, bars, timeline, flow or compare when a card is needed.
- For kind=photo still give a fallback card (used if no good photo exists).
{CARD_HELP}

SLOTS:
""" + "\n".join(lines)
    res = llm(prompt, schema=PLAN_SCHEMA, name="visual_plan", temperature=0.7, models=FAST)
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
               "ninety": "90", "hundred": "100", "thousand": "1000", "once": "1", "twice": "2", "half": "0.5"})


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
VERIFY_SCHEMA = {"type": "object", "properties": {"checks": {"type": "array", "items": {
    "type": "object", "properties": {"n": {"type": "integer"}, "fits": {"type": "boolean"},
                                     "reason": {"type": "string"}},
    "required": ["n", "fits", "reason"]}}}, "required": ["checks"]}


def find_photos(visuals: list[dict], photo_dir: Path, log: dict) -> None:
    """Fill v["photo"] (path + licence record) for photo slots; others keep their card."""
    want = [v for v in visuals if v["kind"] == "photo" and v.get("photo_queries")]
    cands: dict[str, list[dict]] = {}
    for v in want:
        cands[v["id"]] = photos.search(v["photo_queries"][:2], per_source=6)[:12]
    log["photo_slots"] = len(want)
    log["candidates"] = {k: len(c) for k, c in cands.items()}
    asks = [v for v in want if cands[v["id"]]]
    if not asks:
        return
    blocks = []
    for v in asks:
        opts = "\n".join(f"  {c['source'][:4]}:{i}: {c['title'][:90]} | {c['description'][:160]}"
                         for i, c in enumerate(cands[v["id"]]))
        blocks.append(f"[{v['id']}] needs: {v.get('photo_subject', '')} | narration: {v['text']}\n{opts}")
    prompt = """Pick the best photo for each slot from its numbered candidates (title | description).
Choose a candidate if it shows the slot's subject or something closely related that fits the narration
(it does not need to match every detail: a photo of a real handheld GPS receiver fits "a hiker's GPS").
Answer "" only when no candidate is related, or the only related ones would mislead the viewer.
Prefer real photographs over diagrams with small text, logos, or maps with dense labels. Avoid close-up
faces of private people. Do not use the same photo twice.
Answer choice = the candidate number as text, or "".

""" + "\n\n".join(blocks)
    try:
        picks = {p["id"]: p["choice"] for p in llm(prompt, schema=PICK_SCHEMA, name="photo_pick",
                                                     temperature=0.2, models=FAST)["picks"]}
    except LLMError as e:
        log["pick_error"] = str(e)
        return

    used, chosen = set(), []
    for v in asks:
        ch = str(picks.get(v["id"], "")).strip()
        if not ch.isdigit() or int(ch) >= len(cands[v["id"]]):
            continue
        c = cands[v["id"]][int(ch)]
        if c["id"] in used:
            continue
        try:
            path = photos.download(c, photo_dir, v["id"])
        except Exception as e:  # noqa: BLE001
            print(f"[photos] download failed for {v['id']}: {e!r}", flush=True)
            continue
        if path:
            used.add(c["id"])
            v["photo"] = {"path": str(path), **json.loads(path.with_suffix(".licence.json").read_text())}
            chosen.append(v)
    log["downloaded"] = len(chosen)
    _verify(chosen, log)


def _thumb(path: str, size: int = 384) -> bytes:
    from PIL import Image

    im = Image.open(path).convert("RGB")
    im.thumbnail((size, size))
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=80)
    return buf.getvalue()


def _verify(chosen: list[dict], log: dict) -> None:
    """Let the model look at each chosen photo; drop ones that don't show the subject."""
    if not chosen:
        return
    listing = "\n".join(f"Image {i + 1}: should show: {v.get('photo_subject', '')} (narration: {v['text']})"
                        for i, v in enumerate(chosen))
    prompt = f"""You see {len(chosen)} images in order. For each, say if it fits: it must clearly show what it
should show, be a real usable picture (not mostly text, not a blank or broken image, no watermark),
and not be misleading next to the narration.
{listing}"""
    try:
        res = llm(prompt, images=[_thumb(v["photo"]["path"]) for v in chosen], schema=VERIFY_SCHEMA,
                  name="photo_verify", temperature=0.1, models=FAST)
    except LLMError as e:
        log["verify_error"] = str(e)
        return
    rejected = []
    for c in res["checks"]:
        if not c["fits"] and 1 <= c["n"] <= len(chosen):
            v = chosen[c["n"] - 1]
            rejected.append({"id": v["id"], "title": v["photo"]["title"], "reason": c["reason"]})
            v["photo_rejected"] = v.pop("photo")
    log["rejected_after_looking"] = rejected
