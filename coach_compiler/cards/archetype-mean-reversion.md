---
id: archetype-mean-reversion
title: Mean-reversion agent
tags: mean reversion, dip, buy the dip, rsi, bollinger, fade, overreaction, pullback, snap back
---
A mean-reversion agent buys pullbacks — it bets that a sharp drop overshoots
and price snaps back toward its recent average. Lots of small wins, with the
risk that a "dip" is actually the start of a real downtrend.

In Roostoo v1 terms, a typical setup: a faster 5-minute decision frequency (to
catch quick pullbacks), a Volatility-Penalty or Calmar reward (keeps it calm
and drawdown-averse — the "never blow up" part), a tight stop-loss to cap the
damage when a dip keeps dipping, a modest take-profit (it books small bounces),
and a smaller max trade size so no single bad entry sinks it. RSI, Bollinger
Bands and VWAP (all always on) are the natural fit.

Honest trade-off: by design it struggles in strong one-way trends, and since
it's long-only it can only fade drops, not rallies.
