"""Number and unit guard: a plain-code check that runs beside the AI fact-check.

Every number written in digits in a fact sentence must appear in one of its cited
passages, with a unit of the same size (nanoseconds vs microseconds, metres vs
kilometres, kilograms vs pounds). Catches wrong figures and wrong units without
spending API quota. It cannot judge meaning, so it only adds flags.
"""
from __future__ import annotations

import re

# unit word -> (dimension, scale)
UNITS = {}
for words, dim, scale in [
    ("ns nanosecond nanoseconds", "time", 1e-9), ("μs µs microsecond microseconds", "time", 1e-6),
    ("ms millisecond milliseconds", "time", 1e-3), ("s sec second seconds", "time", 1.0),
    ("minute minutes min", "time", 60.0), ("hour hours h", "time", 3600.0),
    ("mm millimetre millimetres millimeter millimeters", "length", 1e-3),
    ("cm centimetre centimetres centimeter centimeters", "length", 1e-2),
    ("m metre metres meter meters", "length", 1.0), ("km kilometre kilometres kilometer kilometers", "length", 1e3),
    ("ft foot feet", "length", 0.3048), ("mi mile miles", "length", 1609.344),
    ("g gram grams", "mass", 1e-3), ("kg kilogram kilograms", "mass", 1.0), ("lb lbs pound pounds", "mass", 0.4536),
    ("hz hertz", "freq", 1.0), ("khz kilohertz", "freq", 1e3), ("mhz megahertz", "freq", 1e6),
    ("ghz gigahertz", "freq", 1e9), ("thz terahertz", "freq", 1e12),
]:
    for w in words.split():
        UNITS[w] = (dim, scale)

_NUM = re.compile(r"(?<![\w.])(\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?)(?:\s*(?:-|\s)?\s*([A-Za-zμµ]+))?")


def _pairs(text: str) -> list[tuple[float, tuple[str, float] | None, str]]:
    """(value, unit or None, raw) for every number written in digits."""
    out = []
    for m in _NUM.finditer(text):
        raw, word = m.group(1), (m.group(2) or "").lower()
        try:
            value = float(raw.replace(",", ""))
        except ValueError:
            continue
        unit = UNITS.get(word)
        if unit is None and word.endswith("s") and word[:-1] in UNITS:
            unit = UNITS[word[:-1]]
        # "per second" after a length: treat "kilometres per second" as its own unit family
        if unit and re.match(r"\s*(per|/)\s*(second|s)\b", text[m.end():]):
            unit = (unit[0] + "/s", unit[1])
        out.append((value, unit, raw))
    return out


def _speed_units(text: str) -> list[tuple[float, tuple[str, float]]]:
    """'3874 m/s' style speeds in source passages."""
    out = []
    for m in re.finditer(r"(\d[\d,]*(?:\.\d+)?)\s*(km|m)/s\b", text):
        out.append((float(m.group(1).replace(",", "")), ("length/s", 1e3 if m.group(2) == "km" else 1.0)))
    return out


def check(sentence: str, passages: list[str]) -> list[str]:
    """Return problems found (empty list = nothing suspicious)."""
    src_pairs = [p for t in passages for p in _pairs(t)] + [(v, u, "") for t in passages for v, u in _speed_units(t)]
    problems = []
    for value, unit, raw in _pairs(sentence):
        same = [u for v, u, _ in src_pairs if abs(v - value) <= 1e-9 * max(1.0, abs(value))]
        if not same:
            problems.append(f"number {raw} is not in the cited sources")
            continue
        if unit is None:
            continue
        src_units = [u for u in same if u is not None]
        if src_units and not any(u[0] == unit[0] and abs(u[1] - unit[1]) <= 1e-12 * max(u[1], 1) for u in src_units):
            problems.append(f"{raw} has a different unit in the sources")
    return problems
