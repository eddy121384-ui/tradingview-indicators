# Issue #109 A2 / A2S finding — trajectory does not earn an Action Layer role

Status: **COMPLETE — EXACT A2 BLOCKED, CURRENT-FEED SCREEN NEGATIVE**

## Evidence chain

### Exact A2 transport

The exact frozen-V6.6 trajectory gate could not be satisfied.

The user-supplied self-contained r4 Pine Logs are frozen by SHA-256:

`6ceb8cf7ba0e9c17949a4d8892b91f9a8c3a94ea1f7462a5b0a4ce114cf5e1bc`

Artifact shape:

- raw Pine Log rows: 4,965
- unique payload dates after duplicate-date collapse: 4,962
- coverage: 2007-01-03 through 2026-09-23
- helper revision: `r4sc`
- 20/63 trajectory fields recompute from logged raw axes to rounding-level error (~5.5e-9 max)

The current TradingView historical feed does **not** reproduce the frozen Issue #64 axis history closely enough to call this exact V6.6 history:

- frozen-axis checkpoint GPI max absolute discrepancy: ~**0.06224**
- frozen-axis checkpoint IPI max absolute discrepancy: ~**29.16793**
- regime agreement on the 51 frozen checkpoints: **41 / 51**

Examples:

- 2007-01-04: frozen IPI -36.6665 vs current-feed r4 -39.4259
- 2010-08-02: frozen IPI -8.1191 vs current-feed r4 +12.1134
- 2022-02-07: frozen IPI +33.8191 vs current-feed r4 +62.9870
- 2026-08-14: frozen IPI -2.2052 vs current-feed r4 +20.1442

Therefore:

`exact_v66_trajectory_not_recoverable_from_current_feed`

No exact A2 payoff comparison was run before this gate failed.

The original #59 operator-local parity log would resolve the exact history if recovered:

- expected source SHA-256: `c0220d4974b2fd0154c4cf8f33b4b3effb27a58e21ee96a1b0109011ce638e3d`
- original shape: 4,943 log rows / 4,935 unique dates
- coverage: 2007-01-03 through 2026-08-14

That raw file was intentionally not committed in #59 and is not currently available in the repository or ChatGPT file library.

## A2S current-feed screening

Because exact history was unavailable, the separately preregistered A2S gate tested whether the **current TradingView-feed** 20/63 trajectory family showed enough incremental value to justify further exact-data recovery work.

Preregistration:

`decisions/issue-109-a2s-current-feed-trajectory-preregistered.md`

Evaluator:

`issue_109_a2s_current_feed_screen.py`

Inputs:

- M0 state baseline: frozen exact Issue #64 / A1 3x3 state history
- M1: M0 plus exactly six current-feed trajectory features:
  - GPI fast 20
  - GPI mid 63
  - GPI acceleration
  - IPI fast 20
  - IPI mid 63
  - IPI acceleration
- primary outcome: frozen A1 3M pairwise spread
- expanding OLS
- minimum 84 complete monthly training rows
- training outcomes must have completed before each forecast origin
- causal training-window standardization
- no interactions, FCPI, new windows, feature selection, or regularization

No A2S payoff result was viewed before that preregistration was committed.

## Full OOS results

### Equity vs Duration — SPY minus TLT

OOS forecasts: **145**, 2014-05-01 through 2026-05-01.

| Metric | M0 state only | M1 + trajectory | M1 - M0 |
|---|---:|---:|---:|
| RMSE | 0.10416 | 0.11715 | **+0.01298 worse** |
| MAE | 0.08118 | 0.09179 | **+0.01061 worse** |
| Correlation | 0.0618 | -0.0182 | **-0.0801 worse** |
| Sign agreement | 51.72% | 51.72% | 0.00pp |

Temporal incremental result:

- pre-2020: materially worse errors, correlation and sign agreement
- 2020-2022: worse errors; correlation improves slightly; sign unchanged
- 2023+: nearly flat error change, correlation worse, sign better

Verdict:

`trajectory_screen_negative`

### Duration vs Cash — TLT minus SHV

OOS forecasts: **145**, 2014-05-01 through 2026-05-01.

| Metric | M0 state only | M1 + trajectory | M1 - M0 |
|---|---:|---:|---:|
| RMSE | 0.07491 | 0.07864 | **+0.00374 worse** |
| MAE | 0.05633 | 0.06148 | **+0.00515 worse** |
| Correlation | -0.1686 | -0.1007 | +0.0679 |
| Sign agreement | 51.03% | 42.07% | **-8.97pp worse** |

Temporal incremental result:

- pre-2020: clearly worse, including -17.65pp sign agreement
- 2020-2022: mixed; correlation improves, but MAE and sign worsen
- 2023+: errors/correlation/sign all improve

The recent-period improvement is not stable across eras and does not overcome worse full-sample errors/sign performance.

Verdict:

`trajectory_screen_negative`

### Gold vs Cash — GLD minus SHV

OOS forecasts: **145**, 2014-05-01 through 2026-05-01.

| Metric | M0 state only | M1 + trajectory | M1 - M0 |
|---|---:|---:|---:|
| RMSE | 0.07957 | 0.08187 | **+0.00230 worse** |
| MAE | 0.06372 | 0.06614 | **+0.00242 worse** |
| Correlation | 0.0683 | 0.0123 | **-0.0559 worse** |
| Sign agreement | 57.93% | 58.62% | +0.69pp |

Errors and correlation worsen in all three preregistered temporal segments.

Verdict:

`trajectory_screen_negative`

### Broad Commodities vs Cash — GSG minus SHV

OOS forecasts: **146**, 2014-05-01 through 2026-06-01.

| Metric | M0 state only | M1 + trajectory | M1 - M0 |
|---|---:|---:|---:|
| RMSE | 0.13993 | 0.14343 | **+0.00350 worse** |
| MAE | 0.10397 | 0.10764 | **+0.00368 worse** |
| Correlation | -0.0275 | -0.0412 | **-0.0137 worse** |
| Sign agreement | 45.21% | 43.84% | **-1.37pp worse** |

Only the post-2023 segment shows modest error/correlation improvement; pre-2020 deteriorates and full-sample performance is worse.

Verdict:

`trajectory_screen_negative`

## Research conclusion

All four pairwise legs fail the preregistered current-feed trajectory screen:

- Equity vs Duration: `trajectory_screen_negative`
- Duration vs Cash: `trajectory_screen_negative`
- Gold vs Cash: `trajectory_screen_negative`
- Broad Commodities vs Cash: `trajectory_screen_negative`

Per the A2S preregistration, a negative screen is sufficient to **stop further trajectory-rescue work inside Issue #109**.

The result does not prove that the unrecoverable historical exact-V6.6 trajectory has zero information. It does show that there is not enough evidence to justify further data/source rescue effort for an Action Layer trajectory feature.

## Product decision

Do **not** use 20/63 GPI/IPI trajectory as a portfolio-tilt input in V6.7.

Trajectory may remain a **descriptive UI context**:

- Growth strengthening / weakening
- Inflation strengthening / weakening
- acceleration / deceleration
- moving toward / away from a state boundary

But it does not change the Action Layer tilt.

The Action Layer therefore remains **sparse and state-only** at this research stage.

A1 production-candidate relationships remain:

1. **Growth Slowdown / Stable Inflation**
   - Equity > Duration candidate
   - Gold > Cash candidate

2. **Slowdown / Disinflation**
   - Gold > Cash candidate

3. **Stagflation Pressure**
   - Gold > Cash candidate

All other state/leg combinations remain **0 / no view**.

Duration vs Cash has no production candidate.
Broad Commodities vs Cash has no production candidate.

## Production boundary

This finding still does **not** define:

- `-2 .. +2` strength thresholds
- allocation percentages
- equity beta
- DV01
- cash weight
- gold weight
- FCPI risk-budget caps

A separate production/design gate is required before V6.7 Pine implementation.

The current research decision is narrower:

> **State-only candidate directions survive; trajectory does not earn incremental Action Layer status.**
