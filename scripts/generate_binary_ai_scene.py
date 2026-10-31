"""Generate and render a binary LED scene from text-only scene instructions."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Running a script by path puts scripts/ on sys.path, not the repository root.
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from yt_auto.binary_scene import render_video
from yt_auto.binary_scene_ai import plan_scene


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scene", required=True, help="Plain-English scene description")
    parser.add_argument("--narration", required=True, help="Narration for this scene")
    parser.add_argument("--duration", type=float, default=8)
    parser.add_argument("--out", default="out/binary-led-ai/scene.mp4")
    args = parser.parse_args()

    plan = plan_scene(args.scene, args.narration, args.duration)
    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    plan_path = output.with_suffix(".plan.json")
    plan_path.write_text(json.dumps(plan, indent=2), encoding="utf-8")
    report = render_video(plan, output)
    report["plan"] = str(plan_path)
    output.with_suffix(".report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
