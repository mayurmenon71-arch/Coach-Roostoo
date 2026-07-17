"""
Roostoo Agent Factory — MCP server.

Exposes the deterministic agent-factory tools (from the coach_compiler package)
over the Model Context Protocol, so any MCP client — this web app, Claude
Desktop, the Go backend, or a future agent — can:

  * read the authoritative v1 parameter registry,
  * validate a config,
  * look up knowledge cards,
  * build a default config for a strategy personality,
  * compile a plain-language intent into a validated config (needs API_KEY),
  * STAGE a validated agent (ready to launch),
  * LAUNCH a staged agent (side-effectful; gated — see launch_agent).

Run (stdio, e.g. for Claude Desktop):   python -m mcp_server.server
Run (HTTP, e.g. for the web backend):    MCP_HTTP=1 python -m mcp_server.server

Requires Python 3.10+ and the `mcp` package (see requirements-mcp.txt).
"""

import os
import sys

# Make the sibling coach_compiler package importable however this is launched.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp.server.fastmcp import FastMCP  # noqa: E402

from coach_compiler import schema as S  # noqa: E402
from coach_compiler.knowledge import retrieve as _retrieve  # noqa: E402
from coach_compiler.validator import validate_config as _validate  # noqa: E402
from coach_compiler.genecard import build_gene_card as _build_card  # noqa: E402

mcp = FastMCP("roostoo-agent-factory")

# In-memory stage store. NOTE: fine for a single stdio process / one dev box.
# For the serverless web app, back this with the user's session or a small KV
# store so stage_id survives across requests (see docs/MCP_PLAN.md, Phase 2).
_STAGED: dict = {}
_stage_counter = {"n": 0}


# ── Read-only tools (no key, no side effects) ────────────────────────────────
@mcp.tool()
def get_registry() -> dict:
    """Return the authoritative v1 parameter registry — the only parameters the
    platform supports. Clients should build configs against this."""
    return {
        "assets": [a + S.QUOTE for a in S.SUPPORTED_ASSETS],
        "assets_min": S.MIN_ASSETS, "assets_max": S.MAX_ASSETS,
        "candle_intervals": list(S.CANDLE_INTERVALS),
        "rewards": list(S.REWARDS),
        "training_steps": list(S.TRAINING_STEPS),
        "pct_bounds": list(S.PCT_BOUNDS),
        "long_only": S.LONG_ONLY,
        "fixed": {
            "policy": S.POLICY, "lookback": S.LOOKBACK,
            "training_data": S.TRAINING_DATA,
            "indicators": list(S.FIXED_INDICATORS),
        },
        "personalities": list(S.ARCHETYPES),
    }


@mcp.tool()
def validate_config(config: dict) -> dict:
    """Deterministically validate a config against the v1 registry.
    Returns {valid, errors, warnings, config?}."""
    return _validate(config)


@mcp.tool()
def retrieve_card(query: str, k: int = 3) -> list:
    """Look up Roostoo knowledge cards (strategies, rewards, fees, platform)."""
    return _retrieve(query, k)


@mcp.tool()
def default_config(archetype: str, assets: list | None = None,
                   name: str | None = None) -> dict:
    """Build a schema-valid v1 config from a personality's defaults.
    archetype is one of: intraday_momentum, mean_reversion, breakout, flow_driven."""
    return S.default_config_for(archetype, assets, name)


# ── Compile: intent -> validated config + gene card (needs API_KEY) ─────────
@mcp.tool()
def compile_intent(messages: list, ui_context: str = "") -> dict:
    """Compile a plain-language conversation into a validated config or a
    clarifying question. `messages` is [{"role","content"}, ...]. Requires the
    model provider API_KEY in the environment. Returns the orchestrator result:
    {type: 'chat'|'gene_card'|'error', text, card?}."""
    from coach_compiler.orchestrator import run_coach
    return run_coach(messages, ui_context=ui_context or None)


# ── Stage / launch (the "user just launches" flow) ──────────────────────────
@mcp.tool()
def stage_agent(config: dict, name: str | None = None) -> dict:
    """Validate a config and STAGE it as a launch-ready agent. Safe and
    idempotent — no training starts. Returns {ok, stage_id, gene_card} on
    success, or {ok: false, errors} if the config is invalid."""
    verdict = _validate(config)
    if not verdict["valid"]:
        return {"ok": False, "errors": verdict["errors"]}
    cfg = verdict["config"]
    if name:
        cfg["name"] = name
    _stage_counter["n"] += 1
    stage_id = "stage_%d" % _stage_counter["n"]
    card = _build_card(cfg, rationale={}, classification={}, warnings=verdict["warnings"])
    _STAGED[stage_id] = cfg
    return {"ok": True, "stage_id": stage_id, "gene_card": card}


@mcp.tool()
def launch_agent(stage_id: str) -> dict:
    """Launch (start training) a previously staged agent. SIDE-EFFECTFUL.

    This is the human-gated step: a UI/host should only call it after the user
    explicitly confirms. It is currently a STUB — it returns what it *would*
    launch. Wire the marked section to the real Roostoo factory/training API
    (or the in-browser sim for a demo). See docs/MCP_PLAN.md, Phase 3."""
    cfg = _STAGED.get(stage_id)
    if cfg is None:
        return {"ok": False, "error": "unknown stage_id — call stage_agent first"}
    # >>> WIRE HERE: POST cfg to the Roostoo training/factory API and return its
    #     job id. Until then this is a no-op stub.
    return {
        "ok": True,
        "status": "staged_not_launched",
        "note": ("Stub: not wired to a training backend yet. This would submit "
                 "the config below to the Roostoo factory to start training."),
        "config": cfg,
    }


# ── Resources ────────────────────────────────────────────────────────────────
@mcp.resource("registry://v1")
def registry_resource() -> str:
    import json
    return json.dumps(get_registry(), indent=2)


def main():
    # Streamable-HTTP for the web/serverless client; stdio for Claude Desktop.
    if os.environ.get("MCP_HTTP"):
        mcp.run(transport="streamable-http")
    else:
        mcp.run()


if __name__ == "__main__":
    main()
