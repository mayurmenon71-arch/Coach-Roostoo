"""
The v1 parameter registry — the ONLY parameters the platform actually exposes.

Coach compiles user intent into a config over exactly these fields; nothing
else. The four strategy "personalities" (archetypes) are an internal
classification aid — they help interpret intent and pick sensible v1 defaults,
but they are NOT stored parameters and the gene card only ever shows real v1
knobs.

v1 registry (authoritative):
  User-selectable : assets (1-10 of 21), training_steps {300k,350k,500k},
                    reward {sharpe,sortino,calmar,entropy,volatility_penalty},
                    candle_interval {5m,15m}, stop_loss %, take_profit %,
                    max_trade % , min_trade %
  Fixed (platform): PPO policy, continuous action space, 50-candle lookback,
                    full historical training data, the 8-indicator bundle
                    (all trained together, no subset selection)
Long-only for now: no shorting on the platform yet.
"""

# ── Governance tiers (for the gene card badges) ─────────────────────────────
USER = "user"          # a choice the user owns
COACH = "coach"        # inferred from intent within v1 ranges, user can change
PLATFORM = "platform"  # fixed by the platform, not tunable

# ── Fixed architecture (registry: Fixed / not user-selectable) ──────────────
POLICY = "PPO"
ACTION_SPACE = "continuous target position"
LOOKBACK = 50                      # candles in the observation
TRAINING_DATA = "full available history per coin"
FIXED_INDICATORS = ("RSI", "ATR", "VWAP", "MACD", "Stochastic RSI",
                    "EMA Crossover", "Bollinger Bands", "OBV")
LONG_ONLY = True                   # no shorting yet; flip when the platform enables it

# ── Universe (registry: 1-10 of these) ──────────────────────────────────────
SUPPORTED_ASSETS = (
    "AAVE", "ADA", "AVAX", "BNB", "BTC", "DOGE", "DOT", "ETH", "FET", "HBAR",
    "LINK", "LTC", "NEAR", "SHIB", "SOL", "SUI", "TRX", "UNI", "VET", "XLM", "XRP",
)
QUOTE = "USDT"
MIN_ASSETS = 1
MAX_ASSETS = 10
# Fan-out cap: at most this many agents compiled from ONE strategy in a single
# request (e.g. "run an agent per coin"). Keeps a single ask from spawning a
# training job for all 21 coins at once.
MAX_AGENTS_PER_BATCH = 6

# ── User-selectable knobs (discrete sets) ───────────────────────────────────
TRAINING_STEPS = (300000, 350000, 500000)
REWARDS = ("sharpe", "sortino", "calmar", "entropy", "volatility_penalty")
REWARD_LABEL = {
    "sharpe": "Sharpe Ratio", "sortino": "Sortino Ratio",
    "calmar": "Calmar Ratio", "entropy": "Entropy",
    "volatility_penalty": "Volatility Penalty",
}
CANDLE_INTERVALS = ("1m", "5m", "15m")  # 1m added on request (not in the base v1 registry)

# ── Continuous knobs (fraction 0.01-1.00 of position / capital) ─────────────
PCT_BOUNDS = (0.01, 1.00)          # stop_loss, take_profit, max_trade, min_trade

ARCHETYPES = ("intraday_momentum", "mean_reversion", "breakout", "flow_driven")

# Plain-language personality line shown in prose (never the raw id).
ARCHETYPE_BLURB = {
    "intraday_momentum": "a momentum-style agent that rides sustained moves and sits out the chop",
    "mean_reversion": "a mean-reversion agent that buys pullbacks and takes profit as price snaps back",
    "breakout": "a breakout agent that waits for quiet ranges and jumps on the expansion",
    "flow_driven": "a flow-driven agent that reacts to funding swings and liquidation spikes",
}

# Per-archetype v1 DEFAULTS (all within the registry ranges above). These are
# starting points Coach adjusts from the user's words; every one is a real v1
# knob. Percentages are fractions of position/capital.
ARCHETYPE_DEFAULTS = {
    "intraday_momentum": {
        "candle_interval": "15m",          # calmer clock -> fewer whipsaws
        "reward": "sortino",               # rewards upside, punishes downside vol
        "training_steps": 500000,
        "stop_loss": 0.10, "take_profit": 0.25,
        "max_trade": 0.40, "min_trade": 0.05,
    },
    "mean_reversion": {
        "candle_interval": "5m",
        "reward": "volatility_penalty",    # keeps it calm; averse to big swings
        "training_steps": 350000,
        "stop_loss": 0.04, "take_profit": 0.06,
        "max_trade": 0.20, "min_trade": 0.02,
    },
    "breakout": {
        "candle_interval": "15m",
        "reward": "sortino",
        "training_steps": 500000,
        "stop_loss": 0.08, "take_profit": 0.30,
        "max_trade": 0.50, "min_trade": 0.05,
    },
    "flow_driven": {
        "candle_interval": "5m",
        "reward": "calmar",                # return over worst drawdown; tail-aware
        "training_steps": 500000,
        "stop_loss": 0.05, "take_profit": 0.15,
        "max_trade": 0.30, "min_trade": 0.05,
    },
}


def default_config_for(archetype, assets=None, name=None):
    """A schema-valid v1 config built purely from an archetype's defaults."""
    if archetype not in ARCHETYPE_DEFAULTS:
        raise ValueError("unknown archetype: %r" % (archetype,))
    d = ARCHETYPE_DEFAULTS[archetype]
    return {
        "name": name or (archetype.replace("_", "-") + "-agent"),
        "assets": list(assets or ["BTC" + QUOTE]),
        "candle_interval": d["candle_interval"],
        "reward": d["reward"],
        "training_steps": d["training_steps"],
        "stop_loss": d["stop_loss"],
        "take_profit": d["take_profit"],
        "max_trade": d["max_trade"],
        "min_trade": d["min_trade"],
    }


# ── Fan-out: one strategy -> many agents (different coins) ──────────────────

def _asset_suffix(assets):
    """A short, human tag for a coin set, used to auto-name fan-out agents."""
    coins = [a[:-len(QUOTE)] if a.endswith(QUOTE) else a for a in (assets or [])]
    if not coins:
        return ""
    if len(coins) <= 2:
        return "+".join(coins)
    return "+".join(coins[:2]) + "+%d" % (len(coins) - 2)   # e.g. BTC+ETH+1


def expand_configs(base, variants=None):
    """Fan a single base config out into one config per variant.

    Each variant is a partial patch: it inherits every field from `base` and
    overrides only the keys it sets (typically `assets`). With no variants this
    returns ``[base]`` unchanged — so the single-agent path is untouched. When a
    variant doesn't name itself, the agent is auto-named by its coin(s), and
    names are de-duplicated so the roster never shows two identical labels.

    This is the deterministic half of the fan-out: the model authors ONE
    strategy plus the per-agent differences; Python does the cloning, so "same
    strategy across coins" is guaranteed by code, not hoped for from the model.
    """
    base = dict(base or {})
    if not variants:
        return [base]
    out, used = [], set()
    stem = base.get("name") or "agent"
    for i, v in enumerate(variants):
        merged = dict(base)
        merged.update({k: val for k, val in (v or {}).items() if val is not None})
        if not (v or {}).get("name"):
            suffix = _asset_suffix(merged.get("assets")) or str(i + 1)
            merged["name"] = ("%s-%s" % (stem, suffix))[:40]
        base_name, n, name = merged["name"], 2, merged["name"]
        while name in used:
            name = "%s-%d" % (base_name[:37], n)
            n += 1
        merged["name"] = name
        used.add(name)
        out.append(merged)
    return out


# ── emit_config tool: exactly the v1 user-selectable knobs ──────────────────

def _config_field_properties():
    """The v1 config field schemas — shared by emit_config's `config` object AND
    each per-agent `variants` patch, so the two can never drift apart."""
    return {
        "name": {"type": "string", "maxLength": 40},
        "assets": {
            "type": "array",
            "minItems": MIN_ASSETS, "maxItems": MAX_ASSETS,
            "items": {"type": "string",
                      "enum": [a + QUOTE for a in SUPPORTED_ASSETS]},
        },
        "candle_interval": {"type": "string", "enum": list(CANDLE_INTERVALS)},
        "reward": {"type": "string", "enum": list(REWARDS)},
        "training_steps": {"type": "integer", "enum": list(TRAINING_STEPS)},
        "stop_loss": {"type": "number", "minimum": PCT_BOUNDS[0],
                      "maximum": PCT_BOUNDS[1],
                      "description": "fraction of position, 0.01-1.00"},
        "take_profit": {"type": "number", "minimum": PCT_BOUNDS[0],
                        "maximum": PCT_BOUNDS[1]},
        "max_trade": {"type": "number", "minimum": PCT_BOUNDS[0],
                      "maximum": PCT_BOUNDS[1],
                      "description": "max fraction of capital per order"},
        "min_trade": {"type": "number", "minimum": PCT_BOUNDS[0],
                      "maximum": PCT_BOUNDS[1],
                      "description": "min fraction of capital per order"},
    }


def build_emit_config_tool():
    return {
        "type": "function",
        "function": {
            "name": "emit_config",
            "description": (
                "Submit a v1 agent configuration for validation. Call this only "
                "after the intent is classified and the elicitation slots "
                "(tempo, risk, assets) are answered or defaulted. Use ONLY the "
                "fields below — these are the only parameters the platform has. "
                "To build SEVERAL agents from one shared strategy in a single "
                "go, add `variants` (see its description)."
            ),
            "parameters": {
                "type": "object",
                "additionalProperties": False,
                "required": ["classification", "config", "rationale"],
                "properties": {
                    "classification": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["archetype", "confidence"],
                        "properties": {
                            "archetype": {"type": "string", "enum": list(ARCHETYPES),
                                          "description": "internal classification only; never shown to the user"},
                            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                            "signals_heard": {"type": "array", "items": {"type": "string"}},
                        },
                    },
                    "config": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["name", "assets", "candle_interval", "reward",
                                     "training_steps", "stop_loss", "take_profit",
                                     "max_trade", "min_trade"],
                        "properties": _config_field_properties(),
                    },
                    "variants": {
                        "type": "array",
                        "maxItems": MAX_AGENTS_PER_BATCH,
                        "additionalProperties": False,
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "properties": _config_field_properties(),
                        },
                        "description": (
                            "OPTIONAL. Use ONLY to build multiple agents from ONE "
                            "shared strategy in a single request — most commonly "
                            "one {\"assets\": [...]} entry per agent. Each entry "
                            "inherits every field from `config` and overrides only "
                            "what it names. Leave this out for a single agent. "
                            "Example — 'run 3 agents on different coins' -> "
                            "variants:[{\"assets\":[\"BTCUSDT\"]},"
                            "{\"assets\":[\"ETHUSDT\"]},{\"assets\":[\"SOLUSDT\"]}]. "
                            "Do NOT use this for one agent that trades a basket of "
                            "coins (that is a single `config` with several assets)."
                        ),
                    },
                    "rationale": {
                        "type": "object",
                        "additionalProperties": {"type": "string"},
                        "description": ("One short plain-language sentence per "
                                        "inferred value, tied to what the user said. "
                                        "Keys are config field names."),
                    },
                },
            },
        },
    }


def build_retrieve_tool():
    return {
        "type": "function",
        "function": {
            "name": "retrieve",
            "description": ("Look up Roostoo knowledge cards (strategies, "
                            "indicators, reward metrics, platform mechanics)."),
            "parameters": {
                "type": "object",
                "required": ["query"],
                "properties": {"query": {"type": "string"},
                               "k": {"type": "integer", "minimum": 1, "maximum": 5}},
            },
        },
    }


def all_tools():
    return [build_emit_config_tool(), build_retrieve_tool()]
