"""Render keyframe images (charts, diagrams, cards) with matplotlib.

Every keyframe is a still image. Motion comes later from FFmpeg (slow zoom
and fades), which keeps CPU use low compared with frame-by-frame animation.
"""
from __future__ import annotations

import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch  # noqa: E402

# Rendered slightly larger than 1080p so the slow zoom stays sharp.
W_IN, H_IN, DPI = 23.04, 12.96, 100

THEME = {
    "bg": "#0f1720",
    "panel": "#17222e",
    "ink": "#eef2f6",
    "muted": "#8fa1b3",
    "accent": "#4cc9f0",
    "accent2": "#f7b32b",
    "grid": "#263544",
}


def _canvas():
    fig = plt.figure(figsize=(W_IN, H_IN), dpi=DPI, facecolor=THEME["bg"])
    return fig


def _title(fig, text, y=0.9, size=46):
    fig.text(0.06, y, text, color=THEME["ink"], fontsize=size, fontweight="bold", ha="left", va="center")


def _save(fig, path: Path):
    fig.savefig(path, facecolor=THEME["bg"], dpi=DPI)
    plt.close(fig)


def _wrap(text: str, width: int) -> str:
    words, lines, cur = text.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > width and cur:
            lines.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    if cur:
        lines.append(cur)
    return "\n".join(lines)


def render_title(spec, path):
    fig = _canvas()
    fig.text(0.5, 0.56, _wrap(spec["title"], 22), color=THEME["ink"], fontsize=84, fontweight="bold",
             ha="center", va="center", linespacing=1.15)
    if spec.get("subtitle"):
        fig.text(0.5, 0.3, spec["subtitle"], color=THEME["accent"], fontsize=38, ha="center", va="center")
    _save(fig, path)


def render_stat(spec, path):
    fig = _canvas()
    fig.text(0.5, 0.58, spec["value"], color=THEME["accent"], fontsize=150, fontweight="bold",
             ha="center", va="center")
    fig.text(0.5, 0.36, _wrap(spec["label"], 48), color=THEME["ink"], fontsize=44, ha="center", va="center")
    if spec.get("note"):
        fig.text(0.5, 0.25, spec["note"], color=THEME["muted"], fontsize=32, ha="center", va="center")
    _save(fig, path)


def render_bullets(spec, path):
    fig = _canvas()
    _title(fig, spec["title"])
    items = spec["items"]
    top, step = 0.7, min(0.17, 0.55 / max(len(items), 1))
    for i, item in enumerate(items):
        y = top - i * step
        fig.add_artist(FancyBboxPatch((0.07, y - 0.012), 0.022, 0.024, boxstyle="round,pad=0.002",
                                          transform=fig.transFigure, color=THEME["accent"]))
        fig.text(0.115, y, _wrap(item, 55), color=THEME["ink"], fontsize=44, ha="left", va="center")
    _save(fig, path)


def render_flow(spec, path):
    fig = _canvas()
    _title(fig, spec["title"])
    steps = spec["steps"]
    n = len(steps)
    margin, gap = 0.06, 0.035
    box_w = (1 - 2 * margin - gap * (n - 1)) / n
    y, h = 0.42, 0.22
    for i, step in enumerate(steps):
        x = margin + i * (box_w + gap)
        color = THEME["accent"] if i == n - 1 else THEME["muted"]
        fig.add_artist(FancyBboxPatch((x, y), box_w, h, boxstyle="round,pad=0.008,rounding_size=0.02",
                                          transform=fig.transFigure, facecolor=THEME["panel"],
                                          edgecolor=color, linewidth=3))
        fig.text(x + box_w / 2, y + h / 2, _wrap(step, max(10, int(box_w * 70))), color=THEME["ink"],
                 fontsize=34 if n <= 4 else 28, ha="center", va="center", linespacing=1.2)
        if i < n - 1:
            fig.add_artist(FancyArrowPatch((x + box_w + 0.004, y + h / 2), (x + box_w + gap - 0.004, y + h / 2),
                                               transform=fig.transFigure, arrowstyle="-|>", mutation_scale=34,
                                               color=THEME["accent2"], linewidth=3))
    _save(fig, path)


def _axes(fig, rect=(0.1, 0.16, 0.82, 0.62)):
    ax = fig.add_axes(rect, facecolor=THEME["bg"])
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(THEME["muted"])
    ax.tick_params(colors=THEME["ink"], labelsize=28)
    ax.grid(axis="y", color=THEME["grid"], linewidth=1)
    ax.set_axisbelow(True)
    return ax


def render_bars(spec, path):
    fig = _canvas()
    _title(fig, spec["title"])
    ax = _axes(fig)
    labels, values = spec["labels"], spec["values"]
    hi = spec.get("highlight")
    colors = [THEME["accent"] if i == hi else THEME["muted"] for i in range(len(values))]
    bars = ax.bar(labels, values, color=colors, width=0.55)
    if spec.get("log"):
        from matplotlib.ticker import FuncFormatter

        ax.set_yscale("log")
        ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,g}"))
    if min(values) < 0:
        lo, hi_v = min(values), max(values)
        ax.set_ylim(lo - 0.25 * (hi_v - lo), hi_v * 1.15)
    ax.axhline(0, color=THEME["muted"], linewidth=1.5)
    for b, v in zip(bars, values):
        va = "bottom" if v >= 0 else "top"
        ax.annotate(f"{v:,g}", (b.get_x() + b.get_width() / 2, v), ha="center", va=va,
                    color=THEME["ink"], fontsize=32, fontweight="bold",
                    xytext=(0, 8 if v >= 0 else -8), textcoords="offset points")
    ax.set_ylabel(spec.get("unit", ""), color=THEME["muted"], fontsize=28)
    _save(fig, path)


def render_line(spec, path):
    fig = _canvas()
    _title(fig, spec["title"])
    ax = _axes(fig)
    ax.plot(spec["x"], spec["y"], color=THEME["accent"], linewidth=5)
    ax.set_xlabel(spec.get("xlabel", ""), color=THEME["muted"], fontsize=28)
    ax.set_ylabel(spec.get("ylabel", ""), color=THEME["muted"], fontsize=28)
    if "mark_x" in spec:
        mx = spec["mark_x"]
        # interpolate y on the line
        xs, ys = spec["x"], spec["y"]
        my = next(ys[i] + (ys[i + 1] - ys[i]) * (mx - xs[i]) / (xs[i + 1] - xs[i])
                  for i in range(len(xs) - 1) if xs[i] <= mx <= xs[i + 1])
        ax.scatter([mx], [my], s=400, color=THEME["accent2"], zorder=5)
        ax.annotate(spec.get("mark_label", ""), (mx, my), xytext=(-30, 40), textcoords="offset points",
                    ha="right", color=THEME["accent2"], fontsize=32, fontweight="bold")
    _save(fig, path)


def render_circles(spec, path):
    """Trilateration sketch: circles around satellites crossing at one point."""
    fig = _canvas()
    _title(fig, spec["title"])
    ax = fig.add_axes((0.2, 0.03, 0.6, 0.78), facecolor=THEME["bg"])
    ax.set_xlim(-13, 13)
    ax.set_ylim(-12, 10)
    ax.set_aspect("equal")
    ax.axis("off")
    target = (0.0, 0.0)
    sats = [(-4.5, 3.5), (5.0, 3.0), (0.5, -5.5)][: spec["count"]]
    colors = [THEME["accent"], THEME["accent2"], "#b388eb"]
    for (sx, sy), c in zip(sats, colors):
        r = math.dist((sx, sy), target)
        ax.add_patch(Circle((sx, sy), r, fill=False, edgecolor=c, linewidth=4))
        ax.scatter([sx], [sy], s=500, marker="s", color=c, zorder=4)
    if spec.get("show_point"):
        ax.scatter([target[0]], [target[1]], s=900, color=THEME["ink"], zorder=6)
        ax.annotate("You", target, xytext=(18, 18), textcoords="offset points",
                    color=THEME["ink"], fontsize=38, fontweight="bold")
    _save(fig, path)


def render_timeline(spec, path):
    fig = _canvas()
    _title(fig, spec["title"])
    events = spec["events"][:5]
    n = len(events)
    y = 0.47
    fig.add_artist(FancyArrowPatch((0.06, y), (0.95, y), transform=fig.transFigure, arrowstyle="-|>",
                                   mutation_scale=40, color=THEME["muted"], linewidth=4))
    for i, ev in enumerate(events):
        x = 0.12 + i * (0.76 / max(n - 1, 1)) if n > 1 else 0.5
        fig.add_artist(Circle((x, y), 0.012, transform=fig.transFigure, color=THEME["accent2"], zorder=5))
        fig.text(x, y + 0.08, ev["when"], color=THEME["accent"], fontsize=40, fontweight="bold", ha="center", va="bottom")
        fig.text(x, y - 0.06, _wrap(ev["label"], 16), color=THEME["ink"], fontsize=30, ha="center", va="top",
                 linespacing=1.2)
    _save(fig, path)


def render_compare(spec, path):
    fig = _canvas()
    _title(fig, spec["title"])
    for k, (x, color) in enumerate(((0.06, THEME["accent"]), (0.52, THEME["accent2"]))):
        side = "left" if k == 0 else "right"
        fig.add_artist(FancyBboxPatch((x, 0.1), 0.42, 0.66, boxstyle="round,pad=0.008,rounding_size=0.02",
                                      transform=fig.transFigure, facecolor=THEME["panel"], edgecolor=color,
                                      linewidth=3))
        fig.text(x + 0.21, 0.69, _wrap(spec.get(f"{side}_title", ""), 22), color=color, fontsize=46,
                 fontweight="bold", ha="center", va="center")
        for j, pt in enumerate(spec.get(f"{side}_points", [])[:3]):
            fig.text(x + 0.03, 0.54 - j * 0.15, _wrap(pt, 26), color=THEME["ink"], fontsize=34, ha="left",
                     va="center", linespacing=1.15)
    _save(fig, path)


def render_photo(spec, path):
    """A real photo filling a 16:9 frame (slightly larger than 1080p for the slow zoom).

    Close to 16:9: crop to fill. Otherwise: whole photo over a blurred, darkened copy.
    A small credit line goes bottom-left (needed for CC BY / BY-SA, polite for NASA).
    """
    from PIL import Image, ImageDraw, ImageFilter, ImageFont

    W, H = int(W_IN * DPI), int(H_IN * DPI)
    im = Image.open(spec["path"]).convert("RGB")
    zoom = float(spec.get("zoom") or 1.0)
    if zoom > 1.0:  # step-by-step: a closer look at one part of the same picture
        cw, ch = im.width / zoom, im.height / zoom
        fx, fy = {"left": (0.3, 0.5), "right": (0.7, 0.5), "top": (0.5, 0.3), "bottom": (0.5, 0.7)}.get(
            spec.get("focus") or "center", (0.5, 0.5))
        x0 = min(max(fx * im.width - cw / 2, 0), im.width - cw)
        y0 = min(max(fy * im.height - ch / 2, 0), im.height - ch)
        im = im.crop((round(x0), round(y0), round(x0 + cw), round(y0 + ch)))
    ratio = im.width / im.height
    if 1.45 <= ratio <= 2.0:
        scale = max(W / im.width, H / im.height)
        im2 = im.resize((round(im.width * scale), round(im.height * scale)), Image.LANCZOS)
        left, top = (im2.width - W) // 2, (im2.height - H) // 2
        canvas = im2.crop((left, top, left + W, top + H))
    else:
        scale = max(W / im.width, H / im.height)
        bg = im.resize((round(im.width * scale), round(im.height * scale)), Image.LANCZOS)
        bg = bg.crop(((bg.width - W) // 2, (bg.height - H) // 2, (bg.width - W) // 2 + W, (bg.height - H) // 2 + H))
        bg = bg.filter(ImageFilter.GaussianBlur(40)).point(lambda v: int(v * 0.45))
        fit = min(W * 0.92 / im.width, H * 0.92 / im.height)
        fg = im.resize((round(im.width * fit), round(im.height * fit)), Image.LANCZOS)
        bg.paste(fg, ((W - fg.width) // 2, (H - fg.height) // 2))
        canvas = bg
    credit = spec.get("credit")
    if credit:
        font_path = Path(matplotlib.get_data_path()) / "fonts" / "ttf" / "DejaVuSans.ttf"
        font = ImageFont.truetype(str(font_path), 26)
        d = ImageDraw.Draw(canvas, "RGBA")
        tw = d.textlength(credit, font=font)
        x0 = (W - tw) / 2  # centred and well inside the edges, so zoom/pan never cuts it off
        d.rectangle((x0 - 12, H - 130, x0 + tw + 12, H - 90), fill=(0, 0, 0, 150))
        d.text((x0, H - 126), credit, font=font, fill=(235, 235, 235, 255))
    canvas.save(path)


RENDERERS = {
    "title": render_title,
    "stat": render_stat,
    "bullets": render_bullets,
    "flow": render_flow,
    "bars": render_bars,
    "line": render_line,
    "circles": render_circles,
    "timeline": render_timeline,
    "compare": render_compare,
    "photo": render_photo,
}


def render_keyframe(spec: dict, path: Path) -> Path:
    kind = spec["type"]
    if kind not in RENDERERS:
        raise ValueError(f"Unknown keyframe type: {kind}")
    RENDERERS[kind](spec, path)
    return path
