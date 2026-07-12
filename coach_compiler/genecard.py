"""
Gene card — a plain, reviewable summary of a validated v1 config.

Only real v1 parameters appear. Each user/coach value carries one short
plain-language reason; a small "fixed by the platform" section lists the
things the user can't change (PPO, lookback, the indicator bundle, long-only).
No internal reward-shaping math, no bps, no jargon.
"""

from . import schema as S

_FREQ_LABEL = {"5m": "every 5 minutes", "15m": "every 15 minutes"}


def _row(path, label, value, tier, rationale=None, locked_reason=None):
    return {"path": path, "label": label, "value": value, "tier": tier,
            "rationale": rationale, "locked_reason": locked_reason,
            "editable": tier != S.PLATFORM}


def build_gene_card(config, rationale, classification, warnings=None):
    rationale = rationale or {}
    arch = (classification or {}).get("archetype")
    blurb = S.ARCHETYPE_BLURB.get(arch, "a trading agent")

    def r(k):
        return rationale.get(k)

    def pct(v):
        return "%g%%" % (round(v * 100, 2))

    choices = [
        _row("assets", "Coins", ", ".join(config["assets"]), S.USER, r("assets")),
        _row("candle_interval", "Trades", _FREQ_LABEL.get(config["candle_interval"],
             config["candle_interval"]), S.COACH, r("candle_interval")),
        _row("reward", "Optimizes for", S.REWARD_LABEL.get(config["reward"], config["reward"]),
             S.COACH, r("reward")),
        _row("training_steps", "Training length", "%dk steps" % (config["training_steps"] // 1000),
             S.COACH, r("training_steps")),
        _row("stop_loss", "Stop-loss", pct(config["stop_loss"]), S.USER, r("stop_loss")),
        _row("take_profit", "Take-profit", pct(config["take_profit"]), S.USER, r("take_profit")),
        _row("max_trade", "Max per trade", pct(config["max_trade"]) + " of capital",
             S.USER, r("max_trade")),
        _row("min_trade", "Min per trade", pct(config["min_trade"]) + " of capital",
             S.USER, r("min_trade")),
    ]

    fixed = [
        _row("policy", "Model", "PPO (reinforcement learning)", S.PLATFORM,
             locked_reason="Every Roostoo agent is a PPO policy — not a fixed rule, not an LLM."),
        _row("direction", "Direction", "long-only", S.PLATFORM,
             locked_reason="The platform only takes long positions right now — no shorting."),
        _row("indicators", "What it sees", ", ".join(S.FIXED_INDICATORS), S.PLATFORM,
             locked_reason="All 8 indicators are always on and trained together — no subset to pick."),
        _row("lookback", "Memory", "%d candles" % S.LOOKBACK, S.PLATFORM,
             locked_reason="It reads the last %d candles each decision." % S.LOOKBACK),
        _row("training_data", "Trained on", "full available history", S.PLATFORM,
             locked_reason="Trained on all available history for each coin."),
    ]

    return {
        "name": config.get("name"),
        "blurb": blurb,
        "classification": classification,
        "sections": [
            {"block": "Your choices", "rows": choices},
            {"block": "Fixed by the platform", "rows": fixed},
        ],
        "warnings": warnings or [],
        "config": config,
    }


def render_text(card):
    """Terminal rendering for the CLI demo / eyeball tests."""
    lines = ["=" * 64,
             "GENE CARD  ·  %s" % card["name"],
             card["blurb"], "=" * 64]
    for sec in card["sections"]:
        lines.append("")
        lines.append("[%s]" % sec["block"])
        for row in sec["rows"]:
            tier = {"user": "you  ", "coach": "coach", "platform": "fixed"}[row["tier"]]
            lines.append("  (%s) %-16s %s" % (tier, row["label"] + ":", row["value"]))
            why = row.get("rationale") or row.get("locked_reason")
            if why:
                lines.append("          -> %s" % why)
    for w in card.get("warnings", []):
        lines.append("  ! %s: %s" % (w.get("path"), w.get("message")))
    return "\n".join(lines)
