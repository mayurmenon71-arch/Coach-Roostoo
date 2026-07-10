"""
Coach Roostoo intent compiler — Vercel serverless function.
Lives at api/compile.py -> serves POST /api/compile automatically.

Contract (stateless, like /api/coach):
  POST { "messages": [ {"role": "user"|"assistant", "content": "..."}, ... ] }
  -> 200 { "type": "chat",      "text": "..." }                     elicitation turn
  -> 200 { "type": "gene_card", "text": "...", "card": {...} }      compiled + validated
  -> 200 { "type": "error",     "text": "...", "errors": [...] }    repair rounds exhausted

Env vars (same as api/coach.py): API_KEY, API_URL, MODEL.
GET /api/compile -> health check incl. a deterministic self-test of the
validator against the three worked-example configs.
"""

import json
import os
import sys
from http.server import BaseHTTPRequestHandler

# The coach_compiler package sits at the repo root, one level above api/.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from coach_compiler import exemplars  # noqa: E402
from coach_compiler.orchestrator import run_create  # noqa: E402
from coach_compiler.validator import validate_config  # noqa: E402


class handler(BaseHTTPRequestHandler):
    def _send(self, code, obj):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    # GET /api/compile -> health + deterministic self-test
    def do_GET(self):
        selftest = all(validate_config(cfg)["valid"]
                       for _, _, _, cfg, _, _, _ in exemplars.WORKED_EXAMPLES)
        self._send(200, {
            "ok": True,
            "keySet": bool(os.environ.get("API_KEY")),
            "model": os.environ.get("MODEL", "openai/gpt-oss-20b"),
            "validator_selftest": "pass" if selftest else "FAIL",
        })

    # POST /api/compile -> one Create-mode turn
    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length) or "{}")
        except Exception:
            self._send(400, {"type": "error", "text": "Invalid request body"})
            return

        messages = body.get("messages")
        if not isinstance(messages, list) or not messages:
            self._send(400, {"type": "error", "text": "Missing messages"})
            return
        # Cap conversation size defensively (stateless contract).
        messages = messages[-20:]

        try:
            out = run_create(messages)
        except Exception as e:  # noqa: BLE001
            print("[compile] error:", str(e))
            self._send(502, {"type": "error",
                             "text": "The compiler backend hit an error contacting the model provider."})
            return

        self._send(200, out)
