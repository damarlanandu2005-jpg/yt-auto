"""One `llm()` function for every text step, so the provider can be swapped.

Providers (all free, no billing):
  * Gemini API (key GEMINI_API_KEY): Gemini Flash models for the jobs where quality matters
    (script, fact-check, plan), and Gemma 4 / Flash-Lite for lighter jobs. Each model has its
    own published free daily limit.
  * GitHub Models (the workflow's GITHUB_TOKEN with `models: read`): retired by GitHub on
    30 Jul 2026; the "github:<publisher>/<model>" path stays but is in no list.
  * Cloudflare Workers AI (owner's CLOUDFLARE_API_TOKEN / CLOUDFLARE_ACCOUNT_ID, free 10,000
    neurons a day, reset 00:00 UTC): backup when every Gemini model is busy or out of free quota
    (owner, 29 Oct). Model ids are written "cf:@cf/<publisher>/<model>". This is another company's
    own free plan, not a second Gemini key.

Keys are sent in headers, never in URLs or logs. Every call is logged to LOG.
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
GITHUB_MODELS = "https://models.github.ai/inference/chat/completions"
CLOUDFLARE = "https://api.cloudflare.com/client/v4/accounts/{account}/ai/v1/chat/completions"  # OpenAI-style

# STRONG: the script, the fact-check and the plan. Never Flash-Lite or small models here: Flash-Lite
# copied source wording and wrote short scripts (run 40402246414).
# After them, Cloudflare's gpt-oss-120b (Apache-2.0 open model): Gemini ran out of free daily quota on
# all three models during the Short tests (run 40846680032), which stopped the whole video.
CF_STRONG = "cf:@cf/openai/gpt-oss-120b"
QUALITY = [m for m in os.environ.get(
    "LLM_QUALITY_MODELS", f"gemini-3.8-flash,gemini-3.6-flash,gemini-3.5-flash,{CF_STRONG}").split(",") if m]
# LIGHT: visual plan, photo pick/check, quality-gate review, topic scoring. Gemma 4 first (free, own
# daily limit), then Flash-Lite models, then GitHub Models, then the strong models as a last resort.
LIGHT = [m for m in os.environ.get(
    "LLM_LIGHT_MODELS",
    "gemma-4-31b-it,gemini-3.5-flash-lite,gemini-3.1-flash-lite,"
    f"{CF_STRONG},gemini-3.6-flash,gemini-3.8-flash").split(",") if m]
# PICTURES: the photo check (sends images). Not Gemma: it answered HTTP 500 to every request with
# pictures (6/6, models checks 40557681397 and 40559021860) while text-only JSON worked.
VISION = [m for m in os.environ.get(
    "LLM_VISION_MODELS",
    "gemini-3.5-flash-lite,gemini-3.1-flash-lite,"
    "gemini-3.6-flash,gemini-3.8-flash").split(",") if m]
FAST = LIGHT                      # older name, kept for callers
MODELS = QUALITY                  # default when a caller names no list
LITE = "gemini-3.5-flash-lite"
GITHUB_MAX_PROMPT_CHARS = 24_000  # GitHub Models' free tier caps request size (about 8k tokens)

# Each failed attempt counts against the free daily limit (pilot video 1 used up all three Flash
# models mostly on 503 "busy" replies), so a busy model is skipped at once, not retried.
ROUNDS, ROUND_WAIT_S = 3, 120
_DOWN: set[str] = set()       # busy in this run: tried last from then on
_EXHAUSTED: set[str] = set()  # daily quota used up (or not available): skipped for the rest of the run

LOG: list[dict] = []
LOG_DIR: Path | None = None  # set by the caller to keep each prompt and reply on disk


class LLMError(RuntimeError):
    pass


class _TryNextModel(Exception):
    pass


def llm(prompt: str, *, system: str = "", schema: dict | None = None, model: str | None = None,
        temperature: float = 0.7, name: str = "llm", images: list | None = None,
        models: list[str] | None = None, max_tries: int = 1, timeout: int = 600, last_resort: bool = False):
    """Send one prompt, return the reply text (or parsed JSON when `schema` is given).

    `images`: JPEG bytes (or (label, bytes) pairs) shown to the model before the prompt.
    `last_resort`: after every round failed, try Flash-Lite once.
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
                if "too long" not in str(e):  # a smaller request may still fit this model later
                    (_EXHAUSTED if any(w in str(e) for w in ("daily", "not available")) else _DOWN).add(m)
        if rnd < ROUNDS and any(m not in _EXHAUSTED for m in order):
            print(f"[llm] {name}: every model busy; waiting {ROUND_WAIT_S}s (round {rnd})", flush=True)
            time.sleep(ROUND_WAIT_S)
    if last_resort and LITE not in _EXHAUSTED:
        try:
            return _call(LITE, prompt, system, schema, temperature, name, images, max_tries, timeout)
        except _TryNextModel as e:
            errors.append(f"{LITE}: {e}")
    raise LLMError(f"{name}: no model available: {errors}")


def _call(model, prompt, system, schema, temperature, name, images, max_tries, timeout):
    if model.startswith("github:"):
        return _call_github(model, prompt, system, schema, temperature, name, images, max_tries, timeout)
    if model.startswith("cf:"):
        return _call_cloudflare(model, prompt, system, schema, temperature, name, images, max_tries, timeout)
    return _call_gemini(model, prompt, system, schema, temperature, name, images, max_tries, timeout)


def _schema_note(schema: dict) -> str:
    return ("\n\nAnswer with ONE JSON object only (no other text, no code fences), matching this JSON schema:\n"
            + json.dumps(schema))


def _json_from_text(text: str):
    """Models without a JSON mode may wrap JSON in fences or add words around it."""
    t = text.strip()
    m = re.search(r"```(?:json)?\s*(.*?)```", t, re.S)
    if m:
        t = m.group(1).strip()
    try:
        return json.loads(t)
    except ValueError:
        start, end = t.find("{"), t.rfind("}")
        if start >= 0 and end > start:
            return json.loads(t[start:end + 1])
        raise


def _post(url: str, body: dict, headers: dict, entry: dict, model: str, name: str, max_tries: int, timeout: int):
    data = json.dumps(body).encode()
    for attempt in range(1, max_tries + 1):
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json", **headers})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                raw, status, ctype = r.read(), r.status, r.headers.get("Content-Type", "")
            try:
                return json.loads(raw), attempt
            except ValueError:  # e.g. an empty or HTML reply: log it and move on (crashed models check 40557681397)
                LOG.append({**entry, "status": status, "attempt": attempt,
                            "error": f"not JSON ({ctype}, {len(raw)} bytes): {raw[:500].decode(errors='replace')}"})
                raise _TryNextModel(f"reply was not JSON (HTTP {status})") from None
        except urllib.error.HTTPError as e:
            err = e.read().decode(errors="replace")
            LOG.append({**entry, "status": e.code, "attempt": attempt, "error": err[:1500]})
            if e.code == 429 and ("PerDay" in err or "per day" in err.lower() or "UserByModelByDay" in err
                                  or "neurons" in err.lower() or "daily" in err.lower()):
                raise _TryNextModel("daily free quota used up") from None
            if e.code in (401, 403, 404):
                raise _TryNextModel(f"not available (HTTP {e.code})") from None
            if e.code == 413 or "tokens_limit_reached" in err or "too large" in err.lower():
                raise _TryNextModel("prompt too long for this model") from None
            if e.code in (429, 500, 502, 503, 504):
                if attempt < max_tries:
                    wait = min(_retry_delay(err) or 30, 60)
                    print(f"[llm] {name}: {model} HTTP {e.code}, retry {attempt} in {wait:.0f}s", flush=True)
                    time.sleep(wait)
                    continue
                raise _TryNextModel(f"HTTP {e.code} (busy)") from None
            if e.code == 400 and model.startswith(("gemma", "github:", "cf:")):
                raise _TryNextModel(f"rejected the request: {err[:200]}") from None
            raise LLMError(f"{name}: HTTP {e.code}: {err[:600]}") from None
        except OSError as e:
            # URLError, timeouts, and ConnectionResetError while reading the reply (not wrapped in URLError;
            # crashed Phase 2 run 40464679016). HTTPError is handled above.
            LOG.append({**entry, "status": None, "attempt": attempt, "error": repr(e)[:300]})
            if attempt < max_tries:
                time.sleep(10 * attempt)
                continue
            raise _TryNextModel(repr(e)) from None
    raise _TryNextModel("no reply")


def _finish(entry, t0, attempt, name, model, system, prompt, text, schema, finish_ok: bool, finish: str, usage: dict):
    entry.update(status=200, seconds=round(time.perf_counter() - t0, 1), attempts=attempt, finish=finish, **usage)
    LOG.append(entry)
    if LOG_DIR:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        n = sum(1 for e in LOG if e.get("status") == 200)
        (LOG_DIR / f"{n:02}_{name}.prompt.txt").write_text(f"[model] {model}\n[system]\n{system}\n\n[user]\n{prompt}",
                                                          encoding="utf-8")
        (LOG_DIR / f"{n:02}_{name}.reply.txt").write_text(text, encoding="utf-8")
    if not finish_ok:
        raise LLMError(f"{name}: stopped early ({finish}); reply starts {text[:200]!r}")
    if schema:
        try:
            return _json_from_text(text)
        except ValueError as e:
            if model.startswith(("gemma", "github:", "cf:")):  # no strict JSON mode: let the next model try
                raise _TryNextModel(f"reply was not valid JSON ({e})") from None
            raise LLMError(f"{name}: reply is not valid JSON: {e}; starts {text[:200]!r}") from None
    return text


def _call_gemini(model, prompt, system, schema, temperature, name, images, max_tries, timeout):
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise LLMError("GEMINI_API_KEY is not set")
    gemma = model.startswith("gemma")
    parts = []
    for img in images or []:
        # (label, bytes): the label goes right before its picture. With 54 unlabelled pictures the
        # model's numbering drifted by one (run 40467512243), so the photo check judged the wrong ones.
        label, data = img if isinstance(img, tuple) else (None, img)
        if label:
            parts.append({"text": label})
        parts.append({"inlineData": {"mimeType": "image/jpeg", "data": base64.b64encode(data).decode()}})
    # Gemma on the Gemini API takes no system instruction and no JSON schema: put both in the prompt.
    text_in = (f"{system}\n\n{prompt}" if gemma and system else prompt) + (_schema_note(schema) if gemma and schema else "")
    parts.append({"text": text_in})
    body: dict = {"contents": [{"role": "user", "parts": parts}], "generationConfig": {"temperature": temperature}}
    if system and not gemma:
        body["systemInstruction"] = {"parts": [{"text": system}]}
    if schema and not gemma:
        body["generationConfig"]["responseMimeType"] = "application/json"
        body["generationConfig"]["responseJsonSchema"] = schema
    entry = {"name": name, "model": model, "prompt_chars": len(prompt) + len(system), "images": len(images or [])}
    t0 = time.perf_counter()
    reply, attempt = _post(f"{GEMINI}/models/{model}:generateContent", body, {"x-goog-api-key": key}, entry, model,
                           name, max_tries, timeout)
    cand = (reply.get("candidates") or [{}])[0]
    text = "".join(p.get("text", "") for p in (cand.get("content") or {}).get("parts", []) if not p.get("thought"))
    u = reply.get("usageMetadata", {})
    usage = {"in_tokens": u.get("promptTokenCount"), "out_tokens": u.get("candidatesTokenCount"),
             "thought_tokens": u.get("thoughtsTokenCount")}
    return _finish(entry, t0, attempt, name, model, system, prompt, text, schema,
                   cand.get("finishReason") in (None, "STOP"), cand.get("finishReason"), usage)


def _call_github(model, prompt, system, schema, temperature, name, images, max_tries, timeout):
    token = os.environ.get("GITHUB_MODELS_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        raise _TryNextModel("not available (no GitHub token)")
    if len(prompt) + len(system) > GITHUB_MAX_PROMPT_CHARS or len(images or []) > 8:
        raise _TryNextModel("prompt too long for this model")
    content: list = []
    for img in images or []:
        label, data = img if isinstance(img, tuple) else (None, img)
        if label:
            content.append({"type": "text", "text": label})
        content.append({"type": "image_url",
                        "image_url": {"url": "data:image/jpeg;base64," + base64.b64encode(data).decode()}})
    content.append({"type": "text", "text": prompt + (_schema_note(schema) if schema else "")})
    messages = ([{"role": "system", "content": system}] if system else []) + [{"role": "user", "content": content}]
    body = {"model": model.split(":", 1)[1], "messages": messages, "temperature": temperature}
    if schema:
        body["response_format"] = {"type": "json_object"}
    entry = {"name": name, "model": model, "prompt_chars": len(prompt) + len(system), "images": len(images or [])}
    t0 = time.perf_counter()
    reply, attempt = _post(GITHUB_MODELS, body, {"Authorization": f"Bearer {token}",
                                                  "Accept": "application/vnd.github+json",
                                                  "X-GitHub-Api-Version": "2022-11-28"},
                           entry, model, name, max_tries, timeout)
    choice = (reply.get("choices") or [{}])[0]
    text = (choice.get("message") or {}).get("content") or ""
    u = reply.get("usage", {})
    usage = {"in_tokens": u.get("prompt_tokens"), "out_tokens": u.get("completion_tokens")}
    return _finish(entry, t0, attempt, name, model, system, prompt, text, schema,
                   choice.get("finish_reason") in (None, "stop"), choice.get("finish_reason"), usage)


def _call_cloudflare(model, prompt, system, schema, temperature, name, images, max_tries, timeout):
    token, account = os.environ.get("CLOUDFLARE_API_TOKEN"), os.environ.get("CLOUDFLARE_ACCOUNT_ID")
    if not token or not account:
        raise _TryNextModel("not available (no Cloudflare secrets)")
    if images:
        raise _TryNextModel("not available (pictures are not sent to Cloudflare text models)")
    messages = ([{"role": "system", "content": system}] if system else []) + \
        [{"role": "user", "content": prompt + (_schema_note(schema) if schema else "")}]
    # Workers AI's default answer length is short: a whole scenes.js file needs several thousand tokens.
    body = {"model": model.split(":", 1)[1], "messages": messages, "temperature": temperature, "max_tokens": 16000}
    if schema:
        body["response_format"] = {"type": "json_object"}
    entry = {"name": name, "model": model, "prompt_chars": len(prompt) + len(system), "images": 0}
    t0 = time.perf_counter()
    reply, attempt = _post(CLOUDFLARE.format(account=account), body, {"Authorization": f"Bearer {token}"},
                           entry, model, name, max_tries, timeout)
    choice = (reply.get("choices") or [{}])[0]
    text = (choice.get("message") or {}).get("content") or ""
    u = reply.get("usage", {})
    usage = {"in_tokens": u.get("prompt_tokens"), "out_tokens": u.get("completion_tokens")}
    return _finish(entry, t0, attempt, name, model, system, prompt, text, schema,
                   choice.get("finish_reason") in (None, "stop"), choice.get("finish_reason"), usage)


def _retry_delay(err: str) -> float | None:
    """Gemini puts the suggested wait in RetryInfo, e.g. "retryDelay": "37s"."""
    m = re.search(r'"retryDelay":\s*"(\d+(?:\.\d+)?)s"', err)
    return float(m.group(1)) + 1 if m else None
