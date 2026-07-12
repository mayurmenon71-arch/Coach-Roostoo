---
id: archetype-breakout
title: Breakout agent
tags: breakout, squeeze, volatility expansion, range, compression, consolidation, explosive
---
A breakout agent waits for a quiet, compressed range and then jumps on the
expansion when price finally breaks out. Real breakouts are rare, so it trades
seldom and accepts small losses on false starts to catch the occasional big
move.

In Roostoo v1 terms: works at either 5-minute or 15-minute frequency, a
Sortino reward (it wants the skewed, catch-the-big-move payoff), a moderate
stop-loss to bail on failed breakouts, and a high take-profit to let a real
expansion run. Bollinger Bands and ATR (always on) capture the "squeeze then
expansion" shape.

Honest trade-off: in a market that just chops sideways it will keep getting
faked out on small losses while it waits — the wins come from the few moves
that actually run. Long-only, so it plays upside breakouts.
