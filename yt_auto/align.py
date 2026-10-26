"""Subtitles from OUR script text, timed to the narration (forced alignment).

Whisper mishears words ("too" for "to"), so its words are never shown. We use:
  1. Exact sentence start/end times (narration is made one sentence at a time).
  2. Inside each sentence, whisper's word times where its word matches ours
     (difflib); unmatched words are spread by character length between matches.
If whisper word times are missing, step 2 falls back to character length alone.
"""
from __future__ import annotations

import difflib
import re
from pathlib import Path

MAX_CHARS = 84          # two lines of ~42 characters
MAX_CUE_S = 5.5
LINE_CHARS = 42


def _norm(w: str) -> str:
    return re.sub(r"[^a-z0-9]", "", w.lower())


def _ts(seconds: float) -> str:
    ms = int(round(max(0.0, seconds) * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def time_words(sentence: str, start: float, end: float, heard: list[dict]) -> list[tuple[str, float, float]]:
    """Give each word of `sentence` a (start, end) inside [start, end]."""
    words = sentence.split()
    times: list[list[float] | None] = [None] * len(words)
    near = [h for h in heard if start - 0.3 <= (h["start"] + h["end"]) / 2 <= end + 0.3]
    if near:
        sm = difflib.SequenceMatcher(a=[_norm(w) for w in words], b=[_norm(h["word"]) for h in near], autojunk=False)
        for blk in sm.get_matching_blocks():
            for k in range(blk.size):
                h = near[blk.b + k]
                a_, b_ = max(start, h["start"]), min(end, h["end"])
                times[blk.a + k] = [min(a_, b_), max(a_, b_)]
    # Fill gaps between known anchors in proportion to word length.
    anchors = [(-1, start)] + [(i, t[0]) for i, t in enumerate(times) if t] + [(len(words), end)]
    out_t = [t[:] if t else None for t in times]
    for (i0, t0), (i1, t1) in zip(anchors, anchors[1:]):
        if i0 >= 0 and out_t[i0]:
            t0 = out_t[i0][1]
        gap = list(range(i0 + 1, i1))
        if not gap:
            continue
        weights = [len(words[g]) + 1 for g in gap]
        span = max(0.0, t1 - t0)
        acc = t0
        for g, wgt in zip(gap, weights):
            d = span * wgt / sum(weights)
            out_t[g] = [acc, acc + d]
            acc += d
    return [(w, t[0], t[1]) for w, t in zip(words, out_t)]


def _two_lines(text: str) -> str:
    if len(text) <= LINE_CHARS:
        return text
    mid = len(text) // 2
    spaces = [m.start() for m in re.finditer(" ", text)]
    cut = min(spaces, key=lambda i: abs(i - mid))
    return text[:cut] + "\n" + text[cut + 1:]


def cues(timed: list[tuple[str, float, float]]) -> list[tuple[float, float, str]]:
    """Group timed words into readable cues; prefer to break after punctuation."""
    out, cur = [], []
    for i, (w, a, b) in enumerate(timed):
        text = " ".join(x[0] for x in cur + [(w, a, b)])
        if cur and (len(text) > MAX_CHARS or b - cur[0][1] > MAX_CUE_S):
            out.append(cur)
            cur = []
        cur.append((w, a, b))
        ends_clause = re.search(r"[,;:.!?]$", w) is not None
        if ends_clause and len(" ".join(x[0] for x in cur)) >= 30:
            out.append(cur)
            cur = []
    if cur:
        out.append(cur)
    return [(c[0][1], c[-1][2], _two_lines(" ".join(x[0] for x in c))) for c in out]


def write_srt(sentences: list[dict], heard: list[dict], out: Path) -> int:
    """sentences: [{"text", "start", "end"}] with times in the final video."""
    all_cues = []
    for s in sentences:
        all_cues += cues(time_words(s["text"], s["start"], s["end"], heard))
    lines = []
    for n, (a, b, text) in enumerate(all_cues, 1):
        nxt = all_cues[n][0] if n < len(all_cues) else b + 1
        b = min(max(b, a + 0.8), nxt - 0.02, b + 0.6) if nxt > b else b  # linger a little, never overlap
        lines.append(f"{n}\n{_ts(a)} --> {_ts(b)}\n{text}\n")
    out.write_text("\n".join(lines), encoding="utf-8")
    return len(all_cues)
