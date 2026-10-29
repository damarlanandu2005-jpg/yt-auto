"""Copy the Twemoji files and library pictures (cartoon/art/) a project's scenes.js uses into its assets/emoji/ (explainroo loads only assets/).
Used by the render workflows for hand-made projects (cartoon/videos/<name>); AI-made ones get them in write_project.

  python3 cartoon/copy_emoji.py <project folder>
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from yt_auto.cartoon import copy_art, copy_emoji  # noqa: E402

project = Path(sys.argv[1])
js = (project / "scenes.js").read_text()
print("emoji copied:", copy_emoji(js, project) or "none")
print("library pictures copied:", copy_art(js, project) or "none")
