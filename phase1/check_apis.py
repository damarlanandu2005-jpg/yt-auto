"""Phase 1 pre-flight: is the Gemini key there, which models can it use for free,
and are the NASA and Wikimedia Commons APIs reachable without a key?

Runs on GitHub Actions (the cloud dev box can't reach these hosts). Writes
check.json plus copies of Google's pricing / rate-limit pages so the limits can
be read from the official source, not from blogs.

The API key is sent in a header and never printed or saved.
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

GEMINI = "https://generativelanguage.googleapis.com/v1beta"
UA = "yt-auto-phase1-check/0.1 (https://github.com/damarlanandu2005-jpg/yt-auto; private research pipeline)"


def http(url: str, data: dict | None = None, headers: dict | None = None, timeout: int = 60) -> dict:
    h = {"User-Agent": UA, **(headers or {})}
    body = None
    if data is not None:
        body = json.dumps(data).encode()
        h["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, headers=h)
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read()
            status, resp_headers = r.status, dict(r.headers)
    except urllib.error.HTTPError as e:
        raw, status, resp_headers = e.read(), e.code, dict(e.headers)
    except Exception as e:  # noqa: BLE001
        return {"status": None, "error": repr(e), "seconds": round(time.perf_counter() - t0, 2)}
    out = {"status": status, "seconds": round(time.perf_counter() - t0, 2),
           "headers": {k: v for k, v in resp_headers.items() if "limit" in k.lower() or k.lower() in ("retry-after", "content-type")}}
    try:
        out["json"] = json.loads(raw)
    except ValueError:
        out["text"] = raw.decode(errors="replace")
    return out


def gemini(out: Path) -> dict:
    key = os.environ.get("GEMINI_API_KEY", "")
    res: dict = {"key_present": bool(key)}
    if not key:
        return res
    hdr = {"x-goog-api-key": key}
    models, page = [], ""
    for _ in range(10):
        r = http(f"{GEMINI}/models?pageSize=200" + (f"&pageToken={page}" if page else ""), headers=hdr)
        if r["status"] != 200:
            res["list_models_error"] = r
            return res
        models += r["json"].get("models", [])
        page = r["json"].get("nextPageToken", "")
        if not page:
            break
    res["models"] = [{"name": m["name"], "display": m.get("displayName"),
                      "methods": m.get("supportedGenerationMethods"),
                      "input_tokens": m.get("inputTokenLimit"), "output_tokens": m.get("outputTokenLimit")}
                     for m in models]
    names = [m["name"] for m in models if "generateContent" in (m.get("supportedGenerationMethods") or [])]

    # One tiny call per candidate. A free-tier quota error (429) names the quota and its value.
    text = [n for n in names if "flash" in n and not any(x in n for x in ("image", "tts", "live", "audio", "embedding"))]
    image = [n for n in names if "image" in n]
    res["calls"] = {}
    for n in text[:8]:
        r = http(f"{GEMINI}/{n}:generateContent", headers=hdr,
                 data={"contents": [{"parts": [{"text": "Reply with the single word OK."}]}]})
        res["calls"][n] = _summary(r)
        time.sleep(4)
    for n in image[:4]:
        r = http(f"{GEMINI}/{n}:generateContent", headers=hdr, timeout=120,
                 data={"contents": [{"parts": [{"text": "A flat, simple vector icon of a satellite on a plain dark background."}]}],
                       "generationConfig": {"responseModalities": ["TEXT", "IMAGE"]}})
        res["calls"][n] = _summary(r)
        time.sleep(4)
    # Imagen models use :predict
    for n in [n for n in (m["name"] for m in models) if "imagen" in n][:2]:
        r = http(f"{GEMINI}/{n}:predict", headers=hdr, timeout=120,
                 data={"instances": [{"prompt": "flat vector icon of a satellite"}], "parameters": {"sampleCount": 1}})
        res["calls"][n] = _summary(r)
    return res


def _summary(r: dict) -> dict:
    s = {"status": r.get("status"), "seconds": r.get("seconds")}
    j = r.get("json") or {}
    if "error" in j:
        s["error"] = j["error"]  # includes QuotaFailure details on 429
    elif "candidates" in j:
        parts = (j["candidates"][0].get("content") or {}).get("parts") or []
        s["parts"] = [("image" if "inlineData" in p else (p.get("text") or "")[:80]) for p in parts]
        s["usage"] = j.get("usageMetadata")
    elif "predictions" in j:
        s["parts"] = ["image"] * len(j["predictions"])
    elif r.get("error"):
        s["error"] = r["error"]
    return s


def nasa() -> dict:
    q = urllib.parse.urlencode({"q": "GPS satellite", "media_type": "image", "page_size": 5})
    r = http(f"https://images-api.nasa.gov/search?{q}")
    res = {"status": r["status"], "seconds": r["seconds"], "headers": r.get("headers"), "error": r.get("error")}
    items = ((r.get("json") or {}).get("collection") or {}).get("items") or []
    res["total_hits"] = ((r.get("json") or {}).get("collection") or {}).get("metadata", {}).get("total_hits")
    res["sample"] = [{"nasa_id": it["data"][0].get("nasa_id"), "title": it["data"][0].get("title"),
                      "center": it["data"][0].get("center"), "secondary_creator": it["data"][0].get("secondary_creator"),
                      "date": it["data"][0].get("date_created"), "asset": it.get("href")} for it in items[:5]]
    if items:
        a = http(items[0]["href"])
        res["asset_manifest"] = {"status": a["status"], "files": (a.get("json") or [])[:8]}
    return res


def commons() -> dict:
    q = urllib.parse.urlencode({
        "action": "query", "format": "json", "formatversion": 2, "generator": "search",
        "gsrsearch": "GPS satellite filetype:bitmap", "gsrnamespace": 6, "gsrlimit": 5,
        "prop": "imageinfo", "iiprop": "url|size|mime|extmetadata", "iiurlwidth": 1920,
        "iiextmetadatafilter": "LicenseShortName|LicenseUrl|Artist|Credit|AttributionRequired|UsageTerms|Copyrighted",
    })
    r = http(f"https://commons.wikimedia.org/w/api.php?{q}")
    res = {"status": r["status"], "seconds": r["seconds"], "headers": r.get("headers"), "error": r.get("error")}
    pages = ((r.get("json") or {}).get("query") or {}).get("pages") or []
    res["sample"] = [{"title": p["title"],
                      "licence": ((p.get("imageinfo") or [{}])[0].get("extmetadata") or {}).get("LicenseShortName", {}).get("value"),
                      "size": [(p.get("imageinfo") or [{}])[0].get("width"), (p.get("imageinfo") or [{}])[0].get("height")]}
                     for p in pages]
    return res


def save_pages(out: Path) -> dict:
    """Official pages, saved so the limits can be read from Google/NASA/Wikimedia directly."""
    pages = {
        "gemini_pricing.html": "https://ai.google.dev/gemini-api/docs/pricing",
        "gemini_rate_limits.html": "https://ai.google.dev/gemini-api/docs/rate-limits",
        "gemini_models.html": "https://ai.google.dev/gemini-api/docs/models",
        "gemini_deprecations.html": "https://ai.google.dev/gemini-api/docs/deprecations",
        "gemini_terms.html": "https://ai.google.dev/gemini-api/terms",
        "nasa_media_guidelines.html": "https://www.nasa.gov/nasa-brand-center/images-and-media/",
        "nasa_api_docs.pdf": "https://images.nasa.gov/docs/images.nasa.gov_api_docs.pdf",
        "wikimedia_api_etiquette.html": "https://www.mediawiki.org/wiki/API:Etiquette",
        "wikimedia_user_agent_policy.html": "https://foundation.wikimedia.org/wiki/Policy:Wikimedia_Foundation_User-Agent_Policy",
        "wikimedia_api_access_policy.html": "https://www.mediawiki.org/wiki/Wikimedia_APIs/Access_policy",
    }
    d = out / "pages"
    d.mkdir(parents=True, exist_ok=True)
    status = {}
    for name, url in pages.items():
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=60) as r:
                (d / name).write_bytes(r.read())
                status[name] = r.status
        except Exception as e:  # noqa: BLE001
            status[name] = repr(e)
    return status


def main() -> None:
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "out/check")
    out.mkdir(parents=True, exist_ok=True)
    result = {"gemini": gemini(out), "nasa": nasa(), "commons": commons(), "pages": save_pages(out)}
    (out / "check.json").write_text(json.dumps(result, indent=2))
    g = result["gemini"]
    print("GEMINI_API_KEY present:", g["key_present"])
    for n, c in (g.get("calls") or {}).items():
        print(f"  {n}: {c['status']}", (c.get("error") or {}).get("message", "")[:150] if isinstance(c.get("error"), dict) else "")
    print("NASA:", result["nasa"]["status"], "hits:", result["nasa"].get("total_hits"))
    print("Commons:", result["commons"]["status"], [s["licence"] for s in result["commons"]["sample"]])


if __name__ == "__main__":
    main()
