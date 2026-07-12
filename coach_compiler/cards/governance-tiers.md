---
id: governance-tiers
title: Who sets what — user vs coach vs platform
tags: governance, user, coach, platform, fixed, gene card, who picks, can I change
---
On the gene card, each value is tagged by who controls it:

- YOU choose: which coins, and your risk settings — stop-loss, take-profit, and
  the max/min trade size per order.
- COACH suggests (you can change): the decision frequency (5m or 15m), the
  reward metric, and the training length — inferred from what you described,
  shown so you can confirm or tweak.
- PLATFORM fixes (not changeable): it's a PPO agent, it always uses all 8
  indicators together (no picking a subset), it reads the last 50 candles, it
  trains on full history, and it's long-only.

The idea: you own the preferences, Coach maps your words to sensible settings,
and the platform locks the parts that keep every agent sound. The worst a bad
choice can produce is a mediocre agent, not a broken one.
