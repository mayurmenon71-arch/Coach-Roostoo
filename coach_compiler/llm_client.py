"""
OpenAI-compatible chat call with tool support — stdlib urllib only, so the
same client runs inside the Vercel serverless function and the FastAPI
server. Mirrors api/coach.py's provider setup (Groq by default).

Env vars: API_KEY (required), API_URL, MODEL — same names as the rest of the
repo.
"""

import json
import os
import re
import time
import urllib.error
import urllib.request

_RETRY_RE = re.compile(r"try again in ([\d.]+)\s*s", re.I)
MAX_RATE_RETRIES = 2       # extra attempts after a 429
MAX_RETRY_SLEEP = 9.0      # cap per-wait so a request never hangs too long

DEFAULT_API_URL = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_MODEL = "llama-3.3-70b-versatile"


class LLMError(RuntimeError):
    pass


def call_chat(messages, tools=None, temperature=0.2, max_tokens=1400):
    """One chat-completions call. Returns the assistant message dict:
    {"role": "assistant", "content": str|None, "tool_calls": [...]|absent}.

    The orchestrator treats this function as injectable — tests pass a fake
    with the same signature instead.
    """
    key = os.environ.get("API_KEY")
    if not key:
        raise LLMError("Server has no API key configured (API_KEY).")
    api_url = os.environ.get("API_URL", DEFAULT_API_URL)
    model = os.environ.get("MODEL", DEFAULT_MODEL)

    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False,
    }
    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"

    req = urllib.request.Request(
        api_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer " + key,
            "User-Agent": "CoachRoostoo-Compiler/0.1",
        },
        method="POST",
    )
    # On a 429 (per-minute token cap briefly exceeded) the provider tells us how
    # long to wait — honor it and retry so transient bursts resolve invisibly
    # instead of surfacing an error to the user.
    for attempt in range(MAX_RATE_RETRIES + 1):
        try:
            with urllib.request.urlopen(req, timeout=90) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            break
        except urllib.error.HTTPError as e:
            try:
                detail = e.read()[:400].decode("utf-8", "replace")
            except Exception:
                detail = ""
            if e.code == 429 and attempt < MAX_RATE_RETRIES:
                m = _RETRY_RE.search(detail)
                wait = min(float(m.group(1)) + 0.4, MAX_RETRY_SLEEP) if m else 3.0
                time.sleep(wait)
                continue
            raise LLMError("provider error %s: %s" % (e.code, detail))
        except Exception as e:
            raise LLMError("provider unreachable: %s" % (e,))

    try:
        return data["choices"][0]["message"]
    except (KeyError, IndexError, TypeError):
        raise LLMError("malformed provider response")
