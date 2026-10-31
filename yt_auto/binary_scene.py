"""Native binary LED scene renderer.

No source images or video frames are used. Scene plans describe objects and motion;
the renderer draws them directly into a 1-bit canvas (ON=black, OFF=white).
"""
from __future__ import annotations

import json
import math
import subprocess
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw

ON = 0       # black LED illuminated
OFF = 255    # white LED not illuminated
WIDTH = 1080
HEIGHT = 1920
FPS = 24


def load_plan(path: str | Path) -> dict[str, Any]:
    plan = json.loads(Path(path).read_text(encoding="utf-8"))
    validate_plan(plan)
    return plan


def validate_plan(plan: dict[str, Any]) -> None:
    if not isinstance(plan.get("duration"), (int, float)) or plan["duration"] <= 0:
        raise ValueError("plan.duration must be a positive number")
    if not isinstance(plan.get("objects"), list):
        raise ValueError("plan.objects must be a list")
    for obj in plan["objects"]:
        if obj.get("type") not in {"rect", "ellipse", "line", "polygon", "text"}:
            raise ValueError(f"unsupported object type: {obj.get('type')}")
        if not isinstance(obj.get("id"), str):
            raise ValueError("every object needs a string id")


def _position(obj: dict[str, Any], t: float) -> tuple[float, float]:
    x, y = float(obj.get("x", 0)), float(obj.get("y", 0))
    motion = obj.get("motion")
    if not motion:
        return x, y
    start, end = float(motion.get("start", 0)), float(motion.get("end", 1))
    if end <= start:
        return x, y
    p = min(1.0, max(0.0, (t - start) / (end - start)))
    p = p * p * (3 - 2 * p) if motion.get("ease", "linear") == "smooth" else p
    return x + float(motion.get("dx", 0)) * p, y + float(motion.get("dy", 0)) * p


def render_frame(plan: dict[str, Any], t: float, width: int = WIDTH, height: int = HEIGHT) -> np.ndarray:
    """Render one exact binary frame; coordinates are normalized 0..1."""
    validate_plan(plan)
    image = Image.new("1", (width, height), 1)  # white/off background
    draw = ImageDraw.Draw(image)
    duration = float(plan["duration"])

    for obj in plan["objects"]:
        visible = obj.get("visible", [0, duration])
        if not (float(visible[0]) <= t <= float(visible[1])):
            continue
        x, y = _position(obj, t)
        w, h = float(obj.get("w", 0.1)), float(obj.get("h", 0.1))
        px = lambda v: int(round(v * width))
        py = lambda v: int(round(v * height))
        box = (px(x), py(y), px(x + w), py(y + h))
        fill = 0  # all shapes are ON; background is OFF

        kind = obj["type"]
        if kind == "rect":
            draw.rectangle(box, fill=fill)
        elif kind == "ellipse":
            draw.ellipse(box, fill=fill)
        elif kind == "line":
            x2 = x + float(obj.get("dx", w))
            y2 = y + float(obj.get("dy", h))
            draw.line((px(x), py(y), px(x2), py(y2)), fill=fill,
                      width=max(1, int(obj.get("width", 0.004) * min(width, height))))
        elif kind == "polygon":
            points = [(px(x + float(a)), py(y + float(b))) for a, b in obj["points"]]
            draw.polygon(points, fill=fill)
        elif kind == "text":
            # Built-in bitmap font: deterministic and requires no external assets.
            draw.text((px(x), py(y)), obj["text"], fill=fill)

    return np.asarray(image.convert("L"), dtype=np.uint8)


def render_video(plan: dict[str, Any], output: str | Path, width: int = WIDTH,
                 height: int = HEIGHT, fps: int = FPS) -> dict[str, Any]:
    """Stream generated binary frames directly to FFmpeg; never reads images/video."""
    validate_plan(plan)
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    frames = int(round(float(plan["duration"]) * fps))
    command = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "gray", "-s", f"{width}x{height}",
        "-r", str(fps), "-i", "-", "-an", "-c:v", "libx264",
        "-preset", "veryfast", "-crf", "0", "-pix_fmt", "gray",
        "-movflags", "+faststart", str(output),
    ]
    process = subprocess.Popen(command, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    on_ratios = []
    try:
        assert process.stdin is not None
        for index in range(frames):
            frame = render_frame(plan, index / fps, width, height)
            values = np.unique(frame)
            if not set(values.tolist()).issubset({ON, OFF}):
                raise RuntimeError(f"non-binary pixel values found: {values}")
            on_ratios.append(float(np.mean(frame == ON)))
            process.stdin.write(frame.tobytes())
        process.stdin.close()
        error = process.stderr.read().decode("utf-8", errors="replace") if process.stderr else ""
        code = process.wait()
        if code:
            raise RuntimeError(f"FFmpeg failed ({code}): {error[-2000:]}")
    except Exception:
        process.kill()
        process.wait()
        raise

    return {
        "output": str(output),
        "width": width,
        "height": height,
        "fps": fps,
        "frames": frames,
        "duration": frames / fps,
        "pixel_states": [0, 255],
        "average_on_ratio": round(float(np.mean(on_ratios)), 4),
        "source_images_used": 0,
        "source_video_used": 0,
    }
