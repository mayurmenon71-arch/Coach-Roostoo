# Coach Roostoo v2 — MCP + one-click launch plan

**Goal:** the Coach LLM auto-selects a validated agent config; the user's only
action is to launch it.

## Framing (what MCP does and doesn't buy us)
Coach already auto-selects configs — that's the `emit_config` tool-call it does
today. MCP (Model Context Protocol) doesn't add that; it standardizes the
agent-factory actions (validate · stage · launch · registry · cards) into one
tool **server** that any client can call — this web app, Claude Desktop, the Go
backend, future agents. The LLM sees MCP tools as ordinary function calls, so it
works with Groq/Llama unchanged (our backend is the MCP *client*).

**The real gap for "just launch" isn't MCP — it's two missing pieces:** (1) an
action that pushes the compiled config into the Lab as a launchable agent, and
(2) a real train/launch backend to hand it to. This plan builds both; MCP is the
clean way to package them.

## Architecture
```
Coach LLM (Groq) → our backend = MCP CLIENT → "Roostoo Agent Factory" MCP SERVER → real factory / sim
   picks config       bridges tools↔LLM         validate · stage · launch · registry · cards
```

## MCP server surface ("roostoo-agent-factory")
**Tools**
- `get_registry()` — authoritative v1 params (keeps the LLM from drifting).
- `validate_config(config)` — the existing deterministic validator.
- `retrieve_card(query)` — knowledge-card lookup.
- `stage_agent(config)` — **new, safe/idempotent:** validates, writes a *pending,
  launchable* agent to the session, returns a `stage_id`. The "ready" step.
- `launch_agent(stage_id)` — **side-effectful:** starts training. Gated (below).

**Resources:** `registry://v1`, `cards://knowledge/*`, later `telemetry://agent/{id}`.

## Phases
| Phase | Work | Est. |
|---|---|---|
| 1 | Wrap existing tools (validate/retrieve/registry) as a Python MCP server over **Streamable-HTTP** (stdio won't run on Vercel; HTTP does). No behavior change — existing tests pass against it. | 1–2 d |
| 2 | Backend becomes the MCP **client**; add `stage_agent`; gene card returns with a single **🚀 Launch** button. This is the "user just launches" UX. | 2–3 d |
| 3 | Wire `launch_agent` to the real training API (the Go factory backend `server.py` already knows), **or** to the in-browser `sim-engine.js` for a demo. | depends (see decisions) |
| 4 (opt.) | Reuse the server from Claude Desktop / Go backend; add `get_telemetry` → unlocks the doc's **Review mode** (post-competition coaching); proactive "here's an agent — launch?". | later |

## Safety (matches the "Rules to Rewards" compliance envelope)
- **Human gate stays at launch.** The LLM auto-selects and *stages*; the *user*
  clicks launch. The LLM never auto-enters a competition or spends real money.
- **Validation stays deterministic and server-side** — nothing invalid can be
  staged, even if the LLM slips.
- **`launch_agent` requires a `stage_id`** from a validated stage — no launching
  arbitrary payloads.

## Decisions needed
1. **Real launch or demo?** Is there a training/launch API to call (the Go
   factory), or should Phase 3 launch into the in-browser sim for now?
2. **Do we actually need MCP's cross-client reuse?** If it's only ever this web
   app, skip the MCP hop and add `stage_agent` + the Launch button to the
   existing function-calling — same UX, fewer moving parts. MCP earns its keep
   the moment a second client needs these tools.

Phases 1–2 are worth doing regardless of the answers.
