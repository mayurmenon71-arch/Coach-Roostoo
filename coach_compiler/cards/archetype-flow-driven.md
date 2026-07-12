---
id: archetype-flow-driven
title: Flow-driven agent
tags: flow, funding, liquidation, cascade, panic, open interest, squeeze, plumbing
---
A flow-driven agent reacts to the market's "plumbing" — funding-rate swings and
liquidation cascades that spike when the crowd gets offside. It tries to buy
the panic and ride the snap-back.

In Roostoo v1 terms: a fast 5-minute decision frequency (flow flips quickly), a
Calmar reward (return relative to worst drawdown — tail-aware, which suits
spiky events), a fairly tight stop-loss to bail if the panic keeps going, and a
moderate take-profit. It reads all 8 indicators; VWAP and RSI help it judge how
stretched things are.

Honest trade-off: the events it lives for are rare, so it can sit quiet for a
while and its live track record matters more than any single backtest. It's
long-only — it buys panics, it doesn't short blow-off tops.
