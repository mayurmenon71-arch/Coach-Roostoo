---
id: reward-terms
title: Reward metrics — what each one optimizes
tags: reward, sharpe, sortino, calmar, entropy, volatility penalty, risk adjusted
---
The reward metric is what the agent is trained to maximize — it shapes the
agent's whole personality. You pick exactly one. The five options in Roostoo
v1:

- Sharpe Ratio — return per unit of total volatility. A balanced, all-round
  risk-adjusted choice.
- Sortino Ratio — like Sharpe but only penalizes DOWNSIDE volatility, so it
  doesn't punish big up-moves. Good for trend/momentum agents that want to let
  winners run.
- Calmar Ratio — return relative to the worst drawdown. Tail-aware; suits
  spiky, event-driven styles that must survive sharp reversals.
- Entropy — rewards keeping the policy varied/exploratory rather than
  collapsing onto one repeated bet; useful against over-fitting to one pattern.
- Volatility Penalty — directly penalizes volatility, producing the calmest,
  most drawdown-averse behavior. The natural pick for "steady" / "never blow
  up" agents.

There are no separate weight knobs to tune — you choose the metric and the RL
training does the rest.
