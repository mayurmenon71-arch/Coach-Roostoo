---
id: research
title: Research — how Roostoo runs RL as a live community-scale experiment
tags: research, rl research, trajectories, data, moat, evaluation, robustness, survival, profit probability, tradingelo, generations, retraining, quarterly, open problems, contribute, how agents learn, how agents are evaluated
---
Roostoo runs reinforcement-learning research as a live, community-scale experiment.
The competition platform is the laboratory, every competition is a forward test on
real market data, and every agent is a probe.

THE DATA ONLY ROOSTOO HAS. Every competition produces trajectories: what each agent
saw, what it did and what it earned, in whatever regime the market was in that day.
Hundreds of agents per competition, every day, add up to a corpus of live,
out-of-sample agent behaviour that no backtest and no closed lab can assemble. The
Factory can produce more than a million distinct agent configurations, and every one
that runs adds to the set. This corpus is the moat; scale figures are published in
the quarterly generations note.

HOW AN AGENT LEARNS — Observe (price, volume, its indicators, its own position) →
Act (long, short or flat, and how much) → Reward (return shaped by the objective you
chose) → Update (adjust the policy toward what paid). This repeats hundreds of
thousands of times in training, then runs forward on live prices in every competition.

HOW AGENTS ARE EVALUATED. Inside a competition, rank is by performance return. On an
agent's evaluation card, three scores are read together so that no single lucky run
can carry it:

| Score | What it rewards | What it punishes |
|---|---|---|
| Robustness | Agents whose weaker runs still clear the bar | Lucky peaks on a fragile floor |
| Survival | A shallow worst-case drawdown | Breaking in stressed markets |
| Profit probability | Finishing in profit consistently | Boom-and-bust equity curves |

Exact formulas, thresholds and weightings are NOT published, so the scores cannot be
gamed. TradingELO, a cross-competition rating built on the latest results and
quantitative metrics, is in development.

GENERATIONS: RETRAINING EVERY QUARTER. Agents are not minted once and left alone.
Each quarter, Roostoo retrains the Factory's models on the newest data pipelines and
on production insights from the community's competitions and live deployments. Every
generation should beat the one before it, and each quarter's note reports the
outcome, not the recipe. The loop: community runs agents (paper competitions and live
deployments) → production data (trajectories and outcomes) → retrain the Factory (new
pipelines, tuned models) → next generation (better agents to mint), every quarter.

OPEN PROBLEMS — Roostoo works on these in public and welcomes proposals (the problems
are open; interim findings are not published):
1. Reward generalisation — which objectives keep working when the regime changes?
2. Action design — how should an agent express size and direction so training stays
   stable on thin markets?
3. Paper-to-live transfer — what separates a great paper record from a great live one?
4. Population dynamics — how should fitness be measured when hundreds of agents trade
   the same window?
5. Observation design — which inputs add signal rather than noise?
6. Risk under non-stationarity — when should guardrails be learned, and when fixed?

CONTRIBUTE. Every agent configuration you run is an experiment, and strong ones inform
the next generation. Proposals against any open problem that pass review are
instrumented in production, and the outcomes are published.
