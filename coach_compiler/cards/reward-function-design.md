---
id: reward-function-design
title: Reward function design — the five objectives and when to pick each
tags: reward, reward function, sharpe, sortino, calmar, entropy, volatility penalty, objective, optimise, which reward, risk adjusted, drawdown
---
The reward is the signal a reinforcement-learning agent optimises during training. It
decides how the policy trades off return against volatility, drawdown and exposure.
Every agent picks exactly one.

| Reward | What it optimises | Pick it when |
|---|---|---|
| Sharpe | Excess return per unit of total volatility | You want the balanced default |
| Sortino | Excess return per unit of downside deviation | You mind drawdowns more than upside swings |
| Calmar | Return divided by max drawdown | You want peak-to-trough loss punished hard |
| Entropy | Diverse action distributions | You want exploration and no premature lock-in on one strategy |
| Volatility Penalty | Return minus a volatility cost | You want a smooth equity curve above all |

After the signal family, the reward is the largest single influence on how an agent
trades. Two agents with identical markets, features and timing but different rewards
can look nothing alike: one scales into trends aggressively, the other holds smaller
and steadier. Read the decision log after a competition and you will see the reward's
fingerprints on every sizing call.

Custom rewards are not exposed yet. New ones are added when production data shows
where the current five fall short, or when a community proposal through Research is
instrumented and published.
