"""Assemble the video with FFmpeg: still keyframes + slow zoom + fades + narration."""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

FPS = 30
OUT_W, OUT_H = 1920, 1080


def _run(cmd: list[str], timeout: int = 900) -> None:
    """Run FFmpeg with no stdin (it can hang waiting for keys on CI) and a hard time limit."""
    if cmd and cmd[0] == "ffmpeg" and "-nostdin" not in cmd:
        cmd = ["ffmpeg", "-nostdin", *cmd[1:]]
    result = subprocess.run(cmd, capture_output=True, text=True, stdin=subprocess.DEVNULL, timeout=timeout)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg failed: {' '.join(cmd[:6])}...\n{result.stderr[-2000:]}")


def threads() -> str:
    return os.environ.get("FFMPEG_THREADS", "0")  # 0 = let FFmpeg decide


def make_segment(image: Path, duration: float, out: Path, zoom_in: bool = True) -> None:
    """One keyframe held for `duration` seconds with a gentle zoom and short fades."""
    frames = max(1, round(duration * FPS))
    step = 0.05 / frames  # total zoom of 5% across the segment
    z = f"min(1+{step:.8f}*on,1.05)" if zoom_in else f"max(1.05-{step:.8f}*on,1.0)"
    fade = min(0.3, duration / 4)
    vf = (
        f"zoompan=z='{z}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={OUT_W}x{OUT_H}:fps={FPS},"
        f"fade=t=in:st=0:d={fade:.2f},fade=t=out:st={max(0, duration - fade):.2f}:d={fade:.2f},format=yuv420p"
    )
    _run([
        "ffmpeg", "-y", "-loglevel", "error", "-i", str(image), "-vf", vf, "-frames:v", str(frames),
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-tune", "stillimage",
        "-threads", threads(), str(out),
    ])


def concat_audio(wavs: list[Path], out: Path) -> None:
    listfile = out.with_suffix(".txt")
    listfile.write_text("".join(f"file '{w.resolve()}'\n" for w in wavs))
    _run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(listfile),
          "-c", "copy", str(out)])


def concat_video(segments: list[Path], out: Path) -> None:
    listfile = out.with_suffix(".txt")
    listfile.write_text("".join(f"file '{s.resolve()}'\n" for s in segments))
    _run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(listfile),
          "-c", "copy", str(out)])


def mux(video: Path, audio: Path, out: Path) -> None:
    """Add narration, normalised to about -16 LUFS (typical for online video)."""
    _run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(video), "-i", str(audio),
          "-map", "0:v", "-map", "1:a", "-c:v", "copy",
          "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-c:a", "aac", "-b:a", "160k", "-ar", "48000",
          "-shortest", "-movflags", "+faststart", str(out)])


def preview(video: Path, out: Path, seconds: int = 60) -> None:
    """Small low-resolution preview for quick checking."""
    _run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(video), "-t", str(seconds),
          "-vf", "scale=854:480", "-c:v", "libx264", "-preset", "veryfast", "-crf", "30",
          "-c:a", "aac", "-b:a", "64k", str(out)])


def probe_duration(path: Path) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=nw=1:nk=1", str(path)], capture_output=True, text=True,
                       stdin=subprocess.DEVNULL, timeout=60)
    return float(r.stdout.strip())
