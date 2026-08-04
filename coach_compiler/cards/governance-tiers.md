---
id: governance-tiers
title: Who sets what — user vs coach vs platform
tags: governance, user, coach, platform, fixed, gene card, who picks, can I change
---
On the gene card, each value is tagged by who controls it:

- YOU choose: which coins the agent trades, and its risk settings — stop-loss,
  take-profit, and the max/min trade size per order (each 1%-100%).
- COACH suggests (you can change): the signal family and strategy variant
  (which together fix the indicators the agent sees), the decision frequency
  (1m, 5m or 15m), the reward metric, and the training length — inferred from
  what you described, shown so you can confirm or tweak.
- PLATFORM fixes (not changeable): it's a PPO agent, it always sees the 7
  base features (log-return, volume ratio, hour, weekday, cash ratio,
  position ratio, unrealized PnL), it reads the last 50 candles, it trains on
  full history, and it's long-only. There are no stop-loss / take-profit /
  trade-size knobs — exits and sizing are learned by the policy, and the
  reward choice is how you shape its risk appetite.

The idea: you own the preferences, Coach maps your words to sensible settings,
and the platform locks the parts that keep every agent sound. The worst a bad
choice can produce is a mediocre agent, not a broken one.
