"""Copy the Twemoji files a project's scenes.js uses into its assets/emoji/ (explainroo loads only assets/).
Used by the render workflows for hand-made projects (cartoon/videos/<name>); AI-made ones get them in write_project.

  python3 cartoon/copy_emoji.py <project folder>
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from yt_auto.cartoon import copy_emoji  # noqa: E402

project = Path(sys.argv[1])
print("emoji copied:", copy_emoji((project / "scenes.js").read_text(), project) or "none")
