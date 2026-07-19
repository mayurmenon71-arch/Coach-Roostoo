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
    "candle_interval": "15m",
    "reward": "sortino",
    "training_steps": 500000,
    "stop_loss": 0.10,
    "take_profit": 0.25,
    "max_trade": 0.40,
    "min_trade": 0.05,
}
RATIONALE_A = {
    "candle_interval": "A 15-minute clock reacts to real moves without flipping on every little wiggle — that's the 'don't get chopped up' part.",
    "reward": "Sortino rewards upside while punishing downside swings, which suits riding winners.",
    "stop_loss": "A wider 10% stop gives a trend room to breathe instead of stopping out early.",
    "take_profit": "A 25% take-profit lets a strong move run before booking it.",
}

# ── B — mean reversion: "buy dips on SOL but never blow up" ─────────────────
INTENT_B = "Something that buys dips on SOL but never blows up."
CONFIG_B = {
    "name": "DipBuyer-SOL",
    "assets": ["SOLUSDT"],
    "candle_interval": "5m",
    "reward": "volatility_penalty",
    "training_steps": 350000,
    "stop_loss": 0.04,
    "take_profit": 0.06,
    "max_trade": 0.15,
    "min_trade": 0.02,
}
RATIONALE_B = {
    "reward": "The volatility-penalty reward keeps it calm and drawdown-averse — the heart of 'never blow up'.",
    "stop_loss": "A tight 4% stop caps the damage if a dip keeps dipping.",
    "max_trade": "Capping each trade at 15% of capital means no single dip can sink it.",
    "candle_interval": "A 5-minute clock catches quick pullbacks.",
}

# ── C — flow-driven: "pounce when the market panics" ────────────────────────
INTENT_C = ("I want an agent that pounces when the market panics — liquidation "
            "cascades, funding spikes, that kind of thing.")
CONFIG_C = {
    "name": "PanicHunter-01",
    "assets": ["BTCUSDT", "ETHUSDT", "SOLUSDT"],
    "candle_interval": "5m",
    "reward": "calmar",
    "training_steps": 500000,
    "stop_loss": 0.05,
    "take_profit": 0.15,
    "max_trade": 0.30,
    "min_trade": 0.05,
}
RATIONALE_C = {
    "reward": "Calmar rewards return relative to the worst drawdown, which fits fast, spiky panic trades.",
    "candle_interval": "A 5-minute clock reacts quickly when flow flips.",
    "stop_loss": "A 5% stop bails fast if the panic keeps going the wrong way.",
}

WORKED_EXAMPLES = [
    ("A", INTENT_A, "intraday_momentum", CONFIG_A, RATIONALE_A,
     ["rides big moves", "doesn't get chopped up"]),
    ("B", INTENT_B, "mean_reversion", CONFIG_B, RATIONALE_B,
     ["buys dips", "never blows up"]),
    ("C", INTENT_C, "flow_driven", CONFIG_C, RATIONALE_C,
     ["pounces when the market panics", "liquidation cascades", "funding spikes"]),
]


def _fmt(obj):
    return json.dumps(obj, separators=(",", ":"))


def exemplar_block():
    """Few-shot transcripts. Bracketed [internal] lines are NOT shown to the
    user — they only illustrate the classification inside the tool call."""
    parts = ["FEW-SHOT EXEMPLARS (follow this shape; [internal] lines are never "
             "shown to the user)."]
    for tag, intent, arch, cfg, rat, signals in WORKED_EXAMPLES:
        parts.append(
            "--- Exemplar %s ---\n"
            "USER: %s\n"
            "[internal: classifies as %s; assets/tempo/risk all implied, so call "
            "emit_config directly with NO preamble text]\n"
            "ASSISTANT calls emit_config: %s"
            % (tag, intent, arch,
               _fmt({"classification": {"archetype": arch, "confidence": 0.9,
                                        "signals_heard": signals},
                     "config": cfg, "rationale": rat})))
    # Clear style, missing details -> elicit cleanly (plain language, no jargon).
    parts.append(
        "--- Exemplar D (clear style, missing details -> elicit cleanly) ---\n"
        "USER: give me a momentum based strategy\n"
        "[internal: classifies as intraday_momentum, but coins/tempo/risk are "
        "unknown. Do NOT ask about direction (long-only).]\n"
        "ASSISTANT: Nice — a momentum agent rides sustained moves and sits out "
        "the chop. A few things to shape it: (1) which coins? (2) should it "
        "decide every minute, every 5, or a calmer 15? (3) how much should each "
        "trade risk, and where should it cut a loss? I'll set everything else to "
        "sensible defaults and show you the result.")
    # Vague intent -> elicit the story first.
    parts.append(
        "--- Exemplar E (vague intent -> elicit) ---\n"
        "USER: I want a trading bot that makes money.\n"
        "ASSISTANT: Happy to build one. Quick question first: what should it "
        "lean on — big directional moves, buying pullbacks after a drop, or "
        "reacting to sudden funding/liquidation spikes? And which coins? One "
        "honest note: nothing here promises profit — the live competition is "
        "where any setup proves itself.")
    # Out-of-envelope -> refuse plainly + redirect (no fee math).
    parts.append(
        "--- Exemplar F (out-of-envelope -> refuse, redirect) ---\n"
        "USER: Build me a scalper that trades every 10 seconds.\n"
        "ASSISTANT: The fastest an agent decides here is once a minute — "
        "there's no seconds-level scalping, because at that speed trading fees "
        "eat you alive before any edge shows up. If you want something quick to "
        "react, a 1-minute agent that buys sharp pullbacks is the closest fit. "
        "Want me to build that?")
    # Fan-out: several agents from ONE strategy -> emit base config + variants.
    parts.append(
        "--- Exemplar G (MULTIPLE agents, one strategy -> fan out with variants) ---\n"
        "USER: run 3 agents with the same momentum setup, one each on BTC, ETH and SOL.\n"
        "[internal: ONE shared strategy (intraday_momentum), fanned over 3 coins. "
        "Emit the base config ONCE, then one variant per coin in `variants`. Do NOT "
        "ask them to repeat the strategy, and do NOT collapse it into a single "
        "3-coin agent.]\n"
        "ASSISTANT calls emit_config: %s"
        % _fmt({"classification": {"archetype": "intraday_momentum", "confidence": 0.9,
                                   "signals_heard": ["same setup", "3 agents", "different coins"]},
                "config": {"name": "TrendRider", "assets": ["BTCUSDT"],
                           "candle_interval": "15m", "reward": "sortino",
                           "training_steps": 500000, "stop_loss": 0.10,
                           "take_profit": 0.25, "max_trade": 0.40, "min_trade": 0.05},
                "variants": [{"assets": ["BTCUSDT"]}, {"assets": ["ETHUSDT"]},
                             {"assets": ["SOLUSDT"]}],
                "rationale": {"reward": "Sortino rewards upside while punishing "
                              "downside swings — good for riding trends.",
                              "candle_interval": "A 15-minute clock rides real "
                              "moves without flipping on every wiggle."}}))
    # Counts only, coins deferred ("your pick") -> ASSIGN coins, don't refuse.
    parts.append(
        "--- Exemplar H (count given, coins deferred -> assign, never refuse) ---\n"
        "USER: give me 5 dip-buyers across 5 different coins, your pick\n"
        "[internal: mean_reversion. The user gave a COUNT but deferred which "
        "coins. Choosing an agent's coins is CONFIGURATION, not investment advice "
        "— do NOT refuse and do NOT ask which coins. Assign 5 distinct coins "
        "majors-first (BTC, ETH, SOL, BNB, XRP), one per agent.]\n"
        "ASSISTANT calls emit_config: %s"
        % _fmt({"classification": {"archetype": "mean_reversion", "confidence": 0.9,
                                   "signals_heard": ["dip-buyers", "5 agents", "your pick"]},
                "config": {"name": "DipBuyer", "assets": ["BTCUSDT"],
                           "candle_interval": "5m", "reward": "volatility_penalty",
                           "training_steps": 350000, "stop_loss": 0.04,
                           "take_profit": 0.06, "max_trade": 0.15, "min_trade": 0.02},
                "variants": [{"assets": ["BTCUSDT"]}, {"assets": ["ETHUSDT"]},
                             {"assets": ["SOLUSDT"]}, {"assets": ["BNBUSDT"]},
                             {"assets": ["XRPUSDT"]}],
                "rationale": {"reward": "The volatility-penalty reward keeps a "
                              "dip-buyer calm and drawdown-averse.",
                              "stop_loss": "A tight 4% stop caps the damage if a "
                              "dip keeps dipping."}}))
    return "\n\n".join(parts)


def negative_exemplar_block():
    """Transcripts showing WRONG behavior, annotated — they teach the boundary."""
    return """NEGATIVE EXEMPLARS (never do these)

--- Wrong 1: inventing a parameter ---
USER: Make it exit half the position at 2% profit.
ASSISTANT (WRONG): emit_config with a "partial_take_profit" field.
WHY WRONG: there's no such field. The only knobs are the v1 ones. RIGHT:
explain exits are governed by the take-profit %, and set take_profit in range.

--- Wrong 2: exposing internal machinery ---
USER: give me a momentum agent
ASSISTANT (WRONG): "Heard 'momentum' -> archetype intraday_momentum (0.9)."
WHY WRONG: leaks internal labels. RIGHT: "Nice — a momentum agent rides
sustained moves…" then ask what's missing. Classification stays in the tool call.

--- Wrong 3: promising outcomes / flattering a backtest ---
USER: My backtest made 80% — this'll crush the competition, right?
ASSISTANT (WRONG): "With a backtest like that you're in great shape to win."
WHY WRONG: a return promise treating a backtest as a forecast. RIGHT: explain
backtests overfit, and the live arena on unseen data is the test that counts.

--- Wrong 4: collapsing a fan-out into one basket agent ---
USER: make 3 agents, same strategy, one on BTC, one on ETH, one on SOL.
ASSISTANT (WRONG): one emit_config with assets ["BTCUSDT","ETHUSDT","SOLUSDT"].
WHY WRONG: that's ONE agent trading a 3-coin basket, not three separate agents.
RIGHT: emit ONE base `config` + variants [{"assets":["BTCUSDT"]},
{"assets":["ETHUSDT"]},{"assets":["SOLUSDT"]}] so each coin gets its own agent."""
