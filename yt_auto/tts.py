"""Narration with Kokoro (kokoro-onnx, CPU only)."""
from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import soundfile as sf

SENTENCE_PAUSE_S = 0.25
SCENE_PAUSE_S = 0.6


def split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p for p in parts if p]


class Narrator:
    def __init__(self, model_path: Path, voices_path: Path, voice: str = "af_heart", speed: float = 1.0):
        from kokoro_onnx import Kokoro  # imported here so other modules don't need onnxruntime

        self.kokoro = Kokoro(str(model_path), str(voices_path))
        self.voice = voice
        self.speed = speed
        self.sample_rate = 24000

    def speak(self, text: str, out_path: Path, tail_pause: float = SCENE_PAUSE_S) -> float:
        """Synthesise one scene sentence by sentence; return duration in seconds."""
        chunks = []
        for sentence in split_sentences(text):
            samples, sr = self.kokoro.create(sentence, voice=self.voice, speed=self.speed, lang="en-us")
            self.sample_rate = sr
            chunks.append(samples.astype(np.float32))
            chunks.append(np.zeros(int(sr * SENTENCE_PAUSE_S), dtype=np.float32))
        chunks.append(np.zeros(int(self.sample_rate * tail_pause), dtype=np.float32))
        audio = np.concatenate(chunks)
        sf.write(out_path, audio, self.sample_rate)
        return len(audio) / self.sample_rate
