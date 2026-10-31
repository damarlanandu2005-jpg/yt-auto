"""Assemble a Stickman Short: checked script + FLUX scene pictures -> short.mp4 (yt_auto/short_video.py).

  python cartoon/make_video.py --script script.json --pictures DIR --out out/short [--sources sources.json] [--models models]

Pictures are named flux2dev_fp16_<scene id>.jpg (or flux2dev_<id>). Plain code and FFmpeg only: no AI request, no key.
"""
from __future__ import annotations

import argparse
import faulthandler
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from yt_auto import cartoon, short_video  # noqa: E402
from yt_auto.tts import Narrator  # noqa: E402


def find_pictures(folder: Path, ids: list[str]) -> dict[str, Path]:
    out = {}
    for sid in ids:
        for pat in (f"flux2dev_fp16_{sid}.*", f"flux2dev_{sid}.*", f"{sid}.*"):
            f = next(iter(sorted(folder.glob(pat))), None)
            if f:
                out[sid] = f
                break
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--script", required=True)
    ap.add_argument("--pictures", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--sources", default="")
    ap.add_argument("--models", default="models")
    ap.add_argument("--voice", default="af_heart")
    a = ap.parse_args()
    faulthandler.dump_traceback_later(40 * 60, exit=True)
    script = json.loads(Path(a.script).read_text())
    sources = json.loads(Path(a.sources).read_text()) if a.sources and Path(a.sources).exists() else None
    pics = find_pictures(Path(a.pictures), cartoon.scene_ids(script))
    narrator = Narrator(Path(a.models) / "kokoro-v1.0.int8.onnx", Path(a.models) / "voices-v1.0.bin", voice=a.voice, speed=0.9)
    report = short_video.build(script, pics, narrator, Path(a.out), sources)
    print(json.dumps(report, indent=1))
    if not all(report["checks"].values()):
        print("::warning::some checks failed: " + ", ".join(k for k, v in report["checks"].items() if not v))


if __name__ == "__main__":
    main()
