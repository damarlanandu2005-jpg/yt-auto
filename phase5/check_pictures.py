"""Re-run the picture check on a finished video's frames (to test the check itself).

Takes visuals.json from bench-results/phase1/<run_id>/ and video.mp4 from its release, grabs one frame
from the middle of each photo/drawing slot, and runs shots._verify on them. About 4 light AI requests.

    python phase5/check_pictures.py visuals.json video.mp4 OUT
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from yt_auto import llm, shots  # noqa: E402


def main() -> None:
    visuals, video, out = json.loads(Path(sys.argv[1]).read_text()), sys.argv[2], Path(sys.argv[3])
    (out / "frames").mkdir(parents=True, exist_ok=True)
    llm.LOG_DIR = out / "llm"
    groups = {"drawings": [], "photos": []}
    for v in visuals:
        p = v.get("photo")
        if not p:
            continue
        f = out / "frames" / f"{v['id']}.jpg"
        t = (v["start"] + v["end"]) / 2
        subprocess.run(["ffmpeg", "-nostdin", "-y", "-loglevel", "error", "-ss", f"{t:.2f}", "-i", video,
                        "-frames:v", "1", "-vf", "scale=640:-2", str(f)], stdin=subprocess.DEVNULL, check=True,
                       timeout=60)
        groups["drawings" if p.get("source") == "ai_drawing" else "photos"].append(
            {**v, "photo": {**p, "path": str(f)}})
    res = {}
    for name, chosen in groups.items():
        log: dict = {}
        shots._verify(chosen, log, drawings=name == "drawings")
        res[name] = {"checked": len(chosen), "kept": [v["id"] for v in chosen if v.get("photo")],
                     "rejected": log.get("rejected_after_looking", []), "seen": log.get("seen", {}),
                     "error": log.get("verify_error")}
        print(f"{name}: checked {len(chosen)}, rejected {len(res[name]['rejected'])}", flush=True)
        for r in res[name]["rejected"]:
            print(f"  REJECT {r['id']}: {r['seen'][:110]} | {r['reason'][:120]}", flush=True)
    (out / "result.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
