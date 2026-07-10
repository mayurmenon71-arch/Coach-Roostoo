---
id: archetype-mean-reversion
title: Mean reversion
tags: mean reversion, dip, buy the dip, rsi, bollinger, zscore, fade, overextension
---
Fade short-term overextensions back to a local mean. The most natural fit for
the Roostoo band — and the most fee-fragile. Fixed-rule twin (and benchmark):
"Buy when RSI(14) < 30 on 1m bars and price < lower Bollinger(20, 2sigma);
exit at mid-band; mirrored for shorts."

Sees: z-scores vs VWAP and rolling means, Bollinger %B, RSI/StochRSI,
short-horizon reversal returns, realized vol, funding extremes (crowding
proxy), position context, time-in-position. Wants: Sharpe flavor with tight
drawdown penalty; an asymmetric penalty on adding to losing positions —
averaging down is this family's classic death; the strictest turnover band in
the library. Acts: capped target position (e.g. +/-0.5 of max), tight band,
minimum holding 15m, hard time-stop (flat after N bars regardless of PnL).
Cadence: 1-5m decisions; holds 15 minutes to hours. Fee drag: HIGH.

What RL adds: learns which deviations revert versus which are the first leg
of a trend, by conditioning on volatility, regime, and funding — the
distinction a fixed 2-sigma band cannot make. Failure modes: catching falling
knives at regime breaks (guards: regime kill-switch, hard time-stop, capped
position); fee fragility (guard: breakeven-alpha screen at config time; 1m
cadence is allowed only when the screen passes). By design this family
underperforms in strong downtrends — name that trade-off out loud.
