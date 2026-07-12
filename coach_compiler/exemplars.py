"""
Step 5 — Few-shot exemplars (Section 7.5 is the seed set; grow to 15-25).

The three worked examples live here as Python dicts so the SAME objects are
(a) rendered into the system prompt as few-shot transcripts,
(b) fixtures for the unit tests, and
(c) golden-set anchors for the evals.
If the schema drifts, the tests fail before the prompt lies.

Exemplars follow reasoning-then-tool-call ordering: the archetype
classification is explicit and auditable BEFORE emit_config. Negative
exemplars show the wrong behavior, annotated with why it is wrong.
"""

import json

# ── Worked example A — Section 7.5-A ─────────────────────────────────────────
INTENT_A = "I want an agent that rides big moves on BTC and ETH but doesn't get chopped up."

CONFIG_A = {
    "identity": {"archetype": "intraday_momentum", "name": "TrendRider-01"},
    "universe": {"assets": ["BTCUSDT", "ETHUSDT"]},
    "cadence": {"decision_interval": "5m"},
    "observation": {
        "feature_families": ["trend", "time"],
        "indicators": [
            {"id": "roc", "windows_bars": [6, 24, 96, 288]},
            {"id": "ema_cross", "fast": 20, "slow": 100},
            {"id": "adx", "window": 14},
            {"id": "atr", "window": 14},
            {"id": "donchian", "window": 144},
        ],
    },
    "reward": {"flavor": "sortino", "lambda_dd": 0.15,
               "turnover_band": [0.02, 0.10], "lambda_band": 0.08,
               "hold_bonus": 0.03, "per_trade_penalty": 0.0008},
    "action": {"range": [0, 1], "band_width": "wide", "min_holding": "4h",
               "max_leverage": 2},
    "risk": {"stop_loss": 0.08, "take_profit": 0.25},
    "training": {"steps": 500000},
}

RATIONALE_A = {
    "cadence.decision_interval": "Big moves play out over hours, so a 5m pulse reacts fast enough without inviting churn.",
    "reward.flavor": "Sortino punishes downside swings only, which fits ride-the-winner payoffs.",
    "reward.turnover_band": "You said 'doesn't get chopped up' — this ceiling implies only a handful of position changes per day.",
    "reward.hold_bonus": "A hold bonus at the top of its range pays the agent for staying with a working trend.",
    "action.band_width": "A wide no-trade band ignores small wiggles instead of trading them.",
    "action.min_holding": "You said 'not chopped up' — a 4h minimum hold makes whipsaw exits impossible.",
}

# ── Worked example B — Section 7.5-B ─────────────────────────────────────────
INTENT_B = "Something that buys dips on SOL but never blows up."

CONFIG_B = {
    "identity": {"archetype": "mean_reversion", "name": "DipBuyer-SOL"},
    "universe": {"assets": ["SOLUSDT"]},
    "cadence": {"decision_interval": "1m"},
    "observation": {
        "feature_families": ["reversion", "flow"],
        "indicators": [
            {"id": "zscore_vwap", "windows": [30, 120]},
            {"id": "boll_pctb", "window": 20, "sigma": 2.0},
            {"id": "rsi", "window": 14},
            {"id": "rvol", "window": 60},
            {"id": "funding_ema", "window": 24},
        ],
    },
    "reward": {"flavor": "sharpe", "lambda_dd": 0.40,
               "turnover_band": [0.05, 0.25], "lambda_band": 0.10,
               "hold_bonus": 0.01, "per_trade_penalty": 0.0010,
               "averaging_down_penalty": 0.05},
    "action": {"range": [0, 0.5], "band_width": "tight", "min_holding": "15m",
               "time_stop": "6h", "max_leverage": 1},
    "risk": {"stop_loss": 0.04, "take_profit": 0.06},
    "training": {"steps": 400000},
}

RATIONALE_B = {
    "reward.lambda_dd": "You said 'never blows up' — drawdown aversion is set to its maximum.",
    "reward.averaging_down_penalty": "Averaging down is how dip-buyers die; adding to losers is explicitly penalized.",
    "action.range": "Long-only and capped at half size: it can buy dips, it cannot lever into a crash.",
    "action.time_stop": "A hard 6h time-stop forces it flat if a dip keeps dipping — no bag-holding.",
    "action.max_leverage": "'Never blows up' means no leverage at all.",
    "risk.stop_loss": "The tightest stop in the library backs up the no-blow-up mandate.",
}

# ── Worked example C — Section 7.5-C ─────────────────────────────────────────
INTENT_C = ("I want an agent that pounces when the market panics — liquidation "
            "cascades, funding spikes, that kind of thing.")

CONFIG_C = {
    "identity": {"archetype": "flow_driven", "name": "PanicHunter-01"},
    "universe": {"assets": ["BTCUSDT", "ETHUSDT", "SOLUSDT"], "max_concurrent": 2},
    "cadence": {"decision_interval": "1m"},
    "observation": {
        "feature_families": ["flow", "reversion", "sentiment"],
        "indicators": [
            {"id": "funding_delta", "window": 8},
            {"id": "oi_delta", "windows": [15, 60]},
            {"id": "liq_cascade_score", "window": 30},
            {"id": "flow_imbalance", "window": 15},
            {"id": "zscore_vwap", "window": 60},
            {"id": "news_risk_llm"},
        ],
    },
    "reward": {"flavor": "cvar", "cvar_alpha": 0.05, "lambda_dd": 0.30,
               "turnover_band": [0.02, 0.15], "lambda_band": 0.10,
               "per_trade_penalty": 0.0010},
    "action": {"range": [0, 0.75], "band_width": "signal_paced",
               "min_holding": "1h", "max_leverage": 2},
    "risk": {"stop_loss": 0.05, "take_profit": 0.15},
    "training": {"steps": 600000, "augmentation": "block_bootstrap"},
}

RATIONALE_C = {
    "reward.flavor": "Panic trades have fat tails in both directions — CVaR optimizes the loss tail explicitly.",
    "action.band_width": "Signal-paced band: the agent effectively trades only when the flow state changes.",
    "action.min_holding": "A 1h lockup stops it from churning inside a single cascade.",
    "training.augmentation": "Cascades are rare, so block-bootstrap augmentation stretches the few real events.",
    "training.steps": "Rare events mean fewer effective samples — more steps fight overfit.",
}

WORKED_EXAMPLES = [
    ("A", INTENT_A, "intraday_momentum", CONFIG_A, RATIONALE_A,
     ["rides big moves", "doesn't get chopped up"],
     "Honest note: momentum agents lose small in chop and win big when the "
     "move runs — expect flat stretches in range-bound markets."),
    ("B", INTENT_B, "mean_reversion", CONFIG_B, RATIONALE_B,
     ["buys dips", "never blows up"],
     "Honest note: this agent will underperform in strong downtrends by "
     "design — that's the trade you just chose. Its 1m cadence passes only "
     "because the turnover band and breakeven screen hold."),
    ("C", INTENT_C, "flow_driven", CONFIG_C, RATIONALE_C,
     ["pounces when the market panics", "liquidation cascades", "funding spikes"],
     "Honest note: cascades are rare, so this agent trains on fewer effective "
     "events and carries higher overfit risk — expect the platform to demand "
     "a longer cross-competition record before taking its stats seriously."),
]


def _fmt(obj):
    return json.dumps(obj, separators=(",", ":"))


def exemplar_block():
    """Render the few-shot transcripts for the system prompt.

    Classification is INTERNAL — it lives inside the emit_config tool call
    (the auditable record) and never in user-facing prose. The exemplars model
    that: no "Heard X -> archetype Y" preambles, no archetype ids on screen.
    """
    parts = ["FEW-SHOT EXEMPLARS (follow this exact shape). Note the bracketed "
             "[internal] lines are NOT shown to the user — they only illustrate "
             "the classification that goes inside the tool call."]
    for tag, intent, arch, cfg, rat, signals, note in WORKED_EXAMPLES:
        parts.append(
            "--- Exemplar %s ---\n"
            "USER: %s\n"
            "[internal: classifies as %s; all five slots implied, so no "
            "elicitation needed — call emit_config directly, with NO preamble "
            "text to the user]\n"
            "ASSISTANT calls emit_config: %s"
            % (tag, intent, arch,
               _fmt({"classification": {"archetype": arch, "confidence": 0.9,
                                        "signals_heard": signals},
                     "config": cfg, "rationale": rat})))
    # Clean-elicitation exemplar — classifiable, but missing slots. Note the
    # reply uses plain language ("a momentum agent") and NEVER the archetype id
    # or a "-> archetype" mapping.
    parts.append(
        "--- Exemplar D (clear style, missing details -> elicit cleanly, no jargon) ---\n"
        "USER: give me a momentum based strategy\n"
        "[internal: classifies as intraday_momentum, but assets/risk are "
        "unknown — ask, don't emit yet. Do NOT ask about direction: the "
        "platform is long-only.]\n"
        "ASSISTANT: Nice — a momentum agent rides sustained moves and sits out "
        "the chop. To shape yours I need a few things: (1) which coins? (2) how "
        "hard should it chase a move — react within a minute, or a calmer "
        "5-15 minute pulse? (3) what's the most it could be down before you'd "
        "want it stopped? Everything else I'll set to sensible defaults and "
        "show you on the gene card.")
    # Vague-intent exemplar — no archetype known yet, elicit the story first.
    parts.append(
        "--- Exemplar E (vague intent -> elicit, do NOT emit yet) ---\n"
        "USER: I want a trading bot that makes money.\n"
        "ASSISTANT: Happy to build one — every agent here is a learned policy "
        "with a personality, so let me pin down three things. (1) What should "
        "it pay attention to — big directional moves, prices snapping back "
        "after overreactions, or market plumbing like funding spikes and "
        "liquidations? (2) What's the most it could be down before you'd want "
        "it stopped? (3) Which assets? One honest note up front: nothing here "
        "promises profit — the live competition arena is where any config "
        "proves itself.")
    # Out-of-envelope exemplar — refusal with numbers + redirect.
    parts.append(
        "--- Exemplar F (out-of-envelope -> refuse with numbers, redirect) ---\n"
        "USER: Build me a scalper that trades every 10 seconds.\n"
        "ASSISTANT calls breakeven_calc: {\"decision_interval\":\"30s\","
        "\"turnover_band_hi\":30}\n"
        "TOOL: {... \"cost_bps_per_day\": 3780, \"passes\": false ...}\n"
        "ASSISTANT: I won't build that one, and here's the honest math: a "
        "position flip costs ~10.5 bps round-trip, so an agent flipping every "
        "few minutes would need to clear ~3,780 bps/day in gross edge — more "
        "edge per minute than well-run funds earn per day — before an "
        "infrastructure latency race retail can't win. The envelope floor is "
        "30s decisions, and speed there buys reaction time, never trade "
        "frequency. If 'fast' is the feeling you want, a mean-reversion or "
        "flow-driven agent at 1m decisions with a strict no-trade band reacts "
        "within a minute without bleeding out in fees. Want me to spec one of "
        "those?")
    return "\n\n".join(parts)


def negative_exemplar_block():
    """2-3 transcripts showing the WRONG behavior, annotated. These teach the
    boundary faster than another positive example would."""
    return """NEGATIVE EXEMPLARS (never do these)

--- Wrong 1: inventing a parameter ---
USER: Make it exit half the position at 2% profit.
ASSISTANT (WRONG): emit_config with {"action":{"partial_take_profit":0.02}}
WHY WRONG: 'partial_take_profit' is not in the schema. The LLM selects from
the registry, it never authors. RIGHT: explain that exits are learned by the
policy within stop/take bounds, and set risk.take_profit inside its range.

--- Wrong 2: mental arithmetic ---
USER: How much do fees eat at 1m cadence?
ASSISTANT (WRONG): "Roughly 15 bps a day, so about 4.5% a month."
WHY WRONG: numbers stated from the model's head. RIGHT: call breakeven_calc
and quote its result verbatim — the validator gates on the same number.

--- Wrong 3: promising outcomes / flattering a backtest ---
USER: My backtest made 80% — this agent is going to crush the competition, right?
ASSISTANT (WRONG): "With a backtest like that you're in great shape to win."
WHY WRONG: return prediction + backtest treated as forecast. RIGHT: the
overfitting clarification (backtest Sharpe predicts live at R^2 < 0.025) plus
the forward-test redirect — the live arena on unseen data is the test that
counts. Deliver it every time, not buried."""
