"""Live check of the light AI models (Phase 5): does each answer in JSON, can it see pictures in the
right order, and what does the provider say about its limits? Uses about 2 requests per model.

    python phase5/check_models.py OUT
"""
from __future__ import annotations

import io
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from yt_auto import llm  # noqa: E402

SCHEMA = {"type": "object", "properties": {"capital": {"type": "string"}, "n": {"type": "integer"}},
          "required": ["capital", "n"]}
VISION = {"type": "object", "properties": {"images": {"type": "array", "items": {"type": "object", "properties": {
    "n": {"type": "integer"}, "colour": {"type": "string"}, "shape": {"type": "string"}},
    "required": ["n", "colour", "shape"]}}}, "required": ["images"]}


def picture(colour: str, shape: str) -> bytes:
    from PIL import Image, ImageDraw

    im = Image.new("RGB", (256, 256), "white")
    d = ImageDraw.Draw(im)
    (d.ellipse if shape == "circle" else d.rectangle)((48, 48, 208, 208), fill=colour)
    buf = io.BytesIO()
    im.save(buf, "JPEG")
    return buf.getvalue()


def main() -> None:
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    rows = {}
    pics = [("Image 1:", picture("red", "square")), ("Image 2:", picture("blue", "circle")),
            ("Image 3:", picture("green", "square"))]
    for m in llm.LIGHT:
        if m in llm.QUALITY:
            continue  # strong models are checked by the real runs
        r = {}
        try:
            a = llm.llm("What is the capital of France, and what is 17 + 25?", schema=SCHEMA, model=m, name=f"json_{m}")
            r["json"] = "ok" if a.get("capital", "").lower() == "paris" and a.get("n") == 42 else f"wrong: {a}"
        except Exception as e:  # noqa: BLE001
            r["json"] = f"failed: {e}"[:300]
        try:
            a = llm.llm("For each image, give its number, colour and shape.", schema=VISION, model=m, images=pics,
                        name=f"vision_{m}")
            got = [(x["n"], x["colour"].lower(), x["shape"].lower()) for x in a["images"]]
            want = [(1, "red", "square"), (2, "blue", "circle"), (3, "green", "square")]
            r["vision"] = "ok" if all(any(w[1] in g[1] and w[2] in g[2] and w[0] == g[0] for g in got) for w in want) \
                else f"wrong: {got}"
        except Exception as e:  # noqa: BLE001
            r["vision"] = f"failed: {e}"[:300]
        rows[m] = r
    # Gemma with one picture (three pictures gave HTTP 500 in run 40557681397)
    try:
        a = llm.llm("Give the colour and shape of the image.", model="gemma-4-31b-it", images=[pics[1]],
                    schema={"type": "object", "properties": {"colour": {"type": "string"}, "shape": {"type": "string"}},
                            "required": ["colour", "shape"]}, name="vision1_gemma")
        rows["gemma-4-31b-it"]["vision_one_image"] = "ok" if "blue" in a["colour"].lower() else f"wrong: {a}"
    except Exception as e:  # noqa: BLE001
        rows["gemma-4-31b-it"]["vision_one_image"] = f"failed: {e}"[:300]
    # GitHub Models: raw replies (both gave non-JSON in run 40557681397)
    raw = {}
    tok = os.environ.get("GITHUB_MODELS_TOKEN")
    if tok:
        h = {"Authorization": f"Bearer {tok}", "Accept": "application/vnd.github+json",
             "X-GitHub-Api-Version": "2022-11-28"}
        tiny = json.dumps({"model": "openai/gpt-4.1-mini", "messages": [{"role": "user", "content": "Say OK."}]}).encode()
        for label, url, data in (("catalog", "https://models.github.ai/catalog/models", None),
                                 ("chat", llm.GITHUB_MODELS, tiny)):
            req = urllib.request.Request(url, data=data, headers={**h, **({"Content-Type": "application/json"} if data else {})})
            try:
                with urllib.request.urlopen(req, timeout=60) as resp:
                    body = resp.read()
                    raw[label] = {"status": resp.status, "url": resp.geturl(), "headers": dict(resp.headers),
                                  "bytes": len(body), "body": body[:1500].decode(errors="replace")}
            except urllib.error.HTTPError as e:
                raw[label] = {"status": e.code, "headers": dict(e.headers), "body": e.read()[:1500].decode(errors="replace")}
            except Exception as e:  # noqa: BLE001
                raw[label] = {"error": repr(e)[:300]}
    catalog = raw
    errors = [{"model": e["model"], "status": e.get("status"), "error": e.get("error", "")[:600]}
              for e in llm.LOG if e.get("status") != 200]
    res = {"models": rows, "errors": errors, "github_catalog": catalog,
           "calls": [{k: e.get(k) for k in ("name", "model", "status", "seconds")} for e in llm.LOG]}
    (out / "models_check.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))
    for m, r in rows.items():
        print(m, {k: v[:120] for k, v in r.items()})
    for k, v in catalog.items():
        print(f"GitHub {k}: status {v.get('status')} bytes {v.get('bytes')} {v.get('body', v.get('error', ''))[:200]!r}")


if __name__ == "__main__":
    main()
