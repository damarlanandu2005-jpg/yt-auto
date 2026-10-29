"""Stickman Thoughts Shorts: topic -> plan -> sources -> short script -> fact-check -> explainroo project.

The template is cartoon/TEMPLATE.md (owner approved 29 Oct). What this module adds to the tested parts:
  * plan_short / write_short: a 110-140 word story (hook question, 4-5 steps, the answer, one closing line)
    in which every factual sentence cites Wikipedia passages, then the SAME fact-check as the long videos
    (writer.fact_check: 30/30 planted errors caught in Phase 2).
  * project files: script.md (with a source note under every scene), video.json, and scenes.js written by
    the AI from cartoon/SCENE_API.md, with the hand-made black-hole Short as the style example.
  * validate_scenes: plain-code checks before any render (forbidden code, missing scenes, word cues that are
    not spoken in their scene, missing captions); explainroo's own layout check runs at render time.
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

from . import writer
from .llm import QUALITY, llm
from .research import as_prompt_text, passage_index

ROOT = Path(__file__).resolve().parents[1]
CARTOON = ROOT / "cartoon"
WORDS = (110, 140)

PLAN_SCHEMA = {"type": "object", "properties": {
    "question": {"type": "string", "description": "the 'what if / why' question, as the viewer would ask it"},
    "title": {"type": "string", "description": "YouTube title, at most 60 characters, usually the question"},
    "emotion": {"type": "string", "description": "the true feeling the story gives: fear, shock, wonder, sadness..."},
    "answer": {"type": "string", "description": "the honest answer in one or two plain sentences"},
    "steps": {"type": "array", "minItems": 4, "maxItems": 5, "items": {"type": "string"},
              "description": "what the stickman lives through, step by step, ending with the answer"},
    "wikipedia_titles": {"type": "array", "minItems": 2, "maxItems": 5, "items": {"type": "string"}},
}, "required": ["question", "title", "emotion", "answer", "steps", "wikipedia_titles"]}

SCRIPT_SCHEMA = {"type": "object", "properties": {
    "scenes": {"type": "array", "minItems": 5, "maxItems": 7, "items": {"type": "object", "properties": {
        "role": {"type": "string", "enum": ["hook", "step", "answer", "end"]},
        "sentences": {"type": "array", "minItems": 1, "maxItems": 3, "items": {"type": "object", "properties": {
            "text": {"type": "string"},
            "kind": {"type": "string", "enum": ["fact", "framing"]},
            "sources": {"type": "array", "items": {"type": "string"}}},
            "required": ["text", "kind", "sources"]}}},
        "required": ["role", "sentences"]}}},
    "required": ["scenes"]}

SCENES_SCHEMA = {"type": "object", "properties": {
    "scenes_js": {"type": "string", "description": "the complete scenes.js file"},
    "notes": {"type": "string", "description": "one line per scene: what the picture shows"}},
    "required": ["scenes_js", "notes"]}

SAFETY = """- Allowed: any subject with a strong, TRUE feeling (space, history, the human body, animals, nature,
  disasters, inventions, everyday mysteries). Not allowed: health, money or legal advice ("you should..."),
  accusations against named companies or living people, tragedies from the last 12 months, gore."""


def plan_short(topic: str) -> dict:
    prompt = f"""Topic idea: {topic}

Plan one YouTube Short (40-60 seconds) for the channel "Stickman Thoughts": a simple stickman lives through a
"what if...?" or "why...?" story and finds out the true answer.
- question: the one big question, the way a curious viewer would ask it.
- emotion: the true feeling of the story (no fake urgency).
- steps: 4 or 5 things the stickman lives through, in order; the last one is the answer.
- answer: the honest answer. The Short must answer its own question (never "watch part 2").
- wikipedia_titles: 2 to 5 exact English Wikipedia article titles that hold every fact needed.
{SAFETY}"""
    return llm(prompt, system=writer.RULES, schema=PLAN_SCHEMA, name="short_plan", temperature=0.8, models=QUALITY)


def write_short(topic: str, plan: dict, sources: dict) -> dict:
    prompt = f"""Topic: {topic}
Question: {plan['question']}
Feeling: {plan['emotion']}
Steps: {json.dumps(plan['steps'])}
Answer: {plan['answer']}

Write the narration of a 40-60 second YouTube Short: {WORDS[0]} to {WORDS[1]} words in total.
- Scene 1 (role "hook"): ONE sentence, the question put to the viewer ("Imagine you..." or "What if you..."),
  ending with a question mark. It is framing: no facts.
- Then 3 or 4 scenes (role "step"), 1 to 3 short sentences each: what the stickman goes through, step by step,
  one idea per scene, each sentence 6 to 16 words.
- One scene (role "answer") that clearly answers the question.
- Last scene (role "end"): ONE plain sentence that sums it up.
- Speak to the viewer as "you". Short words, no lists, no dashes. Never "in this video".
- Mark every sentence "fact" (with the passage ids backing EVERY detail) or "framing" (no checkable claim).
{SAFETY}

SOURCE PASSAGES:
{as_prompt_text(sources)}"""
    script = llm(prompt, system=writer.RULES, schema=SCRIPT_SCHEMA, name="short_script", temperature=0.7, models=QUALITY)
    script["title"] = plan["title"]
    writer.number_sentences(script)
    return script


def check_story(script: dict) -> list[str]:
    """Template rules that are plain to check after the fact-check (R2: the hook is answered)."""
    problems = []
    roles = [sc.get("role") for sc in script["scenes"]]
    if not roles or roles[0] != "hook" or not script["scenes"][0]["sentences"][0]["text"].rstrip().endswith("?"):
        problems.append("the first scene is not a hook question")
    if "answer" not in roles:
        problems.append("the answer scene was dropped by the fact-check (rule R2: the hook must be answered)")
    n = writer.word_count(script)
    if not 80 <= n <= 170:
        problems.append(f"{n} words after the fact-check (want about {WORDS[0]}-{WORDS[1]})")
    return problems


def scene_ids(script: dict) -> list[str]:
    ids, steps = [], 0
    for sc in script["scenes"]:
        role = sc.get("role", "step")
        if role == "step":
            steps += 1
            ids.append(f"step{steps}")
        else:
            ids.append(role if role not in ids else f"{role}{len(ids)}")
    return ids


def script_md(script: dict, sources: dict) -> str:
    """explainroo script.md: one '## id' per scene, the narration, and a source note under each scene."""
    idx = passage_index(sources)
    rev = {a["title"]: a.get("revision_id") for a in sources["articles"]}
    lines = [f"# {script['title']}", "",
             "> Stickman Thoughts Short (cartoon/TEMPLATE.md). Every fact sentence was checked against the passages",
             "> noted under its scene (writer.fact_check); framing sentences make no claims.", ""]
    for sid, sc in zip(scene_ids(script), script["scenes"]):
        hold = " {hold=1.5}" if sc.get("role") == "end" else ""
        lines.append(f"## {sid}{hold}")
        lines.append(" ".join(s["text"] for s in sc["sentences"]))
        for s in sc["sentences"]:
            for pid in s.get("sources", []):
                if pid in idx:
                    p = idx[pid]
                    lines.append(f"> {s['id']} <- {p['article']} (rev {rev.get(p['article'])}), {pid}: "
                                 f"\"{p['text'][:220]}{'...' if len(p['text']) > 220 else ''}\"")
        lines.append("")
    return "\n".join(lines)


def description(script: dict, sources: dict) -> str:
    used = {pid for sc in script["scenes"] for s in sc["sentences"] for pid in s.get("sources", [])}
    idx = passage_index(sources)
    arts = {}
    for pid in sorted(used):
        if pid in idx:
            a = next(x for x in sources["articles"] if x["title"] == idx[pid]["article"])
            arts[a["title"]] = f"https://en.wikipedia.org/w/index.php?title={a['title'].replace(' ', '_')}&oldid={a.get('revision_id')}"
    tags = " ".join("#" + w for w in re.findall(r"[A-Za-z]{4,}", script["title"].lower())[:3])
    return "\n".join([script["title"] + " The stickman finds out.", "", "Sources (facts checked):"]
                     + [f'Wikipedia, "{t}": {u}' for t, u in arts.items()]
                     + ["", "Voice: text-to-speech. Icons: Lucide (ISC licence).", "", f"#shorts #stickman {tags}".strip()]) + "\n"


def scene_texts(script: dict) -> dict[str, str]:
    return {sid: " ".join(s["text"] for s in sc["sentences"]) for sid, sc in zip(scene_ids(script), script["scenes"])}


def write_scenes(script: dict, md: str, feedback: str = "", previous: str = "") -> dict:
    api = (CARTOON / "SCENE_API.md").read_text()
    example = (CARTOON / "videos" / "black-hole-fall" / "scenes.js").read_text()
    ask = f"""Write scenes.js for this Short. Scene ids, in order: {', '.join(scene_ids(script))}.

RULES AND DRAWING FUNCTIONS:
{api}

STYLE EXAMPLE (another video; do NOT copy its pictures, make pictures for THIS story). It times things with
[#markers] like at: '#feet' and s.mark('long'): THIS video's script.md has NO markers, so use spoken words of the
same scene (at: 'ocean') or seconds (at: 1.5) instead:
```js
{example}
```

THIS VIDEO'S script.md (narration per scene; lines starting with > are source notes, not spoken):
{md}
"""
    if feedback:
        ask += f"""
Your previous scenes.js had these problems. Fix ALL of them and return the whole corrected file:
{feedback}

PREVIOUS scenes.js:
```js
{previous}
```"""
    return llm(ask, schema=SCENES_SCHEMA, name="short_scenes_fix" if feedback else "short_scenes", temperature=0.6,
               models=QUALITY, timeout=900)


FORBIDDEN = [r"\bfetch\s*\(", r"\beval\s*\(", r"\bFunction\s*\(", r"\bdocument\b", r"\bwindow\b", r"\bglobalThis\b",
             r"\bsetTimeout\b", r"\bsetInterval\b", r"\brequire\s*\(", r"Math\.random", r"\.filter\s*=", r"\bimport\s*\(",
             r"\bXMLHttpRequest\b", r"\bWebSocket\b", r"\blocalStorage\b"]


def _norm(w: str) -> str:
    return re.sub(r"[^a-z0-9']", "", w.lower())


def validate_scenes(js: str, script: dict) -> list[str]:
    """Plain-code checks before rendering. Returns problems (empty = fine)."""
    problems = []
    for pat in FORBIDDEN:
        if re.search(pat, js):
            problems.append(f"forbidden code: {pat}")
    for m in re.finditer(r"^\s*import\s.*?from\s+['\"]([^'\"]+)['\"]", js, re.M):
        if m.group(1) not in ("./character.js", "./props.js"):
            problems.append(f"imports {m.group(1)}: only ./character.js and ./props.js are allowed")
    if "export default" not in js:
        problems.append("no 'export default { ... }'")
    texts = scene_texts(script)
    starts = []
    for sid in texts:
        m = re.search(rf"^\s*{re.escape(sid)}\s*\(\s*s\s*\)\s*\{{", js, re.M)
        if not m:
            problems.append(f"scene function {sid}(s) is missing")
        else:
            starts.append((m.start(), sid))
    starts.sort()
    for i, (a, sid) in enumerate(starts):
        body = js[a:starts[i + 1][0] if i + 1 < len(starts) else len(js)]
        if "words(s)" not in body:
            problems.append(f"{sid}: words(s) (the captions) is not called")
        if "background(" not in body:
            problems.append(f"{sid}: background(s, kind) is not called")
        spoken = " ".join(_norm(w) for w in texts[sid].split())
        for cue in re.findall(r"\b(?:at|out)\s*:\s*'([^'#][^']*)'", body):
            words = [_norm(w) for w in cue.split()]
            if " ".join(words) not in spoken:
                problems.append(f"{sid}: the cue '{cue}' is not spoken in this scene (spoken: \"{texts[sid]}\")")
        for mark in re.findall(r"(?:at|out)\s*:\s*'#(\w+)'|s\.mark\('(\w+)'\)", body):
            problems.append(f"{sid}: uses a [#marker] ({''.join(mark)}); script.md has no markers, use spoken words")
    r = subprocess.run(["node", "--check", "--input-type=module"], input=js, capture_output=True, text=True, timeout=60)
    if r.returncode:
        problems.append("JavaScript syntax error: " + r.stderr.strip()[-600:])
    return problems


def write_project(out: Path, script: dict, sources: dict, scenes_js: str) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / "script.md").write_text(script_md(script, sources), encoding="utf-8")
    (out / "scenes.js").write_text(scenes_js, encoding="utf-8")
    (out / "video.json").write_text(json.dumps({
        "title": script["title"], "theme": "space-look.json", "size": "9:16", "voice": "af_heart",
        "music": True, "captions": False, "watermark": False}, indent=2) + "\n", encoding="utf-8")
