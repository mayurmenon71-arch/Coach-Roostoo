"""
Step 1 — The config schema (Rules to Rewards, Section 7.2).

Single source of truth for:
  * every parameter, its type, and its allowed range,
  * its governance tier (USER / COACH / PLATFORM),
  * archetype defaults and archetype-specific ranges,
  * the whitelisted indicator registry,
  * the emit_config function-calling tool definition (generated, never
    hand-maintained separately).

The governing rule: any parameter whose wrong value produces a fee-blind
or degenerate agent is never user-tunable. PLATFORM values are hard-coded
here and stamped onto every config server-side — the model never sets them.
"""

# ── Governance tiers ─────────────────────────────────────────────────────────
USER = "user"          # identity-level preference; Coach assists
COACH = "coach"        # LLM-inferred within bounds, shown for confirmation
PLATFORM = "platform"  # locked survival invariant; model never touches it

# ── Archetypes (the four arena families — nothing else exists) ──────────────
ARCHETYPES = ("intraday_momentum", "mean_reversion", "breakout", "flow_driven")

FEATURE_FAMILIES = (
    "trend", "reversion", "breakout", "flow", "sentiment", "time", "cross_asset"
)

# The defining family each archetype MUST include in its observation vector.
DEFINING_FAMILY = {
    "intraday_momentum": "trend",
    "mean_reversion": "reversion",
    "breakout": "breakout",
    "flow_driven": "flow",
}

# ── Universe (mirrors public/assets/sim-engine.js ASSETS) ────────────────────
SUPPORTED_ASSETS = (
    "BTC", "ETH", "SOL", "BNB", "XRP", "ADA", "AVAX", "DOGE", "DOT", "LINK",
    "LTC", "UNI", "NEAR", "SUI", "AAVE", "FET", "HBAR", "SHIB", "TRX", "XLM",
)
QUOTE = "USDT"
VENUE = "roostoo-sim"
MAX_ASSETS = 10

# ── Cadence ──────────────────────────────────────────────────────────────────
DECISION_INTERVALS = ("30s", "1m", "5m", "15m")   # 30s/1m gated by breakeven
STEPS_PER_DAY = {"30s": 2880, "1m": 1440, "5m": 288, "15m": 96}

REWARD_FLAVORS = ("pnl", "sharpe", "sortino", "calmar", "cvar")

BAND_WIDTHS = ("tight", "medium", "wide", "signal_paced")

# min_holding / time_stop are strings like "15m", "4h"; stored bounds in minutes.
MIN_HOLDING_BOUNDS_MIN = (15, 720)     # 15m – 12h (platform envelope)
TIME_STOP_BOUNDS_MIN = (60, 1440)      # 1h – 24h

# ── Whitelisted indicator registry (the LLM selects, never authors) ──────────
# Each entry: families it belongs to + typed params with (min, max, default).
# "windows"/"windows_bars" params accept a list of ints, each within bounds.
INDICATOR_REGISTRY = {
    # trend
    "roc":            {"families": ("trend",), "params": {"windows_bars": ("int_list", 2, 500, [6, 24, 96, 288])}},
    "ema_cross":      {"families": ("trend",), "params": {"fast": ("int", 5, 100, 20), "slow": ("int", 20, 500, 100)}},
    "macd_hist":      {"families": ("trend",), "params": {"fast": ("int", 5, 50, 12), "slow": ("int", 10, 200, 26), "signal": ("int", 3, 50, 9)}},
    "adx":            {"families": ("trend",), "params": {"window": ("int", 12, 500, 14)}},
    "atr":            {"families": ("trend", "breakout"), "params": {"window": ("int", 12, 500, 14)}},
    "donchian":       {"families": ("trend", "breakout"), "params": {"window": ("int", 12, 500, 144)}},
    # reversion
    "zscore_vwap":    {"families": ("reversion",), "params": {"windows": ("int_list", 12, 500, [30, 120]), "window": ("int", 12, 500, 60)}},
    "boll_pctb":      {"families": ("reversion",), "params": {"window": ("int", 12, 500, 20), "sigma": ("float", 1.0, 4.0, 2.0)}},
    "rsi":            {"families": ("reversion",), "params": {"window": ("int", 12, 500, 14)}},
    "stoch_rsi":      {"families": ("reversion",), "params": {"window": ("int", 12, 500, 14)}},
    "reversal_return":{"families": ("reversion",), "params": {"window": ("int", 2, 500, 12)}},
    "rvol":           {"families": ("reversion", "breakout"), "params": {"window": ("int", 12, 500, 60)}},
    # breakout / squeeze
    "squeeze_pctile": {"families": ("breakout",), "params": {"window": ("int", 12, 500, 96)}},
    "atr_pctile":     {"families": ("breakout",), "params": {"window": ("int", 12, 500, 96)}},
    "volume_surge":   {"families": ("breakout", "flow"), "params": {"window": ("int", 12, 500, 48)}},
    "session_time":   {"families": ("time",), "params": {}},
    # flow / funding / sentiment
    "funding_ema":    {"families": ("flow",), "params": {"window": ("int", 2, 500, 24)}},
    "funding_delta":  {"families": ("flow",), "params": {"window": ("int", 2, 500, 8)}},
    "oi_delta":       {"families": ("flow", "breakout"), "params": {"windows": ("int_list", 2, 500, [15, 60]), "window": ("int", 2, 500, 15)}},
    "liq_cascade_score": {"families": ("flow",), "params": {"window": ("int", 2, 500, 30)}},
    "flow_imbalance": {"families": ("flow",), "params": {"window": ("int", 2, 500, 15)}},
    "basis_move":     {"families": ("flow",), "params": {"window": ("int", 2, 500, 30)}},
    "news_risk_llm":  {"families": ("flow", "sentiment"), "params": {}},
    # cross-asset
    "btc_dominance":  {"families": ("cross_asset",), "params": {"window": ("int", 12, 500, 96)}},
    "rel_strength":   {"families": ("cross_asset",), "params": {"window": ("int", 12, 500, 96)}},
    "lead_lag":       {"families": ("cross_asset",), "params": {"window": ("int", 12, 500, 96)}},
}

# ── Platform-locked values (survival invariants — stamped, never model-set) ──
PLATFORM_LOCKED = {
    "cadence": {
        "candle_interval": "30s",
        "competition_clock": True,          # time-remaining always on
    },
    "observation": {
        # position context: the load-bearing after-cost features (arXiv:2406.08013)
        "position_context": ["position", "entry_px", "time_in_pos", "upnl"],
        # market context: same regime inputs every agent receives
        "market_context": ["funding", "regime_label", "rvol", "t_remaining"],
        "normalization": "zscore_rolling_per_feature",
    },
    "reward": {
        "fee_term": True,                    # net of taker fees, spread, slippage
        "funding_term": True,                # funding-inclusive (71% of a 5y agent's
                                             # profit was funding capture, 2201.04699)
    },
    "action": {
        "type": "target_position",           # cost charged only on changes;
                                             # holding is the free default
        "vol_target_scaling": True,
    },
    "risk": {
        "max_drawdown_kill": 0.20,
        "daily_loss_cap": 0.08,
        "liquidation_buffer": 0.25,
    },
    "training": {
        "seeds": 5,                          # the ensemble IS the agent
        "regime_sampling": "mandatory",      # bull/bear/chop blocks
        "walk_forward": "expanding",
        "retrain_cadence": "monthly",
    },
    "evaluation": {
        "benchmark_twin": True,              # fixed-rule twin, same simulator
        "buy_and_hold": True,
        "median_human": True,
        "breakeven_alpha_check": True,       # hard gates before enrollment
        "degeneracy_flags": True,
        "fidelity_score": True,
    },
}

# Platform leverage policy: schedule allows 1–5x gated by demonstrated track
# record; this build has no track-record system yet, so the effective cap is 2.
MAX_LEVERAGE_SCHEDULE = 5
MAX_LEVERAGE_EFFECTIVE = 2   # users/Coach may only go lower

# Platform capability: only LONG positions are supported right now (no
# shorting). Every action.range lower bound must be 0. Flip to False when the
# platform enables shorting, and the validator/prompt/elicitation follow.
LONG_ONLY = True

# ── Coach-tier ranges (global envelope; archetype tables narrow them) ────────
COACH_RANGES = {
    "lambda_dd": (0.05, 0.50),
    "lambda_band": (0.0, 0.20),
    "hold_bonus": (0.0, 0.05),
    "per_trade_penalty": (0.0, 0.002),
    "averaging_down_penalty": (0.0, 0.10),
    "cvar_alpha": (0.01, 0.10),
    "steps": (250_000, 1_000_000),
}

# Risk bounds (User-set, bounded)
STOP_LOSS_BOUNDS = (0.02, 0.15)
TAKE_PROFIT_BOUNDS = (0.04, 0.40)

# ── Archetype defaults + archetype-specific ranges (Sections 4 & 6) ─────────
# turnover_band units: expected |Δposition| per HOUR (fraction of max position).
# Chosen so the doc's worked numbers reproduce: a band ceiling of 0.10/hr on a
# momentum agent implies ~1.2 round-trips/day — "a handful of position changes
# per competition day" (Section 7.5-A note). breakeven.py documents the math.
ARCHETYPE_SPECS = {
    "intraday_momentum": {
        "fee_drag": "low",
        "decision_intervals": ("5m", "15m"),
        "default_interval": "5m",
        "reward_flavors": ("pnl", "sortino"),
        "default_flavor": "sortino",
        "lambda_dd": (0.05, 0.25, 0.15),
        "turnover_band_lo": (0.005, 0.05, 0.02),
        "turnover_band_hi": (0.05, 0.15, 0.10),
        "lambda_band": (0.02, 0.20, 0.08),
        "hold_bonus": (0.01, 0.05, 0.03),
        "per_trade_penalty": (0.0, 0.002, 0.0008),
        "band_width": ("wide", "medium"),
        "default_band_width": "wide",
        "min_holding_min": (120, 720, 240),      # 2–12h, default 4h
        "time_stop_required": False,
        "position_cap": 1.0,
        "default_leverage": 2,
        "steps": (250_000, 1_000_000, 500_000),
        "families_allowed": ("trend", "time", "cross_asset", "flow"),
    },
    "mean_reversion": {
        "fee_drag": "high",                       # the most fee-fragile family
        "decision_intervals": ("1m", "5m"),
        "default_interval": "1m",
        "reward_flavors": ("sharpe",),
        "default_flavor": "sharpe",
        "lambda_dd": (0.25, 0.50, 0.40),
        "turnover_band_lo": (0.02, 0.10, 0.05),
        "turnover_band_hi": (0.10, 0.30, 0.25),   # strictest band in the library
        "lambda_band": (0.05, 0.20, 0.10),
        "hold_bonus": (0.0, 0.02, 0.01),
        "per_trade_penalty": (0.0005, 0.002, 0.0010),
        "band_width": ("tight",),
        "default_band_width": "tight",
        "min_holding_min": (15, 60, 15),          # 15m–1h, default 15m
        "time_stop_required": True,               # flat after N bars regardless
        "default_time_stop_min": 360,             # 6h
        "position_cap": 0.5,                      # capped target (±0.5 of max)
        "default_leverage": 1,
        "steps": (250_000, 800_000, 400_000),
        "families_allowed": ("reversion", "flow", "time", "cross_asset"),
    },
    "breakout": {
        "fee_drag": "medium",
        "decision_intervals": ("1m", "5m"),
        "default_interval": "5m",
        "reward_flavors": ("pnl", "sortino"),
        "default_flavor": "sortino",
        "lambda_dd": (0.10, 0.35, 0.20),
        "turnover_band_lo": (0.005, 0.05, 0.02),
        "turnover_band_hi": (0.05, 0.20, 0.12),
        "lambda_band": (0.02, 0.20, 0.08),
        "hold_bonus": (0.0, 0.03, 0.01),
        "per_trade_penalty": (0.0005, 0.002, 0.0012),  # true breakouts are rare
        "band_width": ("medium", "wide"),
        "default_band_width": "medium",
        "min_holding_min": (60, 240, 60),         # post-entry lockup ≥ 1h
        "time_stop_required": False,
        "position_cap": 1.0,
        "default_leverage": 2,
        "steps": (250_000, 1_000_000, 500_000),
        "families_allowed": ("breakout", "trend", "time", "flow", "cross_asset"),
    },
    "flow_driven": {
        "fee_drag": "medium",
        "decision_intervals": ("1m", "5m", "15m"),
        "default_interval": "1m",
        "reward_flavors": ("cvar", "sharpe"),      # event trades have fat tails
        "default_flavor": "cvar",
        "lambda_dd": (0.15, 0.40, 0.30),
        "turnover_band_lo": (0.005, 0.05, 0.02),
        "turnover_band_hi": (0.05, 0.20, 0.15),
        "lambda_band": (0.05, 0.20, 0.10),
        "hold_bonus": (0.0, 0.02, 0.0),
        "per_trade_penalty": (0.0005, 0.002, 0.0010),
        "band_width": ("signal_paced",),
        "default_band_width": "signal_paced",
        "min_holding_min": (60, 240, 60),         # 1h
        "time_stop_required": False,
        "position_cap": 0.75,
        "default_leverage": 2,
        "steps": (400_000, 1_000_000, 600_000),
        "families_allowed": ("flow", "reversion", "sentiment", "time", "cross_asset"),
    },
}

# ── Helpers ──────────────────────────────────────────────────────────────────

_DUR_UNITS = {"m": 1, "h": 60}


def duration_to_minutes(s):
    """'15m' -> 15, '4h' -> 240. Raises ValueError on anything else."""
    if not isinstance(s, str) or len(s) < 2 or s[-1] not in _DUR_UNITS:
        raise ValueError("bad duration: %r" % (s,))
    return int(s[:-1]) * _DUR_UNITS[s[-1]]


def minutes_to_duration(m):
    return ("%dh" % (m // 60)) if m % 60 == 0 and m >= 60 else ("%dm" % m)


# Default indicator set per archetype (whitelisted ids, sensible params).
_DEFAULT_INDICATORS = {
    "intraday_momentum": [
        {"id": "roc", "windows_bars": [6, 24, 96, 288]},
        {"id": "ema_cross", "fast": 20, "slow": 100},
        {"id": "adx", "window": 14}, {"id": "atr", "window": 14},
        {"id": "donchian", "window": 144},
    ],
    "mean_reversion": [
        {"id": "zscore_vwap", "windows": [30, 120]},
        {"id": "boll_pctb", "window": 20, "sigma": 2.0},
        {"id": "rsi", "window": 14}, {"id": "rvol", "window": 60},
        {"id": "funding_ema", "window": 24},
    ],
    "breakout": [
        {"id": "donchian", "window": 144}, {"id": "squeeze_pctile", "window": 96},
        {"id": "atr_pctile", "window": 96}, {"id": "volume_surge", "window": 48},
        {"id": "oi_delta", "windows": [15, 60]},
    ],
    "flow_driven": [
        {"id": "funding_delta", "window": 8}, {"id": "oi_delta", "windows": [15, 60]},
        {"id": "liq_cascade_score", "window": 30},
        {"id": "flow_imbalance", "window": 15}, {"id": "zscore_vwap", "window": 60},
    ],
}
_DEFAULT_FAMILIES = {
    "intraday_momentum": ["trend", "time"],
    "mean_reversion": ["reversion", "flow"],
    "breakout": ["breakout", "time"],
    "flow_driven": ["flow", "reversion"],
}


def default_config_for(archetype, assets=None, name=None):
    """Build a schema-VALID config from an archetype's defaults alone.

    This is the deterministic "nearest valid config" seed: Coach can start
    from it and only adjust what the user's intent implies, and the eval
    harness uses it as a perfect-model oracle. Every field is a default from
    ARCHETYPE_SPECS, so validate_config() always accepts the result.
    """
    if archetype not in ARCHETYPE_SPECS:
        raise ValueError("unknown archetype: %r" % (archetype,))
    spec = ARCHETYPE_SPECS[archetype]
    assets = assets or ["BTC" + QUOTE]
    cap = spec["position_cap"]

    reward = {
        "flavor": spec["default_flavor"],
        "lambda_dd": spec["lambda_dd"][2],
        "turnover_band": [spec["turnover_band_lo"][2], spec["turnover_band_hi"][2]],
        "lambda_band": spec["lambda_band"][2],
        "hold_bonus": spec["hold_bonus"][2],
        "per_trade_penalty": spec["per_trade_penalty"][2],
    }
    if spec["default_flavor"] == "cvar":
        reward["cvar_alpha"] = 0.05
    if archetype == "mean_reversion":
        reward["averaging_down_penalty"] = 0.05

    action = {
        "range": [0, cap],  # long-only: no shorting on the platform yet
        "band_width": spec["default_band_width"],
        "min_holding": minutes_to_duration(spec["min_holding_min"][2]),
        "max_leverage": spec["default_leverage"],
    }
    if spec["time_stop_required"]:
        action["time_stop"] = minutes_to_duration(spec["default_time_stop_min"])

    return {
        "identity": {"archetype": archetype,
                     "name": name or (archetype.replace("_", "-") + "-agent")},
        "universe": {"assets": list(assets)},
        "cadence": {"decision_interval": spec["default_interval"]},
        "observation": {
            "feature_families": list(_DEFAULT_FAMILIES[archetype]),
            "indicators": [dict(i) for i in _DEFAULT_INDICATORS[archetype]],
        },
        "reward": reward,
        "action": action,
        "risk": {"stop_loss": 0.05, "take_profit": 0.15},
        "training": {"steps": spec["steps"][2]},
    }


def apply_platform_locks(config):
    """Stamp every PLATFORM-locked value onto the config, overwriting anything
    the model may have set there. Deterministic; returns a new dict."""
    import copy
    out = copy.deepcopy(config)
    for block, values in PLATFORM_LOCKED.items():
        out.setdefault(block, {})
        for key, val in values.items():
            out[block][key] = copy.deepcopy(val)
    out.setdefault("universe", {})
    out["universe"]["quote"] = QUOTE
    out["universe"]["venue"] = VENUE
    return out


# ── The emit_config tool definition (generated from this spec) ───────────────

def _num(lo, hi, desc=""):
    return {"type": "number", "minimum": lo, "maximum": hi, "description": desc}


def build_emit_config_tool():
    """OpenAI-style function definition. Constrained decoding is the
    hallucination firewall: the model fills THIS, free text never touches
    the factory. Only USER/COACH-tier parameters appear — platform-locked
    values are stamped server-side by apply_platform_locks()."""
    indicator_ids = sorted(INDICATOR_REGISTRY.keys())
    return {
        "type": "function",
        "function": {
            "name": "emit_config",
            "description": (
                "Submit a complete agent configuration for validation. Call this "
                "ONLY after intent is classified and the five elicitation slots "
                "(tempo, risk, story, assets) are answered or "
                "defaulted. Every value must sit inside the schema ranges; the "
                "deterministic validator rejects anything outside them."
            ),
            "parameters": {
                "type": "object",
                "additionalProperties": False,
                "required": ["classification", "config", "rationale"],
                "properties": {
                    "classification": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["archetype", "confidence", "signals_heard"],
                        "properties": {
                            "archetype": {"type": "string", "enum": list(ARCHETYPES)},
                            "confidence": _num(0, 1, "classification confidence"),
                            "signals_heard": {
                                "type": "array", "items": {"type": "string"},
                                "description": "verbatim user phrases that drove the classification",
                            },
                        },
                    },
                    "config": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["identity", "universe", "cadence",
                                     "observation", "reward", "action", "risk",
                                     "training"],
                        "properties": {
                            "identity": {
                                "type": "object",
                                "additionalProperties": False,
                                "required": ["archetype", "name"],
                                "properties": {
                                    "archetype": {"type": "string", "enum": list(ARCHETYPES)},
                                    "name": {"type": "string", "maxLength": 40,
                                             "description": "letters, digits, spaces, - _ only"},
                                    "description": {"type": "string", "maxLength": 200},
                                },
                            },
                            "universe": {
                                "type": "object",
                                "additionalProperties": False,
                                "required": ["assets"],
                                "properties": {
                                    "assets": {
                                        "type": "array", "minItems": 1, "maxItems": MAX_ASSETS,
                                        "items": {"type": "string",
                                                  "enum": [a + QUOTE for a in SUPPORTED_ASSETS]},
                                    },
                                    "max_concurrent": {"type": "integer", "minimum": 1, "maximum": MAX_ASSETS},
                                },
                            },
                            "cadence": {
                                "type": "object",
                                "additionalProperties": False,
                                "required": ["decision_interval"],
                                "properties": {
                                    "decision_interval": {"type": "string", "enum": list(DECISION_INTERVALS)},
                                },
                            },
                            "observation": {
                                "type": "object",
                                "additionalProperties": False,
                                "required": ["feature_families", "indicators"],
                                "properties": {
                                    "feature_families": {
                                        "type": "array", "minItems": 1, "maxItems": 4,
                                        "items": {"type": "string", "enum": list(FEATURE_FAMILIES)},
                                    },
                                    "indicators": {
                                        "type": "array", "minItems": 2, "maxItems": 10,
                                        "items": {
                                            "type": "object",
                                            "required": ["id"],
                                            "properties": {
                                                "id": {"type": "string", "enum": indicator_ids},
                                            },
                                            # per-indicator params validated by
                                            # the deterministic validator against
                                            # INDICATOR_REGISTRY
                                            "additionalProperties": True,
                                        },
                                    },
                                },
                            },
                            "reward": {
                                "type": "object",
                                "additionalProperties": False,
                                "required": ["flavor", "lambda_dd", "turnover_band", "lambda_band"],
                                "properties": {
                                    "flavor": {"type": "string", "enum": list(REWARD_FLAVORS)},
                                    "cvar_alpha": _num(*COACH_RANGES["cvar_alpha"], desc="required iff flavor=cvar"),
                                    "lambda_dd": _num(*COACH_RANGES["lambda_dd"]),
                                    "turnover_band": {
                                        "type": "array", "minItems": 2, "maxItems": 2,
                                        "items": {"type": "number", "minimum": 0, "maximum": 0.5},
                                        "description": "[lo, hi] expected |Δposition| per hour",
                                    },
                                    "lambda_band": _num(*COACH_RANGES["lambda_band"]),
                                    "hold_bonus": _num(*COACH_RANGES["hold_bonus"], desc="only while profitable & low DD"),
                                    "per_trade_penalty": _num(*COACH_RANGES["per_trade_penalty"]),
                                    "averaging_down_penalty": _num(*COACH_RANGES["averaging_down_penalty"],
                                                                   desc="mean-reversion's classic death; use for that family"),
                                },
                            },
                            "action": {
                                "type": "object",
                                "additionalProperties": False,
                                "required": ["range", "band_width", "min_holding"],
                                "properties": {
                                    "range": {
                                        "type": "array", "minItems": 2, "maxItems": 2,
                                        "items": {"type": "number", "minimum": 0, "maximum": 1},
                                        "description": "[lo, hi]. LONG-ONLY platform: lo MUST be 0 (no shorting yet); hi in (0,1], capped per archetype",
                                    },
                                    "band_width": {"type": "string", "enum": list(BAND_WIDTHS)},
                                    "min_holding": {"type": "string",
                                                    "description": "e.g. '15m', '1h', '4h'; envelope 15m-12h"},
                                    "time_stop": {"type": "string",
                                                  "description": "flat after this long regardless of PnL; 1h-24h"},
                                    "max_leverage": {"type": "integer", "minimum": 1,
                                                     "maximum": MAX_LEVERAGE_EFFECTIVE},
                                },
                            },
                            "risk": {
                                "type": "object",
                                "additionalProperties": False,
                                "required": ["stop_loss", "take_profit"],
                                "properties": {
                                    "stop_loss": _num(*STOP_LOSS_BOUNDS),
                                    "take_profit": _num(*TAKE_PROFIT_BOUNDS),
                                },
                            },
                            "training": {
                                "type": "object",
                                "additionalProperties": False,
                                "required": ["steps"],
                                "properties": {
                                    "steps": {"type": "integer",
                                              "minimum": COACH_RANGES["steps"][0],
                                              "maximum": COACH_RANGES["steps"][1]},
                                    "augmentation": {"type": "string", "enum": ["off", "block_bootstrap"]},
                                },
                            },
                        },
                    },
                    "rationale": {
                        "type": "object",
                        "description": (
                            "One sentence per Coach-inferred value, tied to what the "
                            "user actually said. Keys are dotted param paths (e.g. "
                            "'action.min_holding'), values are the sentence."
                        ),
                        "additionalProperties": {"type": "string"},
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
            "description": (
                "Look up Roostoo knowledge cards (archetypes, indicators, reward "
                "terms, platform mechanics, fees, forward-testing). Use this for "
                "any platform-specific fact you are about to state."
            ),
            "parameters": {
                "type": "object",
                "required": ["query"],
                "properties": {
                    "query": {"type": "string"},
                    "k": {"type": "integer", "minimum": 1, "maximum": 5},
                },
            },
        },
    }


def build_breakeven_tool():
    return {
        "type": "function",
        "function": {
            "name": "breakeven_calc",
            "description": (
                "Compute the exact fee hurdle implied by a cadence + turnover "
                "band. Returns flips/day, cost bps/day, and the monthly/annual "
                "gross-edge hurdle. EVERY fee or cost number you quote to the "
                "user must come from this tool — no arithmetic in your head. "
                "The validator runs the same calculation as a hard gate."
            ),
            "parameters": {
                "type": "object",
                "required": ["decision_interval", "turnover_band_hi"],
                "properties": {
                    "decision_interval": {"type": "string", "enum": list(DECISION_INTERVALS)},
                    "turnover_band_hi": {"type": "number", "minimum": 0, "maximum": 50,
                                         "description": "band ceiling, |Δposition| per hour"},
                },
            },
        },
    }


def all_tools():
    return [build_emit_config_tool(), build_retrieve_tool(), build_breakeven_tool()]
