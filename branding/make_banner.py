"""Channel banner (2560x1440, YouTube's size) drawn in code: black sky, white ink-line planet and orbits,
one red accent, the name and tagline inside the 1546x423 area that every device shows. Own work.

    python branding/make_banner.py "Cosmic Why" "Why" out.png
"""
from __future__ import annotations

import math
import random
import sys
from pathlib import Path

import matplotlib
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 2560, 1440
SAFE_W, SAFE_H = 1546, 423
RED, WHITE, GREY = (232, 60, 60), (245, 245, 245), (150, 150, 150)
FONTS = Path(matplotlib.get_data_path()) / "fonts" / "ttf"


def banner(name: str, red_word: str, out: Path, tagline: str = "Big space questions, answered in plain words") -> None:
    rnd = random.Random(7)
    im = Image.new("RGB", (W, H), (6, 7, 12))
    d = ImageDraw.Draw(im)
    for _ in range(1400):  # stars, a few brighter
        x, y, b = rnd.randrange(W), rnd.randrange(H), rnd.random()
        r = 2 if b > 0.97 else 1
        c = int(90 + 165 * b)
        d.ellipse((x - r, y - r, x + r, y + r), fill=(c, c, c))
    # ink-line ringed planet on the right, outside the text area
    cx, cy, R = 2240, 300, 165  # top right, clear of the text area (rings crossed the name at 2050,760)
    glow = Image.new("RGB", (W, H))
    ImageDraw.Draw(glow).ellipse((cx - R - 60, cy - R - 60, cx + R + 60, cy + R + 60), fill=(40, 40, 60))
    im = Image.composite(im, Image.blend(im, glow.filter(ImageFilter.GaussianBlur(60)), 0.6), Image.new("L", (W, H), 255))
    d = ImageDraw.Draw(im)
    d.ellipse((cx - R, cy - R, cx + R, cy + R), fill=(10, 10, 16), outline=WHITE, width=5)
    for k in range(-4, 5):  # hatched bands
        yy = cy + k * R / 5
        half = math.sqrt(max(R * R - (yy - cy) ** 2, 0))
        d.arc((cx - half, yy - 18, cx + half, yy + 18), 0, 180, fill=GREY, width=2)
    for i, (a, b) in enumerate(((R * 2.1, R * 0.55), (R * 2.45, R * 0.66))):  # rings, tilted
        box = (cx - a, cy - b, cx + a, cy + b)
        ring = Image.new("L", (W, H))
        ImageDraw.Draw(ring).ellipse(box, outline=255, width=6 - 2 * i)
        ring = ring.rotate(-14, center=(cx, cy))
        im.paste(WHITE, mask=ring)
    d = ImageDraw.Draw(im)
    d.ellipse((cx - 260 - 14, cy + 170 - 14, cx - 260 + 14, cy + 170 + 14), fill=RED)  # small red moon
    # orbit lines on the left, outside the text area
    for i, rr in enumerate((330, 470, 610)):
        d.arc((-120 - rr, 760 - rr, -120 + rr, 760 + rr), -70, 70, fill=GREY, width=3 - (i > 0))
    d.ellipse((-120 + 470 * math.cos(math.radians(-25)) - 12, 760 + 470 * math.sin(math.radians(-25)) - 12,
               -120 + 470 * math.cos(math.radians(-25)) + 12, 760 + 470 * math.sin(math.radians(-25)) + 12), fill=WHITE)
    # text inside the safe area
    x0, y0 = (W - SAFE_W) // 2, (H - SAFE_H) // 2
    size = 200
    words = name.upper().split()
    while size > 80:
        font = ImageFont.truetype(str(FONTS / "DejaVuSans-Bold.ttf"), size)
        if font.getlength(" ".join(words)) <= SAFE_W * 0.92:
            break
        size -= 6
    total = font.getlength(" ".join(words))
    x, y = (W - total) / 2, y0 + 40
    for w in words:
        d.text((x, y), w, font=font, fill=RED if w == red_word.upper() else WHITE, stroke_width=4, stroke_fill=(0, 0, 0))
        x += font.getlength(w + " ")
    small = ImageFont.truetype(str(FONTS / "DejaVuSans.ttf"), 64)
    tw = small.getlength(tagline)
    d.text(((W - tw) / 2, y + size + 40), tagline, font=small, fill=GREY)
    note = ImageFont.truetype(str(FONTS / "DejaVuSans.ttf"), 44)
    t2 = "New video every week"
    d.text(((W - note.getlength(t2)) / 2, y + size + 130), t2, font=note, fill=RED)
    im.save(out)


if __name__ == "__main__":
    banner(sys.argv[1], sys.argv[2], Path(sys.argv[3]))
