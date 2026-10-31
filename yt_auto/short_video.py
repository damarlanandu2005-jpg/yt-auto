"""Assemble a Stickman Short from the checked script and the FLUX scene pictures (owner decision 31 Oct 2026).

Per scene: Kokoro narration, one picture (576x1024, upscaled to 1080x1920) shown as several shots of about 2.5 s,
each a different slow zoom/pan of the same picture (cartoon/TEMPLATE.md: something new every 2-4 seconds). One-word
captions (bold white, black edge, numbers yellow) at 72 % of the height, whoosh at scene changes and a soft click at
shot changes (sound.py), final loudness -14 LUFS. No AI is used here: plain code and FFmpeg only.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from . import align, render, sound

W, H = 1080, 1920
SHOT_S = 2.5          # target length of one shot
MIN_SHOT_S = 1.6
SCENE_PAUSE_S = 0.5   # silence after each scene (the long-video default of 1.0 s is slow for a Short)
# (zoom start, zoom end, focus x/y start, focus x/y end): mild, so the hero (usually near the middle) stays in view
MOTIONS = [
    (1.00, 1.22, (0.50, 0.55), (0.50, 0.50)),   # slow push in
    (1.25, 1.05, (0.50, 0.50), (0.50, 0.55)),   # pull back
    (1.15, 1.15, (0.35, 0.50), (0.65, 0.50)),   # drift right
    (1.15, 1.15, (0.65, 0.50), (0.35, 0.50)),   # drift left
    (1.05, 1.30, (0.50, 0.45), (0.50, 0.42)),   # push in on the upper middle
]
YELLOW = r"{\c&H00E8FF&}"   # numbers (ASS colours are BGR)
FONT = "DejaVu Sans"


def delivery(script: dict) -> dict[str, list]:
    """Plain-code delivery marks (the long-video AI marker is gone with Gemini): the answer is a reveal, the closing
    line is slow, the rest normal. Returns {scene index: [(sentence, mark)]}."""
    out = {}
    for i, sc in enumerate(script["scenes"]):
        role = sc.get("role", "step")
        marks = []
        for j, s in enumerate(sc["sentences"]):
            mark = "normal"
            if role == "answer" and j == 0:
                mark = "reveal"
            elif role == "end":
                mark = "slow"
            marks.append((s["text"], mark))
        out[i] = marks
    return out


def split_shots(duration: float) -> list[float]:
    n = max(1, round(duration / SHOT_S))
    while n > 1 and duration / n < MIN_SHOT_S:
        n -= 1
    return [duration / n] * n


def make_audio(script: dict, narrator, out_dir: Path) -> list[dict]:
    """Speak every scene; return [{id, start, end, sentences: [{text, start, end}], wav}] with times in the final video."""
    from .cartoon import scene_ids

    marks = delivery(script)
    scenes, clock = [], 0.0
    for i, (sid, sc) in enumerate(zip(scene_ids(script), script["scenes"])):
        wav = out_dir / f"{sid}.wav"
        dur, spans = narrator.speak_timed(marks[i], wav, tail_pause=SCENE_PAUSE_S)
        sents = [{"text": s["text"], "start": clock + a, "end": clock + b} for s, (a, b) in zip(sc["sentences"], spans)]
        scenes.append({"id": sid, "start": clock, "end": clock + dur, "sentences": sents, "wav": str(wav)})
        clock += dur
    return scenes


def upscale(pic: Path, out: Path) -> Path:
    """The FLUX picture (576x1024) -> 2160x3840, so zoompan has detail to move over; the result is 1080x1920."""
    from PIL import Image, ImageFilter

    im = Image.open(pic).convert("RGB")
    im = im.resize((W * 2, H * 2), Image.LANCZOS).filter(ImageFilter.UnsharpMask(radius=2, percent=60, threshold=2))
    im.save(out, quality=95)
    return out


def make_shot(image: Path, duration: float, motion: tuple, out: Path) -> None:
    z0, z1, (fx0, fy0), (fx1, fy1) = motion
    frames = max(1, round(duration * render.FPS))
    t = f"(on/{frames})"
    z = f"{z0}+({z1}-{z0})*{t}"
    x = f"(iw-iw/zoom)*({fx0}+({fx1}-{fx0})*{t})"
    y = f"(ih-ih/zoom)*({fy0}+({fy1}-{fy0})*{t})"
    vf = f"zoompan=z='{z}':x='{x}':y='{y}':d={frames}:s={W}x{H}:fps={render.FPS},format=yuv420p"
    render._run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(image), "-vf", vf, "-frames:v", str(frames),
                 "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-threads", render.threads(), str(out)],
                name=f"shot_{out.stem}")


def make_video_track(scenes: list[dict], pictures: dict[str, Path], work: Path) -> tuple[Path, list[tuple[float, str]]]:
    """Joined silent video; also the cut times for the sounds: (seconds, 'whoosh' | 'click')."""
    segs, cuts, k = [], [], 0
    for si, sc in enumerate(scenes):
        big = upscale(pictures[sc["id"]], work / f"{sc['id']}_big.jpg")
        if si:
            cuts.append((sc["start"], "whoosh"))
        t = sc["start"]
        shots = split_shots(sc["end"] - sc["start"])
        for j, d in enumerate(shots):
            motion = MOTIONS[0] if j == 0 else (MOTIONS[4] if j == len(shots) - 1 and len(shots) > 2 else MOTIONS[(k + j) % 4])
            seg = work / f"shot_{k:02d}.mp4"
            make_shot(big, d, motion, seg)
            segs.append(seg)
            if j:
                cuts.append((t, "click"))
            t += d
            k += 1
    out = work / "video_silent.mp4"
    render.concat_video(segs, out)
    return out, cuts


def _ts(t: float) -> str:
    cs = int(round(t * 100))
    return f"{cs // 360000}:{cs // 6000 % 60:02}:{cs // 100 % 60:02}.{cs % 100:02}"


def caption_events(scenes: list[dict]) -> list[tuple[float, float, str]]:
    """One word at a time, timed inside each sentence's exact span (words share the span by length)."""
    ev = []
    for sc in scenes:
        for s in sc["sentences"]:
            for w, a, b in align.time_words(s["text"], s["start"], s["end"], []):
                word = w.strip(".,;:!?\"'()")
                if word:
                    ev.append((a, b, word))
    out = []
    for i, (a, b, w) in enumerate(ev):  # a word stays until the next one starts (no flicker), at most 0.9 s
        nxt = ev[i + 1][0] if i + 1 < len(ev) else b + 0.3
        out.append((a, min(max(b, a + 0.25), nxt, a + 0.9), w))
    return out


def write_ass(evs: list[tuple[float, float, str]], path: Path) -> int:
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Word,{FONT},96,&H00FFFFFF,&H00FFFFFF,&H00000000,&H96000000,1,0,0,0,100,100,1,0,1,7,2,2,60,60,470,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = []
    for a, b, w in evs:
        text = (YELLOW if re.search(r"\d", w) else "") + w.upper()
        pop = r"{\fad(40,60)\fscx85\fscy85\t(0,110,\fscx100\fscy100)}"
        lines.append(f"Dialogue: 0,{_ts(a)},{_ts(b)},Word,,0,0,0,,{pop}{text}")
    path.write_text(head + "\n".join(lines) + "\n", encoding="utf-8")
    return len(lines)


def font_dir() -> Path:
    import matplotlib
    return Path(matplotlib.get_data_path()) / "fonts" / "ttf"


def description(script: dict, sources: dict | None) -> str:
    from . import cartoon

    if not sources:
        return script["title"] + "\n"
    d = cartoon.description(script, sources)
    return d.replace("Voice: text-to-speech. Icons: Lucide (ISC licence).",
                     "Voice: text-to-speech. Pictures: AI-made flat cartoon illustrations (not photos of real events).")


def build(script: dict, pictures: dict[str, Path], narrator, out: Path, sources: dict | None = None) -> dict:
    """The whole Short. `pictures`: {scene id: picture file}. Returns the report (also saved as report.json)."""
    import soundfile as sf

    out.mkdir(parents=True, exist_ok=True)
    work = out / "work"
    work.mkdir(exist_ok=True)
    render.LOG_DIR = out / "logs"
    render.LOG_DIR.mkdir(exist_ok=True)
    scenes = make_audio(script, narrator, work)
    missing = [s["id"] for s in scenes if s["id"] not in pictures]
    if missing:
        raise RuntimeError(f"no picture for scene(s): {missing}")
    parts = [Path(s["wav"]) for s in scenes]
    narration = out / "narration.wav"
    render.concat_audio(parts, narration)
    track, cuts = make_video_track(scenes, pictures, work)
    evs = caption_events(scenes)
    ass = out / "captions.ass"
    write_ass(evs, ass)
    burned = work / "video_captions.mp4"
    render.burn_ass(track, ass, font_dir(), burned)
    mixed = out / "mix.wav"
    info = sound.mix(narration, None, cuts, mixed)
    final = out / "short.mp4"
    render.mux(burned, mixed, final, lufs=-14.0)
    (out / "description.txt").write_text(description(script, sources), encoding="utf-8")
    dur = render.probe_duration(final)
    words = sum(len(s["text"].split()) for sc in scenes for s in sc["sentences"])
    report = {"seconds": round(dur, 1), "words": words, "scenes": len(scenes), "shots": sum(1 for _, k in cuts if k == "click") + len(scenes),
              "captions": len(evs), "cuts": len(cuts), "sound": info,
              "checks": {"length_40_62": 40 <= dur <= 62, "captions_cover_words": len(evs) >= 0.9 * words,
                         "every_scene_has_picture": not missing}}
    (out / "report.json").write_text(json.dumps(report, indent=1))
    (out / "timings.json").write_text(json.dumps([{k: v for k, v in s.items() if k != "wav"} for s in scenes], indent=1))
    return report
