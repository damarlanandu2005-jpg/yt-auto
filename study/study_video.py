"""Study someone else's video to learn what makes it look good (not to copy it).

Saves facts (YouTube API), the captions, frames across the whole video on contact sheets, and simple
measures (shot changes per minute, length, loudness). The video file itself is NOT kept.

    python study/study_video.py VIDEO_ID OUT
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import urllib.parse
import urllib.request
from pathlib import Path

API = "https://youtube.googleapis.com/youtube/v3"


def yt(endpoint: str, **params) -> dict:
    params["key"] = os.environ["YOUTUBE_API_KEY"]
    url = f"{API}/{endpoint}?{urllib.parse.urlencode(params)}"
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.loads(r.read())


def run(cmd: list[str], log: Path, timeout: int = 900) -> subprocess.CompletedProcess:
    r = subprocess.run(cmd, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=timeout)
    log.write_text(" ".join(cmd) + "\n\n" + r.stdout[-20000:] + "\n" + r.stderr[-20000:])
    return r


def facts(vid: str, out: Path) -> dict:
    v = yt("videos", part="snippet,contentDetails,statistics,status", id=vid)["items"][0]
    cid = v["snippet"]["channelId"]
    ch = yt("channels", part="snippet,statistics,contentDetails", id=cid)["items"][0]
    up = ch["contentDetails"]["relatedPlaylists"]["uploads"]
    recent = yt("playlistItems", part="contentDetails,snippet", playlistId=up, maxResults=50)["items"]
    ids = ",".join(x["contentDetails"]["videoId"] for x in recent)
    rv = yt("videos", part="snippet,contentDetails,statistics", id=ids)["items"] if ids else []
    res = {"video": v, "channel": {"snippet": ch["snippet"], "statistics": ch["statistics"]},
           "recent_uploads": [{"title": x["snippet"]["title"], "published": x["snippet"]["publishedAt"],
                               "duration": x["contentDetails"]["duration"], "views": x["statistics"].get("viewCount")}
                              for x in rv]}
    (out / "facts.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))
    return res


def main() -> None:
    vid, out = sys.argv[1], Path(sys.argv[2])
    if not re.fullmatch(r"[A-Za-z0-9_-]{11}", vid):
        sys.exit("bad video id")
    out.mkdir(parents=True, exist_ok=True)
    work = Path("work")
    work.mkdir(exist_ok=True)
    summary: dict = {}
    try:
        f = facts(vid, out)
        s = f["video"]["snippet"]
        summary.update(title=s["title"], channel=s["channelTitle"], published=s["publishedAt"],
                       duration=f["video"]["contentDetails"]["duration"], views=f["video"]["statistics"].get("viewCount"),
                       subs=f["channel"]["statistics"].get("subscriberCount"),
                       channel_videos=f["channel"]["statistics"].get("videoCount"),
                       channel_created=f["channel"]["snippet"].get("publishedAt"),
                       uploads_last_50=len(f["recent_uploads"]))
    except Exception as e:  # noqa: BLE001
        summary["facts_error"] = repr(e)[:300]

    url = f"https://www.youtube.com/watch?v={vid}"
    r = run([sys.executable, "-m", "yt_dlp", "-f", "bv*[height<=480]+ba/b[height<=480]/b", "--merge-output-format", "mp4",
             "--write-auto-subs", "--write-subs", "--sub-langs", "en.*,en", "--sub-format", "vtt",
             "-o", str(work / "v.%(ext)s"), url], out / "ytdlp.log", timeout=1200)
    summary["download"] = "ok" if r.returncode == 0 else f"failed (see ytdlp.log): {r.stderr[-300:]}"
    for sub in work.glob("v*.vtt"):
        lines, last = [], ""
        for ln in sub.read_text(errors="replace").splitlines():
            ln = re.sub(r"<[^>]+>", "", ln).strip()
            if not ln or "-->" in ln or ln.startswith(("WEBVTT", "Kind:", "Language:")) or ln == last:
                continue
            lines.append(ln)
            last = ln
        (out / f"transcript_{sub.stem}.txt").write_text("\n".join(lines))
        summary.setdefault("transcript_words", len(" ".join(lines).split()))
    vids = [p for p in work.glob("v.*") if p.suffix in (".mp4", ".webm", ".mkv")]
    if vids:
        v = vids[0]
        dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(v)],
                                   capture_output=True, text=True, stdin=subprocess.DEVNULL, timeout=60).stdout.strip())
        summary["seconds"] = round(dur, 1)
        # Shot changes: frames where the picture changes a lot
        r = run(["ffmpeg", "-nostdin", "-hide_banner", "-i", str(v), "-vf", "select='gt(scene,0.3)',showinfo",
                 "-an", "-f", "null", "-"], out / "scenes.log")
        cuts = [float(m) for m in re.findall(r"pts_time:([0-9.]+)", r.stderr)]
        summary["shot_changes"] = len(cuts)
        summary["shot_changes_per_min"] = round(len(cuts) / dur * 60, 1)
        gaps = [b - a for a, b in zip([0.0] + cuts, cuts + [dur])]
        summary["avg_shot_seconds"] = round(sum(gaps) / len(gaps), 1)
        (out / "shot_times.json").write_text(json.dumps([round(c, 2) for c in cuts]))
        r = run(["ffmpeg", "-nostdin", "-hide_banner", "-i", str(v), "-af", "ebur128", "-vn", "-f", "null", "-"],
                out / "loudness.log")
        m = re.findall(r"I:\s+(-?[0-9.]+) LUFS", r.stderr)
        summary["loudness_lufs"] = float(m[-1]) if m else None
        # Contact sheets: 48 frames per sheet, about 144 frames across the video
        step = max(dur / 144, 1.0)
        summary["sheet_note"] = f"each sheet = one third of the video, 48 frames left to right, one every {step:.1f} s"
        for i in range(3):
            ss = i * dur / 3
            run(["ffmpeg", "-nostdin", "-y", "-hide_banner", "-ss", f"{ss:.2f}", "-t", f"{dur / 3:.2f}", "-i", str(v),
                 "-vf", f"fps=1/{step:.3f},scale=320:-2,tile=6x8", "-frames:v", "1", "-q:v", "4", str(out / f"sheet_{i + 1}.jpg")], out / f"sheet_{i + 1}.log")
        # A few full-size frames to judge detail (text, sharpness, style)
        for k in range(1, 7):
            t = dur * k / 7
            run(["ffmpeg", "-nostdin", "-y", "-hide_banner", "-ss", f"{t:.2f}", "-i", str(v), "-frames:v", "1",
                 "-q:v", "3", str(out / f"frame_{int(t):04d}s.jpg")], out / "frames.log")
    (out / "summary.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False))
    print(json.dumps(summary, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
