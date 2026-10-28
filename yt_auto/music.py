"""Background music from Wikimedia Commons: CC BY / CC BY-SA / CC0 / public domain only (owner OK'd CC BY
with credit, 28 Oct). Mostly Kevin MacLeod's tracks (incompetech, CC BY). Every track gets a licence record
like a photo's, and its credit goes in the description.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
import subprocess
import urllib.parse
from pathlib import Path

from .photos import COMMONS_API, _clean_html, _get, allowed_licence

QUERIES = ["Kevin MacLeod ambient", "Kevin MacLeod", "ambient music instrumental"]
# Calm, spacious moods suit a narrated explainer; anything loud or comic is skipped.
MOOD = re.compile(r"ambient|dream|space|spacial|calm|ether|wind|dawn|echo|float|night|myster|deep|drift|atmos|"
                  r"cinematic|reflect|piano|serene|wonder|frozen|lightless|ossuary", re.I)
AVOID = re.compile(r"funk|polka|comic|silly|circus|rock|metal|dance|march|hit|loop|jazz|vocal|sting", re.I)
AUDIO_MIME = ("audio/ogg", "audio/mpeg", "audio/x-flac", "audio/flac", "audio/wav", "audio/x-wav", "application/ogg")
MIN_S = 90


def _search(query: str, limit: int = 40) -> list[dict]:
    q = urllib.parse.urlencode({
        "action": "query", "format": "json", "formatversion": 2, "generator": "search",
        "gsrsearch": f"{query} filetype:audio", "gsrnamespace": 6, "gsrlimit": limit,
        "prop": "imageinfo", "iiprop": "url|size|mime|extmetadata|metadata",
        "iiextmetadatafilter": "LicenseShortName|LicenseUrl|Artist|Credit|ImageDescription",
    })
    data = _get(f"{COMMONS_API}?{q}")
    out = []
    for p in (data.get("query") or {}).get("pages") or []:
        ii = (p.get("imageinfo") or [{}])[0]
        meta = ii.get("extmetadata") or {}
        lic = allowed_licence((meta.get("LicenseShortName") or {}).get("value", ""))
        if not lic or ii.get("mime") not in AUDIO_MIME:
            continue
        length = next((m.get("value") for m in ii.get("metadata") or [] if m.get("name") == "length"), None)
        title = p["title"].removeprefix("File:").rsplit(".", 1)[0]
        out.append({"source": "wikimedia_commons", "id": p["title"], "title": title,
                    "page_url": ii.get("descriptionurl"), "download_url": ii.get("url"),
                    "licence": lic, "licence_url": (meta.get("LicenseUrl") or {}).get("value", ""),
                    "author": _clean_html((meta.get("Artist") or {}).get("value", "")) or "unknown",
                    "seconds": float(length) if length else None})
    return out


def find(dest: Path, seed: str, log: dict) -> dict | None:
    """Pick one calm track (different videos get different tracks), download it as 24 kHz mono WAV."""
    dest.mkdir(parents=True, exist_ok=True)
    cands, seen = [], set()
    for q in QUERIES:
        try:
            for c in _search(q):
                if c["id"] not in seen:
                    seen.add(c["id"])
                    cands.append(c)
        except Exception as e:  # noqa: BLE001
            log.setdefault("search_errors", []).append(f"{q}: {e!r}"[:200])
    ok = [c for c in cands if not AVOID.search(c["title"]) and (c["seconds"] is None or c["seconds"] >= MIN_S)]
    calm = [c for c in ok if MOOD.search(c["title"])] or ok
    log.update(candidates=len(cands), allowed=len(ok), calm=len(calm))
    if not calm:
        return None
    calm.sort(key=lambda c: hashlib.sha1((seed + c["id"]).encode()).hexdigest())
    for c in calm[:5]:
        try:
            raw = dest / ("track" + Path(urllib.parse.urlparse(c["download_url"]).path).suffix)
            raw.write_bytes(_get(c["download_url"], timeout=120, raw=True))
            wav = dest / "music.wav"
            r = subprocess.run(["ffmpeg", "-nostdin", "-y", "-loglevel", "error", "-i", str(raw), "-vn", "-ac", "1",
                                "-ar", "24000", str(wav)], stdin=subprocess.DEVNULL, capture_output=True, text=True,
                               timeout=300)
            if r.returncode:
                log.setdefault("decode_errors", []).append(f"{c['title']}: {r.stderr[-200:]}")
                continue
            secs = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
                                         "csv=p=0", str(wav)], capture_output=True, text=True,
                                        stdin=subprocess.DEVNULL, timeout=60).stdout.strip() or 0)
            if secs < MIN_S:
                continue
        except Exception as e:  # noqa: BLE001
            log.setdefault("download_errors", []).append(f"{c['title']}: {e!r}"[:200])
            continue
        rec = {"file": "music.wav", "kind": "music", "source": c["source"], "title": c["title"],
               "source_page": c["page_url"], "download_url": c["download_url"], "licence": c["licence"],
               "licence_url": c["licence_url"], "author": c["author"],
               "attribution": f"Music: \"{c['title']}\" by {c['author']}, {c['licence']}, via Wikimedia Commons. "
                              f"{c['page_url']}",
               "downloaded": dt.date.today().isoformat(), "seconds": round(secs, 1), "path": str(wav)}
        (dest / "music.licence.json").write_text(json.dumps(rec, indent=2, ensure_ascii=False))
        return rec
    return None
