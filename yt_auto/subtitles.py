"""Subtitle timing with faster-whisper (CPU, int8)."""
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

import numpy as np
import soundfile as sf


def _ts(seconds: float) -> str:
    ms = int(round(seconds * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def _load_16k_mono(audio: Path) -> np.ndarray:
    """Resample with FFmpeg and read with soundfile.

    We pass whisper a ready array instead of a file path, so it does not depend
    on PyAV (whose newer releases broke faster-whisper's file decoder).
    """
    with tempfile.TemporaryDirectory() as tmp:
        wav16 = Path(tmp) / "a16k.wav"
        subprocess.run(["ffmpeg", "-nostdin", "-y", "-loglevel", "error", "-i", str(audio),
                        "-ac", "1", "-ar", "16000", str(wav16)], check=True,
                       stdin=subprocess.DEVNULL, timeout=300)
        data, _ = sf.read(wav16, dtype="float32")
    return data


def make_srt(audio: Path, out: Path, model_size: str = "base.en") -> int:
    from faster_whisper import WhisperModel

    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    segments, _ = model.transcribe(_load_16k_mono(audio), language="en", vad_filter=True)
    lines, n = [], 0
    for seg in segments:
        n += 1
        lines.append(f"{n}\n{_ts(seg.start)} --> {_ts(seg.end)}\n{seg.text.strip()}\n")
    out.write_text("\n".join(lines), encoding="utf-8")
    return n
