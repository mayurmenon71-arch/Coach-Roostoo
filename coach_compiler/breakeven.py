"""
Step 2 — breakeven_calc: the single most important gate in the factory.

Turns cadence + turnover band + venue fees into the exact cost hurdle.
The number gates configs, so it must be exact, deterministic, and identical
to what the factory enforces — LLM arithmetic is neither. Coach quotes the
number; the validator uses the same call as a hard gate.

Units. turnover_band is expressed as expected |Δposition| per HOUR, as a
fraction of max position (so a value of 0.10 means the agent moves a tenth
of a full position per hour on average). A full round trip (in and out of a
full position) is |Δposition| = 2. This calibration reproduces the paper's
worked example: ~4 position flips/day × ~10 bps round-trip ≈ 40 bps/day ≈
~12%/month of gross edge required before the agent nets a cent.

Venue fee schedule (roostoo-sim, per side / per round trip):
    taker fee   4.0 bps × 2 sides = 8.0 bps
    half-spread 1.5 bps
    slippage    1.0 bps
    ------------------------------------
    round-trip flip cost ≈ 10.5 bps  (inside the doc's 9–12 bps window)
"""

from .schema import DECISION_INTERVALS, STEPS_PER_DAY

# ── Venue fee schedule (PLATFORM — never user- or Coach-tunable) ─────────────
TAKER_FEE_BPS_PER_SIDE = 4.0
SPREAD_BPS = 1.5
SLIPPAGE_BPS = 1.0
ROUND_TRIP_COST_BPS = TAKER_FEE_BPS_PER_SIDE * 2 + SPREAD_BPS + SLIPPAGE_BPS  # 10.5

# ── The gate ─────────────────────────────────────────────────────────────────
# Configs whose band ceiling implies more than this much cost bleed per day
# are rejected at config time — zero compute wasted on doomed agents.
# The peer-reviewed cost-tolerance ceiling (~25 bps per unit turnover,
# arXiv:1911.10107) was measured at DAILY cadence; at 30s–15m cadences the
# band is more load-bearing, not less, so fast cadences get a tighter gate.
MAX_DAILY_COST_BPS = {"30s": 25.0, "1m": 35.0, "5m": 40.0, "15m": 40.0}

TRADING_DAYS_PER_MONTH = 30       # crypto trades every day
TRADING_DAYS_PER_YEAR = 365


def breakeven_calc(decision_interval, turnover_band_hi):
    """Deterministic fee-hurdle computation.

    Args:
        decision_interval: one of DECISION_INTERVALS ("30s"|"1m"|"5m"|"15m")
        turnover_band_hi:  band ceiling, expected |Δposition| per hour

    Returns a dict with every number Coach is allowed to quote, plus
    `passes` (bool) and a plain-language `explanation`.
    """
    if decision_interval not in DECISION_INTERVALS:
        raise ValueError("unknown decision_interval: %r" % (decision_interval,))
    hi = float(turnover_band_hi)
    if hi < 0:
        raise ValueError("turnover_band_hi must be >= 0")

    steps_per_day = STEPS_PER_DAY[decision_interval]

    # Expected daily position movement and its cost.
    daily_turnover = hi * 24.0                       # |Δposition| per day
    round_trips_per_day = daily_turnover / 2.0       # full flip = |Δ| of 2
    cost_bps_per_day = round_trips_per_day * ROUND_TRIP_COST_BPS

    # Physical ceiling: the agent cannot move more than one full position
    # per decision step, whatever the band says.
    max_possible_turnover = steps_per_day * 2.0
    daily_turnover = min(daily_turnover, max_possible_turnover)

    monthly_hurdle_pct = cost_bps_per_day * TRADING_DAYS_PER_MONTH / 100.0
    annual_hurdle_pct = cost_bps_per_day * TRADING_DAYS_PER_YEAR / 100.0

    gate = MAX_DAILY_COST_BPS[decision_interval]
    passes = cost_bps_per_day <= gate

    explanation = (
        "At a {iv} cadence with a turnover-band ceiling of {hi:g}/hr, this agent "
        "can change position up to ~{dt:.1f} position-units/day (~{rt:.1f} round "
        "trips). At ~{flip:.1f} bps per round trip that is ~{cbd:.1f} bps/day — "
        "~{mo:.1f}%/month (~{yr:.0f}% annualized) of gross edge required before "
        "the agent nets a cent. Gate at {iv}: {gate:.0f} bps/day → {verdict}."
    ).format(iv=decision_interval, hi=hi, dt=daily_turnover,
             rt=round_trips_per_day, flip=ROUND_TRIP_COST_BPS,
             cbd=cost_bps_per_day, mo=monthly_hurdle_pct, yr=annual_hurdle_pct,
             gate=gate, verdict="PASSES" if passes else "REJECTED")

    return {
        "decision_interval": decision_interval,
        "turnover_band_hi_per_hr": hi,
        "steps_per_day": steps_per_day,
        "daily_turnover_units": round(daily_turnover, 4),
        "round_trips_per_day": round(round_trips_per_day, 4),
        "round_trip_cost_bps": ROUND_TRIP_COST_BPS,
        "cost_bps_per_day": round(cost_bps_per_day, 2),
        "monthly_hurdle_pct": round(monthly_hurdle_pct, 2),
        "annual_hurdle_pct": round(annual_hurdle_pct, 1),
        "gate_bps_per_day": gate,
        "passes": passes,
        "explanation": explanation,
    }


def scalping_refusal_numbers():
    """The numbers Coach quotes when refusing sub-30s / scalping asks
    (Section 4.5). Deterministic so the refusal is always exact."""
    flips_per_hour = 60  # "flipping every minute"
    cost_bps_per_day = flips_per_hour * 24 * ROUND_TRIP_COST_BPS
    return {
        "round_trip_cost_bps": ROUND_TRIP_COST_BPS,
        "example": (
            "a position flip costs ~{flip:.0f} bps round-trip; an agent flipping "
            "every minute would need to clear ~{day:,.0f} bps/day — more edge per "
            "minute than well-run funds earn per day — before an infrastructure "
            "latency race it cannot win at retail"
        ).format(flip=ROUND_TRIP_COST_BPS, day=cost_bps_per_day),
    }
