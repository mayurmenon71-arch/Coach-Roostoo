# PRD v2 (adjusted to codebase)

# Coach Roostoo — Product Requirements

> **Editor's note.** This is the boss's PRD v2 with the technical specifics
> reconciled to what actually exists in the `Coach Roostoo v2` codebase. The
> product intent is unchanged; only names, tools, model, and mechanisms have
> been corrected. Changes are flagged inline as **[adjusted]**, and a full
> PRD-term → code-artifact map is in §10.

---

## 1. What this is

Coach Roostoo is an LLM chat layer that is the **first touchpoint** of the Roostoo experience. It is positioned as the platform's evolving brain and knowledge base: a component that helps users learn, helps them configure better agents, and over time helps the RL system itself improve by feeding back learnings from forward-testing data.

The bar for v1 is narrow and concrete: **a user completes a meaningful journey (question → agent config → backtest → competition entry) in 2–3 back-and-forths**, and that journey looks great as a ~20-second segment in the launch video.

> **[adjusted]** "template" → "agent config": the built artifact is a validated
> **gene card** (`coach_compiler/genecard.py`), not a saved template the user
> picks from a library. See §4 and §10.

## 2. Goals / non-goals (v1)

**Goals:** conversational agent creation (intent → validated config); guided newbie flow; graceful handling of pro questions; Roostoo knowledge Q&A (competition rules, fees, XP) via RAG; disclaimers built into the flow.

**Non-goals (v1):** live market regime detection; **daily market summary [adjusted — see below]**; custom feature engineering from chat; research/monitoring workflows (wallet tracking, daily reports) — the Coach acknowledges these and points to roadmap; fine-tuned models; multi-language; shorting (**platform is long-only today**, `schema.py: LONG_ONLY = True`).

> **[adjusted] Daily market summary moved to non-goal.** The PRD listed a daily
> market summary as a v1 goal, but the current build has **no live market
> feed** and no `get_market_summary` tool. `coach_compiler/prompt.py` handles
> "what should I build for today's market" by saying plainly it can't see live
> regime data, then giving regime-*conditional* education from the knowledge
> cards. Either (a) accept this as a non-goal for v1, or (b) add a
> `get_market_summary` tool + daily API pull as new scope — it does not exist
> yet.

## 3. Personas

- **Newbie** — curious about agent trading, no strategy vocabulary. Needs a guided flow with options to tap, not a blank chat box.
    - Success = experiments enough to build ≥1 agent; understands roughly what it does.
- **Professional** — crypto-native, has capital, has used Minara/Alva-class tools, asks sophisticated questions (funding, order types, "can it watch whale wallets?"). Needs honest, specific answers, config transparency, and graceful "not yet, here's the roadmap" for out-of-scope asks.
    - Success = trusts the platform enough to build ≥1 agent.

## 4. The core flow (newbie-first)

1. **Intro message + tappable prompt suggestions** on first load.
    1. **[adjusted]** These are the **suggestion chips** in `public/assets/app.js`
       (`CHIPS`, 4 fixed + `SUGGEST_POOL`, 10 rotating), which adapt to the
       user's line of questioning (`TOPIC_FOLLOWUPS`). This is *not* the PRD's
       "10–12 templates" as a fixed grid, and it is *not* backed by a
       `list_templates` tool. If a curated 10–12 starter grid is wanted, it's a
       small frontend addition.
    2. ~~**Market context**: daily market API pull, LLM-summarized.~~ **[adjusted —
       not built]** No live feed in this build; see §2.
2. **Strategy orientation**: Coach explains strategy styles as recommendations (never predictions). These map to the Mint Agent wizard's 5 **signal families** (`MOM` Momentum, `MRV` Mean Reversion, `BRK` Breakout, `FLW` Flow, `ALL` All Indicators) and their **21 strategy variants** — each variant fixes WHICH of the 11 selectable indicators the agent trains on, so `signal_family` and `variant` are **stored config fields**, not just internal hints. The raw codes (`MOM1`, `MRV1`, …) stay internal and are never shown to the user, but friendly names ("Momentum", "Classic Cross") are fine in prose (`prompt.py` TONE rules; classification also lives in `emit_config.classification`).
    1. Down the line, we can feed backtest/production insights back in and have the LLM reason over that context.
3. **Personalize**: at most 2–3 clarifying questions with tappable options (risk comfort, assets, pace). *Open question below on when to skip this entirely.* **[adjusted]** In code this is the **elicit** stage of the Create loop (`orchestrator.run_create`), and the current default is **build-with-defaults**: when the personality is clear, Coach compiles immediately (coins default to BTC+ETH) and only elicits when intent is genuinely vague.
4. **Gene card → backtest → launch/enroll**
    1. **[adjusted]** "Launch Config card" → **gene card** (`geneCardHtml`), rendered inline in chat. Tapping **Launch** posts to `/api/launch`, which re-validates and **stages** the config (real training is still a `>>> WIRE HERE` stub). The **backtest** is the deterministic frontend engine `public/assets/sim-engine.js` (`window.RoostooSim`), narrated in plain language (trades made, worst drawdown, grade). Competition **enrollment** is a Go-backend action (`join_competition`), not part of the Python web path yet.

**Pro flow** rides the same rails, entering with freeform intent instead of chips: `orchestrator.run_coach` routes the ask (question → cheap **Explain** path; build intent → full **Create** path), compiles buildable ideas to the nearest valid config with visible reasoning (the gene card's rationale rows), and for out-of-scope requests states clearly: *agents are for execution and competition, not research/monitoring* — with the roadmap answer. Multi-agent fan-out is supported ("run 3 agents, same strategy, different coins" → `variants` on `emit_config`, expanded by `schema.expand_configs`).

## 5. UX decisions (some locked, some open)

| Decision | Status |
| --- | --- |
| Chat is an option for the agent-creation path — make it clear in the Coach intro; dashboard config panel remains as "advanced" | Yes |
| Full modal/popup for chat instead of cramped right panel | Yes — needs designer input |
| Clarifying questions: Claude-style ask-once-with-options, max 3, only when defaults/intent don't already answer them | Discovery — current code favors **build-with-defaults** (§4.3); test vs. straight-to-creation in demo script |
| Disclaimers: **[adjusted — no stop-loss knob exists]** the platform has no `stop_loss` / `take_profit` / trade-size fields; exits and sizing are **learned by the PPO policy**, and the **reward metric** (e.g. Volatility Penalty, Calmar) is the risk-shaping lever Coach explains instead. The **overfit / forward-testing** framing is woven into every gene card and backtest discussion (`orchestrator._closing_note`, `prompt.py`) — not fine-print | Yes |
| Horizon badge ("short-term trading, hours–days, not investing") after creation | **[adjusted — partially built]** the "not investing / this is the sim" framing exists in prose + the Layer-3 guardrail, but there is no distinct **horizon badge UI**. Small addition if wanted. |
| Out-of-scope fallback script (wallet monitoring, market research asks) | Discovery |

## 6. Architecture (v1)

- **Model:** **[adjusted]** currently **Groq**, OpenAI-compatible, default `llama-3.3-70b-versatile` (env: `API_KEY` / `API_URL` / `MODEL` in `server.py`). **DeepSeek is a candidate** and drops in without code changes (same OpenAI-compatible request shape — noted in `server.py`), but it is *not* the model in use today. Budget guardrail (~$1K/mo at 2–3K DAU) still applies: short contexts, cached cards, no chain-of-thought to users. Note the current Groq free-tier TPM cap is why Q&A uses a lean tool-less path (see below).
- **RAG:** ✅ built. Small curated corpus of Roostoo knowledge cards — **13 cards** in `coach_compiler/cards/*.md` (competition rules, fees/breakeven, tiers/XP/wallets, forward-testing, governance tiers, reward terms, RL-vs-rules, the **5 signal-family cards** — each listing its strategy variants and their indicator subsets — and a scalping-refusal card). Retrieved by deterministic keyword scoring (`coach_compiler/knowledge.py`), exposed to the model as the `retrieve` tool. Cards owned by the quant team, versioned with the platform.
- **Tools — [adjusted, 2 not 4]:** the LLM has **two** tools, not the four named in the PRD:
    - `emit_config` (`schema.py: build_emit_config_tool`) — schema-constrained; submits a v1 config (+ optional `agents` list for fan-out) for **deterministic** validation. ✅ matches the PRD.
    - `retrieve` (`schema.py: build_retrieve_tool`) — RAG lookup over the knowledge cards.
    - `list_templates` → **does not exist**; the family/variant registry and per-family defaults are code (`VARIANTS`, `FAMILY_DEFAULTS`, `default_config_for`), not a tool.
    - `run_backtest` → **does not exist as an LLM tool**; backtesting is the frontend `sim-engine.js`, and staging is the `/api/launch` HTTP endpoint.
    - `get_market_summary` → **does not exist** (no live feed).
    - (Separately, the **Go backend** defines its own action tools — `create_trading_agent`, `join_competition`, `get_my_portfolio` — passed into `/api/coach`. Those are the "act on the platform" tools, distinct from the compiler's two.)
    - **Principle still holds:** everything numeric comes from deterministic code (validator, sim engine, platform locks), never invented by the model.
- **Two interfaces over one core** — worth stating explicitly for implementation:
    - **Web path (what the browser uses):** `public/assets/app.js` → `POST /api/compile` (→ `orchestrator.run_coach`) and `POST /api/launch` (stage/validate). Q&A vs. build is auto-routed: pure questions → lean **Explain** path (no tools, one small call); build intent → **Create** path (emit_config + retrieve + up to 2 repair rounds).
    - **MCP / Go path (external clients):** `POST /api/coach` for the Go backend, plus a separate `mcp_server/server.py` for Claude Desktop / other agents. The web UI never touches these.
- **Guardrails:** ✅ built. No return predictions; no "which agent will win"; backtests always framed as diagnostics with forward-testing (the competition) as the real proof. Enforced by (1) the prompt's REFUSALS carve-out, (2) the deterministic validator (bad picks become repairable errors, never leak), and (3) a **Layer-3 output screen** in `server.py` (`crosses_line` / `SAFE_REDIRECT`) that catches real-money directives.

## 7. Success metrics

Demo: the 20-second segment works unrehearsed. **Needs great UI/UX.**

Product: time-to-first-agent < 2 min for user.

No fires. Out-of-scope asks handled without dead-ends or risky replies.

## 8. Open questions (for us to resolve in this doc)

1. Clarifying-question pattern vs. straight-to-build — which makes the 2–3 exchange budget? (Code currently leans build-with-defaults.)
2. **[adjusted]** Starter suggestions v1: keep the current adaptive chip strip, or add a fixed 10–12 starter grid on first load? And what record do we show per agent (backtest grade only vs. competition record) given Gen-2 timing?
3. Chat modal design — full takeover vs. expandable panel (fold in designer feedback).
4. Where does the Coach live post-creation (agent page? competition page? everywhere?) in v1?
5. Model eval: what's the pass bar for the production model (currently Groq `llama-3.3-70b`, DeepSeek as candidate)? Suggest: archetype/config-selection accuracy + zero out-of-schema configs (validator already enforces this) + tone check on 20 scripted conversations.
6. **[new]** Do we build the daily market summary (`get_market_summary` + daily pull) for v1, or leave it as a stated non-goal? (Not built today.)

## 9. Next steps

- [ ] Further refinement of this PRD2
- [ ] Implementation scope needed (esp. items flagged **[not built]**: market summary, horizon badge, fixed starter grid)
- [ ] Timeline planned and locked

## 10. PRD-term → code-artifact map (reference)

| PRD term | Actual artifact in `Coach Roostoo v2` | Status |
| --- | --- | --- |
| `emit_config` tool | `coach_compiler/schema.py` → `build_emit_config_tool()` | ✅ exists |
| `list_templates` tool | none; 5 **signal families** + 21 **strategy variants** in `schema.py` (`SIGNAL_FAMILIES`, `VARIANTS`, `FAMILY_DEFAULTS`, `default_config_for`) | ❌ not a tool |
| `run_backtest` tool | frontend `public/assets/sim-engine.js` (`window.RoostooSim`) + `/api/launch` staging | ❌ not an LLM tool |
| `get_market_summary` tool | none — no live market feed | ❌ not built |
| RAG corpus | `coach_compiler/cards/*.md` (13 cards) via `knowledge.retrieve()` + `retrieve` tool | ✅ exists |
| "Config card" | **gene card** — `coach_compiler/genecard.py`, `geneCardHtml` in `app.js` | ✅ (renamed) |
| Model = DeepSeek | Groq `llama-3.3-70b-versatile` (`server.py`); DeepSeek is a drop-in candidate | ⚠️ candidate, not current |
| Prompt "templates" on load | suggestion chips — `CHIPS` / `SUGGEST_POOL` in `app.js` | ✅ (different shape) |
| Create/Explain routing | `orchestrator.run_coach` → `run_create` / `run_explain` | ✅ exists |
| Backend endpoints | web: `/api/compile`, `/api/launch`; Go: `/api/coach`; + `mcp_server/` | ✅ exists |
| Output guardrail | `server.py` `crosses_line()` / `SAFE_REDIRECT` (Layer 3) | ✅ exists |
| Stop-loss disclaimer | **no such knob** — exits/sizing are learned by PPO; the reward metric is the risk lever. Validator actively **rejects** `stop_loss`/`take_profit`/`max_trade`/`min_trade`. Overfit framing in `orchestrator`/`prompt` | ⚠️ reframed |
| Signal family + variant | `schema.VARIANTS` (21) / `FAMILY_VARIANTS`; stored config fields, shown on the gene card | ✅ exists |
| Horizon badge UI | framing exists in prose; no distinct badge element | ⚠️ partial |
| Multi-agent fan-out | `emit_config.agents` (legacy `variants` still accepted) + `schema.expand_configs` | ✅ exists |
| Go-backend action tools | `create_trading_agent`, `join_competition`, `get_my_portfolio` | ✅ exists (separate from compiler tools) |
