"""On-screen key words, timed to the voice (owner's watch notes, 28 Oct: hit videos show clear key words as
they are spoken, so the message is understandable even with the sound off).

One light AI request picks the key word or short phrase of each important sentence (copied exactly from the
sentence); whisper word times place it; FFmpeg/libass burns it into the picture with a small pop-in.
"""
from __future__ import annotations

import re
from pathlib import Path

from . import align
from .llm import LIGHT, LLMError, llm

KEY_SCHEMA = {"type": "object", "properties": {"keys": {"type": "array", "items": {"type": "object", "properties": {
    "id": {"type": "string"}, "phrase": {"type": "string"}}, "required": ["id", "phrase"]}}}, "required": ["keys"]}
MIN_S, MAX_S = 1.3, 2.6  # how long a key word stays on screen
FONT = "DejaVu Sans"


def choose(script: dict) -> dict[str, str]:
    lines = "\n".join(f"{s['id']}: {s['text']}" for sc in script["scenes"] for s in sc["sentences"])
    prompt = f"""This is the narration of an explainer video, one sentence per line. For about HALF of the
sentences (the important ones), pick the ONE key word or short phrase (1 to 3 words) a viewer should see on
screen while hearing it: a number with its unit, a name, or the main idea. Copy it EXACTLY as written in the
sentence. Skip filler sentences. Never pick small words like "this" or "it".

{lines}"""
    try:
        res = llm(prompt, schema=KEY_SCHEMA, name="keywords", temperature=0.2, models=LIGHT)
    except LLMError as e:
        return {"_error": str(e)[:300]}
    text = {s["id"]: s["text"] for sc in script["scenes"] for s in sc["sentences"]}
    out = {}
    for k in res["keys"]:
        p = k["phrase"].strip(" .,;:!?\"'")
        if k["id"] in text and 0 < len(p.split()) <= 3 and _find(text[k["id"]].split(), p) is not None:
            out[k["id"]] = p
    return out


def _find(words: list[str], phrase: str) -> int | None:
    want = [align._norm(w) for w in phrase.split()]
    have = [align._norm(w) for w in words]
    for i in range(len(have) - len(want) + 1):
        if have[i:i + len(want)] == want:
            return i
    return None


def events(sentences: list[dict], heard: list[dict], keys: dict[str, str]) -> list[tuple[float, float, str]]:
    ev = []
    for s in sentences:
        p = keys.get(s["id"])
        if not p:
            continue
        timed = align.time_words(s["text"], s["start"], s["end"], heard)
        i = _find([w for w, _, _ in timed], p)
        if i is None:
            continue
        ev.append([timed[i][1], p])
    out = []
    for j, (t, p) in enumerate(ev):
        nxt = ev[j + 1][0] if j + 1 < len(ev) else t + MAX_S
        end = min(t + MAX_S, max(t + MIN_S, nxt - 0.1))
        if out and t < out[-1][1]:  # never two on screen
            out[-1] = (out[-1][0], t - 0.05, out[-1][2])
        out.append((t, end, p))
    return out


def _ts(t: float) -> str:
    cs = int(round(t * 100))
    return f"{cs // 360000}:{cs // 6000 % 60:02}:{cs // 100 % 60:02}.{cs % 100:02}"


def write_ass(evs: list[tuple[float, float, str]], path: Path) -> int:
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Key,{FONT},108,&H00FFFFFF,&H00FFFFFF,&H00000000,&H96000000,1,0,0,0,100,100,1,0,1,6,3,2,80,80,190,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = []
    for a, b, p in evs:
        text = p.upper()
        if re.search(r"\d", p):  # numbers in the channel's red accent
            text = r"{\c&H3C3CE8&}" + text
        pop = r"{\fad(120,160)\fscx80\fscy80\t(0,140,\fscx100\fscy100)}"
        lines.append(f"Dialogue: 0,{_ts(a)},{_ts(b)},Key,,0,0,0,,{pop}{text}")
    path.write_text(head + "\n".join(lines) + "\n", encoding="utf-8")
    return len(lines)
