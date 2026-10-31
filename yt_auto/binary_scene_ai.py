"""LLM scene planner that converts narration into native binary-pixel drawing instructions.

The model receives text only. It does not receive or generate images/video. Its JSON plan is
rendered by yt_auto.binary_scene into strict black/white frames.
"""
from __future__ import annotations

import json
from typing import Any

from . import llm
from .binary_scene import validate_plan

SCENE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["duration", "objects"],
    "properties": {
        "duration": {"type": "number", "minimum": 0.5, "maximum": 60},
        "objects": {
            "type": "array", "minItems": 1, "maxItems": 80,
            "items": {
                "type": "object",
                "required": ["id", "type", "x", "y"],
                "properties": {
                    "id": {"type": "string"},
                    "type": {"type": "string", "enum": ["rect", "ellipse", "line", "polygon", "text"]},
                    "x": {"type": "number", "minimum": 0, "maximum": 1},
                    "y": {"type": "number", "minimum": 0, "maximum": 1},
                    "w": {"type": "number", "minimum": 0, "maximum": 1},
                    "h": {"type": "number", "minimum": 0, "maximum": 1},
                    "dx": {"type": "number", "minimum": -1, "maximum": 1},
                    "dy": {"type": "number", "minimum": -1, "maximum": 1},
                    "width": {"type": "number", "minimum": 0, "maximum": 0.1},
                    "text": {"type": "string"},
                    "points": {"type": "array", "items": {"type": "array", "items": {"type": "number"}}},
                    "visible": {"type": "array", "items": {"type": "number"}, "minItems": 2, "maxItems": 2},
                    "motion": {
                        "type": "object",
                        "properties": {
                            "start": {"type": "number"},
                            "end": {"type": "number"},
                            "dx": {"type": "number"},
                            "dy": {"type": "number"},
                            "ease": {"type": "string", "enum": ["linear", "smooth"]}
                        }
                    }
                }
            }
        }
    }
}


def plan_scene(scene_description: str, narration: str, duration: float) -> dict[str, Any]:
    """Ask the configured text LLM for compact vector-like primitives; no visual assets are involved."""
    if not scene_description.strip():
        raise ValueError("scene_description cannot be empty")
    if not narration.strip():
        raise ValueError("narration cannot be empty")
    if not 0.5 <= duration <= 60:
        raise ValueError("duration must be between 0.5 and 60 seconds")

    system = (
        "You are a 2D animation scene planner for a strict monochrome binary LED renderer. "
        "You output geometry instructions only, never images, image prompts, URLs, SVG, or video."
    )
    prompt = f"""Create one complete, readable animated scene using ONLY geometric drawing primitives.

SCENE: {scene_description}
NARRATION: {narration}
DURATION_SECONDS: {duration}

RENDERER RULES:
- Canvas is portrait 9:16. Coordinates x,y,w,h are normalized from 0 to 1.
- Background is white/OFF. Every drawn primitive is black/ON. No grey, shading, colour, raster image, photo or video.
- Supported types: rect, ellipse, line, polygon, text. Use polygons for recognisable silhouettes.
- Draw all required objects, including background/environment, foreground, characters and important props.
- Use several simple shapes per character/object to make them recognisable (head, torso, arms, legs, wheels, windows).
- Keep important content inside x=0.04..0.96 and y=0.04..0.96. Avoid tiny details; make silhouettes bold.
- Use stable ids. Motion is normalized displacement over its start/end time; keep moving parts attached by giving them matching motion.
- visible is [start_seconds,end_seconds]. All objects must fit the scene duration.
- Text should be short and only when it helps the story. Do not use text as a substitute for drawing objects.
- Return exactly the JSON object matching the schema. Set duration to {duration}.
"""
    result = llm.llm(prompt, system=system, schema=SCENE_SCHEMA, models=llm.LIGHT,
                     temperature=0.2, name="binary_scene_plan")
    if not isinstance(result, dict):
        raise ValueError("AI scene planner did not return a JSON object")
    result["duration"] = float(duration)
    validate_plan(result)
    _validate_geometry(result)
    return result


def _validate_geometry(plan: dict[str, Any]) -> None:
    duration = float(plan["duration"])
    seen: set[str] = set()
    for obj in plan["objects"]:
        oid = obj["id"]
        if oid in seen:
            raise ValueError(f"duplicate object id: {oid}")
        seen.add(oid)
        for key in ("x", "y", "w", "h"):
            if key in obj and not 0 <= float(obj[key]) <= 1:
                raise ValueError(f"{oid}.{key} must be normalized between 0 and 1")
        visible = obj.get("visible", [0, duration])
        if len(visible) != 2 or not 0 <= float(visible[0]) <= float(visible[1]) <= duration:
            raise ValueError(f"{oid}.visible must be within scene duration")
        motion = obj.get("motion")
        if motion and not 0 <= float(motion.get("start", 0)) < float(motion.get("end", duration)) <= duration:
            raise ValueError(f"{oid}.motion timing must be within scene duration")
        if obj["type"] == "polygon" and len(obj.get("points", [])) < 3:
            raise ValueError(f"{oid}: polygon needs at least three points")
        if obj["type"] == "text" and not obj.get("text"):
            raise ValueError(f"{oid}: text object needs text")
