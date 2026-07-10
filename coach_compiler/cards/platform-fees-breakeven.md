---
id: platform-fees-breakeven
title: Fees, the no-trade band, and the breakeven screen
tags: fees, cost, taker, spread, slippage, funding, turnover, band, breakeven, hurdle, bps
---
Two platform invariants apply to every agent, because without them agents die
on fees regardless of strategy: (1) the action space is a TARGET POSITION —
cost is charged only on position changes, so holding is the free default;
(2) the reward is NET of taker fees, spread, slippage, and funding, with a
drawdown penalty. These are not user choices.

Venue schedule (roostoo-sim): taker 4 bps/side, ~1.5 bps half-spread, ~1 bps
slippage — a round-trip position flip costs ~10.5 bps. The breakeven screen
turns cadence + turnover band into the exact gross-edge hurdle and BLOCKS
configs that cannot clear it (e.g. ~4 flips/day ~= 40 bps/day ~= ~12%/month
of gross edge needed before the agent nets a cent). 30s and 1m cadences are
offered only when the screen passes. Funding stays a mandatory cost term AND
a mandatory feature: in the best live-data RL evidence, 71% of a 5-year
agent's profit was funding capture (arXiv:2201.04699). Cadence buys reaction
speed, never trade frequency.
