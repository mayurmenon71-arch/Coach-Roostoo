"""
Step 6 — The gene card.

The output of Create is never raw JSON at the user: it is a preview where
every Coach-inferred value carries one sentence of reasoning tied to what the
user said, every platform lock carries its standard explanation, and the
breakeven numbers are printed where the user cannot miss them. Coach
inferences stay editable in the UI; platform rows do not.
"""

from . import schema as S

# Standard one-liners for platform-locked rows (fixed text — the model never
# writes these, so they can't drift).
_LOCK_REASONS = {
    "action.type": "Target position: costs charge only on changes, so holding is the free default.",
    "action.vol_target_scaling": "Vol-scaled sizing is how sizing survives regime shifts.",
    "reward.fee_term": "Reward is net of taker fees, spread and slippage — fee-blind agents die on fees.",
    "reward.funding_term": "Funding is a mandatory cost and signal: 71% of the best live RL agent's profit was funding capture.",
    "observation.position_context": "Position, entry price, time-in-position and uPnL are load-bearing for after-cost performance.",
    "observation.market_context": "Funding, regime label, realized vol and time-remaining — the same inputs every agent gets.",
    "risk.max_drawdown_kill": "Platform kill-switch: the agent is stopped at -20% regardless of config.",
    "risk.daily_loss_cap": "Daily loss cap, platform schedule.",
    "training.seeds": "The ensemble IS the agent: 5 seeds, averaged policy — halves seed variance.",
    "training.regime_sampling": "Multi-regime training (bull/bear/chop) is mandatory — no single-regime specialists.",
    "evaluation.benchmark_twin": "Every agent races its fixed-rule twin in the same simulator with identical costs.",
    "evaluation.breakeven_alpha_check": "Hard gate before enrollment: implied turnover must clear costs.",
    "evaluation.fidelity_score": "Post-training audit: does it still behave like its archetype, or drift into an impostor?",
}

_TWINS = {
    "intraday_momentum": "Long when EMA(20) > EMA(100) on 5m bars and ADX > 25; exit on cross-down; 2xATR trailing stop.",
    "mean_reversion": "Buy when RSI(14) < 30 on 1m bars and price < lower Bollinger(20, 2σ); exit at mid-band; mirrored for shorts.",
    "breakout": "Buy a 12h-high breakout when realized vol sits below its 3-day 20th percentile; 2xATR trailing stop.",
    "flow_driven": "If funding flips sharply negative while OI spikes and price holds above VWAP support, go long the squeeze; exit when flow normalizes.",
}


def _row(path, label, value, tier, rationale=None, locked_reason=None, editable=None):
    return {
        "path": path, "label": label, "value": value, "tier": tier,
        "rationale": rationale,
        "locked_reason": locked_reason,
        "editable": (tier != S.PLATFORM) if editable is None else editable,
    }


def _fmt_band(band):
    return "[%g, %g] /hr" % (band[0], band[1])


def build_gene_card(config, rationale, classification, breakeven, warnings):
    """Assemble the renderable gene card from a VALIDATED config (with
    platform locks already applied). Deterministic — no model text except the
    per-value rationale sentences, which are attributed as Coach reasoning."""
    rationale = rationale or {}
    arch = config["identity"]["archetype"]
    spec = S.ARCHETYPE_SPECS[arch]

    def r(path):
        return rationale.get(path)

    ident = config["identity"]
    uni = config["universe"]
    cad = config["cadence"]
    obs = config["observation"]
    rew = config["reward"]
    act = config["action"]
    rk = config["risk"]
    tr = config["training"]

    sections = []

    sections.append({"block": "Identity", "rows": [
        _row("identity.name", "Name", ident.get("name"), S.USER),
        _row("identity.archetype", "Archetype", arch, S.USER,
             rationale=r("identity.archetype")),
    ]})

    sections.append({"block": "Universe", "rows": [
        _row("universe.assets", "Assets", ", ".join(uni["assets"]), S.USER),
        _row("universe.max_concurrent", "Max concurrent positions",
             uni.get("max_concurrent", len(uni["assets"])), S.USER),
    ]})

    sections.append({"block": "Cadence", "rows": [
        _row("cadence.decision_interval", "Decision interval",
             cad["decision_interval"], S.COACH, rationale=r("cadence.decision_interval")),
        _row("cadence.candle_interval", "Candle interval", cad["candle_interval"],
             S.PLATFORM, locked_reason="Observes fast, trades rarely — cadence buys reaction speed, never trade frequency."),
    ]})

    ind_desc = ", ".join(
        i["id"] + ("(" + ",".join("%s=%s" % (k, v) for k, v in i.items() if k != "id") + ")"
                   if len(i) > 1 else "")
        for i in obs["indicators"])
    sections.append({"block": "Observation (what it sees)", "rows": [
        _row("observation.feature_families", "Feature families",
             ", ".join(obs["feature_families"]), S.COACH,
             rationale=r("observation.feature_families")),
        _row("observation.indicators", "Indicators", ind_desc, S.COACH,
             rationale=r("observation.indicators")),
        _row("observation.position_context", "Position context",
             ", ".join(config["observation"]["position_context"]), S.PLATFORM,
             locked_reason=_LOCK_REASONS["observation.position_context"]),
        _row("observation.market_context", "Market context",
             ", ".join(config["observation"]["market_context"]), S.PLATFORM,
             locked_reason=_LOCK_REASONS["observation.market_context"]),
    ]})

    reward_rows = [
        _row("reward.flavor", "Risk flavor",
             rew["flavor"] + (" (α=%g)" % rew["cvar_alpha"] if rew["flavor"] == "cvar" else ""),
             S.COACH, rationale=r("reward.flavor")),
        _row("reward.lambda_dd", "Drawdown penalty λ_dd", rew["lambda_dd"],
             S.COACH, rationale=r("reward.lambda_dd")),
        _row("reward.turnover_band", "Turnover band", _fmt_band(rew["turnover_band"]),
             S.COACH, rationale=r("reward.turnover_band")),
        _row("reward.lambda_band", "Band penalty λ", rew["lambda_band"], S.COACH,
             rationale=r("reward.lambda_band")),
    ]
    if "hold_bonus" in rew:
        reward_rows.append(_row("reward.hold_bonus", "Hold bonus", rew["hold_bonus"],
                                S.COACH, rationale=r("reward.hold_bonus")))
    if "per_trade_penalty" in rew:
        reward_rows.append(_row("reward.per_trade_penalty", "Per-trade penalty",
                                rew["per_trade_penalty"], S.COACH,
                                rationale=r("reward.per_trade_penalty")))
    if "averaging_down_penalty" in rew:
        reward_rows.append(_row("reward.averaging_down_penalty", "Averaging-down penalty",
                                rew["averaging_down_penalty"], S.COACH,
                                rationale=r("reward.averaging_down_penalty")))
    reward_rows.append(_row("reward.fee_term", "Fee + funding terms", "always on",
                            S.PLATFORM, locked_reason=_LOCK_REASONS["reward.fee_term"]))
    sections.append({"block": "Reward (what it wants)", "rows": reward_rows})

    _rng = act["range"]
    _rng_txt = ("long-only, up to %g%% of max" % (_rng[1] * 100)
                if _rng[0] == 0 else "[%g, %g]" % tuple(_rng))
    action_rows = [
        _row("action.range", "Position range", _rng_txt,
             S.USER, rationale=r("action.range")),
        _row("action.band_width", "No-trade band", act["band_width"], S.COACH,
             rationale=r("action.band_width")),
        _row("action.min_holding", "Minimum holding", act["min_holding"], S.COACH,
             rationale=r("action.min_holding")),
    ]
    if act.get("time_stop"):
        action_rows.append(_row("action.time_stop", "Hard time-stop", act["time_stop"],
                                S.COACH, rationale=r("action.time_stop")))
    action_rows.append(_row("action.max_leverage", "Max leverage",
                            "%dx" % act.get("max_leverage", spec["default_leverage"]),
                            S.USER,
                            rationale=r("action.max_leverage"),
                            locked_reason="Platform schedule caps leverage; users may only lower it."))
    action_rows.append(_row("action.type", "Action type", "target position", S.PLATFORM,
                            locked_reason=_LOCK_REASONS["action.type"]))
    sections.append({"block": "Action (how it can act)", "rows": action_rows})

    sections.append({"block": "Risk", "rows": [
        _row("risk.stop_loss", "Stop loss", "%.0f%%" % (rk["stop_loss"] * 100),
             S.USER, rationale=r("risk.stop_loss")),
        _row("risk.take_profit", "Take profit", "%.0f%%" % (rk["take_profit"] * 100),
             S.USER, rationale=r("risk.take_profit")),
        _row("risk.max_drawdown_kill", "Max-drawdown kill",
             "%.0f%%" % (rk["max_drawdown_kill"] * 100), S.PLATFORM,
             locked_reason=_LOCK_REASONS["risk.max_drawdown_kill"]),
    ]})

    sections.append({"block": "Training & evaluation", "rows": [
        _row("training.steps", "Training steps", "%dk" % (tr["steps"] // 1000),
             S.COACH, rationale=r("training.steps")),
        _row("training.augmentation", "Augmentation", tr.get("augmentation", "off"),
             S.COACH, rationale=r("training.augmentation")),
        _row("training.seeds", "Seed ensemble", "%d seeds, averaged policy" % tr["seeds"],
             S.PLATFORM, locked_reason=_LOCK_REASONS["training.seeds"]),
        _row("training.regime_sampling", "Regime sampling", "mandatory (bull/bear/chop)",
             S.PLATFORM, locked_reason=_LOCK_REASONS["training.regime_sampling"]),
        _row("evaluation.benchmark_twin", "Benchmark twin", _TWINS[arch],
             S.PLATFORM, locked_reason=_LOCK_REASONS["evaluation.benchmark_twin"]),
        _row("evaluation.gates", "Enrollment gates",
             "breakeven screen · degeneracy flags · fidelity audit", S.PLATFORM,
             locked_reason=_LOCK_REASONS["evaluation.breakeven_alpha_check"]),
    ]})

    return {
        "name": ident.get("name"),
        "archetype": arch,
        "fee_drag": spec["fee_drag"],
        "classification": classification,
        "sections": sections,
        "breakeven": breakeven,
        "warnings": warnings or [],
        "config": config,
    }


def render_text(card):
    """Terminal rendering — used by the CLI demo and eyeball tests."""
    lines = []
    lines.append("=" * 72)
    lines.append("GENE CARD  ·  %s  ·  %s  (fee drag: %s)"
                 % (card["name"], card["archetype"], card["fee_drag"]))
    lines.append("=" * 72)
    for sec in card["sections"]:
        lines.append("")
        lines.append("[%s]" % sec["block"])
        for row in sec["rows"]:
            tier = {"user": "USER    ", "coach": "COACH   ", "platform": "PLATFORM"}[row["tier"]]
            lines.append("  %s %-26s %s" % (tier, row["label"] + ":", row["value"]))
            why = row.get("rationale") or row.get("locked_reason")
            if why:
                lines.append("           └ %s" % why)
    if card.get("breakeven"):
        lines.append("")
        lines.append("[Breakeven preview]")
        lines.append("  " + card["breakeven"]["explanation"])
    for w in card.get("warnings", []):
        lines.append("  ⚠ %s: %s" % (w["path"], w["message"]))
    return "\n".join(lines)
