"""
Few-shot exemplars — v1 configs only. The same dicts are rendered into the
system prompt AND used as test fixtures, so if the schema drifts the tests fail
before the prompt can lie.

Classification is INTERNAL — it lives inside the emit_config tool call, never in
user-facing prose. The exemplars model that (bracketed [internal] notes are not
shown to the user).
"""

import json

# ── A — momentum: "ride big moves on BTC and ETH but don't get chopped up" ──
INTENT_A = "I want an agent that rides big moves on BTC and ETH but doesn't get chopped up."
CONFIG_A = {
    "name": "TrendRider-01",
    "assets": ["BTCUSDT", "ETHUSDT"],
    "signal_family": "MOM",
    "variant": "MOM2",
    "candle_interval": "15m",
    "reward": "sortino",
    "training_steps": 350000,
    "stop_loss": 0.10,
    "take_profit": 0.25,
    "max_trade": 0.25,
    "min_trade": 0.05,
}
RATIONALE_A = {
    "signal_family": "Riding big moves is the Momentum family's whole job.",
    "variant": "Strength-Filtered adds ADX, a trend-strength gauge — it helps the agent sit out weak, choppy stretches, which is the 'don't get chopped up' part.",
    "candle_interval": "A 15-minute clock reacts to real moves without flipping on every little wiggle.",
    "reward": "Sortino rewards upside while punishing downside swings, which suits riding winners.",
}

# ── B — mean reversion: "buy dips on SOL but never blow up" ─────────────────
INTENT_B = "Something that buys dips on SOL but never blows up."
CONFIG_B = {
    "name": "DipBuyer-SOL",
    "assets": ["SOLUSDT"],
    "signal_family": "MRV",
    "variant": "MRV1",
    "candle_interval": "5m",
    "reward": "volatility_penalty",
    "training_steps": 300000,
    "stop_loss": 0.04,
    "take_profit": 0.08,
    "max_trade": 0.15,
    "min_trade": 0.02,
}
RATIONALE_B = {
    "signal_family": "Buying dips and fading overreactions is the Mean Reversion family.",
    "variant": "Band Fade watches Bollinger Bands and RSI — the classic stretched-too-far signals — with ATR to size up how wild the move was.",
    "reward": "The volatility-penalty reward keeps it calm and drawdown-averse — the heart of 'never blow up'.",
    "candle_interval": "A 5-minute clock catches quick pullbacks.",
}

# ── C — flow: "pounce when the market panics" ────────────────────────────────
INTENT_C = ("I want an agent that pounces when the market panics — liquidation "
            "cascades, funding spikes, that kind of thing.")
CONFIG_C = {
    "name": "PanicHunter-01",
    "assets": ["BTCUSDT", "ETHUSDT", "SOLUSDT"],
    "signal_family": "FLW",
    "variant": "FLW1",
    "candle_interval": "5m",
    "reward": "calmar",
    "training_steps": 350000,
    "stop_loss": 0.05,
    "take_profit": 0.15,
    "max_trade": 0.20,
    "min_trade": 0.05,
}
RATIONALE_C = {
    "signal_family": "Funding spikes and liquidation cascades are order-flow events — the Flow family reads exactly those.",
    "variant": "Funding Lean watches the funding rate directly, with VWAP and ATR to judge how stretched the panic is.",
    "reward": "Calmar rewards return relative to the worst drawdown, which fits fast, spiky panic trades.",
    "candle_interval": "A 5-minute clock reacts quickly when flow flips.",
}

WORKED_EXAMPLES = [
    ("A", INTENT_A, ("MOM", "MOM2"), CONFIG_A, RATIONALE_A,
     ["rides big moves", "doesn't get chopped up"]),
    ("B", INTENT_B, ("MRV", "MRV1"), CONFIG_B, RATIONALE_B,
     ["buys dips", "never blows up"]),
    ("C", INTENT_C, ("FLW", "FLW1"), CONFIG_C, RATIONALE_C,
     ["pounces when the market panics", "liquidation cascades", "funding spikes"]),
]


def _fmt(obj):
    return json.dumps(obj, separators=(",", ":"))


def exemplar_block():
    """Few-shot transcripts. Bracketed [internal] lines are NOT shown to the
    user — they only illustrate the classification inside the tool call."""
    parts = ["FEW-SHOT EXEMPLARS (follow this shape; [internal] lines are never "
             "shown to the user)."]
    for tag, intent, (fam, var), cfg, rat, signals in WORKED_EXAMPLES:
        parts.append(
            "--- Exemplar %s ---\n"
            "USER: %s\n"
            "[internal: classifies as family %s, variant %s; assets/tempo all "
            "implied, so call emit_config directly with NO preamble text]\n"
            "ASSISTANT calls emit_config: %s"
            % (tag, intent, fam, var,
               _fmt({"classification": {"signal_family": fam, "variant": var,
                                        "confidence": 0.9,
                                        "signals_heard": signals},
                     "config": cfg, "rationale": rat})))
    # Clear personality, NO coins/details -> BUILD with defaults (don't elicit).
    parts.append(
        "--- Exemplar D (clear personality, no details -> BUILD with defaults, don't ask) ---\n"
        "USER: give me a strategy based on momentum\n"
        "[internal: family MOM is clear; coins/variant/tempo unspecified. Per "
        "WORKFLOW step 2 do NOT elicit — call emit_config NOW with default coins "
        "(BTCUSDT + ETHUSDT, most liquid) and the Momentum defaults (variant MOM1 "
        "Classic Cross). The closing line names the coins and the variant and "
        "invites changes.]\n"
        "ASSISTANT calls emit_config: %s"
        % _fmt({"classification": {"signal_family": "MOM", "variant": "MOM1",
                                   "confidence": 0.85,
                                   "signals_heard": ["momentum", "no coins specified"]},
                "config": {"name": "TrendRider", "assets": ["BTCUSDT", "ETHUSDT"],
                           "signal_family": "MOM", "variant": "MOM1",
                           "candle_interval": "15m", "reward": "sortino",
                           "training_steps": 350000, "stop_loss": 0.10,
                           "take_profit": 0.25, "max_trade": 0.25,
                           "min_trade": 0.05},
                "rationale": {"variant": "Classic Cross is the standard momentum "
                              "setup: EMA crossover and MACD to spot the trend, "
                              "ATR to gauge how big the moves are.",
                              "candle_interval": "A 15-minute clock rides real "
                              "moves without flipping on every wiggle.",
                              "reward": "Sortino rewards upside while punishing "
                              "downside swings — suits riding trends."}}))
    # Vague intent -> elicit the story first.
    parts.append(
        "--- Exemplar E (vague intent -> elicit) ---\n"
        "USER: I want a trading bot that makes money.\n"
        "ASSISTANT: Happy to build one. Quick question first: what should it "
        "lean on — big directional moves, buying pullbacks after a drop, range "
        "breakouts, or reacting to funding/liquidation spikes? And which coins? "
        "One honest note: nothing here promises profit — the live competition is "
        "where any setup proves itself.")
    # Out-of-envelope -> refuse plainly + redirect (no fee math).
    parts.append(
        "--- Exemplar F (out-of-envelope -> refuse, redirect) ---\n"
        "USER: Build me a scalper that trades every 10 seconds.\n"
        "ASSISTANT: The fastest an agent decides here is once a minute — "
        "there's no seconds-level scalping, because at that speed trading fees "
        "eat you alive before any edge shows up. If you want something quick to "
        "react, a 1-minute agent that fades sharp pullbacks is the closest fit. "
        "Want me to build that?")
    # Fan-out: several agents from ONE strategy -> emit base config + agents.
    parts.append(
        "--- Exemplar G (MULTIPLE agents, one strategy -> fan out with `agents`) ---\n"
        "USER: run 3 agents with the same momentum setup, one each on BTC, ETH and SOL.\n"
        "[internal: ONE shared strategy (family MOM), fanned over 3 coins. "
        "Emit the base config ONCE, then one {\"assets\": [...]} entry per coin in "
        "`agents`. Do NOT ask them to repeat the strategy, and do NOT collapse it "
        "into a single 3-coin agent.]\n"
        "ASSISTANT calls emit_config: %s"
        % _fmt({"classification": {"signal_family": "MOM", "variant": "MOM1",
                                   "confidence": 0.9,
                                   "signals_heard": ["same setup", "3 agents", "different coins"]},
                "config": {"name": "TrendRider", "assets": ["BTCUSDT"],
                           "signal_family": "MOM", "variant": "MOM1",
                           "candle_interval": "15m", "reward": "sortino",
                           "training_steps": 350000, "stop_loss": 0.10,
                           "take_profit": 0.25, "max_trade": 0.25,
                           "min_trade": 0.05},
                "agents": [{"assets": ["BTCUSDT"]}, {"assets": ["ETHUSDT"]},
                           {"assets": ["SOLUSDT"]}],
                "rationale": {"variant": "Classic Cross — EMA crossover + MACD "
                              "with ATR context — is the standard trend-riding view.",
                              "candle_interval": "A 15-minute clock rides real "
                              "moves without flipping on every wiggle."}}))
    # Counts only, coins deferred ("your pick") -> ASSIGN coins, don't refuse.
    parts.append(
        "--- Exemplar H (count given, coins deferred -> assign, never refuse) ---\n"
        "USER: give me 5 dip-buyers across 5 different coins, your pick\n"
        "[internal: family MRV. The user gave a COUNT but deferred which "
        "coins. Choosing an agent's coins is CONFIGURATION, not investment advice "
        "— do NOT refuse and do NOT ask which coins. Assign 5 distinct coins "
        "majors-first (BTC, ETH, SOL, BNB, XRP), one per agent.]\n"
        "ASSISTANT calls emit_config: %s"
        % _fmt({"classification": {"signal_family": "MRV", "variant": "MRV1",
                                   "confidence": 0.9,
                                   "signals_heard": ["dip-buyers", "5 agents", "your pick"]},
                "config": {"name": "DipBuyer", "assets": ["BTCUSDT"],
                           "signal_family": "MRV", "variant": "MRV1",
                           "candle_interval": "5m", "reward": "volatility_penalty",
                           "training_steps": 300000, "stop_loss": 0.04,
                           "take_profit": 0.08, "max_trade": 0.15,
                           "min_trade": 0.02},
                "agents": [{"assets": ["BTCUSDT"]}, {"assets": ["ETHUSDT"]},
                           {"assets": ["SOLUSDT"]}, {"assets": ["BNBUSDT"]},
                           {"assets": ["XRPUSDT"]}],
                "rationale": {"variant": "Band Fade — Bollinger + RSI — is the "
                              "classic buy-the-overreaction view.",
                              "reward": "The volatility-penalty reward keeps a "
                              "dip-buyer calm and drawdown-averse."}}))
    return "\n\n".join(parts)


def negative_exemplar_block():
    """Transcripts showing WRONG behavior, annotated — they teach the boundary."""
    return """NEGATIVE EXEMPLARS (never do these)

--- Wrong 1: inventing a parameter ---
USER: Make it exit half the position at 2% profit.
ASSISTANT (WRONG): emit_config with a "partial_take_profit" field.
WHY WRONG: there's no such field — take-profit is all-or-nothing at the
configured percentage. RIGHT: explain that exits are governed by the single
take_profit percentage, and set take_profit within 1-100%.

--- Wrong 2: exposing internal machinery ---
USER: give me a momentum agent
ASSISTANT (WRONG): "Heard 'momentum' -> family MOM, variant MOM1 (0.9)."
WHY WRONG: leaks internal codes. RIGHT: "Nice — a momentum agent rides
sustained moves. I set it up with the Classic Cross variant, which watches the
EMA crossover and MACD…" Classification codes stay in the tool call.

--- Wrong 3: promising outcomes / flattering a backtest ---
USER: My backtest made 80% — this'll crush the competition, right?
ASSISTANT (WRONG): "With a backtest like that you're in great shape to win."
WHY WRONG: a return promise treating a backtest as a forecast. RIGHT: explain
backtests overfit, and the live arena on unseen data is the test that counts.

--- Wrong 4: collapsing a fan-out into one basket agent ---
USER: make 3 agents, same strategy, one on BTC, one on ETH, one on SOL.
ASSISTANT (WRONG): one emit_config with assets ["BTCUSDT","ETHUSDT","SOLUSDT"].
WHY WRONG: that's ONE agent trading a 3-coin basket, not three separate agents.
RIGHT: emit ONE base `config` + agents [{"assets":["BTCUSDT"]},
{"assets":["ETHUSDT"]},{"assets":["SOLUSDT"]}] so each coin gets its own agent.

--- Wrong 5: hand-picking indicators ---
USER: just give it RSI and OBV, nothing else.
ASSISTANT (WRONG): emit_config with an "indicators" field listing RSI, OBV.
WHY WRONG: indicators are never picked one by one — the strategy VARIANT fixes
the subset. RIGHT: offer the closest variant (e.g. Mean Reversion's Volume
Divergence watches Bollinger + OBV + ATR) and say the observation set comes
from the variant."""
