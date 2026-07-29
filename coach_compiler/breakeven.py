"""
The fee hurdle (breakeven-alpha) calculator — Rules to Rewards v1.2, Section 7.6
and 8.1's ``breakeven_calc`` tool.

Purpose (from the paper): "Before training, show — at this cadence and band,
this agent must overcome ~X% in fees before it nets a cent. Block configs where
X is implausible." It is BOTH the single best fee-education moment in the product
AND the gate that makes fast cadences safe to offer. Crucially, the paper insists
this number is deterministic Python, never LLM arithmetic:

    "The number gates configs, so it must be exact, deterministic, and identical
     to what the factory enforces — LLM arithmetic is neither."

So this module is the one source of truth. The gene card renders its output; the
Coach LLM never computes a fee number in prose (see prompt.py NUMBERS POLICY).

── The cost model ───────────────────────────────────────────────────────────
A "position flip" (a full round trip: enter then exit) on Roostoo's perp venue
costs taker fees on both sides plus spread and slippage. The paper pins this at
"roughly 9-12 bps round-trip"; we build it from components so it stays auditable:

    round-trip = 2 x taker_fee_per_side + spread + slippage
               = 2 x 4.0 + 1.5 + 1.0  =  10.5 bps

That reproduces the paper's own worked example exactly (Section 8.1):
    4 position flips/day x ~10 bps  ~=  40 bps/day  ~=  ~12%/month of gross edge
    required before the agent nets a cent.

── v1 adaptation ────────────────────────────────────────────────────────────
The paper's ``breakeven_calc`` keys off ``decision_interval`` + an explicit
``turnover_band``. The v1 registry (schema.py) exposes neither a turnover band
nor a separate decision interval — it has ``candle_interval`` (the decision
clock) and the four strategy personalities. So ``estimate_for_config`` derives an
expected turnover from (candle_interval x archetype): each personality has a
characteristic trades-per-day profile, and a faster clock lifts it. This is the
honest bridge — turnover is estimated, the cost per flip is exact — and it lets
the already-scaffolded fee-drag band on the gene card light up for real configs.
"""

from . import schema as S

# ── Venue cost components (basis points) ────────────────────────────────────
# Perp taker fee per side, plus half-spread and slippage the simulator's honest
# cost model charges on a fill. Tunable in one place if the venue schedule moves.
TAKER_FEE_BPS_PER_SIDE = 4.0
SPREAD_BPS = 1.5
SLIPPAGE_BPS = 1.0

# A full round trip pays taker on BOTH sides, plus spread + slippage once.
ROUND_TRIP_COST_BPS = 2 * TAKER_FEE_BPS_PER_SIDE + SPREAD_BPS + SLIPPAGE_BPS  # 10.5

# Decision steps per 24h for each cadence (used as the physical ceiling on how
# often an agent could possibly flip). 30s/1m are the paper's gated fast band;
# v1 exposes 1m/5m/15m.
DECISION_STEPS_PER_DAY = {"30s": 2880, "1m": 1440, "5m": 288, "15m": 96}

TRADING_DAYS_PER_MONTH = 30
TRADING_DAYS_PER_YEAR = 365

# ── Fee-drag tiers (on cost in bps per day) ─────────────────────────────────
# LOW aligns with the peer-reviewed ~25 bps/unit-turnover cost-tolerance ceiling
# (Section 1). Above SCREEN_MAX the config trips the breakeven screen: it must
# out-earn an implausible amount in fees, so the paper says gate it. In v1 the
# gene card surfaces this as a prominent warning rather than a hard block.
FEE_DRAG_LOW_BPS = 25.0
SCREEN_MAX_DAILY_BPS = 40.0

# ── Expected round trips per day, by personality x decision clock ────────────
# Anchored to the paper's archetype profiles (Section 4 / the Section 6 fee-drag
# column): momentum & breakout trade rarely (wide bands, long holds); mean
# reversion is "the most fee-fragile" and churns; flow-driven is signal-paced.
# A faster clock raises the count. These are deliberate, documented estimates —
# the number that matters for gating (cost per flip) is exact.
ARCHETYPE_ROUND_TRIPS_PER_DAY = {
    "intraday_momentum": {"15m": 1.0, "5m": 2.0, "1m": 4.0},
    "breakout":          {"15m": 0.7, "5m": 1.4, "1m": 2.8},
    "flow_driven":       {"15m": 1.5, "5m": 3.0, "1m": 6.0},
    "mean_reversion":    {"15m": 1.8, "5m": 3.5, "1m": 7.0},
}
# Fallback profile when the archetype is unknown (a middle-of-the-road agent).
_DEFAULT_ROUND_TRIPS_PER_DAY = {"15m": 1.2, "5m": 2.5, "1m": 5.0}

# Friendly, user-safe personality label for the gene card. The product never
# shows raw archetype ids (see prompt.py TONE) — these plain words are fine.
ARCHETYPE_LABEL = {
    "intraday_momentum": "momentum",
    "mean_reversion": "mean reversion",
    "breakout": "breakout",
    "flow_driven": "flow-driven",
}


def fee_drag_label(cost_bps_per_day):
    """Low / Moderate / High, matching the paper's fee-drag column."""
    if cost_bps_per_day <= FEE_DRAG_LOW_BPS:
        return "Low"
    if cost_bps_per_day <= SCREEN_MAX_DAILY_BPS:
        return "Moderate"
    return "High"


def _hurdle(round_trips_per_day, decision_interval):
    """The core arithmetic: round trips/day -> the fee hurdle, every way we quote
    it. Pure and deterministic; both entry points below funnel through here."""
    rt = ROUND_TRIP_COST_BPS
    cost_bps_per_day = round_trips_per_day * rt
    drag = fee_drag_label(cost_bps_per_day)
    return {
        "decision_interval": decision_interval,
        "round_trips_per_day": round(round_trips_per_day, 2),
        "round_trip_cost_bps": round(rt, 2),
        "cost_bps_per_day": round(cost_bps_per_day, 2),
        # bps/day x days / 100 -> percent of gross edge required.
        "daily_hurdle_pct": round(cost_bps_per_day / 100.0, 3),
        "monthly_hurdle_pct": round(cost_bps_per_day * TRADING_DAYS_PER_MONTH / 100.0, 1),
        "annual_hurdle_pct": round(cost_bps_per_day * TRADING_DAYS_PER_YEAR / 100.0, 0),
        "fee_drag": drag,
        # The breakeven screen: does the hurdle stay plausible?
        "passes_screen": cost_bps_per_day <= SCREEN_MAX_DAILY_BPS,
    }


def breakeven_calc(decision_interval, turnover_band_hi):
    """Paper-faithful primitive (Section 8.1): cadence + a turnover-band ceiling
    -> the exact cost hurdle. ``turnover_band_hi`` is the top of the band in full
    position round trips PER HOUR; capped by the cadence's physical step ceiling.

    Kept for parity with the paper's schema and for callers that DO carry an
    explicit turnover band. The v1 gene card uses ``estimate_for_config``."""
    if decision_interval not in DECISION_STEPS_PER_DAY:
        raise ValueError("unknown decision_interval: %r" % (decision_interval,))
    hi = float(turnover_band_hi)
    if hi < 0:
        raise ValueError("turnover_band_hi must be >= 0")
    steps_per_day = DECISION_STEPS_PER_DAY[decision_interval]
    round_trips_per_day = min(hi * 24.0, float(steps_per_day))
    return _hurdle(round_trips_per_day, decision_interval)


def _explanation(h, drag):
    """A plain-language line for the gene card's breakeven band. No jargon, no
    turnover-band talk — just what it costs and what it must clear."""
    rtpd = h["round_trips_per_day"]
    # "about N times a day" reads better than a bare float.
    if rtpd < 1:
        freq = "less than once a day"
    elif rtpd < 1.5:
        freq = "about once a day"
    else:
        freq = "roughly %g times a day" % round(rtpd)
    lead = {
        "Low": "Light fee drag.",
        "Moderate": "Moderate fee drag.",
        "High": "Heavy fee drag — watch this one.",
    }[drag]
    return ("%s It changes position %s. Each round trip costs about %g bps in "
            "fees, spread and slippage, so it has to out-earn roughly %g%%/month "
            "in costs before it turns a profit."
            % (lead, freq, h["round_trip_cost_bps"], h["monthly_hurdle_pct"]))


def estimate_for_config(config, archetype=None):
    """The v1 gene-card entry point. Derives expected turnover from
    (candle_interval x archetype), runs the cost model, and returns a card-ready
    block: the numbers, the fee-drag tier, a plain-language explanation, and a
    ready-to-append warning when the config trips the breakeven screen.

    Never raises on a plausible v1 config: an unknown candle_interval falls back
    to 5m and an unknown archetype to a middle profile, so this can run on any
    validated config without guarding the call site."""
    interval = (config or {}).get("candle_interval")
    if interval not in DECISION_STEPS_PER_DAY:
        interval = "5m"
    table = ARCHETYPE_ROUND_TRIPS_PER_DAY.get(archetype, _DEFAULT_ROUND_TRIPS_PER_DAY)
    round_trips_per_day = table.get(interval, _DEFAULT_ROUND_TRIPS_PER_DAY.get(interval, 2.5))

    h = _hurdle(round_trips_per_day, interval)
    h["archetype_label"] = ARCHETYPE_LABEL.get(archetype, "trading")
    h["explanation"] = _explanation(h, h["fee_drag"])

    # When the screen fails, hand back a warning the card can surface verbatim.
    # This is the paper's "block configs where X is implausible" — rendered as a
    # loud, honest caution in v1 rather than a hard rejection.
    if not h["passes_screen"]:
        h["warning"] = {
            "path": "fee_hurdle",
            "message": ("At this clock this personality trades often, so it must "
                        "clear ~%g%%/month in fees before it profits. A slower "
                        "clock would cut that sharply."
                        % h["monthly_hurdle_pct"]),
        }
    return h


def scalping_refusal_numbers():
    """The exact numbers behind the sub-30s / scalping refusal (Section 4.5).
    Deterministic so the refusal is always precise if a surface wants to quote
    it — an agent flipping every minute would pay ~R x 1440 bps/day."""
    flip = ROUND_TRIP_COST_BPS
    per_min_day_bps = flip * 60 * 24  # a flip every minute, all day
    return {
        "round_trip_cost_bps": round(flip, 2),
        "per_minute_day_bps": round(per_min_day_bps, 0),
        "example": ("a position flip costs ~%g bps round-trip; an agent flipping "
                    "every minute would need to clear ~%s bps/day — more edge "
                    "per minute than well-run funds earn per day — before an "
                    "infrastructure latency race it cannot win at retail"
                    % (flip, format(int(round(per_min_day_bps)), ","))),
    }
