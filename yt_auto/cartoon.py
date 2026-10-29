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
    "wikipedia_titles": {"type": "array", "minItems": 2, "maxItems": 5, "items": {"type": "string"},
                         "description": "articles that directly state the facts of EVERY step, including the answer"},
}, "required": ["question", "title", "emotion", "answer", "steps", "wikipedia_titles"]}

SCRIPT_SCHEMA = {"type": "object", "properties": {
    "facts": {"type": "array", "minItems": 5, "maxItems": 12, "items": {"type": "object", "properties": {
        "id": {"type": "string", "description": "passage id, e.g. A2.14"},
        "fact": {"type": "string", "description": "the fact in plain words, exactly as much as the passage says"}},
        "required": ["id", "fact"]}, "description": "FIRST: the facts the story will use, each from one passage"},
    "scenes": {"type": "array", "minItems": 5, "maxItems": 7, "items": {"type": "object", "properties": {
        "role": {"type": "string", "enum": ["hook", "step", "answer", "end"]},
        "sentences": {"type": "array", "minItems": 1, "maxItems": 3, "items": {"type": "object", "properties": {
            "text": {"type": "string"},
            "kind": {"type": "string", "enum": ["fact", "framing"]},
            "sources": {"type": "array", "items": {"type": "string"}}},
            "required": ["text", "kind", "sources"]}}},
        "required": ["role", "sentences"]}}},
    "required": ["facts", "scenes"]}

SCENES_SCHEMA = {"type": "object", "properties": {
    "notes": {"type": "string", "description": "FIRST, one line per scene: what is DRAWN (the stickman's pose and "
                                               "feeling, the props, where they are) - pictures, not text"},
    "scenes_js": {"type": "string", "description": "the complete scenes.js file"}},
    "required": ["notes", "scenes_js"]}

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
- wikipedia_titles: 2 to 5 exact English Wikipedia article titles that directly state the facts of EVERY
  step. For "what happens to you / your body" stories, include the article about that effect itself (e.g.
  "Barotrauma", "Hypothermia", "Spaghettification"), not only the article about the place (first test, 29 Oct:
  only place articles were chosen, so the facts about what happens to a person were missing).
- Only plan steps that well-known Wikipedia articles can prove. No made-up timings ("for hours") or sensations.
{SAFETY}"""
    return llm(prompt, system=writer.RULES, schema=PLAN_SCHEMA, name="short_plan", temperature=0.8, models=QUALITY)


def write_short(topic: str, plan: dict, sources: dict, feedback: str = "") -> dict:
    prompt = f"""Topic: {topic}
Question: {plan['question']}
Feeling: {plan['emotion']}
Steps: {json.dumps(plan['steps'])}
Answer: {plan['answer']}

Write the narration of a 40-60 second YouTube Short: {WORDS[0]} to {WORDS[1]} words in total.
FACTS FIRST: list 5 to 12 facts from the passages below (with their passage ids). Then build the story ONLY from
those facts. Every detail of a "fact" sentence (numbers, times, causes, what happens to a body) must be in its
passages. If the passages don't say something, leave it out or ask it as a question. (First test, 29 Oct: 5 of 11
sentences were dropped by the fact-check for details like "sinking for hours" that no passage said.)
- Scene 1 (role "hook"): ONE sentence, the question put to the viewer ("Imagine you..." or "What if you..."),
  ending with a question mark. It is framing: no facts.
- Then 3 or 4 scenes (role "step"), 1 to 3 short sentences each: what the stickman goes through, step by step,
  one idea per scene, each sentence 6 to 16 words.
- One scene (role "answer") that clearly answers the question, with facts.
- Last scene (role "end"): ONE plain sentence that sums it up.
- Feelings belong in framing sentences that claim nothing ("Would you even notice?"). Speak to the viewer as
  "you". Short words, no lists, no dashes, no abbreviations. Never "in this video".
- Mark every sentence "fact" (with the passage ids backing EVERY detail) or "framing" (no checkable claim).
{SAFETY}
{feedback}
SOURCE PASSAGES:
{as_prompt_text(sources)}"""
    script = llm(prompt, system=writer.RULES, schema=SCRIPT_SCHEMA, name="short_script_retry" if feedback else "short_script",
                 temperature=0.6, models=QUALITY)
    script["title"] = plan["title"]
    writer.number_sentences(script)
    return script


def rewrite_feedback(report: dict, problems: list[str]) -> str:
    dropped = "\n".join(f"- \"{d['text']}\": {d['problem']}" for d in report.get("dropped", []))
    return f"""
YOUR FIRST VERSION FAILED THESE CHECKS: {'; '.join(problems)}
The fact-check dropped these sentences (the passages don't say it):
{dropped or '- (none)'}
Write a new version that uses only what the passages say, still {WORDS[0]}-{WORDS[1]} words, with a clear answer.
"""


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


def description(script: dict, sources: dict, scenes_js: str = "") -> str:
    used = {pid for sc in script["scenes"] for s in sc["sentences"] for pid in s.get("sources", [])}
    idx = passage_index(sources)
    arts = {}
    for pid in sorted(used):
        if pid in idx:
            a = next(x for x in sources["articles"] if x["title"] == idx[pid]["article"])
            arts[a["title"]] = f"https://en.wikipedia.org/w/index.php?title={a['title'].replace(' ', '_')}&oldid={a.get('revision_id')}"
    stop = {"what", "happens", "happen", "would", "could", "your", "into", "with", "from", "that", "this", "when",
            "where", "which", "does", "have", "fall", "falls", "they", "them", "there", "their", "about", "really"}
    tags = " ".join("#" + w for w in [w for w in re.findall(r"[a-z]{4,}", script["title"].lower()) if w not in stop][:3])
    return "\n".join([script["title"] + " The stickman finds out.", "", "Sources (facts checked):"]
                     + [f'Wikipedia, "{t}": {u}' for t, u in arts.items()]
                     + ["", "Voice: text-to-speech. Icons: Lucide (ISC licence)."
                        + (" Emoji: Twemoji by Twitter and contributors (CC BY 4.0)." if used_emoji(scenes_js) else ""),
                        "", f"#shorts #stickman {tags}".strip()]) + "\n"


def scene_texts(script: dict) -> dict[str, str]:
    return {sid: " ".join(s["text"] for s in sc["sentences"]) for sid, sc in zip(scene_ids(script), script["scenes"])}


def write_scenes(script: dict, md: str, feedback: str = "", previous: str = "") -> dict:
    api = ((CARTOON / "SCENE_API.md").read_text()
           + "\n\n## EMOJI NAMES (the only names emoji() accepts)\n\n" + (EMOJI_DIR / "NAMES.txt").read_text()
           + "\n\n## LIBRARY (the only names place() and art() accept)\n\n" + library_listing())
    example = (CARTOON / "example_scenes.js").read_text()
    ask = f"""Write scenes.js for this Short. Scene ids, in order: {', '.join(scene_ids(script))}.

RULES AND DRAWING FUNCTIONS:
{api}

STYLE EXAMPLE (another video, its narration is in the comment at the top; do NOT copy its pictures, make
pictures for THIS story). Times use spoken words of the same scene (at: 'feet', s.cue('stretched')) or seconds:
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


EMOJI_DIR = CARTOON / "emoji"   # Twemoji (CC BY 4.0), chosen by the owner 29 Oct: animals and objects we have not drawn
EMOJI_CALL = re.compile(r"\bemoji\(\s*s\s*,\s*['\"]([\w-]+)['\"]")


def emoji_names() -> set[str]:
    return set((EMOJI_DIR / "NAMES.txt").read_text().split())  # the list travels to Kaggle; the 945 files do not


def _js_keys(name: str) -> set[str]:
    """Keys of `export const NAME = { key: ... }` in character.js (the poses and faces hero() knows)."""
    js = (CARTOON / "character.js").read_text()
    body = js[js.index(f"export const {name} = {{"):]
    return set(re.findall(r"^  (\w+)\s*:", body[:body.index("\n};")], re.M))


def icon_names() -> set[str]:
    text = (CARTOON / "lucide_names.txt").read_text()
    return set(" ".join(l for l in text.splitlines() if not l.startswith("#")).split())


def used_emoji(js: str) -> list[str]:
    return sorted(set(EMOJI_CALL.findall(js)))


ART_DIR = CARTOON / "art"   # owner's ChatGPT places and objects (29 Oct), cards in art/library.json
PLACE_CALL = re.compile(r"\b(?:place|floorY)\(\s*s\s*,\s*['\"]([\w-]+)['\"]")
ART_CALL = re.compile(r"\bart\(\s*s\s*,\s*['\"]([\w-]+)['\"]")


def art_library() -> dict:
    return json.loads((ART_DIR / "library.json").read_text())


def library_listing() -> str:
    lib = art_library()
    places = [f"- {n}: {', '.join(c['tags'])} (ground: {c['ground']}, light: {c['light']}, open floor from y "
              f"{round(c['floor'] * 1920)})" for n, c in sorted(lib["places"].items())]
    things = [f"- {n}: {', '.join(c['tags'])} ({c['height_m']} m, stands on: {c['stand']})" for n, c in sorted(lib["things"].items())]
    return "Places:\n" + "\n".join(places) + "\n\nArt objects:\n" + "\n".join(things) + "\n"


def copy_art(js: str, project: Path) -> list[str]:
    """Copy the library pictures a scenes.js uses into the project's assets/art/ (explainroo loads only assets/)."""
    lib, used = art_library(), []
    for kind, names in (("places", PLACE_CALL.findall(js)), ("things", ART_CALL.findall(js))):
        for n in sorted(set(names)):
            card = lib[kind].get(n)
            if card and (ART_DIR / card["file"]).exists():
                dst = project / "assets" / "art" / card["file"]
                dst.parent.mkdir(parents=True, exist_ok=True)
                dst.write_bytes((ART_DIR / card["file"]).read_bytes())
                used.append(n)
    return used


def copy_emoji(js: str, project: Path) -> list[str]:
    """Copy the emoji a scenes.js uses into the project's assets/emoji/ (explainroo loads only assets/)."""
    names = [n for n in used_emoji(js) if (EMOJI_DIR / f"{n}.svg").exists()]
    if names:
        (project / "assets" / "emoji").mkdir(parents=True, exist_ok=True)
        for n in names:
            (project / "assets" / "emoji" / f"{n}.svg").write_bytes((EMOJI_DIR / f"{n}.svg").read_bytes())
    return names


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
        if "background(" not in body and "place(" not in body:
            problems.append(f"{sid}: no place(s, name) or background(s, kind) is called")
        spoken = " ".join(_norm(w) for w in texts[sid].split())
        for cue in re.findall(r"\b(?:at|out)\s*:\s*'([^'#][^']*)'", body):
            words = [_norm(w) for w in cue.split()]
            if " ".join(words) not in spoken:
                problems.append(f"{sid}: the cue '{cue}' is not spoken in this scene (spoken: \"{texts[sid]}\")")
        # Show, don't write (run 40843120092: stacks of small labels, 'LUNGS & EARS CRUSHED' where the
        # narration said 'injure'): one short label at most, made only of words the voice says.
        labels = re.findall(r"\blabel\(\s*s\s*,\s*(['\"`])(.*?)\1", body)
        if len(labels) > 1:
            problems.append(f"{sid}: {len(labels)} labels; use at most ONE short label per scene and draw the rest")
        for _, text in labels:
            extra = [w for w in text.split() if _norm(w) and _norm(w) not in spoken.split()]
            if extra or len(text.split()) > 4:
                problems.append(f"{sid}: label '{text}' must be at most 4 words, all spoken in this scene "
                                f"(not spoken: {', '.join(extra) or '-'})")
        for call in ("s.text(", "s.note(", "s.title(", "s.subtitle(", "s.list("):
            if call in body:
                problems.append(f"{sid}: {call} is not allowed (text on screen = one label() at most)")
        if "hero(" not in body:
            problems.append(f"{sid}: no stickman: every scene shows hero(...)")
        # own helper functions defined in the file (e.g. bubbles(s, ...)) that draw count too
        helpers = [h for h in re.findall(r"^function\s+(\w+)\s*\(s\b", js, re.M)]
        drawn = r"\b(thing|emoji|art|blackHole" + "".join(f"|{h}" for h in helpers) + r")\(|s\.(draw|icon|circle|path|line|arrow|number)\("
        if not re.search(drawn, body):
            problems.append(f"{sid}: nothing is drawn besides the stickman: draw what the narration talks about")
        sc = re.search(r"hero\(s,\s*\{[^}]*?scale:\s*([\d.]+)", body)
        if sc and float(sc.group(1)) < 0.8:
            problems.append(f"{sid}: the stickman is too small (scale {sc.group(1)}); use 0.9 to 1.8")
        # names that only fail at render time (Titanic run 40877631750: face 'worried', icon 'question')
        for kind, found, known in (("pose", re.findall(r"\bpose\s*:\s*'(\w+)'", body), _js_keys("POSES")),
                                   ("face", re.findall(r"\bface\s*:\s*'(\w+)'", body), _js_keys("FACES")),
                                   ("icon", re.findall(r"s\.icon\(\s*['\"]([\w-]+)['\"]", body), icon_names())):
            for n in sorted(set(found) - known):
                problems.append(f"{sid}: {kind} '{n}' does not exist (use one from the list in the rules)")
        lib = art_library()
        for kind, names in (("places", PLACE_CALL.findall(body)), ("things", ART_CALL.findall(body))):
            for n in sorted(set(names) - set(lib[kind])):
                problems.append(f"{sid}: {'place' if kind == 'places' else 'art'} '{n}' is not in the library "
                                f"(have: {', '.join(sorted(lib[kind]))})")
        for n in used_emoji(body):
            if n not in emoji_names():
                problems.append(f"{sid}: emoji '{n}' does not exist (use a name from the emoji list, or thing()/your own drawing)")
        for mark in re.findall(r"(?:at|out)\s*:\s*'#(\w+)'|s\.mark\('(\w+)'\)", body):
            problems.append(f"{sid}: uses a [#marker] ({''.join(mark)}); script.md has no markers, use spoken words")
    try:
        r = subprocess.run(["node", "--check", "--input-type=module"], input=js, capture_output=True, text=True, timeout=60)
    except FileNotFoundError:  # no Node.js here (e.g. a Kaggle test): explainroo's own check still runs at render
        return problems
    if r.returncode:
        problems.append("JavaScript syntax error: " + r.stderr.strip()[-600:])
    return problems


def write_project(out: Path, script: dict, sources: dict, scenes_js: str) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / "script.md").write_text(script_md(script, sources), encoding="utf-8")
    (out / "scenes.js").write_text(scenes_js, encoding="utf-8")
    copy_emoji(scenes_js, out)
    copy_art(scenes_js, out)
    (out / "video.json").write_text(json.dumps({
        "title": script["title"], "theme": "space-look.json", "size": "9:16", "voice": "af_heart",
        "music": True, "captions": False, "watermark": False}, indent=2) + "\n", encoding="utf-8")


SEEN = {"type": "object", "properties": {"images": {"type": "array", "items": {"type": "object", "properties": {
    "n": {"type": "integer"}, "seen": {"type": "string"}}, "required": ["n", "seen"]}}}, "required": ["images"]}
JUDGE = {"type": "object", "properties": {"scenes": {"type": "array", "items": {"type": "object", "properties": {
    "scene": {"type": "string"}, "ok": {"type": "boolean"},
    "problems": {"type": "array", "items": {"type": "string"}}}, "required": ["scene", "ok", "problems"]}}},
    "required": ["scenes"]}


def review_pictures(stills: Path, script: dict) -> dict:
    """Look at the last frame of every scene: blind description first (VISION), then a text judge (LIGHT)
    against the narration and the template's picture rules. Returns {scene: [problems]} (empty = fine)."""
    import io

    from PIL import Image

    from .llm import LIGHT, VISION

    texts = scene_texts(script)
    shots = [(sid, stills / f"{sid}@end.png") for sid in texts if (stills / f"{sid}@end.png").exists()]
    if not shots:
        return {"error": "no stills found"}
    images = []
    for i, (_, f) in enumerate(shots, 1):
        im = Image.open(f).convert("RGB")
        im.thumbnail((432, 768))
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=80)
        images.append((f"Image {i}:", buf.getvalue()))
    seen = llm(f"""Above are {len(shots)} frames of a vertical cartoon video, each after its label "Image n:". For EVERY
image, describe plainly what is drawn and where: the stick figure (pose, face), objects, every piece of text
(quote it), and whether any text or object covers the stick figure's head or body or is cut off at an edge.""",
               images=images, schema=SEEN, name="short_pictures_seen", temperature=0.1, models=VISION, last_resort=True)
    by_n = {x["n"]: x["seen"] for x in seen["images"]}
    listing = "\n".join(f"Scene {sid} (Image {i}): narration: \"{texts[sid]}\"\n  described as: {by_n.get(i, '(none)')}"
                        for i, (sid, _) in enumerate(shots, 1))
    res = llm(f"""Someone described the last frame of each scene of a cartoon Short WITHOUT knowing the story. Judge each
scene. A scene has a problem when: text covers the stick figure's head or body; something is cut off at the
edge; the picture does not show what the narration says (or shows something it doesn't say); an abbreviation
like "ATM", "km", "x10" is on screen; a number on screen is not in the narration; the picture looks the same as
the scene before; there is more than one short piece of text; a text says more or stronger than the narration
("crushed" when it says "injure"); the stick figure is small or hard to see; the drawing does not show the
thing the narration names. Be concrete: say what to change. If a scene is fine, ok = true and no problems.

{listing}""", schema=JUDGE, name="short_pictures_judge", temperature=0.1, models=LIGHT, last_resort=True)
    out = {sid: [] for sid, _ in shots}
    for r in res["scenes"]:
        if r["scene"] in out and not r["ok"]:
            out[r["scene"]] = r["problems"] or ["judged not ok"]
    return {"seen": {sid: by_n.get(i, "") for i, (sid, _) in enumerate(shots, 1)}, "problems": out}
