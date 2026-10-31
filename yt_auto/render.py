"""Assemble the video with FFmpeg: still keyframes + slow zoom + fades + narration."""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

FPS = 30
OUT_W, OUT_H = 1920, 1080


LOG_DIR: Path | None = None  # set by the caller to keep one FFmpeg log per command
DIAGNOSTICS: list[dict] = []  # filled when a command hangs


class FFmpegHang(RuntimeError):
    pass


def _snapshot(pid: int) -> dict:
    """What is a running process doing? CPU time rising = busy; flat = frozen."""
    try:
        import psutil

        p = psutil.Process(pid)
        t = p.cpu_times()
        return {"status": p.status(), "threads": p.num_threads(),
                "cpu_user_s": round(t.user, 2), "cpu_system_s": round(t.system, 2),
                "rss_mb": round(p.memory_info().rss / 1e6, 1)}
    except Exception as e:  # noqa: BLE001
        return {"error": repr(e)}


def _run(cmd: list[str], timeout: int = 900, name: str = "ffmpeg") -> float:
    """Run FFmpeg with no stdin, its log saved to a file, and a hard time limit.

    On timeout, record whether FFmpeg was still using CPU (slow) or not (frozen),
    plus the end of its log, then raise FFmpegHang.
    """
    import time

    if cmd and cmd[0] == "ffmpeg":
        cmd = [c for c in cmd if c not in ("-nostdin",)]
        cmd = ["ffmpeg", "-nostdin", *cmd[1:]]
        # keep FFmpeg's own progress output in the log
        if "-loglevel" in cmd:
            i = cmd.index("-loglevel")
            cmd[i + 1] = "info"
        cmd.insert(1, "-stats")
    log_path = (LOG_DIR / f"{name}.log") if LOG_DIR else Path(os.devnull)
    t0 = time.perf_counter()
    with open(log_path, "w") as log:
        proc = subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT)
        try:
            proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            first = _snapshot(proc.pid)
            time.sleep(10)
            second = _snapshot(proc.pid)
            proc.kill()
            proc.wait()
            log.flush()
            tail = Path(log_path).read_text(errors="replace")[-3000:] if LOG_DIR else ""
            DIAGNOSTICS.append({"command": name, "timeout_s": timeout, "argv": cmd,
                                "snapshot_at_timeout": first, "snapshot_10s_later": second,
                                "log_tail": tail})
            raise FFmpegHang(f"{name} did not finish in {timeout}s")
    if proc.returncode != 0:
        tail = Path(log_path).read_text(errors="replace")[-2000:] if LOG_DIR else ""
        raise RuntimeError(f"FFmpeg failed ({name}): exit {proc.returncode}\n{tail}")
    return round(time.perf_counter() - t0, 2)


def threads() -> str:
    return os.environ.get("FFMPEG_THREADS", "0")  # 0 = let FFmpeg decide


def make_segment(image: Path, duration: float, out: Path, zoom_in: bool = True, motion: str | None = None,
                 fade_in: bool = True, fade_out: bool = True) -> None:
    """One keyframe held for `duration` seconds with gentle motion (Ken Burns) and optional fades.

    motion: zoom_in | zoom_out | pan_left | pan_right (default from zoom_in, as in Phase 0).
    Photos move a little more (8%) than cards (5%) so they feel alive.
    """
    motion = motion or ("zoom_in" if zoom_in else "zoom_out")
    frames = max(1, round(duration * FPS))
    amount = 0.08 if motion.startswith("pan") else 0.05
    step = amount / frames
    cx, cy = "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"
    if motion == "zoom_in":
        z, x, y = f"min(1+{step:.8f}*on,{1 + amount})", cx, cy
    elif motion == "zoom_out":
        z, x, y = f"max({1 + amount}-{step:.8f}*on,1.0)", cx, cy
    else:  # pan across at a fixed zoom
        z = f"{1 + amount}"
        span = f"(iw-iw/zoom)"
        x = f"{span}*on/{frames}" if motion == "pan_right" else f"{span}*(1-on/{frames})"
        y = cy
    fade = min(0.3, duration / 4)
    fades = ""
    if fade_in:
        fades += f",fade=t=in:st=0:d={fade:.2f}"
    if fade_out:
        fades += f",fade=t=out:st={max(0, duration - fade):.2f}:d={fade:.2f}"
    vf = f"zoompan=z='{z}':x='{x}':y='{y}':d={frames}:s={OUT_W}x{OUT_H}:fps={FPS}{fades},format=yuv420p"
    _run([
        "ffmpeg", "-y", "-loglevel", "error", "-i", str(image), "-vf", vf, "-frames:v", str(frames),
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-tune", "stillimage",
        "-threads", threads(), str(out),
    ], name=f"segment_{out.stem}")


def make_clip_segment(clip: Path, duration: float, out: Path, fade_in: bool = True, fade_out: bool = True) -> None:
    """A slot filled with real footage: the cut clip, frozen on its last frame if it is a little short."""
    frames = max(1, round(duration * FPS))
    fade = min(0.3, duration / 4)
    fades = (f",fade=t=in:st=0:d={fade:.2f}" if fade_in else "") + \
            (f",fade=t=out:st={max(0, duration - fade):.2f}:d={fade:.2f}" if fade_out else "")
    vf = f"scale={OUT_W}:{OUT_H},fps={FPS},tpad=stop_mode=clone:stop_duration={duration:.2f}{fades},format=yuv420p"
    _run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(clip), "-an", "-vf", vf, "-frames:v", str(frames),
          "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-threads", threads(), str(out)],
         name=f"segment_{out.stem}")


def concat_audio(wavs: list[Path], out: Path) -> None:
    listfile = out.with_suffix(".txt")
    listfile.write_text("".join(f"file '{w.resolve()}'\n" for w in wavs))
    _run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(listfile),
          "-c", "copy", str(out)], name="concat_audio")


def concat_video(segments: list[Path], out: Path) -> None:
    listfile = out.with_suffix(".txt")
    listfile.write_text("".join(f"file '{s.resolve()}'\n" for s in segments))
    _run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(listfile),
          "-c", "copy", str(out)], name="concat_video")


def burn_ass(video: Path, ass: Path, fonts_dir: Path, out: Path) -> float:
    """Burn the on-screen key words (ASS file) into the joined video. One full re-encode."""
    return _run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(video),
                 "-vf", f"ass=filename={ass.resolve()}:fontsdir={fonts_dir.resolve()},format=yuv420p",
                 "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-threads", threads(), str(out)],
                timeout=1800, name="keywords_burn")


def mux(video: Path, audio: Path, out: Path, lufs: float = -16.0) -> None:
    """Add narration, normalised to about -16 LUFS (typical for online video; Shorts use -14)."""
    _run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(video), "-i", str(audio),
          "-map", "0:v", "-map", "1:a", "-c:v", "copy",
          "-af", f"loudnorm=I={lufs}:TP=-1.5:LRA=11", "-c:a", "aac", "-b:a", "160k", "-ar", "48000",
          "-shortest", "-movflags", "+faststart", str(out)], name="mux")


def preview(video: Path, out: Path, seconds: int = 60, threads_n: str | None = None,
            timeout: int = 180, name: str = "preview") -> float:
    """Small low-resolution preview for quick checking. Returns seconds taken."""
    thread_args = ["-threads", threads_n] if threads_n else []
    return _run(["ffmpeg", "-y", "-loglevel", "error", *thread_args, "-i", str(video), "-t", str(seconds),
                 "-vf", "scale=854:480", "-c:v", "libx264", "-preset", "veryfast", "-crf", "30",
                 *thread_args, "-c:a", "aac", "-b:a", "64k", str(out)], timeout=timeout, name=name)


def probe_duration(path: Path) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=nw=1:nk=1", str(path)], capture_output=True, text=True,
                       stdin=subprocess.DEVNULL, timeout=60)
    return float(r.stdout.strip())
