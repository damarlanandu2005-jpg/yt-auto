"""Narration with Kokoro (kokoro-onnx, CPU only)."""
from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import soundfile as sf

SENTENCE_PAUSE_S = 0.4   # pause between sentences
SCENE_PAUSE_S = 1.0      # pause between scenes


def split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p for p in parts if p]


class Narrator:
    def __init__(self, model_path: Path, voices_path: Path, voice: str = "af_heart", speed: float = 0.9):
        from kokoro_onnx import Kokoro  # imported here so other modules don't need onnxruntime

        self.kokoro = Kokoro(str(model_path), str(voices_path))
        self.voice = voice
        self.speed = speed
        self.sample_rate = 24000

    def speak(self, text: str | list[str], out_path: Path, tail_pause: float = SCENE_PAUSE_S) -> float:
        """Synthesise one scene sentence by sentence; return duration in seconds."""
        return self.speak_timed(text, out_path, tail_pause)[0]

    def speak_timed(self, text: str | list[str], out_path: Path,
                    tail_pause: float = SCENE_PAUSE_S) -> tuple[float, list[tuple[float, float]]]:
        """Like speak(), but also return each sentence's (start, end) in seconds within the file.

        We make the audio one sentence at a time, so these times are exact: this is
        what lines up subtitles and visuals with our own script text.
        """
        sentences = split_sentences(text) if isinstance(text, str) else text
        chunks, spans, pos = [], [], 0
        for sentence in sentences:
            samples, sr = self.kokoro.create(sentence, voice=self.voice, speed=self.speed, lang="en-us")
            self.sample_rate = sr
            samples = samples.astype(np.float32)
            a, b = _speech_bounds(samples, sr)
            spans.append(((pos + a) / sr, (pos + b) / sr))
            pause = np.zeros(int(sr * SENTENCE_PAUSE_S), dtype=np.float32)
            chunks += [samples, pause]
            pos += len(samples) + len(pause)
        chunks.append(np.zeros(int(self.sample_rate * tail_pause), dtype=np.float32))
        audio = np.concatenate(chunks)
        sf.write(out_path, audio, self.sample_rate)
        return len(audio) / self.sample_rate, spans


def _speech_bounds(x: np.ndarray, sr: int, threshold: float = 0.01) -> tuple[int, int]:
    """First and last sample of real speech (Kokoro adds a little silence at both ends)."""
    loud = np.flatnonzero(np.abs(x) > threshold)
    if loud.size == 0:
        return 0, len(x)
    pad = int(0.03 * sr)
    return max(0, int(loud[0]) - pad), min(len(x), int(loud[-1]) + pad)
