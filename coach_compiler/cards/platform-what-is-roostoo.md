---
id: platform-what-is-roostoo
title: What is Roostoo — build, prove and deploy RL trading agents
tags: what is roostoo, overview, intro, mission, paper mode, real mode, flywheel, tradingelo, self-custodial, agent factory, why roostoo, no code
---
Roostoo is where reinforcement-learning trading agents are built, proven in live
competition and put to work with real capital. You mint an agent without writing
code. It races hundreds of others on the same live market, on the same clock, and
its results land on a public leaderboard and an on-chain record that cannot be
bought or backfilled. The mission in one line: scale the market where AI agents
earn the trust for capital.

THE THREE STEPS:
1. **Build** — pick markets and asset models, a signal family, model configuration
   and a reward function. Roostoo has already pre-trained and backtested the agent
   for live deployment.
2. **Prove** — enter live daily competitions in Paper Mode to build the agent's
   track record. Top agents split meaningful USDT prize pools.
3. **Earn** — switch to Real Mode and let the agent trade your capital on a DEX.
   You keep the wallet keys and permissions (a self-custodial wallet).

Paper Mode and Real Mode share the same agents, wallet and account. Flip between
them with the switch at the top of the app.

WHY ROOSTOO EXISTS:
- **LLMs are the wrong tool for trading** — language models are expensive per
  decision and non-deterministic; ask one the same question twice and you can get
  two different trades.
- **Good agents are hard to find** — there has been no scalable way to discover
  medium-frequency directional agents: ones that take a view, hold for minutes to
  hours, and survive a live market.

Roostoo's answer is an agent factory plus a live competition platform with prize
incentives: mint quantitative RL agents at scale, race them on the real market to
tell good agents apart, and let track records qualify which ones deserve capital.

THE FLYWHEEL — more agents minted, raced and deployed produce more live data from
every competition, which retrains better agents every quarter, which earns more
profits for the whole community. Every competition you enter and every ticket you
deploy adds data the next generation learns from.

LIVE COMPETITIONS ARE LIVE FORWARD TESTS. Unlike a backtest, competition prices
have not happened yet, so nothing can be fitted to them, and every agent faces the
same tape on the same clock. Slippage and commission fees are factored into every
fill, so a Paper Mode record means more than any backtest.

QUANT MODELS, NOT CHATBOTS. A Roostoo agent is a neural-network policy trained with
PPO on cleansed, normalised market data and backtested; it is deterministic (same
input, same output), decides in milliseconds with a negligible cost per decision,
and learns from trading outcomes — the opposite of an LLM trading bot.

TRACK RECORDS YOU CAN TRUST. Every enrollment, payout and Real Mode deployment is a
transaction on BNB Chain you can check on BscScan, and backtests are labelled as
backtests. Inside a competition, rank is by performance return. Across competitions,
Roostoo is developing TradingELO, a rating built on the latest results and
quantitative metrics that weighs win rate and return against drawdown, scaled by
competitions played. It is early and will appear on leaderboards as it matures.

WHAT ROOSTOO DOES NOT DO:
- Hold your money — wallets are self-custodial. In Real Mode, Roostoo holds a
  trade-only key that can place orders and can never withdraw.
- Trade your money unless you say so — paper competitions run on virtual
  portfolios; real capital moves only when you deploy it.
- Promise returns — agents lose competitions, and real trading can lose money.
