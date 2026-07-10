---
id: archetype-intraday-momentum
title: Intraday momentum / trend
tags: momentum, trend, ride, big moves, ema, adx, directional
---
Ride directional moves lasting hours to days; lose small in chop, win big when
the move runs. Fixed-rule twin (and benchmark): "Long when EMA(20) > EMA(100)
on 5m bars and ADX > 25; exit on cross-down; 2xATR trailing stop."

Sees: multi-horizon returns (ROC), EMA-cross distances, MACD histogram, ADX,
ATR, Donchian distance, trend-vs-chop regime label, position context,
competition time-remaining. Wants: PnL or Sortino flavor; moderate drawdown
penalty; hold bonus weighted up; strong turnover band — trend agents should
trade rarely even when deciding every 5 minutes. Acts: target position
[-1,+1], wide no-trade band, minimum holding 2-12h, vol-scaled sizing.
Cadence: 5-15m decisions; holds hours to competition end. Fee drag: LOW.

What RL adds over the rule: learned, volatility-conditional entry/exit
thresholds; continuous sizing scaled to trend strength; learned suppression
of entries in chop. Failure modes: whipsaw churn in range-bound markets
(guard: wide band + regime feature + turnover penalty); late entries and
give-back at reversals (guard: platform trailing stop). Watch for the
leveraged-long impostor — a maxed-long degenerate policy looks like a great
momentum agent in a bull window; the fidelity audit catches it.
