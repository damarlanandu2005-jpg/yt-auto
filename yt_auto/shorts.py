"""Shorts from a finished long video: one "zoom journey" story, vertical 1080x1920, under 60 seconds.

Owner's study of a top Short (28 Oct, "How Stitches Work"): one continuous camera journey with no hard cuts
(wide -> close -> inside -> back out), every stage changing exactly on its words, a complete mini story.
We copy that structure (not its realistic 3D look):
  * the words are sentences of the long video's fact-checked script, reused verbatim (ids kept), plus one hook
    question and a closing line, neither with any claim: so every fact stays checked and sourced;
  * 6-8 ink drawings of ONE subject, each a closer view than the last, then back out, each looked at by the
    blind picture check; a rejected one becomes a closer crop of the drawing before it;
  * slow non-stop zoom with soft dissolves between drawings (no hard cuts), big captions 1-3 words at a time,
    numbers and the key word in red, music and whoosh as in the long video, louder mix (-13 LUFS) for phones.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

from . import align, drawings, keywords, render, shots
from .llm import LIGHT, llm

W, H, FPS = 1080, 1920, 30
XFADE = 0.5                  # dissolve between drawings
LONG_S = 6.5                 # longest time one view stays on screen
MAX_S, MIN_WORDS, MAX_WORDS = 58.0, 55, 115
END_LINE = "The full story is in our long video on this channel."
STYLE = drawings.STYLE + ", tall vertical composition with the subject in the centre"

PLAN_SCHEMA = {"type": "object", "properties": {"shorts": {"type": "array", "items": {"type": "object", "properties": {
    "title": {"type": "string", "description": "Short title, at most 60 characters, honest"},
    "hook": {"type": "string", "description": "ONE short question (max 14 words), no numbers, no claim"},
    "sentences": {"type": "array", "items": {"type": "string"}, "description": "ids of consecutive script sentences"},
    "subject": {"type": "string", "description": "ONE physical, drawable object"},
    "shots": {"type": "array", "minItems": 6, "maxItems": 8, "items": {"type": "object", "properties": {
        "sentence": {"type": "string"}, "view": {"type": "string"}}, "required": ["sentence", "view"]}}},
    "required": ["title", "hook", "sentences", "subject", "shots"]}}}, "required": ["shorts"]}


def plan(script: dict, n: int) -> list[dict]:
    lines = "\n".join(f"{s['id']}: {s['text']}" for sc in script["scenes"] for s in sc["sentences"])
    prompt = f"""Below is the fact-checked narration of a long explainer video, one sentence per line with its id.
Plan {n} YouTube Short(s), each a "zoom journey" like the best science Shorts: one complete mini story
(a puzzle, then the answer) told with drawings of ONE subject seen ever closer, then pulled back out.
For each Short:
- sentences: 4 to 9 CONSECUTIVE sentence ids that together tell a complete mini story and make sense alone,
  {MIN_WORDS}-{MAX_WORDS} words in total. Use the sentences exactly as they are; do not invent new facts.
- hook: one short question that opens the Short and makes people stay. Plain words only: NO numbers,
  no claim, no fake urgency (the numbers come in the checked sentences).
- title: honest, at most 60 characters.
- subject: ONE physical object a child could draw and anyone would recognise, which the sentences are about
  or which the script itself uses as a comparison (e.g. "planet Earth", "a spiral galaxy", "a rubber band
  with dots on it", "a telescope"). NOT an idea, beam, field, fabric, energy or "space itself": those come
  out as abstract light bursts that viewers cannot read.
- shots: 6 to 8 pictures of that subject in order: start wide, move closer step by step, go inside or
  close up, then pull back out to a wide view at the end. Each view is one plain sentence naming the
  concrete objects in the picture and where they are, e.g. "planet Earth small in the centre, surrounded
  by many tiny spiral galaxies". No people's faces, no text, no logos, no abstract light rays.
  Each shot names the sentence id it plays under; spread the shots over all the sentences.
{"Different Shorts must use different sentences." if n > 1 else ""}

{lines}"""
    res = llm(prompt, schema=PLAN_SCHEMA, name="shorts_plan", temperature=0.6, models=LIGHT)
    return _clean_plans(res["shorts"], script)


def _clean_plans(plans: list[dict], script: dict) -> list[dict]:
    order = [s["id"] for sc in script["scenes"] for s in sc["sentences"]]
    text = {s["id"]: s for sc in script["scenes"] for s in sc["sentences"]}
    out, used = [], set()
    for p in plans:
        ids = [i for i in p["sentences"] if i in text and i not in used]
        if not ids:
            continue
        a, b = order.index(ids[0]), order.index(ids[-1])
        ids = order[a:b + 1]  # consecutive, as asked
        while sum(len(text[i]["text"].split()) for i in ids) > MAX_WORDS and len(ids) > 3:
            ids = ids[:-1]
        if sum(len(text[i]["text"].split()) for i in ids) < MIN_WORDS - 20:
            continue
        hook = p["hook"].strip()
        if not hook.endswith("?") or len(hook.split()) > 14 or re.search(r"\d", hook):
            hook = ""  # a hook may only be a plain question: it is not fact-checked
        shots_ = [s for s in p["shots"] if s.get("view")][:8]
        if any(s.get("sentence") not in ids for s in shots_):  # spread them evenly over the sentences instead
            for k, s in enumerate(shots_):
                s["sentence"] = ids[min(len(ids) - 1, k * len(ids) // len(shots_))]
        shots_.sort(key=lambda s: ids.index(s["sentence"]))  # keep the story order
        out.append({**p, "sentences": ids, "hook": hook, "shots": shots_})
        used.update(ids)
    return out


def _speech(p: dict, script: dict, delivery: dict, narrator, out: Path) -> tuple[list[dict], float]:
    text = {s["id"]: s for sc in script["scenes"] for s in sc["sentences"]}
    items = ([("hook", p["hook"], "slow")] if p["hook"] else []) + \
        [(i, text[i]["text"], delivery.get(i, "normal")) for i in p["sentences"]] + [("end", END_LINE, "normal")]
    dur, spans = narrator.speak_timed([(t, d) for _, t, d in items], out, tail_pause=0.4)
    return [{"id": k, "text": t, "start": a, "end": b} for (k, t, _), (a, b) in zip(items, spans)], dur


def _shot_times(p: dict, lines: list[dict], total: float) -> list[tuple[float, float]]:
    """Each drawing starts with its sentence (the first one at 0); shots sharing a sentence split it."""
    start = {x["id"]: x["start"] for x in lines}
    end = {x["id"]: x["end"] for x in lines}
    by_sent: dict[str, list[int]] = {}
    for k, s in enumerate(p["shots"]):
        by_sent.setdefault(s["sentence"], []).append(k)
    t0 = []
    for k, s in enumerate(p["shots"]):
        group = by_sent[s["sentence"]]
        a, b = start[s["sentence"]], end[s["sentence"]]
        t0.append(a + (b - a) * group.index(k) / len(group))
    t0[0] = 0.0
    t0 = [max(t, t0[i - 1] + 1.2) if i else t for i, t in enumerate(t0)]  # each at least 1.2 s
    return [(a, (t0[i + 1] if i + 1 < len(t0) else total)) for i, a in enumerate(t0)]


def _vertical(src: Path, out: Path, zoom: float = 1.0) -> None:
    """Square drawing -> 1080x1920 portrait crop (centre), optionally closer."""
    from PIL import Image

    im = Image.open(src).convert("RGB")
    ch = im.height / zoom
    cw = ch * W / H
    if cw > im.width / zoom:
        cw = im.width / zoom
        ch = cw * H / W
    x0, y0 = (im.width - cw) / 2, (im.height - ch) / 2
    im.crop((round(x0), round(y0), round(x0 + cw), round(y0 + ch))).resize((W, H), Image.LANCZOS).save(out)


def _draw(p: dict, out: Path, log: dict) -> list[Path]:
    """One drawing per shot (Cloudflare FLUX, square), checked blind; a rejected one = closer crop of the one before."""
    raw = out / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    made, vis = {}, []
    for k, s in enumerate(p["shots"]):
        f = raw / f"shot{k + 1}.png"
        try:
            data = drawings.cloud_draw(f"{p['subject']}: {s['view']}, {STYLE}")
        except Exception as e:  # noqa: BLE001
            log.setdefault("draw_errors", []).append(f"shot{k + 1}: {e!r}"[:200])
            continue
        f.write_bytes(data)
        made[k] = f
        rec = drawings.record(f, f"{p['subject']}: {s['view']}", cloud=True)
        rec["prompt"] = f"{p['subject']}: {s['view']}, {STYLE}"
        f.with_suffix(".licence.json").write_text(json.dumps(rec, indent=1, ensure_ascii=False))
        vis.append({"id": f"shot{k + 1}", "k": k, "photo": {"path": str(f), **rec},
                    "photo_subject": f"{p['subject']}: {s['view']}", "text": s["view"]})
    check: dict = {}
    shots._verify(vis, check, drawings=True)
    ok = {v["k"] for v in vis if v.get("photo")} if not check.get("verify_error") else set()  # fail closed
    log.update(drawn=len(made), passed=len(ok), rejected=check.get("rejected_after_looking", []),
               verify_error=check.get("verify_error"))
    redo = [v for v in vis if v["k"] not in ok]
    if redo and not check.get("verify_error"):  # one more try, plainer prompt, for the rejected ones
        again = []
        for v in redo:
            k = v["k"]
            f = raw / f"shot{k + 1}b.png"
            try:
                f.write_bytes(drawings.cloud_draw(f"simple clear drawing of {p['subject']}: {p['shots'][k]['view']}, "
                                                  f"{STYLE}"))
            except Exception as e:  # noqa: BLE001
                log.setdefault("draw_errors", []).append(f"shot{k + 1}b: {e!r}"[:200])
                continue
            rec = drawings.record(f, v["photo_subject"], cloud=True)
            f.with_suffix(".licence.json").write_text(json.dumps(rec, indent=1, ensure_ascii=False))
            again.append({**v, "id": f"shot{k + 1}b", "photo": {"path": str(f), **rec}})
        check2: dict = {}
        shots._verify(again, check2, drawings=True)
        if not check2.get("verify_error"):
            for v in again:
                if v.get("photo"):
                    made[v["k"]] = Path(v["photo"]["path"])
                    ok.add(v["k"])
        log.update(redrawn=len(again), passed=len(ok), rejected_again=check2.get("rejected_after_looking", []))
    frames, last, zoom = [], None, 1.0
    for k in range(len(p["shots"])):
        f = out / f"frame{k + 1}.png"
        if k in ok:
            _vertical(made[k], f)
            last, zoom = made[k], 1.0
        elif last is not None:  # stand-in: a closer look at the last good drawing
            zoom = min(zoom + 0.35, 2.0)
            _vertical(last, f, zoom)
        else:
            continue
        frames.append((k, f))
    log["stand_ins"] = len(p["shots"]) - len(ok)
    return frames


def _video(frames: list[tuple[int, Path]], times: list[tuple[float, float]], out: Path) -> Path:
    """Slow zoom on every drawing, soft dissolves between them (no hard cuts)."""
    parts = []  # (picture, seconds): a picture held longer than LONG_S becomes closer views of itself
    for j, (k, f) in enumerate(frames):
        a = times[k][0]
        b = times[frames[j + 1][0]][0] if j + 1 < len(frames) else times[-1][1]
        d = max(b - a, 1.0)
        n_parts = max(1, round(d / 4.5)) if d > LONG_S else 1
        for i in range(n_parts):
            g = f
            if i:
                g = out / f"{f.stem}_closer{i}.png"
                _vertical(f, g, 1 + 0.3 * i)
            parts.append((g, d / n_parts))
    segs, durs = [], []
    for j, (f, d) in enumerate(parts):
        frames_left = len(parts) - j - 1
        length = d + (XFADE if frames_left else 0)
        n = round(length * FPS)
        seg = out / f"seg{j + 1}.mp4"
        z = "min(1+0.0009*on,1.15)" if j % 2 == 0 else "max(1.15-0.0009*on,1.0)"
        render._run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-i", str(f), "-vf",
                     f"scale={int(W * 1.15)}:{int(H * 1.15)},zoompan=z='{z}':x='iw/2-(iw/zoom/2)':"
                     f"y='ih/2-(ih/zoom/2)':d={n}:s={W}x{H}:fps={FPS},format=yuv420p",
                     "-frames:v", str(n), "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", str(seg)],
                    name=f"short_{out.name}_seg{j + 1}")
        segs.append(seg)
        durs.append(d)
    joined = out / "joined.mp4"
    if len(segs) == 1:
        segs[0].replace(joined)
        return joined
    inputs, chain, last, off = [], [], "[0:v]", 0.0
    for s in segs:
        inputs += ["-i", str(s)]
    for j in range(1, len(segs)):
        off += durs[j - 1]
        tag = f"[v{j}]"
        chain.append(f"{last}[{j}:v]xfade=transition=fade:duration={XFADE}:offset={off:.3f}{tag}")
        last = tag
    render._run(["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex", ";".join(chain), "-map", last,
                 "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", str(joined)],
                timeout=900, name=f"short_{out.name}_join")
    return joined


def _captions(lines: list[dict], heard: list[dict], key: dict[str, str], path: Path) -> int:
    """Big captions, 1-3 words at a time, timed to the voice; numbers and the key phrase in red."""
    events = []
    for x in lines:
        timed = align.time_words(x["text"], x["start"], x["end"], heard)
        red = {align._norm(w) for w in key.get(x["id"], "").split()}
        chunk: list = []
        for i, (w, a, b) in enumerate(timed):
            chunk.append((w, a, b, bool(re.search(r"\d", w)) or align._norm(w) in red))
            if len(chunk) == 3 or re.search(r"[.,?!;:]$", w) or i == len(timed) - 1:
                events.append(chunk)
                chunk = []
    out = []
    for j, ch in enumerate(events):
        a = ch[0][1]
        b = events[j + 1][0][1] if j + 1 < len(events) else ch[-1][2] + 0.3
        words = []
        for w, _, _, hot in ch:
            t = w.upper()
            if hot:
                t = r"{\c&H3C3CE8&}" + t + r"{\c&HFFFFFF&}"
            words.append(t)
        out.append(f"Dialogue: 0,{keywords._ts(a)},{keywords._ts(b)},Cap,,0,0,0,,"
                   r"{\fad(60,60)\fscx90\fscy90\t(0,90,\fscx100\fscy100)}" + " ".join(words))
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,{keywords.FONT},96,&H00FFFFFF,&H00FFFFFF,&H00000000,&H96000000,1,0,0,0,100,100,1,0,1,7,3,2,70,70,520,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    path.write_text(head + "\n".join(out) + "\n", encoding="utf-8")
    return len(out)


def make(p: dict, n: int, script: dict, sources: dict, delivery: dict, key: dict, narrator, track: dict | None,
         root: Path, out: Path) -> dict:
    """Build Short number n; returns its report."""
    import matplotlib

    from . import sound

    out.mkdir(parents=True, exist_ok=True)
    log: dict = {"title": p["title"], "hook": p["hook"], "sentences": p["sentences"], "subject": p["subject"]}
    lines, total = _speech(p, script, delivery, narrator, out / "narration.wav")
    log["seconds"] = round(total, 1)
    if total > MAX_S + 2:
        log["error"] = f"{total:.1f} s is too long for a Short"
        return log
    r = subprocess.run([sys.executable, "-m", "yt_auto.subtitles", "--words", str(out / "narration.wav"),
                        str(out / "heard.json")], cwd=root, capture_output=True, text=True,
                       stdin=subprocess.DEVNULL, timeout=600)
    heard = json.loads((out / "heard.json").read_text()) if r.returncode == 0 else []
    times = _shot_times(p, lines, total)
    frames = _draw(p, out, log)
    if len(frames) < 3:
        log["error"] = f"only {len(frames)} usable drawings"
        return log
    joined = _video(frames, times, out)
    n_caps = _captions(lines, heard, key, out / "captions.ass")
    fonts = Path(matplotlib.get_data_path()) / "fonts" / "ttf"
    render.burn_ass(joined, out / "captions.ass", fonts, out / "captioned.mp4")
    cuts = [(times[k][0], "whoosh") for k, _ in frames[1:]]
    sound.mix(out / "narration.wav", Path(track["path"]) if track else None, cuts, out / "mix.wav")
    render._run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(out / "captioned.mp4"), "-i", str(out / "mix.wav"),
                 "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-af", "loudnorm=I=-13:TP=-1.0:LRA=9",
                 "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-shortest", "-movflags", "+faststart",
                 str(out / f"short{n}.mp4")], name=f"short_{n}_mux")
    log.update(captions=n_caps, video=f"short{n}.mp4", seconds=round(render.probe_duration(out / f"short{n}.mp4"), 1))
    # description: honest, with the sources of the sentences used and the credits
    idx = {pp["id"]: a for a in sources["articles"] for pp in a["passages"]}
    used = {pid for sc in script["scenes"] for s in sc["sentences"] if s["id"] in p["sentences"] for pid in s["sources"]}
    arts = {idx[x]["title"]: f"{idx[x]['url']}?oldid={idx[x]['revision_id']}" for x in used if x in idx}
    desc = [p["title"], "", "From our long video (full explanation on the channel).", "", "Sources (facts checked):"]
    desc += [f"- {t}: {u}" for t, u in arts.items()]
    desc += ["", "Illustrations: AI-generated drawings (FLUX.1 schnell, Apache-2.0)."]
    if track:
        desc.append(f"Music: \"{track['title']}\" by {track['author']}, {track['licence']} {track['source_page']}")
    desc += ["Narration voice: Kokoro text-to-speech (synthetic voice). Fact-checked and reviewed by a human.",
             "", "#Shorts #space #science"]
    (out / f"short{n}_description.txt").write_text("\n".join(desc) + "\n", encoding="utf-8")
    return log
