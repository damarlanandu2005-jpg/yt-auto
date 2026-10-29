"""The owner's own voice (Phase 5 pilot): recording script out, phone recording in.

1. recording_script(): a simple sheet to read from, one numbered sentence per line, per scene.
2. prepare(): the owner's files (one per scene: s01.m4a, s02.m4a ... or one file for the whole video)
   -> cleaned narration.wav (low rumble cut, light noise reduction, pauses over 1 s shortened),
   -> word times from faster-whisper (own process), sentence times from OUR script words,
   -> how closely the recording follows the checked script (the quality gate fails a recording
      that skips or changes sentences: those words were never fact-checked).
"""
from __future__ import annotations

import difflib
import json
import re
import subprocess
import sys
from pathlib import Path

from . import align

AUDIO_EXT = {".m4a", ".mp3", ".wav", ".aac", ".ogg", ".opus", ".flac", ".amr", ".3gp", ".webm", ".mp4"}
SCENE_PAUSE_S = 1.0
CLEAN = "highpass=f=80,afftdn=nf=-25"   # cut low rumble, light noise reduction
QUIET_DB = -45.0      # below this (20 ms windows) counts as a pause
MAX_PAUSE_S = 1.0     # longer pauses inside a file are cut down to KEEP_PAUSE_S
KEEP_PAUSE_S = 0.6
EDGE_S = 0.15         # silence kept at the start and end of each file


def shorten_pauses(path: Path) -> dict:
    """Trim the ends and shorten long pauses, in plain numpy so it behaves the same on every FFmpeg.

    (FFmpeg's silenceremove left a 1.4 s tail untouched on 6.1; its options changed between versions.)"""
    import numpy as np
    import soundfile as sf

    x, sr = sf.read(path, dtype="float32")
    win = int(0.02 * sr)
    n = len(x) // win
    if n == 0:
        return {"cut_s": 0.0}
    rms = np.sqrt(np.mean(x[: n * win].reshape(n, win) ** 2, axis=1) + 1e-12)
    loud = 20 * np.log10(rms) > QUIET_DB
    if not loud.any():
        return {"cut_s": 0.0}
    first, last = int(np.argmax(loud)), int(n - 1 - np.argmax(loud[::-1]))
    keep_edge = int(EDGE_S / 0.02)
    keep = np.zeros(n, dtype=bool)
    keep[max(0, first - keep_edge): min(n, last + 1 + keep_edge)] = True
    i = first
    while i <= last:  # long quiet runs inside: keep only KEEP_PAUSE_S of them
        if not loud[i]:
            j = i
            while j <= last and not loud[j]:
                j += 1
            if (j - i) * 0.02 > MAX_PAUSE_S:
                half = int(KEEP_PAUSE_S / 0.02 / 2)
                keep[i + half: j - half] = False
            i = j
        else:
            i += 1
    y = x[: n * win].reshape(n, win)[keep].reshape(-1)
    sf.write(path, y, sr)
    return {"cut_s": round((len(x) - len(y)) / sr, 2)}


def recording_script(script: dict, path: Path) -> None:
    lines = [f"# Recording script: {script['title']}", "",
             "How to record (about 10 minutes):",
             "- Quiet room, phone about a hand's width from your mouth, same place for every scene.",
             "- One file per scene, named s01, s02, ... (any phone format: m4a, mp3, wav). One file for the "
             "whole video also works.",
             "- Read every sentence as written. A small slip is fine; don't skip or change sentences "
             "(each one was fact-checked as written).",
             "- If you stumble, record that scene's file again (retakes inside a file stay in the video).",
             "- Upload: GitHub repo -> Add file -> Upload files -> folder voice/<the name I give you>/", ""]
    for sc in script["scenes"]:
        lines += [f"## {sc['id']} — {sc['heading']}", ""]
        for i, s in enumerate(sc["sentences"], 1):
            lines.append(f"{i}. {s['text']}")
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def _files(audio_dir: Path) -> list[Path]:
    return sorted(p for p in audio_dir.iterdir() if p.suffix.lower() in AUDIO_EXT)


def _clean(src: Path, dst: Path, log: Path) -> None:
    r = subprocess.run(["ffmpeg", "-nostdin", "-y", "-hide_banner", "-loglevel", "error", "-i", str(src), "-vn",
                        "-ac", "1", "-ar", "24000", "-af", CLEAN, str(dst)], stdin=subprocess.DEVNULL,
                       capture_output=True, text=True, timeout=600)
    log.write_text(r.stderr)
    if r.returncode:
        raise RuntimeError(f"could not read {src.name}: {r.stderr[-400:]}")


def _duration(p: Path) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1",
                        str(p)], stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=60)
    return float(r.stdout.strip())


def _silence(path: Path, seconds: float) -> None:
    subprocess.run(["ffmpeg", "-nostdin", "-y", "-loglevel", "error", "-f", "lavfi", "-i",
                    f"anullsrc=r=24000:cl=mono", "-t", f"{seconds}", str(path)],
                   stdin=subprocess.DEVNULL, check=True, timeout=60)


def prepare(audio_dir: Path, script: dict, out: Path, root: Path) -> dict:
    files = _files(audio_dir)
    if not files:
        raise RuntimeError(f"no recordings found in {audio_dir}")
    scenes = script["scenes"]
    per_scene = len(files) == len(scenes) and all(re.match(rf"s0*{i + 1}\b", f.stem.lower()) for i, f in enumerate(files))
    if not per_scene and len(files) != 1:
        raise RuntimeError(f"expected one file per scene (s01..s{len(scenes):02}) or one file for the whole video; "
                           f"found {[f.name for f in files]}")
    work = out / "audio"
    work.mkdir(exist_ok=True)
    pause = work / "scene_pause.wav"
    _silence(pause, SCENE_PAUSE_S)
    parts, ranges, offset = [], [], 0.0  # ranges: (scene ids covered, start, end)
    for i, f in enumerate(files):
        dst = work / f"owner_{i + 1:02}.wav"
        _clean(f, dst, out / "ffmpeg_logs" / f"owner_clean_{i + 1:02}.log")
        cut = shorten_pauses(dst)
        print(f"[voice] {f.name}: removed {cut['cut_s']} s of long pauses and silent ends", flush=True)
        d = _duration(dst)
        ids = [scenes[i]["id"]] if per_scene else [sc["id"] for sc in scenes]
        ranges.append((ids, offset, offset + d))
        parts += [dst, pause]
        offset += d + SCENE_PAUSE_S
    listfile = work / "owner_concat.txt"
    listfile.write_text("".join(f"file '{p.resolve()}'\n" for p in parts))
    subprocess.run(["ffmpeg", "-nostdin", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(listfile),
                    "-c", "copy", str(out / "narration.wav")], stdin=subprocess.DEVNULL, check=True, timeout=600)
    total = _duration(out / "narration.wav")

    # Word times from whisper (separate process: CLAUDE.md lesson 2)
    r = subprocess.run([sys.executable, "-m", "yt_auto.subtitles", "--words", str(out / "narration.wav"),
                        str(out / "heard_words.json")], cwd=root, capture_output=True, text=True,
                       stdin=subprocess.DEVNULL, timeout=1200)
    heard = json.loads((out / "heard_words.json").read_text()) if r.returncode == 0 else []

    sentences, scene_rows, match = [], [], {"by_scene": {}, "missing_sentences": []}
    by_id = {sc["id"]: sc for sc in scenes}
    total_words = matched_words = 0
    for ids, a, b in ranges:
        sents = [s for sid in ids for s in by_id[sid]["sentences"]]
        text = " ".join(s["text"] for s in sents)
        timed = align.time_words(text, a, b, heard)
        words = text.split()
        near = [h for h in heard if a - 0.3 <= (h["start"] + h["end"]) / 2 <= b + 0.3]
        sm = difflib.SequenceMatcher(a=[align._norm(w) for w in words], b=[align._norm(h["word"]) for h in near],
                                     autojunk=False)
        hit = [False] * len(words)
        for blk in sm.get_matching_blocks():
            for k in range(blk.size):
                hit[blk.a + k] = True
        k = 0
        for s in sents:
            n = len(s["text"].split())
            span = timed[k:k + n]
            got = sum(hit[k:k + n]) / max(n, 1)
            if heard and got < 0.5:
                match["missing_sentences"].append({"id": s["id"], "text": s["text"], "heard_share": round(got, 2)})
            sentences.append({"id": s["id"], "scene": next(sid for sid in ids if s in by_id[sid]["sentences"]),
                              "text": s["text"], "start": round(span[0][1], 3), "end": round(span[-1][2], 3)})
            k += n
        total_words += len(words)
        matched_words += sum(hit)
        for sid in ids:
            ss = [x for x in sentences if x["scene"] == sid]
            scene_rows.append({"id": sid, "heading": by_id[sid]["heading"], "start": ss[0]["start"] if per_scene is False else a,
                               "end": ss[-1]["end"] if per_scene is False else b})
    match["heard_words"] = len(heard)
    match["script_words_heard"] = round(matched_words / max(total_words, 1), 3) if heard else None
    match["mode"] = "one file per scene" if per_scene else "one file"
    match["files"] = [f.name for f in files]
    (out / "voice_match.json").write_text(json.dumps(match, indent=1, ensure_ascii=False), encoding="utf-8")
    scene_rows[0]["start"] = 0.0
    return {"sentences": sentences, "scenes": scene_rows, "total": total, "heard": heard, "match": match}
