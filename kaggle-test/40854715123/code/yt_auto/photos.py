"""Real photos: NASA Image and Video Library + Wikimedia Commons.

Only these licences are allowed: public domain, CC0, CC BY, CC BY-SA.
Never CC BY-NC or ND, never GFDL-only or "fair use". Every downloaded file gets
a licence JSON next to it (source URL, licence + version, attribution, date).

Both APIs are free and need no key. We are polite: a proper User-Agent,
one request at a time, a short pause between Commons calls.
"""
from __future__ import annotations

import datetime as dt
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

UA = "yt-auto/0.1 (https://github.com/damarlanandu2005-jpg; educational explainer videos) python-urllib"
COMMONS_API = "https://commons.wikimedia.org/w/api.php"
NASA_API = "https://images-api.nasa.gov/search"
MAX_BYTES = 40_000_000
MIN_WIDTH = 1000  # smaller photos look soft at 1080p

# NASA media is public domain unless a third party holds the copyright; skip anything that says so.
_NASA_THIRD_PARTY = re.compile(
    r"©|copyright|getty|ap photo|associated press|reuters|afp|courtesy of(?! nasa)|\besa\b|jaxa|roscosmos|"
    r"used with permission|all rights reserved", re.I)

_last_commons = 0.0


def _get(url: str, timeout: int = 60, raw: bool = False):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                data = r.read(MAX_BYTES + 1)
                return data if raw else json.loads(data)
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503) and attempt < 2:
                time.sleep(float(e.headers.get("Retry-After") or 5 * (attempt + 1)))
                continue
            raise
        except (urllib.error.URLError, TimeoutError):
            if attempt < 2:
                time.sleep(3)
                continue
            raise


AI_MODEL_LICENCES = ("Apache-2.0", "MIT")  # drawing models whose licences put no limits on their output


def record_allowed(r: dict) -> bool:
    """Is a picture's licence record allowed? NASA: public domain. AI drawings: the model's licence."""
    if r.get("source") == "nasa_image_library":
        return True
    if r.get("source") == "ai_drawing":
        return r.get("model_licence") in AI_MODEL_LICENCES
    return bool(allowed_licence(r.get("licence", "")))


def allowed_licence(short_name: str) -> str | None:
    """Return a normalised licence name if allowed, else None."""
    s = (short_name or "").strip()
    u = s.upper()
    if not s or "NC" in re.split(r"[-\s]", u) or "ND" in re.split(r"[-\s]", u):
        return None
    if u.startswith("CC0") or u in ("PUBLIC DOMAIN", "PD") or u.startswith("PD-") or u.startswith("PUBLIC DOMAIN"):
        return s
    if re.match(r"^CC BY(-SA)? \d(\.\d)?", u):
        return s
    return None


def _clean_html(s: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", s or "")).strip()


def search_commons(query: str, limit: int = 8) -> list[dict]:
    global _last_commons
    wait = 1.0 - (time.time() - _last_commons)
    if wait > 0:
        time.sleep(wait)
    q = urllib.parse.urlencode({
        "action": "query", "format": "json", "formatversion": 2, "generator": "search",
        "gsrsearch": f"{query} filetype:bitmap", "gsrnamespace": 6, "gsrlimit": limit,
        "prop": "imageinfo", "iiprop": "url|size|mime|extmetadata", "iiurlwidth": 1920,
        "iiextmetadatafilter": "LicenseShortName|LicenseUrl|Artist|Credit|ImageDescription|AttributionRequired",
    })
    data = _get(f"{COMMONS_API}?{q}")
    _last_commons = time.time()
    out = []
    for p in (data.get("query") or {}).get("pages") or []:
        ii = (p.get("imageinfo") or [{}])[0]
        meta = ii.get("extmetadata") or {}
        lic = allowed_licence((meta.get("LicenseShortName") or {}).get("value", ""))
        if not lic or ii.get("mime") not in ("image/jpeg", "image/png") or (ii.get("width") or 0) < MIN_WIDTH:
            continue
        out.append({
            "source": "wikimedia_commons",
            "id": p["title"],
            "title": p["title"].removeprefix("File:").rsplit(".", 1)[0],
            "description": _clean_html((meta.get("ImageDescription") or {}).get("value", ""))[:300],
            "page_url": ii.get("descriptionurl"),
            "download_url": ii.get("thumburl") or ii.get("url"),
            "width": ii.get("width"), "height": ii.get("height"),
            "licence": lic,
            "licence_url": (meta.get("LicenseUrl") or {}).get("value", ""),
            "author": _clean_html((meta.get("Artist") or {}).get("value", "")) or "unknown",
            "credit": _clean_html((meta.get("Credit") or {}).get("value", "")),
        })
    return out


def search_nasa(query: str, limit: int = 8) -> list[dict]:
    q = urllib.parse.urlencode({"q": query, "media_type": "image", "page_size": limit})
    data = _get(f"{NASA_API}?{q}")
    out = []
    for it in (data.get("collection") or {}).get("items") or []:
        d = it["data"][0]
        text = " ".join(str(d.get(k, "")) for k in ("description", "photographer", "secondary_creator", "title"))
        if _NASA_THIRD_PARTY.search(text):
            continue
        nid = d["nasa_id"]
        out.append({
            "source": "nasa_image_library",
            "id": nid,
            "title": d.get("title", ""),
            "description": _clean_html(d.get("description", ""))[:300],
            "page_url": f"https://images.nasa.gov/details/{urllib.parse.quote(nid)}",
            "manifest_url": it.get("href"),
            "licence": "Public domain (NASA media, not copyrighted in the US)",
            "licence_url": "https://www.nasa.gov/nasa-brand-center/images-and-media/",
            "author": d.get("photographer") or d.get("secondary_creator") or f"NASA ({d.get('center', '')})".replace(" ()", ""),
            "credit": "NASA",
            "date_created": d.get("date_created"),
        })
    return out


def search(queries: list[str], per_source: int = 6) -> list[dict]:
    seen, out = set(), []
    for q in queries:
        for fn in (search_nasa, search_commons):
            try:
                found = fn(q, per_source)
            except Exception as e:  # noqa: BLE001 — one failed search shouldn't stop the video
                print(f"[photos] {fn.__name__}({q!r}) failed: {e!r}", flush=True)
                continue
            for c in found:
                if c["id"] not in seen:
                    seen.add(c["id"])
                    out.append(c)
    return out


def _nasa_file_url(manifest_url: str) -> str | None:
    files = _get(manifest_url)
    for suffix in ("~large.jpg", "~orig.jpg", "~medium.jpg"):
        for f in files:
            if f.endswith(suffix):
                return f.replace("http://", "https://")
    return None


def download(cand: dict, dest_dir: Path, stem: str) -> Path | None:
    """Download one chosen photo and write its licence record. Returns the image path."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    url = cand.get("download_url") or _nasa_file_url(cand["manifest_url"])
    if not url:
        return None
    data = _get(url, timeout=120, raw=True)
    if len(data) > MAX_BYTES:
        return None
    ext = ".png" if url.lower().endswith(".png") else ".jpg"
    path = dest_dir / f"{stem}{ext}"
    path.write_bytes(data)
    record = {
        "file": path.name,
        "kind": "photo",
        "source": cand["source"],
        "title": cand["title"],
        "source_page": cand["page_url"],
        "download_url": url,
        "licence": cand["licence"],
        "licence_url": cand.get("licence_url", ""),
        "author": cand["author"],
        "attribution": attribution(cand),
        "downloaded": dt.date.today().isoformat(),
    }
    path.with_suffix(".licence.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    return path


def attribution(cand: dict) -> str:
    if cand["source"] == "nasa_image_library":
        return f"{cand['title']} — {cand['author']}, NASA, public domain. {cand['page_url']}"
    return f"\"{cand['title']}\" by {cand['author']}, {cand['licence']}, via Wikimedia Commons. {cand['page_url']}"
