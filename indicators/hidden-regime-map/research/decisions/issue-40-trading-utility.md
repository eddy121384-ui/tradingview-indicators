# Issue #40 — Hidden Regime HMM trading-utility decision

## Decision

**Outcome:** `no_incremental_value`

The predeclared SPY 1D experiment completed successfully, but neither the K=3 baseline HMM nor the K=8 five-feature HMM demonstrated incremental out-of-sample trading or risk-management value across at least two transparent baselines.

This is a valid negative result. It does **not** establish that every HMM design is useless. It establishes that the two current candidates, the predeclared state-role mapping, and the three fixed regime uses do not justify advancing as a validated trading layer on this frozen SPY 1D experiment.

**Issue #41 readiness:** `false` under the current roadmap premise. Building an HMM-driven adaptive strategy now would treat an unvalidated regime layer as if it had passed #40.

## Frozen experiment

- Frozen input: Run #58 SPY 1D OHLC.
- Decompressed SHA-256: `016448a0492769c527a8dc8e24d60fbda4c4e0e4bbdbcf27506caf30b76dddc4`.
- Durable input: `research/data/issue-40-spy-1d-run58.csv.gz`.
- Usable rows: 4,064.
- Fit period: 2,438 rows, ending 2020-01-31.
- Exploratory OOS: 812 rows, 2020-02-03 through 2023-04-24.
- Final OOS: 814 rows, 2023-04-25 through 2026-07-23.
- Cost: 5 bps per unit of absolute turnover.
- Execution: confirmed-bar target applied to the following close-to-close return.
- Candidates: K=3 original features and K=8 `baseline_er_downside`.
- Baselines: buy-and-hold, 100-day trend, and 63-day momentum.
- Simpler comparator: 200-day moving-average filter.
- HMM roles: favorable filter, continuous size modifier, and defensive switch.

The candidates, periods, costs, mappings, thresholds, gates, and mechanical outcome were fixed before final-period evaluation. A later evidence-completeness patch added trade-episode statistics without changing the gates or outcome.

## Final-period evidence

| Strategy | Annualized return | Sharpe | Calmar | Max drawdown | Completed round trips |
|---|---:|---:|---:|---:|---:|
| Buy-and-hold | 21.26% | 1.354 | 1.133 | -18.76% | 0 |
| Buy-and-hold + SMA200 | 17.22% | 1.400 | 1.689 | -10.20% | 3 |
| Trend 100 | 17.91% | **1.541** | **2.119** | -8.45% | 5 |
| Momentum 63 | 15.74% | 1.398 | 1.873 | -8.41% | 8 |
| K8 defensive switch on buy-and-hold | 14.54% | 1.371 | 1.739 | -8.36% | 14 |
| K8 defensive switch on Trend 100 | 12.17% | 1.199 | 1.456 | -8.36% | 14 |
| K8 defensive switch on Momentum 63 | 8.59% | 0.897 | 0.983 | -8.73% | 19 |
| K3 size modifier on buy-and-hold | 10.09% | 1.273 | 1.440 | -7.00% | 0 |
| K8 size modifier on Trend 100 | 7.15% | 1.191 | 1.743 | -4.10% | 5 |

### Closest HMM result

The K8 defensive switch applied to buy-and-hold was the closest candidate:

- maximum drawdown improved from -18.76% to -8.36%;
- Sharpe rose only from 1.354 to 1.371, an improvement of 0.017;
- annualized return fell from 21.26% to 14.54%, a sacrifice of 6.72 percentage points;
- it did not beat the simpler SMA200 filter's Sharpe of 1.400;
- the same candidate/role materially weakened the Trend 100 and Momentum 63 baselines.

It therefore failed both the predeclared trading-value and risk-value gates.

### General pattern

- Hard favorable-state filters cut exposure and drawdown, but surrendered too much return and lowered Sharpe.
- Continuous size modifiers often reduced drawdown further, but their return sacrifice was much larger than allowed.
- Defensive switching was the strongest HMM use, yet its benefit was not robust across baselines.
- The transparent Trend 100 baseline produced the strongest final Sharpe and Calmar without HMM.
- No candidate/role passed on two or more baselines. `trading_winners` and `risk_winners` are both empty.

## Correctness and validation

Codex review identified two defects in the first draft:

1. period drawdown did not seed the running peak with opening equity 1.0;
2. carried positions were mislabeled as completed round trips.

Both were corrected before this decision was recorded. Regression tests now cover a negative first-period return and positions carried across period boundaries.

Final corrected validation:

- Hidden Regime Trading Utility Run #7 (`30517967469`): success.
- Validated head: `02e1484e26bec7a2a7f6d1f70aa2f3c988a159c3`.
- 94 research tests passed.
- Frozen-input SHA verification passed.
- Evaluation and strict JSON validation passed.
- Artifact: `hidden-regime-issue-40-trading-utility`, artifact id `8749621581`.
- Artifact digest: `sha256:c6c87f8875881854759fedab23e3ed828a5789be3c35aa0c6f3c67e9f09eba4c`.

The corrected drawdown implementation did not change the numerical outcome on this sample, but the original draft is not used as evidence.

## Interpretation boundaries

This result is limited to:

- SPY daily data;
- one frozen historical sample and one 60/20/20 split;
- the current K=3 and K=8 candidates;
- the declared emission-risk mapping;
- the three declared HMM roles;
- long-only daily strategies and a fixed 5 bps turnover cost.

The experiment does not test every HMM feature set, rolling-refit schedule, asset, timeframe, strategy family, or state-to-action mapping. It also does not provide formal sampling-confidence intervals.

Those limitations do not make the result inconclusive. The declared question was answered: **the current Hidden Regime candidates did not add robust incremental value under the agreed test.**

## Roadmap consequence

Do not proceed directly to Issue #41 as though HMM utility were proven.

The next project decision should choose one of two bounded paths:

1. accept the negative result and stop or park the HMM trading-product route; or
2. authorize a narrowly specified hypothesis revision with a new untouched evaluation design.

Open-ended K, threshold, feature, or strategy tuning against the final period would invalidate this evidence and is outside Issue #40.

## Final status

`complete_negative_result`
