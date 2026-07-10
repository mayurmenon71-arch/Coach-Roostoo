---
id: reward-terms
title: Reward terms — what each knob does
tags: reward, sharpe, sortino, calmar, cvar, drawdown, lambda, hold bonus, penalty, turnover band
---
Flavor: PnL (raw return), Sharpe (return per unit total vol), Sortino
(penalizes downside vol only — fits trend riders with skewed payoffs),
Calmar (return over max drawdown), CVaR(alpha) (optimizes the loss tail
explicitly — fits fat-tailed event trades). Locked add-ons for everyone:
fee/funding-inclusive PnL and a drawdown penalty.

Coach-tunable within ranges: lambda_dd 0.05-0.50 (drawdown aversion — "never
blows up" maps high); turnover_band [lo, hi] with zero penalty inside the
band and lambda_band outside (the band is measured as expected position
change per hour — the ceiling implies a concrete number of position flips
per day, which the breakeven screen prices in bps); hold_bonus 0-0.05 (paid
only while profitable and low-drawdown — "don't get chopped up" maps high);
per_trade_penalty 0-0.002 (makes each trade cost something extra — breakout
agents use it because true breakouts are rare); averaging_down_penalty
(asymmetric penalty on adding to losers — mandatory for mean reversion).
The user says a feeling; the compiler makes it mechanical.
