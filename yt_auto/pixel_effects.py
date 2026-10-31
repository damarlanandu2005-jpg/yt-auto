"""Story-driven RGB pixel effects for rendered Short frames.

Effects are overlays on the existing scene artwork, not replacement drawings.
Each decoded frame is an RGB array; effects change pixel colour/brightness and,
where appropriate, shift pixels by a few rows/columns. The scene image remains
the source of the characters and objects.
"""
from __future__ import annotations

import math
import subprocess
from pathlib import Path
from typing import Iterable

import numpy as np

W, H, FPS = 1080, 1920, 30


def infer_effects(text: str) -> list[str]:
    """Choose restrained effects from narration; explicit scene tags can override this."""
    s = text.casefold()
    effects: list[str] = []
    if any(k in s for k in ("snow", "blizzard", "freezing", "frost", "iceberg", "icy", "cold")):
        effects.extend(("snow", "ice_shimmer"))
    if any(k in s for k in ("ocean", "sea", "water", "wave", "sinking", "ship")):
        effects.append("water")
    if any(k in s for k in ("lantern", "lifeboat", "candle", "torch")):
        effects.append("lantern")
    if any(k in s for k in ("crash", "collision", "impact", "struck", "hit the iceberg")):
        effects.append("impact")
    # Keep ordering stable and avoid applying an effect twice.
    return list(dict.fromkeys(effects))


def apply_effects(frame: np.ndarray, t: float, effects: Iterable[str], seed: int = 0) -> np.ndarray:
    """Return one RGB frame with deterministic, time-varying story effects."""
    if frame.ndim != 3 or frame.shape[2] != 3:
        raise ValueError("frame must have shape (height, width, 3) in RGB order")
    out = np.asarray(frame, dtype=np.uint8).copy()
    h, w, _ = out.shape
    active = set(effects)
    # Broadcast 1-D coordinate arrays instead of allocating two full-frame grids.
    x = np.arange(w, dtype=np.float32)[None, :]
    y = np.arange(h, dtype=np.float32)[:, None]

    if "water" in active:
        # Thin moving cyan highlights follow a low-amplitude wave pattern.
        wave = np.sin(x * 0.018 + y * 0.006 + t * 5.2)
        band = (wave > 0.965) & (y > int(h * 0.48))
        out[band, 0] = np.maximum(out[band, 0], 65)
        out[band, 1] = np.maximum(out[band, 1], 145)
        out[band, 2] = np.maximum(out[band, 2], 190)

    if "ice_shimmer" in active:
        # Sparse, moving cool-white glints, limited to small pixel clusters.
        phase = np.sin(x * 0.031 + y * 0.017 + t * 4.0 + seed)
        mask = (phase > 0.997) & (y < int(h * 0.72))
        out[mask] = np.maximum(out[mask], np.array([190, 225, 245], dtype=np.uint8))

    if "snow" in active:
        # Deterministic drifting flecks; no random flicker between identical renders.
        count = max(45, (w * h) // 18000)
        idx = np.arange(count, dtype=np.int64)
        xs = (idx * 7919 + seed * 97) % w
        ys = ((idx * 104729 + int(t * 92) * (1 + idx % 3)) % h).astype(int)
        for radius in (0, 1):
            px = np.clip(xs + radius, 0, w - 1)
            py = ys
            out[py, px] = np.maximum(out[py, px], np.array([215, 232, 245], dtype=np.uint8))

    if "lantern" in active:
        # Warm local glow around a fixed lower-middle focal point; subtle flicker.
        cx, cy = int(w * 0.52), int(h * 0.62)
        radius = max(1, int(min(w, h) * 0.20))
        dist2 = ((x - cx) ** 2 + (y - cy) ** 2) / float(radius * radius)
        glow = np.clip(1.0 - dist2, 0.0, 1.0) ** 2
        flicker = 0.78 + 0.12 * math.sin(t * 17.0) + 0.07 * math.sin(t * 29.0 + seed)
        amount = (glow * flicker * 34).astype(np.uint8)
        out[..., 0] = np.clip(out[..., 0].astype(np.uint16) + amount, 0, 255).astype(np.uint8)
        out[..., 1] = np.clip(out[..., 1].astype(np.uint16) + (amount * 0.48).astype(np.uint16), 0, 255).astype(np.uint8)

    if "impact" in active:
        # A brief 2-3 pixel RGB frame displacement at a deterministic beat.
        beat = (t % 1.8)
        if beat < 0.16:
            dx = 3 if beat < 0.08 else -3
            dy = -2 if beat < 0.08 else 2
            out = np.roll(out, shift=(dy, dx), axis=(0, 1))

    return out


def apply_video_effects(source: Path, destination: Path, effects: Iterable[str],
                        width: int = W, height: int = H, fps: int = FPS, seed: int = 0) -> None:
    """Stream RGB frames through NumPy and encode them; does not load the whole video into RAM."""
    tags = tuple(dict.fromkeys(effects))
    if not tags:
        destination.write_bytes(source.read_bytes())
        return

    decode = ["ffmpeg", "-v", "error", "-i", str(source), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    encode = ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
              "-s", f"{width}x{height}", "-r", str(fps), "-i", "-", "-an",
              "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p",
              str(destination)]
    decoder = subprocess.Popen(decode, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    encoder = subprocess.Popen(encode, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    frame_bytes = width * height * 3
    frame_no = 0
    try:
        assert decoder.stdout is not None and encoder.stdin is not None
        while True:
            raw = decoder.stdout.read(frame_bytes)
            if not raw:
                break
            if len(raw) != frame_bytes:
                raise RuntimeError("FFmpeg returned an incomplete RGB frame")
            frame = np.frombuffer(raw, dtype=np.uint8).reshape((height, width, 3))
            encoder.stdin.write(apply_effects(frame, frame_no / fps, tags, seed + frame_no // max(fps, 1)).tobytes())
            frame_no += 1
        encoder.stdin.close()
        dec_err = decoder.stderr.read().decode("utf-8", "replace") if decoder.stderr else ""
        enc_err = encoder.stderr.read().decode("utf-8", "replace") if encoder.stderr else ""
        dec_code, enc_code = decoder.wait(), encoder.wait()
        if dec_code or enc_code:
            raise RuntimeError(f"pixel effects ffmpeg failed (decode={dec_code}, encode={enc_code}): {dec_err[-1000:]} {enc_err[-1000:]}")
        if frame_no == 0:
            raise RuntimeError("input video contained no frames")
    finally:
        for proc in (decoder, encoder):
            if proc.poll() is None:
                proc.kill()
                proc.wait()
