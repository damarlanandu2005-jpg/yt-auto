"""Add ChatGPT picture batches to the library (cartoon/art/): unpack, cut the white background off objects, write the
cards in library.json and the browser copy cartoon/art_cards.js. Run it on any zip the owner sends (a zip of batch
zips is fine). Names come from the file names (BATCHES.md); a batch is a place batch if its name has "places".

  python3 cartoon/art/add_batch.py images.zip [--cards cards.json]

--cards: optional JSON {name: {...card fields...}} for the new pictures (floor/ground/light/tags for places,
height_m/stand/tags for objects). Pictures without a card get safe defaults and are listed so a card can be added.
"""
from __future__ import annotations

import argparse
import datetime
import io
import json
import re
import zipfile
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

ART = Path(__file__).resolve().parent
LIB = ART / "library.json"
NAME = re.compile(r"[\w.-]+\.(png|jpg|jpeg|webp)", re.I)


def cut_white(im: Image.Image) -> Image.Image:
    """Make the plain white background transparent: flood fill from the border, so white INSIDE stays."""
    a = np.asarray(im.convert("RGB")).astype(int)
    h, w, _ = a.shape
    white = (a.min(axis=2) > 232) & ((a.max(axis=2) - a.min(axis=2)) < 22)
    bg = np.zeros((h, w), bool)
    q = deque((y, x) for y in range(h) for x in (0, w - 1) if white[y, x])
    q.extend((y, x) for x in range(w) for y in (0, h - 1) if white[y, x])
    for y, x in q:
        bg[y, x] = True
    while q:
        y, x = q.popleft()
        for ny, nx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
            if 0 <= ny < h and 0 <= nx < w and white[ny, nx] and not bg[ny, nx]:
                bg[ny, nx] = True
                q.append((ny, nx))
    alpha = Image.fromarray(np.where(bg, 0, 255).astype("uint8")).filter(ImageFilter.GaussianBlur(0.8))
    out = im.convert("RGBA")
    out.putalpha(alpha)
    out = out.crop(out.getbbox())
    out.thumbnail((640, 640), Image.LANCZOS)
    return out


def pictures(path: Path, batch: str = ""):
    """(batch name, file name, bytes) for every picture in a zip, also inside zips in the zip."""
    z = zipfile.ZipFile(path) if isinstance(path, Path) else zipfile.ZipFile(io.BytesIO(path))
    for info in z.infolist():
        if info.is_dir():
            continue
        name = Path(info.filename).name
        if name.lower().endswith(".zip"):
            yield from pictures(z.read(info), Path(name).stem)
        elif NAME.fullmatch(name):
            yield batch or Path(info.filename).parent.name, name, z.read(info)


def write_cards(lib: dict) -> None:
    places = {n: {k: v[k] for k in ("file", "floor", "ground", "light")} for n, v in lib["places"].items()}
    things = {n: {"file": v["file"], "w": v["size"][0], "h": v["size"][1], "height_m": v["height_m"], "stand": v["stand"]}
              for n, v in lib["things"].items()}
    (ART.parent / "art_cards.js").write_text(
        "// Made from cartoon/art/library.json by cartoon/art/add_batch.py: do not edit by hand.\n"
        f"export const PLACES = {json.dumps(places, indent=1)};\nexport const ART = {json.dumps(things, indent=1)};\n")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("zip", type=Path)
    ap.add_argument("--cards", type=Path)
    args = ap.parse_args()
    lib = json.loads(LIB.read_text())
    cards = json.loads(args.cards.read_text()) if args.cards else {}
    prompts = {}
    for f in ("PROMPTS.md", "BATCHES.md"):
        for line in (ART / f).read_text().splitlines():
            m = re.match(r"\|\s*[PO]\d+\s*\|\s*(\w+)\s*\|\s*(.+?)\s*\|$", line)
            if m:
                prompts[m.group(1)] = m.group(2)
    added, no_card = [], []
    for batch, name, data in pictures(args.zip):
        n = Path(name).stem.lower()
        im = Image.open(io.BytesIO(data))
        card = cards.get(n, {})
        if "place" in batch:
            (ART / "places").mkdir(exist_ok=True)
            im.convert("RGB").save(ART / "places" / f"{n}.jpg", quality=92)
            lib["places"][n] = {"file": f"places/{n}.jpg", "size": list(im.size), "prompt": prompts.get(n, ""), "batch": batch,
                                "floor": card.get("floor", 0.66), "ground": card.get("ground", "floor"),
                                "light": card.get("light", "day"), "tags": card.get("tags", n.split("_"))}
        else:
            (ART / "things").mkdir(exist_ok=True)
            t = cut_white(im)
            t.save(ART / "things" / f"{n}.png", optimize=True)
            lib["things"][n] = {"file": f"things/{n}.png", "size": list(t.size), "prompt": prompts.get(n, ""), "batch": batch,
                                "height_m": card.get("height_m", 1.0), "stand": card.get("stand", "floor"),
                                "tags": card.get("tags", n.split("_"))}
        added.append(n)
        if not card:
            no_card.append(n)
    lib["licence"]["added"] = datetime.date.today().isoformat()
    LIB.write_text(json.dumps(lib, indent=1))
    write_cards(lib)
    print(f"added {len(added)}: {', '.join(added)}")
    if no_card:
        print(f"default cards (check floor / size): {', '.join(no_card)}")


if __name__ == "__main__":
    main()
