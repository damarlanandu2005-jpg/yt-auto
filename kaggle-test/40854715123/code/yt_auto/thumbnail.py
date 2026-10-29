"""Thumbnail (rule R1 needs one): the strongest checked picture of the video + 2 to 4 big, honest words.

One light AI request chooses the picture (from what the blind picture check SAW in each one, so only pictures
that passed are used) and the words; rule R2: the words must be true and match the video. Research (28 Oct):
thumbnail style alone doesn't separate hits from normal videos, so this is kept simple and clear: one subject,
dark side for the text, one word in the channel's red.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

from .llm import LIGHT, LLMError, llm

W, H = 1280, 720
RED, WHITE = (232, 60, 60), (255, 255, 255)
SCHEMA = {"type": "object", "properties": {
    "picture": {"type": "string"}, "text": {"type": "string", "description": "2 to 4 words, no punctuation"},
    "red_word": {"type": "string", "description": "the one word of text shown in red"}},
    "required": ["picture", "text", "red_word"]}


def choose(title: str, question: str, seen: dict[str, str], key_lines: str = "") -> dict:
    lines = "\n".join(f"{k}: {v}" for k, v in seen.items())
    prompt = f"""Make a YouTube thumbnail for this video.
Title: {title}
Question it answers: {question}

Pick ONE picture (by its id) that will read best at phone size: one clear, dramatic subject that fits the
title. Then write 2 to 4 big words to put on it: honest (true, kept by the video), not the title repeated,
no fake urgency, no question marks or punctuation. Use words the narration itself uses (pilot video 2 got
'universe grew faster', which the video never says). Pick one of those words to show in red.

KEY LINES OF THE NARRATION:
{key_lines}

PICTURES (what a viewer sees in each):
{lines}"""
    try:
        return llm(prompt, schema=SCHEMA, name="thumbnail", temperature=0.5, models=LIGHT)
    except LLMError as e:
        return {"error": str(e)[:300]}


def compose(picture: Path, text: str, red_word: str, out: Path) -> None:
    from PIL import Image, ImageDraw, ImageFont

    im = Image.open(picture).convert("RGB")
    s = max(W / im.width, H / im.height)
    im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    im = im.crop(((im.width - W) // 2, (im.height - H) // 2, (im.width - W) // 2 + W, (im.height - H) // 2 + H))
    shade = Image.new("L", (W, H))
    sd = ImageDraw.Draw(shade)
    for x in range(W):  # dark on the left for the words, clear on the right for the picture
        sd.line([(x, 0), (x, H)], fill=int(190 * max(0.0, 1 - x / (W * 0.62))))
    im = Image.composite(Image.new("RGB", (W, H), (0, 0, 0)), im, shade)
    font_path = Path(matplotlib.get_data_path()) / "fonts" / "ttf" / "DejaVuSans-Bold.ttf"
    words = text.upper().split()
    lines = [" ".join(words[:2]), " ".join(words[2:])] if len(words) > 2 else [" ".join(words)]
    lines = [ln for ln in lines if ln]
    size = 150
    while size > 60:
        font = ImageFont.truetype(str(font_path), size)
        if all(font.getlength(ln) <= W * 0.58 for ln in lines):
            break
        size -= 6
    d = ImageDraw.Draw(im)
    y = (H - len(lines) * size * 1.08) / 2
    for ln in lines:
        x = 56
        for w in ln.split():
            col = RED if w.strip(".,!?") == red_word.upper().strip(".,!?") else WHITE
            d.text((x, y), w, font=font, fill=col, stroke_width=max(4, size // 22), stroke_fill=(0, 0, 0))
            x += font.getlength(w + " ")
        y += size * 1.08
    im.save(out, quality=92)


def make(out_dir: Path, title: str, question: str, visuals: list[dict], seen: dict[str, str],
         script: dict | None = None) -> dict:
    pics = {v["id"]: v for v in visuals if v.get("photo") and float(v.get("zoom") or 1.0) == 1.0}
    seen = {k: s for k, s in seen.items() if k in pics and s}
    key = ""
    if script:  # the hook and the answer: the first and last scene
        key = "\n".join(s["text"] for sc in (script["scenes"][:1] + script["scenes"][-1:]) for s in sc["sentences"])
    res = choose(title, question, seen, key) if seen else {"error": "no checked pictures"}
    pick = res.get("picture", "").strip()
    if pick not in pics:  # fall back: the first checked picture, words from the title
        pick = next(iter(seen), None) or next(iter(pics), None)
        res = {**res, "fallback": True, "text": " ".join(title.split()[:3]), "red_word": title.split()[0]}
    if not pick:
        return {"error": "no picture for a thumbnail"}
    text = " ".join(res["text"].replace("?", "").replace("!", "").split()[:4])
    compose(Path(pics[pick]["photo"]["path"]), text, res.get("red_word", ""), out_dir / "thumbnail.jpg")
    info = {"picture": pick, "text": text, "red_word": res.get("red_word", ""), "seen": seen.get(pick, ""),
            "picture_source": pics[pick]["photo"].get("source_page"), **({"fallback": True} if res.get("fallback") else {}),
            **({"ai_error": res["error"]} if res.get("error") else {})}
    (out_dir / "thumbnail.json").write_text(json.dumps(info, indent=1, ensure_ascii=False), encoding="utf-8")
    return info
