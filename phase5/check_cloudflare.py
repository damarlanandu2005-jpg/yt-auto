"""Why did Cloudflare say 'daily free allocation of 10,000 neurons used up' (models check 40851161489)
when the owner's dashboard shows nothing used today? Tiny requests, exact replies saved.

    python phase5/check_cloudflare.py out/dir      (needs CLOUDFLARE_API_TOKEN and CLOUDFLARE_ACCOUNT_ID)

Each probe costs only a few neurons. Keys go in headers and are never printed.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

BASE = "https://api.cloudflare.com/client/v4/accounts/{a}/ai"


def call(url: str, body: dict | None, token: str) -> dict:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers={"Authorization": f"Bearer {token}",
                                                          **({"Content-Type": "application/json"} if data else {})})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return {"status": r.status, "body": r.read()[:3000].decode(errors="replace")}
    except urllib.error.HTTPError as e:
        return {"status": e.code, "body": e.read()[:3000].decode(errors="replace")}
    except OSError as e:
        return {"status": None, "body": repr(e)[:300]}


def main() -> None:
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    token, account = os.environ["CLOUDFLARE_API_TOKEN"], os.environ["CLOUDFLARE_ACCOUNT_ID"]
    base = BASE.format(a=account)
    hi = [{"role": "user", "content": "Say OK."}]
    probes = {
        # 1. a small, cheap model on the native endpoint
        "llama8b_native_small": (f"{base}/run/@cf/meta/llama-3.1-8b-instruct", {"messages": hi, "max_tokens": 10}),
        # 2. the same big model as the check, native endpoint, tiny answer
        "gptoss_native_small": (f"{base}/run/@cf/openai/gpt-oss-120b", {"input": "Say OK.", "max_tokens": 50}),
        # 3. the big model on the OpenAI-style endpoint we use, tiny answer
        "gptoss_openai_small": (f"{base}/v1/chat/completions",
                                {"model": "@cf/openai/gpt-oss-120b", "messages": hi, "max_tokens": 50}),
        # 4. exactly like the check: OpenAI-style endpoint, max_tokens 16000
        "gptoss_openai_16000": (f"{base}/v1/chat/completions",
                                {"model": "@cf/openai/gpt-oss-120b", "messages": hi, "max_tokens": 16000}),
        # 5. another strong model
        "llama70b_openai_small": (f"{base}/v1/chat/completions",
                                  {"model": "@cf/meta/llama-3.3-70b-instruct-fp8-fast", "messages": hi, "max_tokens": 50}),
    }
    res = {k: call(u, b, token) for k, (u, b) in probes.items()}
    (out / "cloudflare_check.json").write_text(json.dumps(res, indent=1))
    for k, v in res.items():
        print(k, v["status"], v["body"][:300].replace("\n", " "))


if __name__ == "__main__":
    main()
