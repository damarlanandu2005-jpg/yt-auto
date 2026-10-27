"""Study a channel (by @handle): facts, upload pace, views per video, top videos' titles, descriptions
and thumbnails. About 5 YouTube API units.

    python study/study_channel.py @handle OUT
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from study_video import get, yt  # noqa: E402


def main() -> None:
    handle, out = sys.argv[1], Path(sys.argv[2])
    if not re.fullmatch(r"@[A-Za-z0-9._-]{3,40}", handle):
        sys.exit("bad handle")
    out.mkdir(parents=True, exist_ok=True)
    ch = yt("channels", part="snippet,statistics,contentDetails,brandingSettings", forHandle=handle)["items"][0]
    up = ch["contentDetails"]["relatedPlaylists"]["uploads"]
    items = yt("playlistItems", part="contentDetails", playlistId=up, maxResults=50)["items"]
    ids = ",".join(x["contentDetails"]["videoId"] for x in items)
    vids = yt("videos", part="snippet,contentDetails,statistics,status", id=ids)["items"] if ids else []
    rows = [{"id": v["id"], "title": v["snippet"]["title"], "published": v["snippet"]["publishedAt"],
             "duration": v["contentDetails"]["duration"], "views": int(v["statistics"].get("viewCount", 0)),
             "likes": int(v["statistics"].get("likeCount", 0)), "comments": int(v["statistics"].get("commentCount", 0)),
             "tags": v["snippet"].get("tags", [])[:15], "description": v["snippet"].get("description", "")[:2500]}
            for v in vids]
    res = {"channel": {"title": ch["snippet"]["title"], "created": ch["snippet"]["publishedAt"],
                       "description": ch["snippet"].get("description", ""), "country": ch["snippet"].get("country"),
                       **ch["statistics"]}, "videos": rows}
    (out / "channel.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))
    top = sorted(rows, key=lambda r: -r["views"])[:4]
    for i, r in enumerate(top, 1):
        try:
            (out / f"top{i}_{r['id']}.jpg").write_bytes(get(f"https://i.ytimg.com/vi/{r['id']}/hqdefault.jpg"))
        except Exception as e:  # noqa: BLE001
            print(f"thumbnail {r['id']}: {e!r}")
    print(json.dumps(res["channel"], indent=1, ensure_ascii=False)[:1500])
    for r in rows:
        print(r["published"][:10], r["duration"], r["views"], r["title"][:80])


if __name__ == "__main__":
    main()
