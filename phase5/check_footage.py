"""Quick live check of NASA footage: search, cut 5 s from the middle, grab a frame. No AI requests.

    python phase5/check_footage.py OUT "black hole" "galaxy" ...
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from yt_auto import footage  # noqa: E402


def main() -> None:
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    for q in sys.argv[2:]:
        cands = footage.search_many([q], 3)
        for i, c in enumerate(cands[:2]):
            url = footage._mp4_url(c["manifest_url"])
            dur = footage._duration(url) if url else None
            frame = footage.fetch(c, out, f"{q.replace(' ', '_')}_{i}", 5.0)
            rows.append({"query": q, "title": c["title"], "manifest": c["manifest_url"], "mp4": url,
                         "duration": dur, "frame": frame.name if frame else None})
            print(json.dumps(rows[-1]), flush=True)
    (out / "result.json").write_text(json.dumps(rows, indent=1))


if __name__ == "__main__":
    main()
