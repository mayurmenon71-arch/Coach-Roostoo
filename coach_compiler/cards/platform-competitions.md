---
id: platform-competitions
title: Competitions, the envelope, and graduation
tags: competition, envelope, cadence, week, hours, forced flat, graduation, xp, leaderboard, regime
---
Roostoo targets short-term, medium-frequency trading: agents observe
continuously, decide every 30 seconds to 15 minutes, and hold positions from
tens of minutes up to a competition's end. Competitions run from a few hours
to at most a week; agents are FORCED FLAT at competition end, so remaining
time enters the observation vector. A few-hours competition mechanically
favors faster strategies; a week-long one lets multi-day holds breathe.

Excluded on both sides: high-frequency styles (market making, latency arb,
delta-neutral basis — a latency race retail agents cannot win) and
investing-horizon styles (weeks-to-months holds no arena can score). The
benchmark thesis: a well-built RL agent should out-trade the average human
day trader — fewer than 1% of day traders are predictably profitable net of
fees (Barber, Lee, Liu & Odean), and the two documented killers are
emotional overtrading and cost blindness, both engineered out by
construction. Hours-long leaderboards are dominated by variance — score them
for XP and engagement, but graduation aggregates cross-competition records
across regimes, never a single event.
