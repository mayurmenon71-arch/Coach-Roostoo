---
id: rl-vs-rules
title: What an RL agent is (vs a fixed-rule bot, vs an LLM trader)
tags: rl, reinforcement learning, ppo, rules, bot, llm trader, thresholds, features, reward, prior
---
The sentence to teach every user: in a fixed-rule bot, the human picks the
signals AND the thresholds; in an RL agent, you pick what it SEES (features),
what it WANTS (reward), and how it is allowed to ACT (constraints) — and it
learns the thresholds itself. "Buy when RSI < 30" is a single hand-picked
point in exactly the space Roostoo exposes: RSI is an observation choice, 30
is a threshold the policy can learn, "buy" is an action-space choice, and
"until it reverts" is a reward choice.

A signal family + strategy variant is therefore a PRIOR, not a rule: the
variant is a curated indicator subset, paired with a reward shape and a
cadence, that biases the learned policy toward that family's style — while
thresholds, sizing, and timing are learned from data. Each family ships with
its fixed-rule twin as a
mandatory benchmark in the same simulator with identical costs — "did
learning add anything over the rule?" is always on the chart. LLMs do not
belong in the execution loop: in the only public real-money arena (Alpha
Arena, live Hyperliquid perps), four of six frontier LLMs lost money. Their
strength is upstream — research, feature scoring, intent translation.
