"""
Coach Roostoo intent compiler — Vercel serverless function.
Lives at api/compile.py -> serves POST /api/compile automatically.

Contract (stateless, like /api/coach):
  POST { "messages": [ {"role": "user"|"assistant", "content": "..."}, ... ] }
  -> 200 { "type": "chat",      "text": "..." }                     elicitation turn
  -> 200 { "type": "gene_card", "text": "...", "card": {...} }      compiled + validated
  -> 200 { "type": "error",     "text": "...", "errors": [...] }    repair rounds exhausted

Env vars (same as api/coach.py): API_KEY, API_URL, MODEL.
GET /api/compile -> health check + deterministic validator self-test. If the
coach_compiler package failed to import (the classic serverless bundling
gotcha), GET returns a diagnostic payload instead of the whole function
crashing — so you can see exactly what went wrong from the browser.
"""

import json
import os
import sys
from http.server import BaseHTTPRequestHandler

# ---------------------------------------------------------------------------
# Resilient import of the coach_compiler package.
#
# On Vercel the working directory and bundle layout aren't guaranteed, so we
# add every plausible root to sys.path and import inside a try. If it still
# fails we DON'T crash the function at module-load (which yields an opaque
# FUNCTION_INVOCATION_FAILED); instead we record the error and surface it from
# the health endpoint with enough context to fix it.
# ---------------------------------------------------------------------------
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT_CANDIDATES = [
    os.path.dirname(_HERE),   # repo root (parent of api/) — the intended one
    _HERE,                    # api/ itself
    os.getcwd(),              # process CWD
    "/var/task",              # AWS Lambda / Vercel task root
]
for _r in _ROOT_CANDIDATES:
    if _r and _r not in sys.path:
        sys.path.insert(0, _r)

_IMPORT_OK = True
_IMPORT_ERROR = None
try:
    from coach_compiler import exemplars
    from coach_compiler.orchestrator import run_create
    from coach_compiler.validator import validate_config
except Exception as _e:  # noqa: BLE001
    _IMPORT_OK = False
    _IMPORT_ERROR = "%s: %s" % (type(_e).__name__, _e)


def _diagnostic():
    """What the health endpoint reports when the package didn't import — a
    map of each candidate root and whether coach_compiler is visible there."""
    seen = {}
    for r in _ROOT_CANDIDATES:
        pkg = os.path.join(r, "coach_compiler")
        try:
            seen[r] = sorted(os.listdir(pkg))[:8] if os.path.isdir(pkg) else "(no coach_compiler here)"
        except Exception as e:  # noqa: BLE001
            seen[r] = "(unreadable: %s)" % e
    return {"import_error": _IMPORT_ERROR, "roots_checked": seen,
            "sys_path_head": sys.path[:5]}


class handler(BaseHTTPRequestHandler):
    def _send(self, code, obj):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    # GET /api/compile -> health + deterministic self-test (or diagnostic)
    def do_GET(self):
        if not _IMPORT_OK:
            self._send(500, {"ok": False,
                             "error": "coach_compiler failed to import",
                             "diagnostic": _diagnostic()})
            return
        selftest = all(validate_config(cfg)["valid"]
                       for _, _, _, cfg, _, _, _ in exemplars.WORKED_EXAMPLES)
        self._send(200, {
            "ok": True,
            "keySet": bool(os.environ.get("API_KEY")),
            "model": os.environ.get("MODEL", "llama-3.3-70b-versatile"),
            "validator_selftest": "pass" if selftest else "FAIL",
        })

    # POST /api/compile -> one Create-mode turn
    def do_POST(self):
        if not _IMPORT_OK:
            self._send(500, {"type": "error",
                             "text": "Server misconfigured: coach_compiler did not "
                                     "bundle. Hit GET /api/compile for the diagnostic.",
                             "detail": _IMPORT_ERROR})
            return
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
                             "text": "The compiler backend hit an error contacting the model provider.",
                             "detail": str(e)})
            return

        self._send(200, out)
