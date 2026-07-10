---
id: archetype-breakout
title: Breakout / volatility expansion
tags: breakout, squeeze, volatility expansion, range, donchian, compression
---
Buy strength out of compression; asymmetric bets on range expansion.
Fixed-rule twin (and benchmark): "Buy a 12h-high breakout when realized vol
sits below its 3-day 20th percentile; 2xATR trailing stop."

Sees: Donchian high/low distances, squeeze metrics (Bollinger-width
percentile, ATR percentile), volume surge ratio, open-interest change,
session/time features, position context. Wants: PnL/Sortino flavor tolerant
of tail-seeking (skewed payoffs are the point); moderate drawdown penalty;
a meaningful per-trade penalty — true breakouts are rare, so trading should
be too. Acts: near-discrete {-1, 0, +1} with fast full-size entry, learned
trailing exit, post-entry lockup (min holding 1h). Cadence: 1-5m decisions;
holds hours to days. Fee drag: MEDIUM.

What RL adds: false-breakout filtering — the rule fires on every channel
poke, while the policy learns the joint signature (squeeze depth x volume x
OI change x funding) that separates expansions from traps. Failure modes:
churn on failed breakouts in mean-reverting regimes (guards: per-trade
penalty, post-entry lockup); gap risk on entry slippage during fast moves
(guard: honest slippage term in the simulator, taker-fee-inclusive reward).
