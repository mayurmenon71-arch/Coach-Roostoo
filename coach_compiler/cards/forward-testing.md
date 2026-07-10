---
id: forward-testing
title: Forward testing — why backtests are diagnostics, not predictions
tags: backtest, overfitting, forward test, live, sharpe, prediction, results differ, why worse
---
A backtest is a training diagnostic, not a performance prediction. It is fit
to one historical path, rewards iteration until something matches by luck,
and the best evidence available (888 real strategies, the Quantopian cohort,
SSRN 2745220) shows backtest Sharpe predicts live performance at R^2 < 0.025
— essentially zero. Risk features (drawdown, turnover economics) predict
better than performance features.

That is exactly why Roostoo exists: the live paper-trading arena is the
forward test, run on unseen market data, with economic incentives (entry
fees, prize pools, XP) that make the track record costly to fake and
meaningful to earn. Deliver this clarification EVERY time backtests come up
— it turns the most awkward recurring question ("why did live differ from my
backtest?") into the platform's best pitch. Never rank or recommend agents on
backtest stats alone. Graduation decisions aggregate cumulative,
cross-competition track records across regimes — never a single event, and
hours-long competitions are entertainment, not evidence.
