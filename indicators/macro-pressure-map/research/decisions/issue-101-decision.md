# Issue #101 finding

## Verdict

`state_dependence_not_enough_linear_speed_problem_persists`

The state-dependent hypothesis was tested by adding exactly two causal interactions:

- inflation level × inflation acceleration
- growth level × growth acceleration

to the frozen M2 policy-reaction model.

The result is negative.

### Primary Proxy Funds Rate target

Full OOS, 1990-01 to 2025-06:

- M1 RMSE 1.184
- M2 RMSE 1.304
- M3 RMSE 1.334

M3 versus M2:
- RMSE **+0.030**
- MAE **+0.021**

M3 versus M1:
- RMSE **+0.150**
- MAE **+0.096**

So the interaction model makes the primary continuous policy forecast worse.

### Across eras

Proxy M3 RMSE is worse than M2 in all three preregistered periods:

- pre-Dec-2008
- post-Dec-2008 unconventional-policy era
- 2020-2025

All leave-one-subperiod-out checks also keep M3 worse than M2 on RMSE and MAE.

### EFFR cross-check

M3 does partially improve on M2 for EFFR, but it still does not beat M1 full-sample and becomes substantially worse in the pandemic/post-pandemic segment.

This is not stable enough to rescue the mechanism.

## Interpretation

This does **not** prove that central banks ignore level, direction or speed.

It rejects a narrower model:

> CPI/IP level + six-month acceleration + two own-axis linear interactions.

The next study should change the economic state representation itself — for example labor-market slack, inflation expectations/anchoring, or policy regime — rather than keep adding algebra to the same CPI/IP specification.

Treasury transmission remains closed.
