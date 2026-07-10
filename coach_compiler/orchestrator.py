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

from . import schema as S
from .breakeven import breakeven_calc
from .genecard import build_gene_card
from .knowledge import retrieve
from .prompt import create_mode_prompt
from .validator import validate_config

MAX_MODEL_CALLS = 6   # hard ceiling per request
MAX_REPAIR_ROUNDS = 2  # per Section 8.3 WORKFLOW step 4


def _tool_result(call_id, name, payload):
    return {
        "role": "tool",
        "tool_call_id": call_id,
        "name": name,
        "content": json.dumps(payload),
    }


def run_create(messages, llm=None):
    """Run one Create-mode turn.

    Args:
        messages: [{"role": "user"|"assistant", "content": str}, ...] —
                  the conversation so far (no system message; we own that).
        llm:      injectable chat function (tests pass a fake); defaults to
                  llm_client.call_chat.

    Returns one of:
        {"type": "chat",      "text": str}                       # elicitation / explanation
        {"type": "gene_card", "card": {...}, "text": str}        # compiled + validated
        {"type": "error",     "text": str, "errors": [...]}      # repair rounds exhausted
    """
    if llm is None:
        from .llm_client import call_chat as llm

    convo = [{"role": "system", "content": create_mode_prompt()}]
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

            elif name == "breakeven_calc":
                try:
                    convo.append(_tool_result(call_id, name, breakeven_calc(
                        args.get("decision_interval"),
                        args.get("turnover_band_hi", 0),
                    )))
                except (ValueError, KeyError) as e:
                    convo.append(_tool_result(call_id, name, {"error": str(e)}))

            elif name == "emit_config":
                config = args.get("config") or {}
                rationale = args.get("rationale") or {}
                classification = args.get("classification") or {}
                verdict = validate_config(config)
                last_errors = verdict["errors"]

                if verdict["valid"]:
                    pending_card = build_gene_card(
                        verdict["config"], rationale, classification,
                        verdict["breakeven"], verdict["warnings"],
                    )
                    convo.append(_tool_result(call_id, name, {
                        "valid": True,
                        "warnings": verdict["warnings"],
                        "breakeven": verdict["breakeven"],
                        "next": ("Validation passed. Present the gene card now: "
                                 "one short message with the honest trade-off "
                                 "the user chose. Do not call more tools."),
                    }))
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
