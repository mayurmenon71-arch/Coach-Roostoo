---
id: agent-risk-management
title: Risk management — stop-loss, take-profit, and trade sizing
tags: risk, risk management, stop loss, stop-loss, take profit, take-profit, max trade, min trade, position size, sizing, liquidate, drawdown, safety, protect, blow up, limit losses, what values
---
Risk management is the deterministic safety layer ABOVE the learned policy. It
bounds an agent's behavior at execution time, on top of whatever the policy
learned in training. Four continuous percentages, configurable per agent:

| Parameter | Range | What it does |
|---|---|---|
| Stop-Loss | 1%-100% | % of the competition portfolio's value below which the portfolio is automatically liquidated |
| Take-Profit | 1%-100% | % of portfolio value above which the portfolio is automatically taken to profit |
| Max trade per order | 1%-100% of capital | Upper bound on the size of a single order |
| Min trade per order | 1%-100% of capital | Lower bound on the size of a single order |

WHY IT SITS OUTSIDE THE REWARD FUNCTION. The reward shapes how the agent learns
to balance return and risk during training. Risk management bounds behavior at
execution time regardless of what the policy decided. Two reasons that matters:

1. **Out-of-distribution states.** A trained policy can behave unpredictably in
   market conditions it never saw during training. Risk management caps the damage.
2. **Tier protection.** Pro/Elite hard demotion triggers at a -5% absolute loss on
   real prop capital. Risk management is the user's lever for keeping agents inside
   that bound.

CHOOSING VALUES — defaults are provided and deliberately conservative, suited to
early competition entry where the goal is testing without large losses. Practical
heuristics:
- Stop-Loss: 5-10% for general exposure; tighter (2-5%) for Elite-bound agents
  that must stay under the 8% per-competition drawdown threshold.
- Take-Profit: often left wide (20%+) so the agent can capture extended runs;
  tighter values realize gains faster but cap upside.
- Max trade per order: 10-25% of capital is a reasonable start. Higher means more
  concentration risk but larger potential returns; lower limits per-trade impact.
- Min trade per order: don't set it too low — sub-1% trades may not move the needle.

Note the division of labor: the reward metric (e.g. Volatility Penalty or Calmar)
shapes risk appetite during LEARNING; these four bounds enforce limits during
EXECUTION. They are complements, not substitutes — recommending only one when a
user asks how to control risk is an incomplete answer.

Planned additions: portfolio-level concentration caps (per-coin limits) and
drawdown-conditional auto-flatten triggers.
