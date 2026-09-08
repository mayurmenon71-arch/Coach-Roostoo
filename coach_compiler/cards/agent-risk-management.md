---
id: agent-risk-management
title: Risk management — guards in Paper vs Real Mode, stop-loss, leverage
tags: risk, risk management, stop loss, take profit, ticket, max leverage, 3x, guards, paper mode, real mode, order size, stop button, choosing values, position size, protect, drawdown, leverage
---
Roostoo agents make their own decisions. Once a competition opens or a ticket is
enabled, the policy chooses every entry, exit and position size on its own, and
nobody at Roostoo steers it. The guardrails you set are the only limits on what it
can do, so choose them as you would for a trader you had never met. Between those
guards the agent acts autonomously: it can be wrong, it can stay wrong for a while,
and it will not ask first. Roostoo does not monitor or override individual agents and
cannot step in when a position moves against you. The guards are your intervention,
set in advance.

GUARDS AT A GLANCE:
| Guard | Paper Mode | Real Mode |
|---|---|---|
| Max trade per order | Yes | No |
| Min trade per order | Yes | No |
| Ticket, with a minimum size | No | Yes |
| Stop-loss | No | Yes |
| Take-profit | No | Yes |
| Max leverage | No | 3x |
| Stop button | No | Yes |

IN PAPER MODE. There is no stop-loss or take-profit in a paper competition. The agent
manages its exposure with the position sizing it learned, bounded by the two
order-size limits you set at mint time, and the competition ends when the clock does.
Nothing real is at stake, which makes Paper Mode the place to learn how an agent
behaves before you give it capital.

IN REAL MODE. Guards travel with the allocation and are enforced at the venue. The
ticket caps the capital, above a minimum shown in the app. Stop-loss and take-profit
close the allocation at the limits you set. Leverage is capped at 3x. Stop flattens
the agent's positions whenever you choose.

SET A STOP-LOSS. EVERY TIME. Without a stop-loss, the only floor on an allocation is
the ticket itself, and an agent that stays wrong can lose all of it. A stop-loss
turns open-ended exposure into a number you chose in advance. Treat it as part of
sizing the ticket, not an optional extra.

LEVERAGE MOVES THE THRESHOLDS CLOSER. Leverage multiplies the effect of every price
move on the allocation, so both thresholds are reached sooner:

| Market move | Effect at 1x | At 2x | At 3x |
|---|---|---|---|
| 1% | 1% | 2% | 3% |
| 3% | 3% | 6% | 9% |
| 5% | 5% | 10% | 15% |

A 10% stop-loss is hit by a 10% market move unlevered, but by roughly a 3.3% move at
3x. Leverage does not move your thresholds — it changes how quickly ordinary market
noise reaches them, so size the stop-loss with the leverage in mind.

WHY HARD GUARDRAILS LIKE STOP-LOSS:
- Out-of-distribution tape — a policy will meet market conditions it never trained on;
  guards cap the damage while it is wrong.
- Capital protection — in Real Mode the guard is the difference between a bad hour and
  a bad month.

CHOOSING VALUES:
| Guard | Starting point | Adjust when |
|---|---|---|
| Stop-loss | 5 to 10% of the ticket at low leverage | Tighten as leverage rises; widen if normal volatility keeps triggering it |
| Take-profit | Wide | Tighten only if you want to bank gains quickly (tight targets cap the upside) |
| Max trade per order | 10 to 25% of the portfolio | Higher concentrates risk, lower dilutes impact |
| Ticket | Size of capital deployed per agent ticket session | Above the minimum, several tickets across signal families beat one large one |

Planned: portfolio-level concentration caps and drawdown-conditional auto-flatten.
