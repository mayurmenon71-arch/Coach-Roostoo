"""
Coach Roostoo — Vercel serverless function.
Lives at api/coach.py → serves /api/coach automatically.

Supports TWO calling contracts:

  1. UI / legacy  { "system": "...", "message": "..." }
     → returns plain text (browser reads res.text())

  2. Go backend   { "Messages": [{Role, Content, ToolCallId?, ToolName?}],
                    "UserContext": {"UserId": 123},
                    "Tools": [{Name, Description, Parameters}] }
     → returns JSON  { "Reply": "..." , "ModelID": "..." }
                  OR { "ToolCall": { "ToolCallId", "Name", "Params" }, "ModelID": "" }

Env vars (set in Vercel dashboard):
  API_KEY              - Groq (or OpenAI-compatible) API key
  API_URL              - chat-completions endpoint (default: Groq)
  MODEL                - model name
  COACH_SERVICE_SECRET - shared secret validated via X-Internal-Token header
"""

import os
import re
import json
import urllib.request
import urllib.error
from http.server import BaseHTTPRequestHandler

KEY            = os.environ.get("API_KEY")
INTERNAL_TOKEN = os.environ.get("COACH_SERVICE_SECRET", "")
API_URL        = os.environ.get("API_URL", "https://api.groq.com/openai/v1/chat/completions")
MODEL          = os.environ.get("MODEL", "llama-3.3-70b-versatile")

# ── System prompt (Go contract path) ─────────────────────────────────────────
# Pull the platform registry (signal families, strategy variants, indicators)
# from the compiler package when it's importable, so this legacy function
# describes the same product as server.py. Falls back to "" if the package
# isn't bundled with this function.
try:
    import sys as _sys
    _sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from coach_compiler.prompt import registry_brief as _registry_brief
    _REGISTRY = "\n\n" + _registry_brief()
except Exception:  # noqa: BLE001
    _REGISTRY = ""

SYSTEM_PROMPT = (
    "You are Coach Roostoo, an expert trading educator inside the Roostoo "
    "platform. You help users understand trading concepts, the agents, "
    "signal families and strategy variants, and how to use the Roostoo "
    "platform — but you never give real-money financial advice or directives. "
    "Keep answers clear, concise, and educational, always grounded in the "
    "Roostoo context." + _REGISTRY + "\n\n"
    "You have access to tools that let you act on the platform on the user's behalf. "
    "IMPORTANT: before calling any action tool (create_trading_agent, join_competition), "
    "you MUST first describe exactly what you are about to do and ask the user to confirm. "
    "Only call a tool after the user explicitly agrees (e.g. 'yes', 'go ahead', 'do it'). "
    "For read-only tools (get_my_portfolio) you may call them immediately without asking."
)

# ── Output guardrail ──────────────────────────────────────────────────────────
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

SAFE_REDIRECT = (
    "I can't tell you what to do with real money or real assets — Coach Roostoo "
    "is here to help you learn inside the Roostoo simulator, where nothing is real. "
    "What I can do is explain the concept behind your question and how an agent "
    "configured like yours might handle it in the sandbox, so you can test the idea "
    "safely. Want me to break down the mechanics or the risks instead?"
)


def crosses_line(text):
    if not text:
        return False
    for s in re.split(r"(?<=[.!?\n])\s+", text):
        if not DIRECTIVE.search(s):
            continue
        if SIM_SCOPED.search(s):
            continue
        if REAL_ASSET.search(s):
            return True
    return False


def _call_llm(messages, tools=None):
    """Call the LLM and return (data_dict, error_string)."""
    payload = {
        "model":       MODEL,
        "messages":    messages,
        "temperature": 0.4,
        "max_tokens":  2000,
        "stream":      False,
    }
    if tools:
        payload["tools"] = tools

    req = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type":  "application/json",
            "Authorization": "Bearer " + (KEY or ""),
            "User-Agent":    "CoachRoostoo/2.0",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8")), None
    except urllib.error.HTTPError as e:
        try:
            detail = e.read()[:300].decode("utf-8", errors="replace")
        except Exception:
            detail = ""
        rate = e.code == 429 or "rate limit" in detail.lower()
        msg = ("rate-limited" if rate else f"provider error {e.code}")
        print(f"[coach] LLM {msg}: {detail}")
        return None, msg
    except Exception as exc:
        print("[coach] LLM error:", exc)
        return None, str(exc)


class handler(BaseHTTPRequestHandler):
    def _cors(self):
        # Allow browser clients on any origin (e.g. the published design) to call
        # this stateless proxy. No cookies/credentials are used, so "*" is safe.
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Internal-Token")
        self.send_header("Access-Control-Max-Age", "86400")

    def _send_json(self, code, obj):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self._cors()
        self.end_headers()
        self.wfile.write(body)

    def _send_text(self, code, text):
        body = text.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self._cors()
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        # CORS preflight — browsers send this before the JSON POST.
        self.send_response(204)
        self._cors()
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self):
        self._send_json(200, {"ok": True, "model": MODEL, "keySet": bool(KEY)})

    def do_POST(self):
        # ── Auth: validate X-Internal-Token when secret is configured ─────────
        if INTERNAL_TOKEN:
            token = self.headers.get("X-Internal-Token", "")
            if token != INTERNAL_TOKEN:
                self._send_json(401, {"error": "Unauthorized"})
                return

        # ── Parse body ────────────────────────────────────────────────────────
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length) or "{}")
        except Exception:
            self._send_json(400, {"error": "Invalid JSON body"})
            return

        if not KEY:
            self._send_json(500, {"error": "Server has no API key configured."})
            return

        # ── Detect contract: UI (legacy) vs Go backend ────────────────────────
        frontend_message = body.get("message")
        go_messages      = body.get("Messages", [])
        go_tools         = body.get("Tools", [])

        if frontend_message:
            # ── UI / legacy path ──────────────────────────────────────────────
            # Always apply the server-side coach persona + guardrail behaviour,
            # regardless of what the client sends. An optional client `system`
            # (e.g. runtime config context) is layered on top, and an optional
            # `history` array carries prior turns for multi-turn memory.
            mode = "text"
            messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            if body.get("system"):
                messages.append({"role": "system", "content": body["system"]})
            for m in (body.get("history") or [])[-12:]:
                role = (m.get("role") or "").lower()
                content = m.get("content") or ""
                if role in ("user", "assistant") and content:
                    messages.append({"role": role, "content": content})
            messages.append({"role": "user", "content": frontend_message})
            oai_tools = None

        elif go_messages:
            # ── Go backend path ───────────────────────────────────────────────
            mode = "json"
            messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            for m in go_messages:
                role = (m.get("Role") or "").lower()
                if not role:
                    continue
                if role == "tool":
                    messages.append({
                        "role":         "tool",
                        "tool_call_id": m.get("ToolCallId", "call_unknown"),
                        "content":      m.get("Content") or "",
                    })
                elif role == "assistant" and m.get("ToolCallId"):
                    messages.append({
                        "role":    "assistant",
                        "content": None,
                        "tool_calls": [{
                            "id":   m["ToolCallId"],
                            "type": "function",
                            "function": {
                                "name":      m.get("ToolName", ""),
                                "arguments": "{}",
                            },
                        }],
                    })
                else:
                    content = m.get("Content") or ""
                    if content:
                        messages.append({"role": role, "content": content})

            oai_tools = [
                {
                    "type": "function",
                    "function": {
                        "name":        t["Name"],
                        "description": t["Description"],
                        "parameters":  t["Parameters"],
                    },
                }
                for t in go_tools
                if t.get("Name")
            ] or None

        else:
            self._send_json(400, {"error": "Missing message"})
            return

        # ── Call LLM ──────────────────────────────────────────────────────────
        data, err = _call_llm(messages, tools=oai_tools if mode == "json" else None)
        if err:
            human = ("The coach is briefly rate-limited — try again in a few seconds."
                     if "rate" in err else
                     "The coach couldn't reach the model provider right now.")
            if mode == "text":
                self._send_text(502, human)
            else:
                self._send_json(502, {"error": human})
            return

        choice = data["choices"][0]
        finish = choice.get("finish_reason", "")

        # ── Tool call path ────────────────────────────────────────────────────
        if finish == "tool_calls" and mode == "json":
            tc_list = choice["message"].get("tool_calls", [])
            if tc_list:
                tc = tc_list[0]
                try:
                    args = json.loads(tc["function"].get("arguments") or "{}")
                except Exception:
                    args = {}
                print(f"[coach][tool] LLM requested: {tc['function']['name']} args={args}")
                self._send_json(200, {
                    "ToolCall": {
                        "ToolCallId": tc["id"],
                        "Name":       tc["function"]["name"],
                        "Params":     args,
                    },
                    "ModelID": MODEL,
                })
                return

        # ── Normal text response ──────────────────────────────────────────────
        try:
            full = choice["message"]["content"] or ""
        except (KeyError, IndexError, TypeError):
            full = ""

        release = full.strip()
        if crosses_line(release):
            print("[coach][guardrail] directive-on-real-asset detected — replacing.")
            release = SAFE_REDIRECT

        if mode == "text":
            self._send_text(200, release or "(no response)")
        else:
            self._send_json(200, {"Reply": release or "(no response)", "ModelID": MODEL})
