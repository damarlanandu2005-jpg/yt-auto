"""Subtitle timing with faster-whisper (CPU, int8)."""
from __future__ import annotations

from pathlib import Path


def _ts(seconds: float) -> str:
    ms = int(round(seconds * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def make_srt(audio: Path, out: Path, model_size: str = "base.en") -> int:
    from faster_whisper import WhisperModel

    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    segments, _ = model.transcribe(str(audio), language="en", vad_filter=True)
    lines, n = [], 0
    for seg in segments:
        n += 1
        lines.append(f"{n}\n{_ts(seg.start)} --> {_ts(seg.end)}\n{seg.text.strip()}\n")
    out.write_text("\n".join(lines), encoding="utf-8")
    return n
