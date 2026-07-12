"""
Coach Roostoo intent compiler — scoped to the v1 parameter registry.

A compiler from conversational intent to a validated v1 agent config ("gene
card"). The LLM selects values inside a typed schema of ONLY the parameters
the platform actually exposes; everything load-bearing (validation, routing)
is plain deterministic Python. The four strategy "personalities" (archetypes)
are an internal classification aid, not stored parameters.

Modules
  schema.py       the v1 parameter registry, governance tiers, tool defs
  validator.py    deterministic range / enum / coherence checks
  knowledge.py    retrieve() over the versioned knowledge cards
  prompt.py       unified Coach prompt (Explain + Create) + lean Explain prompt
  exemplars.py    few-shot worked examples + negative exemplars (v1 configs)
  genecard.py     config + rationale + tiers -> renderable gene card
  orchestrator.py router (run_coach) + the Create loop and the Explain path
  llm_client.py   OpenAI-compatible chat call with tools (stdlib urllib)
"""

__version__ = "0.1.0"
