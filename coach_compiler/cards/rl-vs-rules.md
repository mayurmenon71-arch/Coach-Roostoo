---
id: rl-vs-rules
title: Why RL for trading — RL vs static rules, supervised ML and LLMs
tags: rl, reinforcement learning, why rl, ppo, static rules, supervised ml, llm, rules bot, sequential decision, reward feedback, adaptation, why not llm, why not rules
---
Trading is a sequential decision problem with reward feedback: observe, act, receive
a return, update. That is the shape reinforcement learning was built for. The hard
part was never training an agent in a sandbox — it was running one against live
markets at scale, with reward signals that do not lie to the policy. Roostoo is built
to solve that part in the open.

FOUR WAYS TO AUTOMATE A TRADE:

| | Static rules | Supervised ML | LLM strategies | RL agent |
|---|---|---|---|---|
| Learns from outcomes in deployment | No | No | No | Yes |
| Signal, sizing and risk optimised together | No | No | No | Yes |
| Same input, same output | Yes | Yes | No | Yes |
| Decision latency | Milliseconds | Milliseconds | Seconds | Milliseconds |
| Cost per decision | Negligible | Negligible | High | Negligible |
| Where it breaks | Regime shifts | Errors compound through sizing | Slow, expensive, no reward signal | Needs a truthful reward loop |

WHERE THE ALTERNATIVES BREAK:
- **Static rules** (moving-average crossovers, RSI thresholds, mean-reversion bands)
  — performance is locked at design time, and a regime shift means re-engineering by
  hand.
- **Supervised ML** — a model forecasts price, then a separate rules layer turns the
  forecast into a position and a stop. Prediction error compounds through sizing and
  risk, and nothing re-optimises the whole pipeline when the regime changes.
- **LLM strategies** — token-by-token reasoning is too slow for execution and too
  expensive to scale, and with no native reward signal every improvement means
  re-prompting and offline human evaluation.

WHY RL FITS:
- Reward-driven adaptation — the policy learns directly from outcomes and keeps
  updating as the regime shifts.
- End-to-end optimisation — signal, position size and exit are learned jointly, so no
  stage compensates for another's error.
- Fast inference — a forward pass takes milliseconds, competitive with hand-written
  rules and far ahead of an LLM.

WHAT ROOSTOO IS BETTING ON: that open, continuous evaluation produces better trading
agents than closed-shop research. The bet is falsifiable — every agent's record is
on-chain, and every competition closes with a verifiable result.
