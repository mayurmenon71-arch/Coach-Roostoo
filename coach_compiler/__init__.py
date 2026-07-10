"""
Coach Roostoo intent compiler — "Rules to Rewards" (v1.2) implementation.

The LLM translates, RL learns, the arena proves. This package is the
translation layer: a compiler from conversational intent to a validated
agent config ("gene card"). The LLM selects values inside a typed schema;
everything load-bearing (validation, breakeven math, platform locks) is
plain deterministic Python.

Modules
  schema.py       Step 1 — full parameter set, governance tiers, tool defs
  breakeven.py    Step 2 — the fee-hurdle calculator (the gate that matters)
  validator.py    Step 2 — deterministic range / coherence / archetype checks
  knowledge.py    Step 2 — retrieve() over the versioned knowledge cards
  prompt.py       Step 3 — the Create-mode system prompt (Section 8.3)
  exemplars.py    Step 5 — few-shot worked examples + negative exemplars
  genecard.py     Step 6 — config + rationale + tiers -> renderable gene card
  orchestrator.py the Create loop: classify -> elicit -> emit -> validate -> card
  llm_client.py   OpenAI-compatible chat call with tools (stdlib urllib)
"""

__version__ = "0.1.0"
