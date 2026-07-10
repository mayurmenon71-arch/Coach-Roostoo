"""
Step 2 — validate_config: the deterministic rule engine.

Range checks, coherence rules, archetype consistency, and the breakeven-alpha
screen. Validation must be reproducible and auditable — which is exactly why
the LLM never does it. Errors come back machine-readable (dotted param paths)
so Coach can explain the rejection in plain language and propose the nearest
valid config (max 2 repair rounds, then hand off to the UI).

Design note: the validator is strict about REJECTING out-of-schema values,
not about silently fixing them. The one exception is platform-locked blocks,
which are stamped by apply_platform_locks() before validation — anything the
model wrote there is overwritten, and that is by design, not an error.
"""

import re

from . import schema as S
from .breakeven import breakeven_calc

_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 _\-]{0,39}$")


class _Ctx:
    def __init__(self):
        self.errors = []    # hard failures — config cannot reach the factory
        self.warnings = []  # allowed but worth surfacing on the gene card

    def err(self, path, msg):
        self.errors.append({"path": path, "message": msg})

    def warn(self, path, msg):
        self.warnings.append({"path": path, "message": msg})


def _rng(ctx, path, val, lo, hi):
    """Numeric range check."""
    if not isinstance(val, (int, float)) or isinstance(val, bool):
        ctx.err(path, "must be a number")
        return False
    if not (lo <= val <= hi):
        ctx.err(path, "value %g outside allowed range [%g, %g]" % (val, lo, hi))
        return False
    return True


def validate_config(config):
    """Validate a config dict (as emitted by the model, BEFORE platform locks).

    Returns:
        {
          "valid": bool,
          "errors": [{"path", "message"}, ...],
          "warnings": [...],
          "breakeven": <breakeven_calc result or None>,
          "config": <the config with platform locks applied>  (only if valid)
        }
    """
    ctx = _Ctx()
    if not isinstance(config, dict):
        ctx.err("", "config must be an object")
        return {"valid": False, "errors": ctx.errors, "warnings": ctx.warnings,
                "breakeven": None}

    # ── identity ────────────────────────────────────────────────────────────
    ident = config.get("identity") or {}
    archetype = ident.get("archetype")
    if archetype not in S.ARCHETYPES:
        ctx.err("identity.archetype",
                "must be one of %s" % (", ".join(S.ARCHETYPES)))
        return {"valid": False, "errors": ctx.errors, "warnings": ctx.warnings,
                "breakeven": None}
    spec = S.ARCHETYPE_SPECS[archetype]

    name = ident.get("name", "")
    if not _NAME_RE.match(name or ""):
        # Names are a prompt-injection surface (they get echoed into reviews);
        # restrict to a safe charset and length.
        ctx.err("identity.name",
                "name must be 1-40 chars: letters, digits, spaces, - _ only")

    # ── universe ────────────────────────────────────────────────────────────
    uni = config.get("universe") or {}
    assets = uni.get("assets") or []
    valid_assets = {a + S.QUOTE for a in S.SUPPORTED_ASSETS}
    if not (1 <= len(assets) <= S.MAX_ASSETS):
        ctx.err("universe.assets", "need 1-%d assets" % S.MAX_ASSETS)
    else:
        if len(set(assets)) != len(assets):
            ctx.err("universe.assets", "duplicate assets in roster")
        for a in assets:
            if a not in valid_assets:
                ctx.err("universe.assets", "%r is not on the supported roster" % (a,))
    max_conc = uni.get("max_concurrent", len(assets) or 1)
    if not isinstance(max_conc, int) or not (1 <= max_conc <= max(1, len(assets))):
        ctx.err("universe.max_concurrent",
                "must be an integer between 1 and the roster size")

    # ── cadence (+ archetype gate) ──────────────────────────────────────────
    cad = config.get("cadence") or {}
    interval = cad.get("decision_interval")
    if interval not in S.DECISION_INTERVALS:
        ctx.err("cadence.decision_interval",
                "must be one of %s" % (", ".join(S.DECISION_INTERVALS)))
        interval = None
    elif interval not in spec["decision_intervals"]:
        ctx.err("cadence.decision_interval",
                "%s agents run at %s only" % (archetype, " or ".join(spec["decision_intervals"])))

    # ── observation ─────────────────────────────────────────────────────────
    obs = config.get("observation") or {}
    fams = obs.get("feature_families") or []
    for f in fams:
        if f not in S.FEATURE_FAMILIES:
            ctx.err("observation.feature_families", "unknown family %r" % (f,))
        elif f not in spec["families_allowed"]:
            ctx.err("observation.feature_families",
                    "family %r is not in %s's allowed set %s"
                    % (f, archetype, spec["families_allowed"]))
    defining = S.DEFINING_FAMILY[archetype]
    if defining not in fams:
        ctx.err("observation.feature_families",
                "%s must include its defining family %r" % (archetype, defining))

    inds = obs.get("indicators") or []
    if not (2 <= len(inds) <= 10):
        ctx.err("observation.indicators", "need 2-10 indicators")
    for i, ind in enumerate(inds):
        path = "observation.indicators[%d]" % i
        iid = (ind or {}).get("id")
        reg = S.INDICATOR_REGISTRY.get(iid)
        if reg is None:
            ctx.err(path, "indicator %r is not in the whitelisted registry" % (iid,))
            continue
        # every supplied param must exist in the registry entry and sit in range
        for pname, pval in ind.items():
            if pname == "id":
                continue
            pspec = reg["params"].get(pname)
            if pspec is None:
                ctx.err(path + "." + pname,
                        "parameter not in the registry for %r — the LLM selects, never authors" % (iid,))
                continue
            ptype, lo, hi = pspec[0], pspec[1], pspec[2]
            if ptype == "int_list":
                if (not isinstance(pval, list) or not pval
                        or not all(isinstance(v, int) and lo <= v <= hi for v in pval)):
                    ctx.err(path + "." + pname,
                            "must be a list of ints each in [%d, %d]" % (lo, hi))
            elif ptype == "int":
                if not isinstance(pval, int) or not (lo <= pval <= hi):
                    ctx.err(path + "." + pname, "must be an int in [%d, %d]" % (lo, hi))
            else:  # float
                _rng(ctx, path + "." + pname, pval, lo, hi)
        # coherence: fast < slow where both exist
        if iid in ("ema_cross", "macd_hist"):
            f_, s_ = ind.get("fast"), ind.get("slow")
            if isinstance(f_, int) and isinstance(s_, int) and f_ >= s_:
                ctx.err(path, "fast (%d) must be < slow (%d)" % (f_, s_))

    # ── reward ──────────────────────────────────────────────────────────────
    rew = config.get("reward") or {}
    flavor = rew.get("flavor")
    if flavor not in S.REWARD_FLAVORS:
        ctx.err("reward.flavor", "must be one of %s" % (", ".join(S.REWARD_FLAVORS)))
    elif flavor not in spec["reward_flavors"]:
        ctx.err("reward.flavor",
                "%s agents use %s" % (archetype, " or ".join(spec["reward_flavors"])))
    if flavor == "cvar":
        if "cvar_alpha" not in rew:
            ctx.err("reward.cvar_alpha", "required when flavor is cvar")
        else:
            _rng(ctx, "reward.cvar_alpha", rew["cvar_alpha"], *S.COACH_RANGES["cvar_alpha"])
    elif "cvar_alpha" in rew:
        ctx.warn("reward.cvar_alpha", "ignored — flavor is not cvar")

    lo_a, hi_a, _ = spec["lambda_dd"]
    _rng(ctx, "reward.lambda_dd", rew.get("lambda_dd"), lo_a, hi_a)

    band = rew.get("turnover_band")
    band_ok = (isinstance(band, (list, tuple)) and len(band) == 2
               and all(isinstance(v, (int, float)) for v in band))
    if not band_ok:
        ctx.err("reward.turnover_band", "must be [lo, hi]")
    else:
        blo, bhi = float(band[0]), float(band[1])
        if blo >= bhi:
            ctx.err("reward.turnover_band", "lo must be < hi")
        _rng(ctx, "reward.turnover_band[0]", blo, spec["turnover_band_lo"][0], spec["turnover_band_lo"][1])
        _rng(ctx, "reward.turnover_band[1]", bhi, spec["turnover_band_hi"][0], spec["turnover_band_hi"][1])

    _rng(ctx, "reward.lambda_band", rew.get("lambda_band"), spec["lambda_band"][0], spec["lambda_band"][1])
    if "hold_bonus" in rew:
        _rng(ctx, "reward.hold_bonus", rew["hold_bonus"], spec["hold_bonus"][0], spec["hold_bonus"][1])
    if "per_trade_penalty" in rew:
        _rng(ctx, "reward.per_trade_penalty", rew["per_trade_penalty"],
             spec["per_trade_penalty"][0], spec["per_trade_penalty"][1])
    if archetype == "mean_reversion":
        if "averaging_down_penalty" not in rew:
            ctx.err("reward.averaging_down_penalty",
                    "required for mean_reversion — averaging down is this family's classic death")
        else:
            _rng(ctx, "reward.averaging_down_penalty", rew["averaging_down_penalty"],
                 *S.COACH_RANGES["averaging_down_penalty"])
    elif "averaging_down_penalty" in rew:
        _rng(ctx, "reward.averaging_down_penalty", rew["averaging_down_penalty"],
             *S.COACH_RANGES["averaging_down_penalty"])

    # ── action ──────────────────────────────────────────────────────────────
    act = config.get("action") or {}
    rng = act.get("range")
    if not (isinstance(rng, (list, tuple)) and len(rng) == 2
            and all(isinstance(v, (int, float)) for v in rng)):
        ctx.err("action.range", "must be [lo, hi]")
    else:
        rlo, rhi = float(rng[0]), float(rng[1])
        cap = spec["position_cap"]
        if not (-1.0 <= rlo <= 0.0):
            ctx.err("action.range[0]", "lo must be in [-1, 0]")
        if not (0.0 < rhi <= 1.0):
            ctx.err("action.range[1]", "hi must be in (0, 1]")
        if abs(rlo) > cap or rhi > cap:
            ctx.err("action.range",
                    "%s positions are capped at ±%g of max" % (archetype, cap))

    bw = act.get("band_width")
    if bw not in S.BAND_WIDTHS:
        ctx.err("action.band_width", "must be one of %s" % (", ".join(S.BAND_WIDTHS)))
    elif bw not in spec["band_width"]:
        ctx.err("action.band_width",
                "%s uses %s" % (archetype, " or ".join(spec["band_width"])))

    mh_min = None
    try:
        mh_min = S.duration_to_minutes(act.get("min_holding"))
    except (ValueError, TypeError):
        ctx.err("action.min_holding", "must be a duration like '15m' or '4h'")
    if mh_min is not None:
        lo_m, hi_m = spec["min_holding_min"][0], spec["min_holding_min"][1]
        glo, ghi = S.MIN_HOLDING_BOUNDS_MIN
        if not (glo <= mh_min <= ghi):
            ctx.err("action.min_holding",
                    "platform envelope is %s-%s" % (S.minutes_to_duration(glo), S.minutes_to_duration(ghi)))
        elif not (lo_m <= mh_min <= hi_m):
            ctx.err("action.min_holding",
                    "%s holds %s-%s minimum" % (archetype, S.minutes_to_duration(lo_m), S.minutes_to_duration(hi_m)))

    if spec["time_stop_required"]:
        ts = act.get("time_stop")
        if ts is None:
            ctx.err("action.time_stop",
                    "required for %s — flat after N bars regardless of PnL" % archetype)
        else:
            try:
                ts_min = S.duration_to_minutes(ts)
                lo_t, hi_t = S.TIME_STOP_BOUNDS_MIN
                if not (lo_t <= ts_min <= hi_t):
                    ctx.err("action.time_stop", "must be between %s and %s"
                            % (S.minutes_to_duration(lo_t), S.minutes_to_duration(hi_t)))
                elif mh_min is not None and ts_min <= mh_min:
                    ctx.err("action.time_stop", "must be longer than min_holding")
            except (ValueError, TypeError):
                ctx.err("action.time_stop", "must be a duration like '6h'")

    lev = act.get("max_leverage", spec["default_leverage"])
    if not isinstance(lev, int) or not (1 <= lev <= S.MAX_LEVERAGE_EFFECTIVE):
        ctx.err("action.max_leverage",
                "1-%dx until a cross-competition track record unlocks more (platform schedule caps at %dx)"
                % (S.MAX_LEVERAGE_EFFECTIVE, S.MAX_LEVERAGE_SCHEDULE))

    # ── risk (user-set, bounded) ────────────────────────────────────────────
    rk = config.get("risk") or {}
    sl_ok = _rng(ctx, "risk.stop_loss", rk.get("stop_loss"), *S.STOP_LOSS_BOUNDS)
    tp_ok = _rng(ctx, "risk.take_profit", rk.get("take_profit"), *S.TAKE_PROFIT_BOUNDS)
    if sl_ok and tp_ok and rk["take_profit"] <= rk["stop_loss"]:
        ctx.err("risk.take_profit", "must be greater than stop_loss")

    # ── training ────────────────────────────────────────────────────────────
    tr = config.get("training") or {}
    steps = tr.get("steps")
    if not isinstance(steps, int):
        ctx.err("training.steps", "must be an integer")
    else:
        lo_s, hi_s = spec["steps"][0], spec["steps"][1]
        if not (lo_s <= steps <= hi_s):
            ctx.err("training.steps", "%s trains %dk-%dk steps"
                    % (archetype, lo_s // 1000, hi_s // 1000))
    aug = tr.get("augmentation", "off")
    if aug not in ("off", "block_bootstrap"):
        ctx.err("training.augmentation", "must be 'off' or 'block_bootstrap'")

    # ── breakeven-alpha screen (the hard gate) ──────────────────────────────
    be = None
    if interval and band_ok and not ctx.errors:
        be = breakeven_calc(interval, float(band[1]))
        if not be["passes"]:
            ctx.err("cadence.decision_interval",
                    "breakeven screen REJECTED this config: " + be["explanation"])
        elif interval in ("30s", "1m"):
            ctx.warn("cadence.decision_interval",
                     "%s cadence allowed only because the breakeven screen passes: %s"
                     % (interval, be["explanation"]))

    # ── degeneracy screens ──────────────────────────────────────────────────
    if band_ok and float(band[1]) <= 0:
        ctx.err("reward.turnover_band", "a zero band ceiling is a zero-trade degenerate agent")

    valid = not ctx.errors
    out = {"valid": valid, "errors": ctx.errors, "warnings": ctx.warnings,
           "breakeven": be}
    if valid:
        out["config"] = S.apply_platform_locks(config)
    return out
