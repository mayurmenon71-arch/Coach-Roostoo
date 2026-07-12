---
id: archetype-intraday-momentum
title: Momentum agent
tags: momentum, trend, ride, big moves, ema, breakout, directional, trend follow
---
A momentum agent rides sustained directional moves and sits out the chop —
small losses when the market is range-bound, bigger wins when a move runs.

In Roostoo v1 terms, a good momentum setup usually means: a calmer 15-minute
decision frequency (so it isn't whipsawed by every wiggle), a Sortino reward
(rewards upside, punishes downside swings), a wider stop-loss so a trend has
room to breathe, and a higher take-profit so winners can run. It still reads
all 8 indicators (RSI, ATR, VWAP, MACD, StochRSI, EMA Crossover, Bollinger,
OBV) — the trend-ish ones (EMA crossover, MACD) do the heavy lifting.

Honest trade-off: momentum agents underperform in flat, choppy markets — they
need a real move to work. It's long-only, so it profits from up-moves and
sits in cash otherwise.
