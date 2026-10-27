"""Upload-ready package for the owner's review: description, credits, licences, review sheet.

Nothing here uploads anything. The owner reviews and uploads by hand in YouTube Studio.
"""
from __future__ import annotations

import json
from pathlib import Path

VOICE_RECORD = {
    "kind": "voice model", "name": "Kokoro-82M v1.0 (int8 ONNX via kokoro-onnx)",
    "source_page": "https://huggingface.co/hexgrad/Kokoro-82M",
    "download_url": "https://github.com/thewh1teagle/kokoro-onnx/releases/tag/model-files-v1.0",
    "licence": "Apache-2.0 (model weights); kokoro-onnx code MIT", "attribution": "Narration voice: Kokoro (hexgrad)",
}
OWNER_VOICE_RECORD = {
    "kind": "voice model", "name": "The channel owner's own voice, recorded on a phone",
    "source_page": "own recording", "licence": "own work (all rights held by the channel owner)",
    "attribution": "none required",
}
FONT_RECORD = {
    "kind": "font", "name": "DejaVu Sans (bundled with matplotlib)",
    "source_page": "https://dejavu-fonts.github.io/",
    "licence": "Bitstream Vera / DejaVu free font licence (free to use and embed)", "attribution": "none required",
}


DESC_LIMIT = 4900  # YouTube's limit is 5,000 characters; keep a little room for the owner's edits


def credit_lines(photos: list[dict]) -> dict:
    """Short credits for the description, full ones for credits.txt.

    NASA photos are public domain: one line. Each Commons photo: author, licence, page link;
    each licence's own link once at the end (CC BY / BY-SA ask for a link to the licence)."""
    from urllib.parse import unquote

    seen, nasa, pd, commons, licences, full = set(), 0, 0, [], {}, []
    for p in photos:
        if p["source_page"] in seen:
            continue
        seen.add(p["source_page"])
        full.append(f"- {p['attribution']}")
        if p["source"] == "nasa_image_library":
            nasa += 1
        elif not p["licence"].upper().startswith("CC BY"):  # public domain / CC0: no attribution required
            pd += 1
        else:
            author = p["author"] if len(p["author"]) <= 40 else p["author"][:38] + "…"
            commons.append(f"- {author}, {p['licence']}: {unquote(p['source_page'])}")
            if p.get("licence_url"):
                licences[p["licence"]] = p["licence_url"]
    short = ([f"- {nasa} images: NASA (public domain)"] if nasa else []) + \
        ([f"- {pd} images: public domain / CC0, via Wikimedia Commons"] if pd else []) + commons
    if licences:
        short += ["Licences: " + "; ".join(f"{k} {v}" for k, v in sorted(licences.items()))]
    return {"short": short, "full": full}


def _mmss(t: float) -> str:
    t = int(t)
    return f"{t // 60}:{t % 60:02}"


class RightsError(RuntimeError):
    pass


def rights_gate(photos: list[dict]) -> None:
    """Stop before packaging if any picture lacks a complete record or an allowed licence."""
    from .photos import allowed_licence

    bad = []
    for p in photos:
        missing = [k for k in ("source_page", "licence", "author", "attribution", "downloaded") if not p.get(k)]
        if missing:
            bad.append(f"{p.get('file')}: missing {missing}")
        elif p["source"] != "nasa_image_library" and not allowed_licence(p["licence"]):
            bad.append(f"{p.get('file')}: licence {p['licence']!r} is not allowed")
    if bad:
        raise RightsError("Rights check failed:\n" + "\n".join(bad))


def fact_table(script: dict, sources: dict, path: Path) -> None:
    """One row per sentence: what it says, its check result, and the exact source text and link."""
    import csv

    idx = {p["id"]: (a, p) for a in sources["articles"] for p in a["passages"]}
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["sentence_id", "kind", "sentence", "check", "source_id", "source_title", "source_link",
                    "retrieved", "source_text"])
        for sc in script["scenes"]:
            for s in sc["sentences"]:
                for pid in s["sources"] or [""]:
                    a, p = idx.get(pid, ({}, {}))
                    link = f"{a['url']}?oldid={a['revision_id']}" if a else ""
                    w.writerow([s["id"], s["kind"], s["text"], s.get("check", ""), pid, a.get("title", ""), link,
                                a.get("retrieved", ""), p.get("text", "")])


def chapters(scenes: list[dict]) -> list[str]:
    """YouTube chapters: first at 0:00, at least 3, each at least 10 s long."""
    out, last = [], -100.0
    for i, sc in enumerate(scenes):
        t = 0.0 if i == 0 else sc["start"]
        if t - last >= 10:
            out.append(f"{_mmss(t)} {sc['heading']}")
            last = t
    return out if len(out) >= 3 else []


def write(out: Path, script: dict, the_plan: dict, sources: dict, visuals: list[dict], scenes: list[dict],
          factcheck: dict, run_info: dict) -> None:
    photos = [v["photo"] for v in visuals if v.get("photo")]
    rights_gate(photos)
    # Licences: every asset in the video.
    owner = run_info.get("voice") == "owner"
    records = [OWNER_VOICE_RECORD if owner else VOICE_RECORD, FONT_RECORD] + \
        [{k: p[k] for k in p if k != "path"} for p in photos]
    (out / "licences.json").write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")

    fact_table(script, sources, out / "facts.csv")

    # Description (draft — the owner edits it in YouTube Studio).
    used_ids = {pid for sc in script["scenes"] for s in sc["sentences"] for pid in s["sources"]}
    arts = [a for a in sources["articles"] if any(p["id"] in used_ids for p in a["passages"])]
    lines = [script["title"], "", the_plan["question"], ""]
    ch = chapters(scenes)
    if ch:
        lines += ["Chapters:"] + ch + [""]
    lines += ["Sources (facts checked against these):"]
    lines += [f"- {a['title']} — Wikipedia, revision {a['revision_id']}: "
              f"{a['url']}?oldid={a['revision_id']}" for a in arts]
    footer = ["", "NASA images are used for education and do not imply NASA endorsement.",
              ("Narrated by the creator. " if owner else "Narration voice: Kokoro text-to-speech (synthetic voice). ")
              + "Script researched and written with AI help, fact-checked against the sources above and reviewed "
              "by a human before upload."]
    credits = credit_lines(photos)
    (out / "credits.txt").write_text("Image credits:\n" + "\n".join(credits["full"]) + "\n", encoding="utf-8")
    body = lines + ["", "Image credits:"] + credits["short"] + footer
    if len("\n".join(body)) > DESC_LIMIT:  # YouTube allows 5,000 characters; the GPS video had 9,850
        body = lines + ["", "Image credits: NASA (public domain) and Wikimedia Commons contributors. "
                            "Full list with licences in the pinned comment."] + footer
    lines = body
    (out / "description.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

    # Review sheet: every sentence, its sources and its check result.
    idx = {p["id"]: (a, p) for a in sources["articles"] for p in a["passages"]}
    md = [f"# Review: {script['title']}", "",
          f"**Question:** {the_plan['question']}  ", f"**Angle:** {the_plan['angle']}  ",
          f"**Structure:** {the_plan['structure']}", "",
          f"Words: {run_info.get('words')} · Video: {run_info.get('video_seconds')} s · "
          f"Visuals: {run_info.get('visuals')} ({run_info.get('photos')} photos, {run_info.get('cards')} cards)", "",
          "## Fact-check summary", "",
          f"- Sentences checked: {factcheck['checked']}, passed first time: {factcheck['supported_first_pass']}",
          f"- Fixed: {len(factcheck['fixed'])}, dropped: {len(factcheck['dropped'])}, "
          f"bad source ids: {len(factcheck['bad_ids'])}, copied 8-word phrases: {len(factcheck['copied'])}", ""]
    for f in factcheck["fixed"]:
        md.append(f"- FIXED {f['id']}: ~~{f['old']}~~ → {f['new']} ({f['problem']})")
    for d in factcheck["dropped"]:
        md.append(f"- DROPPED {d['id']}: {d['text']} ({d['problem']})")
    md += ["", "## Script with sources", ""]
    for sc in script["scenes"]:
        md += [f"### {sc['heading']}", ""]
        for s in sc["sentences"]:
            src = ", ".join(f"[{pid}]({idx[pid][0]['url']}?oldid={idx[pid][0]['revision_id']})"
                            for pid in s["sources"] if pid in idx) or "—"
            md.append(f"- `{s['id']}` {s['text']}  \n  _{s['kind']}, {s.get('check', '')}; sources: {src}_")
        md.append("")
    md += ["## Before you upload (owner checklist)", "",
           "- [ ] Watch the whole video. Pictures match what is said? No wrong or odd photo?",
           "- [ ] Read the script above. Any sentence that sounds wrong, check its source link.",
           "- [ ] Title and description honest? Edit description.txt as you like.",
           "- [ ] Upload subtitles.srt as English subtitles in YouTube Studio.",
           "- [ ] AI disclosure ('altered or synthetic content'): only needed for realistic AI depictions of real "
           "people, places or events. This video uses real photos, charts and a TTS voice, so normally: No.",
           "- [ ] Made for kids: No (general audience explainer)."]
    (out / "review.md").write_text("\n".join(md) + "\n", encoding="utf-8")


def contact_sheet(frames: list[Path], out: Path, cols: int = 8, width: int = 320) -> None:
    """All keyframes on one image, in order: a quick way to judge the visuals."""
    from PIL import Image, ImageDraw

    if not frames:
        return
    h = width * 9 // 16
    rows = (len(frames) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * width, rows * h), (0, 0, 0))
    d = ImageDraw.Draw(sheet)
    for i, f in enumerate(frames):
        im = Image.open(f).convert("RGB").resize((width, h))
        x, y = (i % cols) * width, (i // cols) * h
        sheet.paste(im, (x, y))
        d.text((x + 6, y + 4), f.stem, fill=(255, 255, 0))
    sheet.save(out, quality=85)
