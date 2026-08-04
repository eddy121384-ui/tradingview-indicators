# Hidden Regime Map v0.4 — U.S. Rates K=6 Visual Prototype

## 1. Purpose

This prototype makes a fixed six-state Gaussian HMM visible on a U.S. Treasury yield chart so Eddy can inspect what the model is actually classifying.

It is not a duration-allocation strategy, a profitability claim, or evidence that K=6 is the uniquely correct state count.

## 2. Market and data

The model observes four daily U.S. Treasury constant-maturity yields:

- DGS2;
- DGS5;
- DGS10;
- DGS30.

The Python profile uses the checksum-verifiable Issue #50 frozen dataset and its inner common-date calendar with no yield interpolation. The first Pine verification target is a daily `FRED:DGS10` chart. The other maturities are requested internally through explicit, configurable `FRED:DGS*` ticker inputs.

TradingView symbol availability and exact feed alignment remain verification items until the script compiles and exports actual chart data.

## 3. Features

The model uses exactly five causal features:

1. `curve_level`: mean of DGS2, DGS5, DGS10, and DGS30, in percent;
2. `slope_2s10s`: DGS10 minus DGS2, in percentage points;
3. `slope_5s30s`: DGS30 minus DGS5, in percentage points;
4. `level_change_bp`: one-observation change in curve level multiplied by 100;
5. `level_vol_20_bp`: population standard deviation of the most recent 20 observed `level_change_bp` values.

Python and Pine must update the feature history only on dates where all four yields are present. Pine must not replace missing observations with invented yield values.

## 4. Fit and interpretation boundary

The initial profile is fitted on all frozen feature rows through July 2026. This is deliberate because the visual prototype must include both the low-rate pre-2022 environment and the later high-rate/inverted-curve environment that broke the older static models.

Consequences:

- historical state colors are retrospective in-sample descriptions;
- historical colors are not OOS validation;
- fixed-parameter forward filtering is causal only after the profile is frozen;
- the prototype cannot establish predictive or trading value.

The profile must display this boundary in its metadata and generated Pine source.

## 5. K=6 fitting and representative-model selection

- Gaussian HMM with diagonal covariance;
- K fixed at 6;
- deterministic seed groups 42, 84, and 126;
- existing restart offsets `[0, 1, 2]` within each seed group;
- retain the highest full-sample likelihood valid fit within each group;
- align the three group-best fits to the group-42 reference using the existing emission-distribution alignment;
- choose one actual fitted model as the representative medoid.

The medoid minimizes total scale-aware parameter distance to the other two aligned fits. The distance combines emission-mean RMSE, log-variance RMSE, transition-matrix RMSE, and start-probability RMSE. Parameters are not averaged by hand.

## 6. State ordering

State names remain neutral `R1` through `R6`.

After selecting the representative fit, states are ordered by ascending:

`standardized level_change_bp + 0.75 × standardized level_vol_20_bp`

Ties use curve level, 2s10s, 5s30s, and the prior aligned state index. This creates deterministic colors and identifiers without forcing a bull/bear taxonomy.

Any later descriptive labels must be derived from learned raw-feature means, duration, occupancy, volatility, and transitions and require human review.

## 7. Visual design

### Main chart

- stable six-color background;
- opacity determined by maximum posterior concentration;
- optional state-transition marker;
- confirmed observations only;
- background persists between valid common observations without recomputing the model.

### Dashboard

Show:

- current `R1`–`R6` state;
- maximum posterior and top-two margin;
- current state duration in valid observations;
- all six posterior values;
- curve level;
- 2s10s and 5s30s in basis points;
- feature-drift diagnostic;
- rolling state-concentration diagnostic;
- profile ID and cutoff;
- 1D/feed/retrospective-fit boundary.

Six posterior lines remain Data Window/export diagnostics and are not plotted over the chart by default.

## 8. Instability diagnostics

The prototype must expose the failure mode observed in Issue #50.

### Feature drift

Statistic: maximum absolute standardized feature value on the current model update.

Prototype warning threshold: `>= 3.0`.

This means at least one feature is three or more training-sample standard deviations from the full-sample mean. It is a visible diagnostic, not a universal proof that the HMM is invalid.

### State concentration

Statistic: maximum dominant-state share across R1–R6 over the latest 126 valid model observations.

Prototype warning threshold: `>= 90%`.

This is designed to reveal prolonged state collapse or near-collapse. It is not the same as the Issue #50 final-period promotion guardrail and must not be described as such.

## 9. Parity and repaint boundary

- Pine v6;
- `request.security(..., lookahead_off)` for every rate series;
- update only on confirmed chart bars with all four yields present;
- fixed scaler and HMM parameters;
- forward-filtered posterior only;
- no Viterbi smoothing or future-aware decoding;
- no historical relabeling;
- checkpoint fixture contains raw features, scaled features, six posterior probabilities, dominant state, and probability sum;
- FRED-to-TradingView differences are measured and reported, not assumed away.

## 10. Deliverables

- `research/export_rates_k6_visual.py`;
- `research/generate_rates_k6_pine.py`;
- focused unit tests;
- deterministic CI artifact containing profile, checkpoint fixture, report, and generated Pine;
- committed profile and generated assets after the first clean CI run;
- TradingView compilation and exported checkpoint comparison;
- Eddy visual-review decision.

## 11. Non-goals

No strategy, duration allocation, PnL, entries, exits, alerts, MTF, rolling Pine refit, automatic K selection, SPY model reuse, semantic state claims, or publication decision.
