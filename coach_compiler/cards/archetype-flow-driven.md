---
id: archetype-flow-driven
title: Fast signal / flow-driven
tags: flow, funding, liquidation, cascade, panic, news, open interest, squeeze, plumbing
---
Trade the market's plumbing: funding swings, OI shocks, liquidation cascades,
breaking-news risk. Fixed-rule twin (and benchmark): "If funding flips
sharply negative while OI spikes and price holds above VWAP support, go long
the squeeze; exit when flow normalizes."

Sees: funding changes and extremes, OI deltas, liquidation-cascade intensity,
volume/flow imbalance, spot-perp basis moves, sentiment spikes, LLM-scored
breaking-news risk, baseline price/vol features, position context. Wants:
CVaR or Sharpe flavor — event trades have fat tails, so tail-aware objectives
fit; moderate turnover band paced to signal-state changes. Acts: target
position; band calibrated so the agent effectively trades only when the flow
state changes; minimum holding 1h. Cadence: 1-15m decisions; holds hours.
Fee drag: MEDIUM.

What RL adds: this is where RL most clearly beats rules — it learns the
response function (magnitude, decay, interactions across several weak, fast
signals) instead of hand-set thresholds on each. The right way to use LLMs is
upstream as features, not in the execution loop (FinRL-DeepSeek,
arXiv:2502.07393). Slow on-chain valuation signals (MVRV, NVT) are out.
Failure modes: stale/repainted data (guard: point-in-time discipline); event
clustering creating correlated over-sizing (guard: vol-scaled sizing +
exposure caps); fewer effective samples for rare events — elevated overfit
risk, so expect the platform to demand a longer cross-competition record.
