from __future__ import annotations

import argparse
import json
from pathlib import Path

from yt_auto.binary_scene import load_plan, render_video


def main() -> None:
    parser = argparse.ArgumentParser(description="Render a video from generated binary ON/OFF scene instructions.")
    parser.add_argument("--plan", default="examples/binary_driving_scene.json")
    parser.add_argument("--out", default="out/binary-led-demo/binary-led-demo.mp4")
    args = parser.parse_args()
    plan = load_plan(args.plan)
    report = render_video(plan, args.out)
    report_path = Path(args.out).with_suffix(".report.json")
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
