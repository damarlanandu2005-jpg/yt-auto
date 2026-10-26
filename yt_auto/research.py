"""Sources: fetch Wikipedia articles and save them as numbered passages.

Every factual script sentence must cite passage ids from here (e.g. "A2.14"), so a
reviewer can open sources.json and see the exact text behind each claim. Each
article keeps its URL, revision id and download date. We only take facts from the
text and write our own sentences; we never read it out (YouTube's rule on
reused content, and the text is CC BY-SA).
"""
from __future__ import annotations

import datetime as dt
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

from .photos import UA

API = "https://en.wikipedia.org/w/api.php"
SKIP_SECTIONS = {"references", "see also", "external links", "further reading", "notes", "bibliography",
                 "sources", "citations", "footnotes", "gallery", "explanatory notes"}
MAX_CHARS_PER_ARTICLE = 30_000
_last = 0.0


def _api(params: dict) -> dict:
    global _last
    wait = 1.0 - (time.time() - _last)  # one request at a time, about 1 per second
    if wait > 0:
        time.sleep(wait)
    url = f"{API}?{urllib.parse.urlencode({**params, 'format': 'json', 'formatversion': 2})}"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                _last = time.time()
                return json.loads(r.read())
        except Exception:  # noqa: BLE001
            if attempt == 2:
                raise
            time.sleep(5 * (attempt + 1))
    return {}


def resolve_title(title: str) -> str | None:
    d = _api({"action": "query", "list": "search", "srsearch": title, "srlimit": 1, "srnamespace": 0})
    hits = (d.get("query") or {}).get("search") or []
    return hits[0]["title"] if hits else None


def fetch_article(title: str) -> dict | None:
    d = _api({"action": "query", "prop": "extracts|revisions|info", "explaintext": 1, "exsectionformat": "wiki",
              "rvprop": "ids|timestamp", "inprop": "url", "redirects": 1, "titles": title})
    pages = (d.get("query") or {}).get("pages") or []
    if not pages or pages[0].get("missing") or not pages[0].get("extract"):
        found = resolve_title(title)
        if not found or found == title:
            return None
        return fetch_article(found)
    p = pages[0]
    rev = (p.get("revisions") or [{}])[0]
    return {"title": p["title"], "url": p.get("fullurl"), "revision_id": rev.get("revid"),
            "revision_time": rev.get("timestamp"), "text": p["extract"]}


def passages(text: str) -> list[dict]:
    """Split a plain-text article into paragraphs, each tagged with its section."""
    out, section, total = [], "Introduction", 0
    for line in text.split("\n"):
        line = line.strip()
        m = re.match(r"^(=+)\s*(.*?)\s*\1$", line)
        if m:
            if len(m.group(1)) == 2:  # top-level section; subsections inherit its skip status
                section = m.group(2)
            continue
        if section.lower() in SKIP_SECTIONS or len(line) < 80:
            continue
        out.append({"section": section, "text": line})
        total += len(line)
        if total > MAX_CHARS_PER_ARTICLE:
            break
    return out


def gather(titles: list[str], out_path: Path) -> dict:
    """Fetch articles, number their passages A<article>.<paragraph>, save sources.json."""
    articles, seen = [], set()
    for t in titles:
        try:
            art = fetch_article(t)
        except Exception as e:  # noqa: BLE001
            print(f"[research] {t!r} failed: {e!r}", flush=True)
            continue
        if not art or art["title"] in seen:
            continue
        seen.add(art["title"])
        n = len(articles) + 1
        art["id"] = f"A{n}"
        art["passages"] = [{"id": f"A{n}.{i + 1}", **p} for i, p in enumerate(passages(art.pop("text")))]
        art["licence"] = "CC BY-SA 4.0 (Wikipedia text; facts used, wording not copied)"
        art["retrieved"] = dt.date.today().isoformat()
        articles.append(art)
        print(f"[research] {art['id']} {art['title']}: {len(art['passages'])} passages", flush=True)
    data = {"articles": articles}
    out_path.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")
    return data


def passage_index(sources: dict) -> dict[str, dict]:
    return {p["id"]: {**p, "article": a["title"], "url": a["url"]} for a in sources["articles"] for p in a["passages"]}


def as_prompt_text(sources: dict) -> str:
    lines = []
    for a in sources["articles"]:
        lines.append(f"### {a['id']}: {a['title']}")
        sec = None
        for p in a["passages"]:
            if p["section"] != sec:
                sec = p["section"]
                lines.append(f"[section: {sec}]")
            lines.append(f"{p['id']}: {p['text']}")
    return "\n".join(lines)
