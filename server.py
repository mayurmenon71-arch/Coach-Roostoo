"""
Coach Roostoo — FastAPI server (Groq / OpenAI-compatible build).

  - POST /api/coach   : called by the Go backend — validates X-Internal-Token,
                        builds prompt from history, calls LLM, screens output,
                        returns JSON { Reply, ModelID }
  - GET  /api/health  : { ok, model, keySet }
  - serves the UI from ./public (index.html) so it's one link

PROVIDER CONFIG (generic env names, currently set up for Groq):
  API_KEY              - your provider's API key
  API_URL              - the provider's chat-completions endpoint
  MODEL                - the model name to call
  COACH_SERVICE_SECRET - shared secret validated via X-Internal-Token header

NOTE: this build targets GROQ, which is OpenAI-compatible — it uses a
"messages" array in the request and choices[0].message.content in the response,
with a Bearer auth header. This is the SAME shape as DeepSeek/OpenAI, and is
DIFFERENT from Gemini's native format.

Run locally:
  pip install fastapi uvicorn httpx python-dotenv
  uvicorn server:app --host 0.0.0.0 --port 8788
"""

import os
import re

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import (PlainTextResponse, JSONResponse, FileResponse,
                               RedirectResponse)
from fastapi.staticfiles import StaticFiles

load_dotenv()

PORT           = int(os.environ.get("PORT", "8788"))
KEY            = os.environ.get("API_KEY")
INTERNAL_TOKEN = os.environ.get("COACH_SERVICE_SECRET", "")
# Groq's OpenAI-compatible chat-completions endpoint.
API_URL        = os.environ.get("API_URL", "https://api.groq.com/openai/v1/chat/completions")
MODEL          = os.environ.get("MODEL", "llama-3.3-70b-versatile")

if not KEY:
    print("\n[Coach Roostoo] No API key set yet.")
    print("Set API_KEY in your environment and restart.\n")

# System prompt — Python owns this; the Go backend does not send one.
SYSTEM_PROMPT = (
    "You are Coach Roostoo, an expert trading educator inside the Roostoo "
    "paper-trading simulator. You help users understand trading concepts, "
    "strategies, risk management, and how to use the Roostoo platform — but "
    "you never give real-money financial advice or directives. "
    "Keep answers clear, concise, and educational, always grounded in the "
    "Roostoo simulation context."
)

app = FastAPI()

# ============================================================================
# LAYER 3 — OUTPUT GUARDRAIL (provider-agnostic — screens text)
# ============================================================================

REAL_ASSET = re.compile(
    r"\b(bitcoin|btc|ethereum|eth|crypto|stock|stocks|shares?|tesla|tsla|apple|aapl|s&p|sp500|nasdaq|forex|gold|real money|your portfolio|your money|your account)\b",
    re.IGNORECASE,
)

DIRECTIVE = re.compile(
    r"\b(you should (buy|sell|short|long|hold|invest|put|allocate)|i (recommend|suggest|advise) (you )?(buy|sell|short|investing|allocating)|buy now|sell now|go (all in|long|short)|the best (coin|stock|asset|investment) (is|to)|put your money|invest in)\b",
    re.IGNORECASE,
)

SIM_SCOPED = re.compile(
    r"(sandbox|simulator|sim|training|agent|episode|backtest|in roostoo|the feed)",
    re.IGNORECASE,
)


def crosses_line(text: str) -> bool:
    if not text:
        return False
    sentences = re.split(r"(?<=[.!?\n])\s+", text)
    for s in sentences:
        if not DIRECTIVE.search(s):
            continue
        if SIM_SCOPED.search(s):
            continue  # directive scoped to the sim -> allowed
        if REAL_ASSET.search(s):
            return True  # real-world directive about a real asset/money
    return False


SAFE_REDIRECT = (
    "I can't tell you what to do with real money or real assets — Coach Roostoo "
    "is here to help you learn inside the Roostoo simulator, where nothing is real. "
    "What I can do is explain the concept behind your question and how an agent "
    "configured like yours might handle it in the sandbox, so you can test the idea "
    "safely. Want me to break down the mechanics or the risks instead?"
)


@app.post("/api/coach")
async def coach(request: Request):
    # ── Auth: validate shared secret from Go backend ──────────────────────────
    if INTERNAL_TOKEN:
        token = request.headers.get("X-Internal-Token", "")
        if token != INTERNAL_TOKEN:
            return JSONResponse({"error": "Unauthorized"}, status_code=401)

    body = await request.json()

    # Two supported contracts:
    #   * This app's UI (public/assets/app.js): {"system": "...", "message": "..."}
    #     -> respond with PLAIN TEXT (app.js reads res.text()).
    #   * Go backend: {"Messages": [{"Role","Content"}], "UserContext": {...}}
    #     -> respond with JSON {"Reply", "ModelID"}.
    frontend_message = body.get("message")
    go_messages = body.get("Messages", [])

    if frontend_message:
        mode = "text"
        messages = []
        if body.get("system"):
            messages.append({"role": "system", "content": body["system"]})
        messages.append({"role": "user", "content": frontend_message})
    elif go_messages:
        mode = "json"
        messages = [
            {"role": m["Role"], "content": m["Content"]}
            for m in go_messages
            if m.get("Role") and m.get("Content")
        ]
        if not messages or messages[0]["role"] != "system":
            messages.insert(0, {"role": "system", "content": SYSTEM_PROMPT})
    else:
        return JSONResponse({"error": "Missing message"}, status_code=400)

    if not KEY:
        return JSONResponse({"error": "Server has no API key configured."}, status_code=500)

    payload = {
        "model": MODEL,
        "messages": messages,
        "temperature": 0.4,
        "max_tokens": 2000,
        "stream": False,  # we buffer the full response for the guardrail
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            upstream = await client.post(
                API_URL,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {KEY}",
                },
                json=payload,
            )

        if upstream.status_code != 200:
            detail = upstream.text[:400]
            print("[coach] LLM provider error:", upstream.status_code, detail)
            msg = "[error contacting model provider] %s" % detail
            if mode == "text":
                return PlainTextResponse(msg, status_code=502)
            return JSONResponse({"error": "error contacting model provider",
                                 "detail": detail}, status_code=502)

        # OpenAI-style response: answer is at choices[0].message.content.
        data = upstream.json()
        try:
            full = data["choices"][0]["message"]["content"] or ""
        except (KeyError, IndexError, TypeError):
            full = ""

        # ---- LAYER 3: screen the complete answer ----
        release = full.strip()
        if crosses_line(release):
            print("[coach][guardrail] directive-on-real-asset detected — replacing response.")
            release = SAFE_REDIRECT

        if mode == "text":
            return PlainTextResponse(release or "(no response)")
        return JSONResponse({"Reply": release or "(no response)", "ModelID": MODEL})

    except Exception as err:  # noqa: BLE001
        print("[coach] error:", str(err))
        if mode == "text":
            return PlainTextResponse("[server error] %s" % err, status_code=500)
        return JSONResponse({"error": "internal server error", "detail": str(err)},
                            status_code=500)


@app.get("/api/health")
async def health():
    return {"ok": True, "model": MODEL, "keySet": bool(KEY)}


# ============================================================================
# INTENT COMPILER — "Rules to Rewards" Create mode (coach_compiler package)
# ============================================================================
# POST /api/compile { messages: [{role, content}, ...] }
#   -> {type: "chat"|"gene_card"|"error", text, card?, errors?}
# Plain `def` endpoints: FastAPI runs them in a threadpool, so the blocking
# urllib call inside the orchestrator doesn't stall the event loop.

from coach_compiler import exemplars as _exemplars  # noqa: E402
from coach_compiler.orchestrator import run_create as _run_create  # noqa: E402
from coach_compiler.validator import validate_config as _validate_config  # noqa: E402


@app.post("/api/compile")
def compile_intent(body: dict):
    messages = body.get("messages")
    if not isinstance(messages, list) or not messages:
        return JSONResponse({"type": "error", "text": "Missing messages"}, status_code=400)
    try:
        return JSONResponse(_run_create(messages[-20:]))
    except Exception as err:  # noqa: BLE001
        print("[compile] error:", str(err))
        return JSONResponse(
            {"type": "error",
             "text": "The compiler backend hit an error contacting the model provider.",
             "detail": str(err)},
            status_code=502)


@app.get("/api/compile/health")
def compile_health():
    selftest = all(_validate_config(cfg)["valid"]
                   for _, _, _, cfg, _, _, _ in _exemplars.WORKED_EXAMPLES)
    return {"ok": True, "model": MODEL, "keySet": bool(KEY),
            "validator_selftest": "pass" if selftest else "FAIL"}


# Serve the coach UI from ./public (mounted last so /api routes take priority).
# Resolve public/ relative to THIS file, not the process CWD: on Vercel the
# function runs from /var/task and a bare "public" fails to resolve. Guard the
# mount so a missing directory can never crash import (which would take the
# whole app — and every /api route — down with it).
_PUBLIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "public")


# Explicit root route: StaticFiles(html=True) serves /index.html but its
# bare-"/" index resolution doesn't fire under Vercel's routing, so serve the
# landing page here. Defined before the mount so it takes priority for GET /.
@app.get("/")
def _root():
    # On Render the file is on disk → serve it directly (clean URL). On Vercel
    # public/ is served by the CDN and isn't in the function bundle, so fall
    # back to redirecting to /index.html, which the CDN serves.
    index = os.path.join(_PUBLIC_DIR, "index.html")
    if os.path.isfile(index):
        return FileResponse(index)
    return RedirectResponse(url="/index.html")


if os.path.isdir(_PUBLIC_DIR):
    app.mount("/", StaticFiles(directory=_PUBLIC_DIR, html=True), name="static")
else:
    print(f"[Coach Roostoo] static dir not found at {_PUBLIC_DIR}; "
          "serving API only (static assets will 404).")


if __name__ == "__main__":
    import uvicorn

    print(f"\n[Coach Roostoo] running on http://localhost:{PORT}")
    print(f"[Coach Roostoo] open that link in your browser. Model: {MODEL}")
    print("[Coach Roostoo] Layer 3 output guardrail: ACTIVE\n")
    uvicorn.run(app, host="0.0.0.0", port=PORT)
