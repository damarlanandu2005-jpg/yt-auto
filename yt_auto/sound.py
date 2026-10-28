"""Final sound mix: narration + quiet background music + soft transition sounds.

Owner's watch notes (28 Oct): hit videos use very quiet music, silences that feel intense, and soft click
sounds when the picture changes. Music sits about 20 dB under the voice while it speaks and rises a little
in the pauses. The transition sounds are made here from noise and a tone, so they are our own work (no
licence needed). The clean narration.wav stays untouched for the subtitles.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import soundfile as sf

UNDER_SPEECH_DB, UNDER_PAUSE_DB = -21.0, -14.0  # music level vs the voice's average loudness
CLICK_DB, WHOOSH_DB = -16.0, -11.0              # transition sounds vs the voice
SFX_RECORD = {"kind": "sound effects", "name": "transition click and whoosh, generated in code (yt_auto/sound.py)",
              "source_page": "own work", "licence": "own work (all rights held by the channel owner)",
              "attribution": "none required"}


def _db(x: float) -> float:
    return 10 ** (x / 20)


def click(sr: int) -> np.ndarray:
    n = int(0.06 * sr)
    t = np.arange(n) / sr
    rng = np.random.default_rng(1)
    tone = np.sin(2 * np.pi * 1400 * t) * np.exp(-t * 90)
    tick = rng.standard_normal(n) * np.exp(-t * 220) * 0.4
    return (tone + tick).astype(np.float32)


def whoosh(sr: int) -> np.ndarray:
    n = int(0.55 * sr)
    t = np.linspace(0, 1, n)
    rng = np.random.default_rng(2)
    noise = rng.standard_normal(n)
    k = int(sr / 1500)  # soften: moving average = low-pass
    noise = np.convolve(noise, np.ones(k) / k, mode="same")
    env = np.sin(np.pi * t) ** 2
    return (noise * env / (np.abs(noise).max() + 1e-9)).astype(np.float32)


def _smooth(x: np.ndarray, sr: int, seconds: float) -> np.ndarray:
    a = 1 - np.exp(-1 / (seconds * sr / 512))
    y = np.empty_like(x)
    acc = x[0]
    for i, v in enumerate(x):
        acc += a * (v - acc)
        y[i] = acc
    return y


def mix(narration: Path, music: Path | None, cuts: list[tuple[float, str]], out: Path) -> dict:
    """cuts: (time in seconds, "click" | "whoosh"). Returns numbers for the report."""
    voice, sr = sf.read(narration, dtype="float32")
    if voice.ndim > 1:
        voice = voice.mean(axis=1)
    n = len(voice)
    hop = 512
    frames = n // hop + 1
    rms = np.sqrt(np.array([np.mean(voice[i * hop:(i + 1) * hop] ** 2) if i * hop < n else 0.0
                            for i in range(frames)]) + 1e-12)
    speaking = rms > 0.01
    voice_rms = float(np.sqrt(np.mean(voice[np.repeat(speaking, hop)[:n]] ** 2))) if speaking.any() else 0.1
    info = {"music": bool(music), "cuts": len(cuts)}
    outbuf = voice.copy()
    if music:
        bed, msr = sf.read(music, dtype="float32")
        if bed.ndim > 1:
            bed = bed.mean(axis=1)
        if msr != sr:
            raise RuntimeError(f"music sample rate {msr} != {sr}")
        reps = int(np.ceil(n / len(bed)))
        bed = np.tile(bed, reps)[:n]
        bed /= float(np.sqrt(np.mean(bed ** 2))) + 1e-9
        target = np.where(speaking, _db(UNDER_SPEECH_DB), _db(UNDER_PAUSE_DB)) * voice_rms
        gain = np.repeat(_smooth(target.astype(np.float64), sr, 0.35), hop)[:n]
        fade = np.ones(n)
        f_in, f_out = int(2 * sr), int(3 * sr)
        fade[:f_in] = np.linspace(0, 1, f_in)
        fade[-f_out:] = np.linspace(1, 0, f_out)
        outbuf += (bed * gain * fade).astype(np.float32)
    c, w = click(sr), whoosh(sr)
    for t, kind in cuts:
        snd, lvl = (w, WHOOSH_DB) if kind == "whoosh" else (c, CLICK_DB)
        i = int(t * sr) - (len(snd) // 2 if kind == "whoosh" else 0)
        i = max(0, i)
        j = min(n, i + len(snd))
        outbuf[i:j] += snd[:j - i] * _db(lvl) * voice_rms * 3
    peak = float(np.abs(outbuf).max())
    if peak > 0.98:
        outbuf *= 0.98 / peak
    sf.write(out, outbuf, sr)
    info["voice_rms"] = round(voice_rms, 4)
    return info
