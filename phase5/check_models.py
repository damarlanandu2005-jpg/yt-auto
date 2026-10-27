"""Live check of the light AI models (Phase 5): does each answer in JSON, can it see pictures in the
right order, and what does the provider say about its limits? Uses about 2 requests per model.

    python phase5/check_models.py OUT
"""
from __future__ import annotations

import io
import json
import os
import sys
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
    # GitHub Models catalog: which models exist and their rate-limit tier
    catalog = []
    tok = os.environ.get("GITHUB_MODELS_TOKEN")
    if tok:
        try:
            req = urllib.request.Request("https://models.github.ai/catalog/models",
                                         headers={"Authorization": f"Bearer {tok}", "Accept": "application/vnd.github+json"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                catalog = [{"id": x.get("id"), "tier": x.get("rate_limit_tier"), "limits": x.get("limits")}
                           for x in json.loads(resp.read())]
        except Exception as e:  # noqa: BLE001
            catalog = [{"error": repr(e)[:200]}]
    errors = [{"model": e["model"], "status": e.get("status"), "error": e.get("error", "")[:600]}
              for e in llm.LOG if e.get("status") != 200]
    res = {"models": rows, "errors": errors, "github_catalog": catalog,
           "calls": [{k: e.get(k) for k in ("name", "model", "status", "seconds")} for e in llm.LOG]}
    (out / "models_check.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))
    for m, r in rows.items():
        print(f"{m}: json {r['json'][:80]} | vision {r['vision'][:80]}")
    print(f"GitHub catalog: {len(catalog)} models")


if __name__ == "__main__":
    main()
