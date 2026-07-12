"""
Deterministic validation of a v1 config — range/enum/coherence checks over the
v1 registry only. Reproducible and auditable; the LLM never does this itself.
Errors come back as {path, message} so Coach can explain and re-emit.
"""

import re

from . import schema as S

_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 _\-]{0,39}$")


class _Ctx:
    def __init__(self):
        self.errors = []
        self.warnings = []

    def err(self, path, msg):
        self.errors.append({"path": path, "message": msg})

    def warn(self, path, msg):
        self.warnings.append({"path": path, "message": msg})


def _pct(ctx, path, val):
    lo, hi = S.PCT_BOUNDS
    if not isinstance(val, (int, float)) or isinstance(val, bool):
        ctx.err(path, "must be a number")
        return None
    if not (lo <= val <= hi):
        ctx.err(path, "must be between %g%% and %g%%" % (lo * 100, hi * 100))
        return None
    return float(val)


def validate_config(config):
    """Validate a v1 config dict. Returns
    {valid, errors, warnings, config} (config echoed back when valid)."""
    ctx = _Ctx()
    if not isinstance(config, dict):
        return {"valid": False, "errors": [{"path": "", "message": "config must be an object"}],
                "warnings": []}

    # name
    if not _NAME_RE.match(config.get("name") or ""):
        ctx.err("name", "1-40 chars: letters, digits, spaces, - _ only")

    # assets
    assets = config.get("assets") or []
    valid_assets = {a + S.QUOTE for a in S.SUPPORTED_ASSETS}
    if not (S.MIN_ASSETS <= len(assets) <= S.MAX_ASSETS):
        ctx.err("assets", "pick %d-%d coins" % (S.MIN_ASSETS, S.MAX_ASSETS))
    else:
        if len(set(assets)) != len(assets):
            ctx.err("assets", "duplicate coins")
        for a in assets:
            if a not in valid_assets:
                ctx.err("assets", "%r is not a supported coin" % (a,))

    # candle interval
    if config.get("candle_interval") not in S.CANDLE_INTERVALS:
        ctx.err("candle_interval", "must be one of %s" % ", ".join(S.CANDLE_INTERVALS))

    # reward
    if config.get("reward") not in S.REWARDS:
        ctx.err("reward", "must be one of %s" % ", ".join(S.REWARDS))

    # training steps
    if config.get("training_steps") not in S.TRAINING_STEPS:
        ctx.err("training_steps", "must be one of %s"
                % ", ".join("%dk" % (s // 1000) for s in S.TRAINING_STEPS))

    # risk / sizing percentages
    sl = _pct(ctx, "stop_loss", config.get("stop_loss"))
    tp = _pct(ctx, "take_profit", config.get("take_profit"))
    mx = _pct(ctx, "max_trade", config.get("max_trade"))
    mn = _pct(ctx, "min_trade", config.get("min_trade"))

    # coherence
    if mx is not None and mn is not None and mn > mx:
        ctx.err("min_trade", "min trade per order can't exceed max trade per order")

    valid = not ctx.errors
    out = {"valid": valid, "errors": ctx.errors, "warnings": ctx.warnings}
    if valid:
        out["config"] = dict(config)
    return out
