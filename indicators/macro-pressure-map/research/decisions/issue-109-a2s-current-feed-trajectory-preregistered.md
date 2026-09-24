# Issue #109 A2S — current-Feed trajectory screening preregistration

Status: **PREREGISTERED BEFORE ANY A2 TRAJECTORY PAYOFF RESULT**

## Why A2S exists

The exact A2 gate failed before payoff inspection because the current TradingView historical feed does not reproduce the frozen Issue #64 axis history closely enough.

User-supplied self-contained r4 Pine Logs:

- file: `pine-logs-MPM V6.6 A2 SC r4.csv`
- SHA-256: `6ceb8cf7ba0e9c17949a4d8892b91f9a8c3a94ea1f7462a5b0a4ce114cf5e1bc`
- raw rows: 4,965
- unique payload dates after duplicate collapse: 4,962
- payload coverage: 2007-01-03 through 2026-09-23
- `helper_rev=r4sc`: present on all raw rows
- duplicate-date policy: identical duplicate payload dates collapse to the last identical row

The r4 trajectory features are internally reproducible from the logged raw axes to about 5.5e-9 maximum absolute error.

However the frozen Issue #64 checkpoint gate fails:

- frozen GPI checkpoint max absolute discrepancy: approximately **0.06224**
- frozen IPI checkpoint max absolute discrepancy: approximately **29.16793**
- checkpoint regime agreement: **41 / 51**

This is materially above the frozen exact-axis tolerance.

Likely cause is historical source-feed drift/revision, especially in market inputs used by IPI; this is a transport/data-history issue, not an authorized V6.6 formula change.

No A2 asset-payoff result was viewed before this preregistration.

## Scientific status

A2S is a **screening study only**.

It may answer:

> Does the current TradingView-feed 20/63 trajectory family add enough incremental information over the frozen exact state baseline to justify further exact-data work?

It may **not** answer:

> Has exact frozen V6.6 trajectory been validated for production?

A positive A2S result requires a later exact confirmation before any V6.7 production Action Layer may use trajectory.

A negative A2S result is sufficient to stop further trajectory rescue work under Issue #109.

## Frozen signal inputs

### M0 — exact frozen state baseline

Use the same frozen Issue #64 V6.6 3x3 state history used in A1.

M0:
- intercept;
- eight one-hot indicators for the nine frozen states.

### M1 — M0 + current-feed trajectory screen

Add exactly six r4 features measured on the A1 signal date:

- `gpi_fast20`
- `gpi_mid63`
- `gpi_acc`
- `ipi_fast20`
- `ipi_mid63`
- `ipi_acc`

The r4 formulas remain:

```
fast_slope_X = (X_t - X_t-20) / 20
mid_slope_X  = (X_t - X_t-63) / 63
acceleration_X = fast_slope_X - mid_slope_X
```

No alternative windows, features, interactions, thresholds, or source substitutions.

## Outcomes

Reuse the already-frozen A1 monthly origin table and pairwise 3M outcomes.

Legs:

- Equity vs Duration = SPY - TLT
- Duration vs Cash = TLT - SHV
- Gold vs Cash = GLD - SHV
- Broad Commodities vs Cash = GSG - SHV

Primary horizon:
- 3M = 63 common trading rows

1M/6M are not promoted into A2S model selection.

## Timing

For each A1 monthly origin:

- frozen state comes from A1's already-lagged exact state;
- trajectory features must match the recorded A1 `signal_date`;
- if a signal-date trajectory row is missing, drop that origin from both M0 and M1;
- M0 and M1 always use identical complete-case origins.

No same-origin-day trajectory lookup.

## OOS estimation

For each leg separately:

- expanding-window OLS;
- monthly origins;
- first forecast only after at least **84 complete monthly training rows**;
- feature standardization uses training-window moments only;
- state dummies are not standardized;
- trajectory features are standardized causally using training-window mean/std;
- no regularization;
- no hyperparameter tuning;
- no interaction terms;
- no FCPI input.

Because 3M outcomes are only known after the 63-row horizon, a forecast origin's training set may include only prior rows whose 3M outcome end date is strictly before the forecast origin.

This outcome-availability rule is mandatory.

## Metrics

Primary:
- RMSE
- MAE
- Pearson correlation
- sign agreement

Report:
- full OOS;
- pre-2020;
- 2020-2022;
- 2023-latest completed origin.

Diagnostic:
- mean realized pairwise spread conditional on predicted positive vs negative sign.

## A2S decision rule

For each leg:

`trajectory_screen_positive` only if M1:

1. improves RMSE or MAE versus M0;
2. improves or preserves correlation;
3. does not materially worsen sign agreement;
4. shows the same broad direction of incremental value in at least two temporal segments with usable forecasts;
5. does not owe essentially all improvement to one temporal segment.

`trajectory_screen_negative` if M1 has no stable incremental improvement or degrades M0 on the major metrics.

`trajectory_screen_inconclusive` if sample/segment coverage prevents the rule above from being assessed.

No coefficient-sign storytelling can override the metric gate.

## Production boundary

A2S can never authorize:
- production Pine trajectory tilts;
- -2..+2 intensity thresholds;
- portfolio weights;
- exact V6.6 trajectory claims.

Positive A2S => exact-data confirmation still required.
Negative A2S => stop trajectory work and keep Action Layer state-only.

## Forbidden rescue paths

Do not:
- change r4 source history;
- calibrate r4 IPI back to frozen checkpoints;
- optimize a mapping between current-feed and frozen axes;
- drop IPI or GPI after viewing payoff;
- add FCPI;
- change 20/63;
- add interactions;
- change primary horizon;
- use diagnostic 1M/6M to overturn 3M;
- claim the current-feed r4 history is exact frozen V6.6.

No A2S payoff result had been viewed when this preregistration was committed.
