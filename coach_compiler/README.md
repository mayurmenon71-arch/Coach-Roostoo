# Coach Roostoo — intent compiler

The **Create** mode from *Rules to Rewards* (v1.2): a compiler from
conversational intent to a validated agent config ("gene card"). The LLM
translates, deterministic Python validates, the arena proves.

> **Design invariant:** the LLM *selects* values inside a typed schema; it
> never *authors* validation, math, or platform policy. Everything
> load-bearing is plain deterministic Python, so every config is valid by
> construction or rejected with a reason.

## How it maps to the build order

| Step | File(s) | What it is |
|------|---------|------------|
| 1 — Lock the schema | `schema.py` | Full Section 7.2 parameter set: enums, per-block min/max, **User/Coach/Platform** governance tiers, indicator registry, archetype defaults, and the generated `emit_config` tool. Platform-locked values are hard-coded and stamped by `apply_platform_locks()` — the model never touches them. |
| 2 — The tools | `validator.py`, `breakeven.py`, `knowledge.py` | `validate_config()` (deterministic range/coherence/archetype checks), `breakeven_calc()` (the fee-hurdle gate), `retrieve()` (RAG over `cards/`). |
| 3 — System prompt | `prompt.py` | Section 8.3 Create-mode prompt: ROLE, OPERATING ENVELOPE, strict WORKFLOW, BACKTESTING/NUMBERS policies, REFUSALS. |
| 4 — Elicitation | `prompt.py` (WORKFLOW §2) | The five questions — tempo, risk, direction, story, assets — asked only when unanswered. |
| 5 — Few-shot | `exemplars.py` | The three Section 7.5 worked examples (reasoning-then-tool-call) + vague/out-of-envelope exemplars + 3 negative exemplars. The configs double as test fixtures. |
| 6 — Gene card | `genecard.py`, `orchestrator.py` | The Create loop (classify → elicit → emit → validate+breakeven → gene card, max 2 repair rounds) and the renderable card with per-value rationale + tier badges. |

Supporting: `llm_client.py` (OpenAI-compatible call, stdlib `urllib`, same
env vars as `api/coach.py`), `cards/` (the versioned knowledge corpus),
`__main__.py` (CLI demo).

## Try it

```bash
# Offline — renders the three worked examples through the real validator
# + gene-card renderer, zero model calls:
python3 -m coach_compiler

# Live — needs a provider key (Groq by default, like the rest of the repo):
API_KEY=... python3 -m coach_compiler "buy dips on SOL but never blow up"
```

Served over HTTP by both back ends:

- **Local / Render** (`uvicorn server:app`) → `POST /api/compile`, UI at `/create.html`
- **Vercel** → `api/compile.py` auto-routes to `/api/compile`

Request/response contract (stateless, like `/api/coach`):

```
POST /api/compile { "messages": [ {"role":"user","content":"..."} ] }
  -> { "type": "chat",      "text": ... }              elicitation turn
  -> { "type": "gene_card", "text": ..., "card": {...} } compiled + validated
  -> { "type": "error",     "text": ..., "errors": [...] } repair rounds exhausted
```

## Tests & evals

```bash
# Deterministic core — NO API key required. This is the CI regression gate.
python3 -m unittest tests.test_offline           # 43 tests

# Model-in-the-loop eval sets (Section 8.4) — need API_KEY; skip cleanly without.
API_KEY=... python3 evals/run_evals.py
```

Hard gates (map one-to-one to product disasters): archetype classification
≥95%, slot-level range compliance 100%, zero out-of-schema emissions reaching
the factory, refusal correctness ≥98% on the adversarial set.

## What's intentionally NOT here

Per the tuning ladder (Section 8.5), rungs 1–2 (prompt + few-shot, then
knowledge cards) reach shippable quality on a frontier model. **No
fine-tuning** — that's a cost/latency optimization for after ~5–10k logged
real sessions, and only with this eval suite as a regression gate. There is
also no live market-context or UI-state tool in this build; the prompt's
CONTEXT POLICY tells Coach to say so plainly rather than guess.
