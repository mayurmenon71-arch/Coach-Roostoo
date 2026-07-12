"""
The Create-mode loop (Section 7.1, stages 1-4 + 6):

    classify -> elicit -> compile (emit_config) -> validate + breakeven
    -> gene card, max 2 repair rounds.

The LLM is a translator inside this loop, never a validator: every
emit_config lands in deterministic Python (validator + breakeven screen +
platform locks) and the model only sees the machine-readable verdict.

run_create(messages) is stateless — the frontend sends the whole
conversation each time, exactly like the existing /api/coach contract.
"""

import json
import re

from . import schema as S
from .genecard import build_gene_card
from .knowledge import retrieve
from .prompt import create_mode_prompt, explain_prompt
from .validator import validate_config

MAX_MODEL_CALLS = 6   # hard ceiling per request
MAX_REPAIR_ROUNDS = 2  # per Section 8.3 WORKFLOW step 4

# ── Cheap intent router: Q&A vs build ────────────────────────────────────────
# A pure question goes to the lean, tool-less Explain path (one small call).
# Anything that describes/asks to build an agent — or any conversation that has
# already started building — goes to the heavy Create path (tool schema +
# exemplars + possible repair rounds). This keeps everyday questions cheap.
_BUILD_RE = re.compile(
    r"\b(build|make me|make a|create|generate|set (me )?up|spin up|design|"
    r"configure|i want (a|an|to build|to make)|i'?d like (a|an)|give me (a|an)|"
    r"an agent that|a bot that|something that)\b", re.I)
_STRATEGY_RE = re.compile(
    r"\b(ride|rides|riding|buy (the )?dip|buy dips|dip.?buyer|fade|fades|pounce|"
    r"scalp|scalper|momentum|mean.?revert|breakout|trend.?follow|panic)\b", re.I)
_QSTART_RE = re.compile(
    r"^\s*(what|whats|what's|why|how|hows|how's|which|when|who|whose|whom|where|"
    r"does|do|did|is|are|am|was|were|can|could|would|should|will|explain|define|"
    r"describe|tell me|help me understand|difference between|compare)\b", re.I)


def is_question(text):
    """Conservative: only treat clearly-interrogative, non-build text as a
    question. Build verbs / strategy descriptions are never questions, so the
    build path is never starved by a misread."""
    t = (text or "").strip()
    if _BUILD_RE.search(t) or _STRATEGY_RE.search(t):
        return False
    return bool(t.endswith("?") or _QSTART_RE.match(t))


def _wants_build(messages):
    """A conversation is a build conversation if ANY user turn is not a pure
    question (a build intent, or an elicitation answer mid-build)."""
    user = [m for m in messages
            if m.get("role") == "user" and m.get("content")]
    if not user:
        return False
    return any(not is_question(m["content"]) for m in user)


# Per-archetype honest trade-off note, appended when the gene card is returned.
# Templated (not a second LLM call) to keep a compile to a single round-trip.
# Short, plain-language trade-off note per personality (no jargon, no math).
_ARCHETYPE_NOTE = {
    "intraday_momentum": "Expect flat, patient stretches in range-bound markets "
        "— that's the trade-off for not chasing every wiggle.",
    "mean_reversion": "By design it struggles in strong one-way trends — it's "
        "betting on bounces, not chasing breakdowns.",
    "breakout": "Real breakouts are rare, so it trades seldom and takes small "
        "losses on false starts to catch the occasional big move.",
    "flow_driven": "Those spikes are rare, so it sits quiet between events — its "
        "live track record matters more than any single backtest.",
}


def _closing_note(card):
    arch = (card.get("classification") or {}).get("archetype")
    parts = ["Here's **%s** — %s."
             % (card.get("name"), card.get("blurb", "your agent"))]
    note = _ARCHETYPE_NOTE.get(arch)
    if note:
        parts.append(note)
    parts.append("A strong backtest can overfit, so treat this as a starting "
                 "point — the live arena on unseen data is the real test.")
    return " ".join(parts)


def _tool_result(call_id, name, payload):
    return {
        "role": "tool",
        "tool_call_id": call_id,
        "name": name,
        "content": json.dumps(payload),
    }


def run_create(messages, llm=None, ui_context=None):
    """Run one unified Coach turn (answers questions OR compiles an agent).

    Args:
        messages: [{"role": "user"|"assistant", "content": str}, ...] —
                  the conversation so far (no system message; we own that).
        llm:      injectable chat function (tests pass a fake); defaults to
                  llm_client.call_chat.
        ui_context: optional plain-text snapshot of the user's current Strategy
                  Lab config, so "my agent" questions are grounded.

    Returns one of:
        {"type": "chat",      "text": str}                       # elicitation / explanation
        {"type": "gene_card", "card": {...}, "text": str}        # compiled + validated
        {"type": "error",     "text": str, "errors": [...]}      # repair rounds exhausted
    """
    if llm is None:
        from .llm_client import call_chat as llm

    convo = [{"role": "system", "content": create_mode_prompt(ui_context)}]
    convo.extend({"role": m["role"], "content": m["content"]}
                 for m in messages
                 if m.get("role") in ("user", "assistant") and m.get("content"))

    tools = S.all_tools()
    repair_rounds = 0
    pending_card = None
    last_errors = []

    for _ in range(MAX_MODEL_CALLS):
        reply = llm(convo, tools=tools)
        content = (reply.get("content") or "").strip()
        tool_calls = reply.get("tool_calls") or []

        if not tool_calls:
            # Plain assistant turn: elicitation questions, an explanation, or
            # the gene-card narration if a card is already validated.
            if pending_card is not None:
                return {"type": "gene_card", "card": pending_card,
                        "text": content or "Here is your agent's gene card."}
            return {"type": "chat", "text": content or "(no response)"}

        # Echo the assistant turn (with its tool calls) into the transcript.
        convo.append({"role": "assistant", "content": reply.get("content"),
                      "tool_calls": tool_calls})

        for tc in tool_calls:
            fn = tc.get("function", {})
            name = fn.get("name")
            call_id = tc.get("id", "call_0")
            try:
                args = json.loads(fn.get("arguments") or "{}")
            except ValueError:
                convo.append(_tool_result(call_id, name or "unknown",
                                          {"error": "arguments were not valid JSON"}))
                continue

            if name == "retrieve":
                convo.append(_tool_result(call_id, name, {
                    "cards": retrieve(args.get("query", ""), args.get("k", 3)),
                }))

            elif name == "emit_config":
                config = args.get("config") or {}
                rationale = args.get("rationale") or {}
                classification = args.get("classification") or {}
                verdict = validate_config(config)
                last_errors = verdict["errors"]

                if verdict["valid"]:
                    card = build_gene_card(
                        verdict["config"], rationale, classification,
                        verdict["warnings"],
                    )
                    # Return the gene card immediately with a templated closing
                    # note. The card already carries every value + its rationale,
                    # so a second LLM call just to narrate is redundant — and on
                    # rate-limited tiers that extra round-trip is what tips a
                    # compile over the per-minute token budget.
                    return {"type": "gene_card", "card": card,
                            "text": _closing_note(card)}
                else:
                    repair_rounds += 1
                    if repair_rounds > MAX_REPAIR_ROUNDS:
                        return {
                            "type": "error",
                            "text": ("I couldn't produce a valid config after "
                                     "%d repair attempts. The remaining issues: %s"
                                     % (MAX_REPAIR_ROUNDS, "; ".join(
                                         "%s — %s" % (e["path"], e["message"])
                                         for e in verdict["errors"][:5]))),
                            "errors": verdict["errors"],
                        }
                    convo.append(_tool_result(call_id, name, {
                        "valid": False,
                        "errors": verdict["errors"],
                        "repair_round": repair_rounds,
                        "next": ("Rejected by the deterministic validator. "
                                 "Explain the rejection in plain language, then "
                                 "re-emit the nearest valid config. Round %d of %d."
                                 % (repair_rounds, MAX_REPAIR_ROUNDS)),
                    }))

            else:
                convo.append(_tool_result(call_id, name or "unknown",
                                          {"error": "unknown tool"}))

    # Model-call budget exhausted.
    if pending_card is not None:
        return {"type": "gene_card", "card": pending_card,
                "text": "Here is your agent's gene card."}
    return {"type": "error",
            "text": "The compiler ran out of turns before producing a valid config.",
            "errors": last_errors}


def run_explain(messages, llm=None, ui_context=None):
    """Lightweight Q&A path: one tool-less call with a lean prompt. No
    emit_config schema, no few-shot exemplars — a fraction of the tokens of the
    build path, so questions stay cheap. Returns {"type": "chat", "text": ...}."""
    if llm is None:
        from .llm_client import call_chat as llm
    convo = [{"role": "system", "content": explain_prompt(ui_context)}]
    # A short tail is enough context for follow-up questions; keeping it small
    # is the whole point of this path.
    tail = [{"role": m["role"], "content": m["content"]}
            for m in messages
            if m.get("role") in ("user", "assistant") and m.get("content")][-4:]
    convo.extend(tail)
    reply = llm(convo)  # NO tools -> guaranteed single call
    return {"type": "chat",
            "text": (reply.get("content") or "").strip() or "(no response)"}


def run_coach(messages, llm=None, ui_context=None):
    """Unified entry point. Routes pure-question conversations to the cheap
    Explain path and anything build-related to the full Create path."""
    if _wants_build(messages):
        return run_create(messages, llm=llm, ui_context=ui_context)
    return run_explain(messages, llm=llm, ui_context=ui_context)
