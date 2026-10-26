"""Topic -> plan -> sourced script -> fact-check -> fixed script.

Ground rules built in:
  * Every factual sentence cites passage ids from sources.json. No source, no claim.
  * A second, separate model call checks each factual sentence against the exact
    text it cites. Sentences that fail are rewritten from the sources once, checked
    again, and dropped if they still fail. Everything is logged for the reviewer.
  * Wording must be our own (8-word overlap check against the sources).
  * No persona, no advice, no accusations against named companies or people.
"""
from __future__ import annotations

import json
import re

from .llm import QUALITY, llm
from .research import as_prompt_text, passage_index

AUDIENCE = ("a curious worldwide English-speaking audience (many are non-native speakers, "
            "many in India); smart but not specialists")

RULES = f"""You write narration for an original, fact-checked YouTube explainer video.
Audience: {AUDIENCE}.
Hard rules:
- Use ONLY facts found in the numbered source passages given to you. Never add facts from memory.
- Write in your own words. Never copy a phrase of 8 or more words from a source.
- Plain spoken English: short sentences (mostly 8-18 words, never more than 24), common words,
  explain any technical term the first time it appears.
- Write numbers as digits and units in full words ("20,200 kilometres", "per cent"); no abbreviations
  like km, mph, e.g., etc., no symbols like % or ~, no brackets, no lists. US/UK spelling is fine but be consistent (UK).
- No "I", no expert persona, no "as a scientist". Speak to the viewer as "you".
- No financial, legal, medical or health advice. No accusations against named companies or people.
- Do not write "according to NASA" or attribute statements to NASA or any organisation unless the passage
  quotes them directly.
- No clickbait, no false suspense, no "smash that like button". One short honest call to think at the end is fine.
"""

PLAN_SCHEMA = {
    "type": "object",
    "properties": {
        "question": {"type": "string", "description": "the single clear question this video answers"},
        "angle": {"type": "string", "description": "what makes this video's take original and interesting"},
        "structure": {"type": "string", "description": "the storytelling structure chosen for THIS topic and why"},
        "outline": {"type": "array", "items": {"type": "string"}, "minItems": 5, "maxItems": 8},
        "wikipedia_titles": {"type": "array", "items": {"type": "string"}, "minItems": 3, "maxItems": 7},
    },
    "required": ["question", "angle", "structure", "outline", "wikipedia_titles"],
}

SCRIPT_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string", "description": "honest YouTube title, at most 70 characters"},
        "scenes": {"type": "array", "minItems": 5, "maxItems": 9, "items": {
            "type": "object",
            "properties": {
                "heading": {"type": "string"},
                "sentences": {"type": "array", "minItems": 3, "items": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string"},
                        "kind": {"type": "string", "enum": ["fact", "framing"],
                                 "description": "fact = states anything checkable; framing = a question, transition or "
                                                "invitation with no factual content"},
                        "sources": {"type": "array", "items": {"type": "string"},
                                    "description": "passage ids, e.g. A2.14; required for every fact"},
                    },
                    "required": ["text", "kind", "sources"],
                }},
            },
            "required": ["heading", "sentences"],
        }},
    },
    "required": ["title", "scenes"],
}

CHECK_SCHEMA = {
    "type": "object",
    "properties": {"results": {"type": "array", "items": {
        "type": "object",
        "properties": {
            "id": {"type": "string"},
            "verdict": {"type": "string", "enum": ["supported", "partly", "unsupported"]},
            "problem": {"type": "string", "description": "what is wrong or missing; empty if supported"},
            "fixed_text": {"type": "string", "description": "a corrected sentence fully supported by the cited "
                                                            "passages, in the same style; empty if supported or unfixable"},
        },
        "required": ["id", "verdict", "problem", "fixed_text"],
    }}},
    "required": ["results"],
}


def plan(topic: str) -> dict:
    prompt = f"""Topic: {topic}

Plan one 6-minute explainer video about this topic.
- Pick ONE clear question the video answers, and an angle that makes it worth watching.
- Choose a structure that suits THIS topic (for example: mystery then reveal, myth vs fact, step by step,
  history timeline, comparison, "what would happen if"). Do not default to a generic list.
- Outline 5 to 8 parts.
- List 3 to 7 English Wikipedia article titles (exact titles) that together contain the facts needed."""
    return llm(prompt, system=RULES, schema=PLAN_SCHEMA, name="plan", temperature=0.9)


def write_script(topic: str, the_plan: dict, sources: dict, words: tuple[int, int] = (1000, 1100)) -> dict:
    # Asks a little above the 900-1,000 target: the fact-check usually removes a few sentences.
    prompt = f"""Topic: {topic}
Question: {the_plan['question']}
Angle: {the_plan['angle']}
Structure: {the_plan['structure']}
Outline: {json.dumps(the_plan['outline'])}

Write the full narration: {words[0]} to {words[1]} words in total, in 5 to 8 scenes that follow the outline.
- Scene 1 opens with a hook in the first 2 sentences that sets up the question. The last scene answers it clearly
  and recaps in one or two sentences.
- Split the narration into single sentences. Mark each as "fact" (with the passage ids that support EVERY detail
  in it) or "framing" (no checkable content at all). When in doubt, it is a fact and needs sources.
- Prefer concrete numbers, comparisons and everyday examples that are in the sources.

SOURCE PASSAGES:
{as_prompt_text(sources)}"""
    return llm(prompt, system=RULES, schema=SCRIPT_SCHEMA, name="script", temperature=0.8, models=QUALITY)


def number_sentences(script: dict) -> None:
    for si, sc in enumerate(script["scenes"], 1):
        sc["id"] = f"s{si:02}"
        for ti, s in enumerate(sc["sentences"], 1):
            s["id"] = f"s{si:02}.{ti:02}"


def _shingles(text: str, n: int = 8) -> set[str]:
    w = re.findall(r"[a-z0-9]+", text.lower())
    return {" ".join(w[i:i + n]) for i in range(len(w) - n + 1)}


def copied_phrases(text: str, idx: dict) -> list[str]:
    src = set()
    for p in idx.values():
        src |= _shingles(p["text"])
    return sorted(_shingles(text) & src)


def check(sentences: list[dict], idx: dict, name: str) -> dict[str, dict]:
    """Ask a separate model call whether each factual sentence is backed by its cited passages."""
    items = []
    for s in sentences:
        cited = [f"{pid}: {idx[pid]['text']}" for pid in s["sources"] if pid in idx]
        if s["kind"] == "framing":
            items.append(f"[{s['id']}] FRAMING SENTENCE: {s['text']}")
        else:
            items.append(f"[{s['id']}] SENTENCE: {s['text']}\nCITED PASSAGES:\n" + ("\n".join(cited) or "(none)"))
    prompt = """You are a strict fact-checker. For each sentence below, decide using ONLY its cited passages
(not your own knowledge):
- supported: every detail (numbers, names, dates, causes, comparisons) is stated in or directly follows from them.
- partly: the main point is backed but some detail is not, or it overstates / oversimplifies into something false.
- unsupported: the cited passages do not back it, or there are none.
For partly/unsupported, give fixed_text: a corrected sentence in the same plain spoken style that the cited
passages fully support (keep digits and full unit words; no copying 8+ words). Leave fixed_text empty if impossible.
A FRAMING SENTENCE has no passages: it is "supported" only if it makes no checkable claim at all (a question,
transition or invitation). If it states any fact, mark it "unsupported" with an empty fixed_text.

""" + "\n\n".join(items)
    res = llm(prompt, schema=CHECK_SCHEMA, name=name, temperature=0.1, models=QUALITY)
    return {r["id"]: r for r in res["results"]}


def fact_check(script: dict, sources: dict) -> dict:
    """Check every factual sentence; fix or drop the ones that fail. Returns a report."""
    idx = passage_index(sources)
    facts = [s for sc in script["scenes"] for s in sc["sentences"]]  # framing too: it must hold no claims
    report = {"checked": len(facts), "supported_first_pass": 0, "fixed": [], "dropped": [], "bad_ids": [],
              "copied": []}
    for s in facts:
        bad = [p for p in s["sources"] if p not in idx]
        if bad:
            report["bad_ids"].append({"id": s["id"], "ids": bad})
            s["sources"] = [p for p in s["sources"] if p in idx]
    first = check(facts, idx, "factcheck")

    to_fix, to_reword = [], []
    for s in facts:
        r = first.get(s["id"]) or {"verdict": "unsupported", "problem": "not returned by checker", "fixed_text": ""}
        s["check"] = r["verdict"]
        copied = copied_phrases(s["text"], idx)
        if copied:
            report["copied"].append({"id": s["id"], "phrases": copied})
        if r["verdict"] == "supported" and not copied:
            report["supported_first_pass"] += 1
        elif r["verdict"] == "supported":
            to_reword.append((s, copied))
        elif r.get("fixed_text"):
            to_fix.append((s, s["text"], r))
            s["text"] = r["fixed_text"]
        else:
            to_fix.append((s, s["text"], r))
            s["drop"] = True

    # True but too close to the source wording: say it in our own words (then it is re-checked below).
    if to_reword:
        new_text = reword(to_reword)
        for s, _ in to_reword:
            old = s["text"]
            if new_text.get(s["id"]):
                s["text"] = new_text[s["id"]]
                to_fix.append((s, old, {"problem": "reworded: too close to source wording"}))
            else:
                s["drop"] = True
                to_fix.append((s, old, {"problem": "copied source wording; reword failed"}))

    # Second pass: re-check every rewritten sentence; anything still failing is dropped.
    rewritten = [s for s, _, _ in to_fix if not s.get("drop")]
    second = check(rewritten, idx, "factcheck2") if rewritten else {}
    for s, old, r in to_fix:
        r2 = second.get(s["id"])
        if s.get("drop") or not r2 or r2["verdict"] != "supported" or copied_phrases(s["text"], idx):
            s["drop"] = True
            report["dropped"].append({"id": s["id"], "text": old, "problem": r["problem"]})
        else:
            s["check"] = "supported (after fix)"
            report["fixed"].append({"id": s["id"], "old": old, "new": s["text"], "problem": r["problem"]})
    for sc in script["scenes"]:
        sc["sentences"] = [s for s in sc["sentences"] if not s.get("drop")]
    script["scenes"] = [sc for sc in script["scenes"] if sc["sentences"]]
    report["words_after"] = word_count(script)
    return report


REWORD_SCHEMA = {"type": "object", "properties": {"sentences": {"type": "array", "items": {
    "type": "object", "properties": {"id": {"type": "string"}, "text": {"type": "string"}},
    "required": ["id", "text"]}}}, "required": ["sentences"]}


def reword(items: list[tuple[dict, list[str]]]) -> dict[str, str]:
    """Rewrite sentences that copy source phrases, keeping exactly the same facts."""
    lines = [f"[{s['id']}] {s['text']}\n  copied phrases to avoid: {'; '.join(c[:3])}" for s, c in items]
    prompt = """Each sentence below is correct but copies wording from its source. Rewrite each one in your own
plain spoken words: exactly the same facts and numbers, nothing added or removed, and no run of 8 words
that matches the copied phrases. Names (like "United States Space Force") may stay.

""" + "\n".join(lines)
    res = llm(prompt, system=RULES, schema=REWORD_SCHEMA, name="reword", temperature=0.6, models=QUALITY)
    return {x["id"]: x["text"] for x in res["sentences"]}


def word_count(script: dict) -> int:
    return sum(len(s["text"].split()) for sc in script["scenes"] for s in sc["sentences"])
