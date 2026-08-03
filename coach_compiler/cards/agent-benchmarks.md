---
id: agent-benchmarks
title: How agents are scored — the 3D Fitness Vector and per-episode metrics
tags: benchmark, score, grade, evaluation, evaluation card, fitness vector, pareto, m-factor, survival floor, profit probability, drawdown, win rate, episode, metrics, how is my agent judged
---
Every agent built in the Factory is scored against a standardized evaluation suite,
reported on a pre-deployment evaluation card and again after every live competition.

THE 3D FITNESS VECTOR — a Pareto-style evaluation across three independent axes at
once, rather than collapsing everything into a single Sharpe ratio (which rewards
lucky-peak agents whose worst runs erase months of gains). Each axis penalizes a
different failure mode:

- **M-Factor Robustness** — consistency across regimes. Anchors on the 25th
  percentile of per-episode returns, so an agent only scores well if its
  bottom-quartile runs still clear a 2% benchmark; an interquartile-range
  denominator sharply shrinks the score for high-variance returns.
- **Survival Floor** — worst-case drawdown floor: the 10th percentile of max
  drawdown across episodes. Higher (less negative) is better, so -5% beats -20%.
  An agent that survives normal markets but breaks in stressed regimes scores badly.
- **Profit Probability** — win-rate consistency, same shape as M-Factor Robustness
  but applied to raw net returns.

Why three: improving one usually costs another — a high-return agent may have
catastrophic drawdowns, a low-drawdown agent may be too conservative to clear the
benchmark. An agent's standing is its position on the Pareto frontier across all
three, not an average of them.

PER-EPISODE METRICS, computed for every backtest and live competition episode and
listed individually on the evaluation card: net return, log return, average return,
max drawdown, win rate (share of episodes with net return >= +1%), best episode,
worst episode, volatility (standard deviation of episode returns), and trade
count / turnover with average holding period. An "episode" is one full evaluation
window — a single backtest replay, or a single live competition open to close.

WHERE PUBLISHED: per-agent on the evaluation card (multi-regime historical data),
per-competition on-chain with the full leaderboard, and quarterly in the aggregated
RL Trading Benchmark Report.

Keep the honest framing: the evaluation card is a diagnostic, not a forecast. A
strong card can still be an overfit card — the live arena on unseen data is the
test that counts.
