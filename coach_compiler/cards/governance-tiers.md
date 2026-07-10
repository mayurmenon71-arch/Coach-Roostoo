---
id: governance-tiers
title: Who sets what — the three governance tiers
tags: governance, user, coach, platform, locked, leverage, gene card, tiers, who picks
---
Users own identity-level choices — what kind of trader, which assets, how
much risk — because those are preferences, not engineering. Coach owns
calibration-level choices within validated ranges, because an LLM is good at
mapping "I hate getting chopped up" to a wider band and a longer minimum
hold, and bad at inventing reward mathematics. The platform owns
survival-level invariants — cost-inclusive rewards, position context, vol
targeting, ensembling (3-5 seeds, averaged policy), multi-regime training,
evaluation gates — because these are the difference between a factory that
mass-produces fee victims and one that produces plausible competitors.

The governing rule: any parameter whose wrong value produces a fee-blind or
degenerate agent is never user-tunable. Leverage is a platform schedule
(1-5x gated by demonstrated track record; users may always go LOWER — this
build caps at 2x). With survival invariants locked, the worst any user or
LLM error can produce is a mediocre agent, not a dangerous one. Every
Coach-inferred value appears on the gene card with one sentence of reasoning
and stays editable there.
