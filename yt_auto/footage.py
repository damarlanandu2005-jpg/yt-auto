"""Real moving footage from the NASA Image and Video Library (public domain, same rules as NASA photos).

The TON 618 comparison (owner, 28 Oct): top videos use moving scenes, we only had stills. NASA's free library
also holds launches, spacecraft, Earth from orbit and NASA animations of stars, galaxies and black holes.
Only the needed seconds are cut straight from NASA's server (FFmpeg reads the URL), from the middle of the clip
(NASA videos often open with titles or a logo). A middle frame is what the blind picture check looks at.
"""
from __future__ import annotations

import datetime as dt
import json
import subprocess
import urllib.parse
from pathlib import Path

from .photos import NASA_API, _NASA_THIRD_PARTY, _clean_html, _get

OUT_W, OUT_H, FPS = 1920, 1080, 30
PREFER = ("~medium.mp4", "~large.mp4", "~orig.mp4", "~small.mp4")


def search(query: str, limit: int = 6) -> list[dict]:
    q = urllib.parse.urlencode({"q": query, "media_type": "video", "page_size": limit})
    data = _get(f"{NASA_API}?{q}")
    out = []
    for it in (data.get("collection") or {}).get("items") or []:
        d = it["data"][0]
        text = " ".join(str(d.get(k, "")) for k in ("description", "photographer", "secondary_creator", "title"))
        if _NASA_THIRD_PARTY.search(text):
            continue
        nid = d["nasa_id"]
        out.append({
            "source": "nasa_image_library", "kind": "video", "id": "video:" + nid,
            "title": d.get("title", ""), "description": _clean_html(d.get("description", ""))[:300],
            "page_url": f"https://images.nasa.gov/details/{urllib.parse.quote(nid)}",
            "manifest_url": it.get("href"),
            "licence": "Public domain (NASA media, not copyrighted in the US)",
            "licence_url": "https://www.nasa.gov/nasa-brand-center/images-and-media/",
            "author": d.get("photographer") or d.get("secondary_creator") or f"NASA ({d.get('center', '')})".replace(" ()", ""),
            "credit": "NASA", "date_created": d.get("date_created"),
        })
    return out


def _mp4_url(manifest_url: str) -> str | None:
    files = _get(manifest_url)
    for suffix in PREFER:
        for f in files:
            if f.endswith(suffix):
                return urllib.parse.quote(f.replace("http://", "https://"), safe=":/~%")
    return None


def _duration(url: str) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", url],
                       stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=90)
    return float(r.stdout.strip() or 0)


def fetch(cand: dict, dest_dir: Path, stem: str, seconds: float) -> Path | None:
    """Cut `seconds` (+ a little) from the middle of the clip; save it, a middle frame (JPEG) and the licence
    record (on the frame, like a photo, with the clip's path under 'video_clip'). Returns the frame path."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    url = _mp4_url(cand["manifest_url"])
    if not url:
        return None
    total = _duration(url)
    if total < 3:
        return None
    want = min(seconds + 0.5, max(total - 1, 1))
    start = max(min(total * 0.5 - want / 2, total - want - 0.5), min(3.0, total * 0.2))
    clip, frame = dest_dir / f"{stem}.clip.mp4", dest_dir / f"{stem}.jpg"
    vf = (f"scale={OUT_W}:{OUT_H}:force_original_aspect_ratio=increase,crop={OUT_W}:{OUT_H},fps={FPS},"
          "format=yuv420p")
    r = subprocess.run(["ffmpeg", "-nostdin", "-y", "-loglevel", "error", "-ss", f"{start:.2f}", "-t", f"{want:.2f}",
                        "-i", url, "-an", "-vf", vf, "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", str(clip)],
                       stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=300)
    if r.returncode or not clip.exists():
        print(f"[footage] cut failed for {cand['title'][:60]}: {r.stderr[-300:]}", flush=True)
        return None
    subprocess.run(["ffmpeg", "-nostdin", "-y", "-loglevel", "error", "-ss", f"{want / 2:.2f}", "-i", str(clip),
                    "-frames:v", "1", "-q:v", "3", str(frame)], stdin=subprocess.DEVNULL, capture_output=True,
                   timeout=60)
    if not frame.exists():
        return None
    record = {
        "file": frame.name, "kind": "video", "source": cand["source"], "title": cand["title"],
        "source_page": cand["page_url"], "download_url": url, "licence": cand["licence"],
        "licence_url": cand["licence_url"], "author": cand["author"],
        "attribution": f"{cand['title']} — {cand['author']}, NASA, public domain (video). {cand['page_url']}",
        "downloaded": dt.date.today().isoformat(), "clip_start_s": round(start, 2), "clip_seconds": round(want, 2),
        "video_clip": str(clip),
    }
    frame.with_suffix(".licence.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    return frame
