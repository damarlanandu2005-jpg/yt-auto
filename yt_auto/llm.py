"""One `llm()` function for every text step, so the provider can be swapped later.

Today: Gemini API free tier over plain HTTPS (no SDK, no billing). The key comes
from the GEMINI_API_KEY environment variable (a GitHub repo secret) and is sent in
a header, never in a URL or log.

Every call is logged (prompt size, model, seconds, tokens) to LOG so a run can show
how much of the free daily quota it used.
"""
from __future__ import annotations

import base64
import json
import os
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

GEMINI = "https://generativelanguage.googleapis.com/v1beta"
# Free-tier text models, best first (Gemini pricing page, 26 Oct 2026; each tested by
# phase1/check_apis.py). When one is overloaded (503) or out of daily quota (429), the
# next one is tried. Override with LLM_MODELS="a,b,c".
MODELS = [m for m in os.environ.get(
    "LLM_MODELS", "gemini-3.8-flash,gemini-3.6-flash,gemini-3.5-flash,gemini-3.5-flash-lite").split(",") if m]
# For quick structured jobs (visual plan, photo pick/check). First test run, 26 Oct 2026: 3.8 Flash
# answered 503 "high demand" on 5 of 7 calls and took 219 s for the visual plan; 3.6 Flash took 6-70 s.
FAST = ["gemini-3.6-flash", "gemini-3.5-flash", "gemini-3.8-flash", "gemini-3.5-flash-lite"]
# For the script and the fact-check: never Flash-Lite (it copied source wording; run 40402246414).
QUALITY = ["gemini-3.8-flash", "gemini-3.6-flash", "gemini-3.5-flash"]
# Free tier is about 20 requests/day per model (429 quotaValue 20 for 3.8 Flash, 26 Oct 2026),
# and failed 503 attempts seem to count, so retries are few and spread out.
ROUNDS, ROUND_WAIT_S = 3, 60
_DOWN: set[str] = set()       # gave up with 503 in this run: tried last from then on
_EXHAUSTED: set[str] = set()  # daily quota used up: skipped for the rest of the run

LOG: list[dict] = []
LOG_DIR: Path | None = None  # set by the caller to keep each prompt and reply on disk


class LLMError(RuntimeError):
    pass


def llm(prompt: str, *, system: str = "", schema: dict | None = None, model: str | None = None,
        temperature: float = 0.7, name: str = "llm", images: list[bytes] | None = None,
        models: list[str] | None = None, max_tries: int = 2, timeout: int = 600):
    """Send one prompt, return the reply text (or parsed JSON when `schema` is given).

    `images`: optional JPEG bytes shown to the model before the prompt.
    """
    errors = []
    for rnd in range(1, ROUNDS + 1):
        order = [m for m in ([model] if model else (models or MODELS)) if m not in _EXHAUSTED]
        order = [m for m in order if m not in _DOWN] + [m for m in order if m in _DOWN]
        if not order:
            break
        for m in order:
            try:
                return _call(m, prompt, system, schema, temperature, name, images, max_tries, timeout)
            except _TryNextModel as e:
                print(f"[llm] {name}: {m} unavailable ({e}); trying next model", flush=True)
                errors.append(f"{m}: {e}")
                (_EXHAUSTED if "daily" in str(e) else _DOWN).add(m)
        if rnd < ROUNDS and any(m not in _EXHAUSTED for m in order):
            print(f"[llm] {name}: every model busy; waiting {ROUND_WAIT_S}s (round {rnd})", flush=True)
            time.sleep(ROUND_WAIT_S)
    raise LLMError(f"{name}: no model available: {errors}")


class _TryNextModel(Exception):
    pass


def _call(model, prompt, system, schema, temperature, name, images, max_tries, timeout):
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise LLMError("GEMINI_API_KEY is not set")
    parts = [{"inlineData": {"mimeType": "image/jpeg", "data": base64.b64encode(b).decode()}} for b in images or []]
    parts.append({"text": prompt})
    body: dict = {"contents": [{"role": "user", "parts": parts}],
                  "generationConfig": {"temperature": temperature}}
    if system:
        body["systemInstruction"] = {"parts": [{"text": system}]}
    if schema:
        body["generationConfig"]["responseMimeType"] = "application/json"
        body["generationConfig"]["responseJsonSchema"] = schema

    url = f"{GEMINI}/models/{model}:generateContent"
    data = json.dumps(body).encode()
    entry = {"name": name, "model": model, "prompt_chars": len(prompt) + len(system), "images": len(images or [])}
    t0 = time.perf_counter()
    for attempt in range(1, max_tries + 1):
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json",
                                                               "x-goog-api-key": key})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                reply = json.loads(r.read())
            break
        except urllib.error.HTTPError as e:
            err = e.read().decode(errors="replace")
            LOG.append({**entry, "status": e.code, "attempt": attempt, "error": err[:1500]})
            if e.code == 429 and ("PerDay" in err or "per day" in err):
                raise _TryNextModel("daily free quota used up") from None
            if e.code == 404:
                raise _TryNextModel("model not available to this key") from None
            # 429 = per-minute limit, 5xx = overloaded: wait and retry. Others are our bug.
            if e.code in (429, 500, 503, 504):
                if attempt < max_tries:
                    wait = min(_retry_delay(err) or 30, 60)
                    print(f"[llm] {name}: {model} HTTP {e.code}, retry {attempt} in {wait:.0f}s", flush=True)
                    time.sleep(wait)
                    continue
                raise _TryNextModel(f"HTTP {e.code} after {max_tries} tries") from None
            raise LLMError(f"{name}: HTTP {e.code}: {err[:600]}") from None
        except OSError as e:
            # Network trouble: URLError, timeouts, and ConnectionResetError raised while reading the
            # reply (not wrapped in URLError; crashed Phase 2 run 40464679016). HTTPError is handled above.
            LOG.append({**entry, "status": None, "attempt": attempt, "error": repr(e)[:300]})
            if attempt < max_tries:
                print(f"[llm] {name}: {model} network error {e!r}, retry {attempt} in {10 * attempt}s", flush=True)
                time.sleep(10 * attempt)
                continue
            raise _TryNextModel(repr(e)) from None

    cand = (reply.get("candidates") or [{}])[0]
    text = "".join(p.get("text", "") for p in (cand.get("content") or {}).get("parts", []) if not p.get("thought"))
    usage = reply.get("usageMetadata", {})
    entry.update(status=200, seconds=round(time.perf_counter() - t0, 1), attempts=attempt,
                 finish=cand.get("finishReason"), in_tokens=usage.get("promptTokenCount"),
                 out_tokens=usage.get("candidatesTokenCount"), thought_tokens=usage.get("thoughtsTokenCount"))
    LOG.append(entry)
    if LOG_DIR:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        n = sum(1 for e in LOG if e.get("status") == 200)
        (LOG_DIR / f"{n:02}_{name}.prompt.txt").write_text(f"[model] {model}\n[system]\n{system}\n\n[user]\n{prompt}",
                                                          encoding="utf-8")
        (LOG_DIR / f"{n:02}_{name}.reply.txt").write_text(text, encoding="utf-8")
    if cand.get("finishReason") not in (None, "STOP"):
        raise LLMError(f"{name}: stopped early ({cand.get('finishReason')}); reply starts {text[:200]!r}")
    if schema:
        try:
            return json.loads(text)
        except ValueError as e:
            raise LLMError(f"{name}: reply is not valid JSON: {e}; starts {text[:200]!r}") from None
    return text


def _retry_delay(err: str) -> float | None:
    """Gemini puts the suggested wait in RetryInfo, e.g. "retryDelay": "37s"."""
    m = re.search(r'"retryDelay":\s*"(\d+(?:\.\d+)?)s"', err)
    return float(m.group(1)) + 1 if m else None
