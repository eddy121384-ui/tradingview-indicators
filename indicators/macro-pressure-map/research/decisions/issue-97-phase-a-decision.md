# Issue #97 Phase A finding

## Verdict

`policy_relation_era_dependent`

The hypothesis was that adding macro **direction / speed** to growth and inflation levels would improve prediction of the Federal Reserve's next six-month policy move.

It does not do so reliably.

### Full 1970–2025 out-of-sample result

M1 — growth + inflation levels:
- RMSE 1.623
- MAE 1.102
- correlation 0.192
- balanced accuracy 35.9%
- tighten/ease direction accuracy 38.5%

M2 — levels + growth/inflation acceleration:
- RMSE 1.660
- MAE 1.126
- correlation 0.162
- balanced accuracy 36.3%
- direction accuracy 39.2%

M2 therefore worsens the two primary continuous-error measures. Its directional improvement is only about 0.7 percentage point.

### Era dependence

M2 has worse RMSE than M1 in every preregistered era.

The only conspicuous directional improvement is 2020–2025, where balanced accuracy improves by about 5.5pp and tighten/ease accuracy by 6.3pp. That gain does not generalize to the Great Inflation, pre-GFC, or GFC/QE eras.

### What survives

The macro variables are not meaningless.

Inflation and growth **level** coefficients are positive almost all the time, and growth acceleration is also usually positive. But coefficient sign stability is not enough: adding acceleration does not improve out-of-sample forecast error.

## Stop rule

Phase B Treasury-minus-cash testing for Issue #97 is **blocked**.

The preregistration explicitly said not to use Treasury outcomes to rescue a weak or era-dependent policy model. Treasury outcomes remain unopened in this issue.

The next step, if pursued, must be a new preregistered reaction-function hypothesis rather than a change to the six-month horizon, ±25bp labels, acceleration lookback, or a post-hoc market variable.
