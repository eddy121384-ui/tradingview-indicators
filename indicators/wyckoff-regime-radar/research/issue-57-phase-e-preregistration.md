# Issue #57 — Phase E independent validation preregistration

Status: **PREREGISTERED / HOLDOUT SELECTION AMENDED PRE-EVALUATION / SEALED**

This document is committed before evaluating v0.6 on the Phase-E holdout.

## Pre-evaluation source-contract amendment

The first draft named `NZDUSD` and assumed underscore-form static source paths plus a source commit identifier that are not part of the actual Issue #55 static-data helper contract. CI caught that mismatch before the freeze/evaluation step ran.

No v0.6 output, regime label, path statistic, PnL statistic, or other holdout outcome was computed from any Phase-E market before this amendment.

The holdout is therefore amended, before evaluation, to three untouched markets that exist in the same static source family used by Issue #55:

- USDCAD
- USDCHF
- EURCHF

Source repository: `ejtraderLabs/historical-data`

Source ref at freeze: `main`

Expected source paths and coverage are locked per pair before any evaluation:

- `USDCAD/USDCADd1.csv` — 2400 rows, 2012-12-04 through 2022-03-04
- `USDCHF/USDCHFd1.csv` — 2400 rows, 2012-12-03 through 2022-03-04
- `EURCHF/EURCHFd1.csv` — 2400 rows, 2012-11-16 through 2022-03-04

The pair-specific start dates are intentionally preserved rather than trimming or repairing the source files to force a common calendar. The freeze manifest records the exact Git blob SHA, raw SHA-256, normalized-file SHA-256, row count, and date range for each pair. Once the manifest exists, the freeze script refuses to redefine the holdout.

## Why cross-market holdout instead of a later-date feed

Issue #55 documented material reproducibility/data-quality problems in candidate later-period free FX feeds. Phase E therefore uses an untouched **cross-market holdout** from the same reproducible static daily-data source family and normalization rules as Issue #55.

This keeps bar construction and OHLC validation consistent while testing three currency pairs that were never used in Issue #55 or v0.6 Phases A-D.

A later-date independent test remains desirable after this cross-market gate, but is not substituted with a lower-quality feed merely to obtain newer dates.

These markets were not used to select:

- Phase-A boundary smoothing;
- the `0.25 ATR` transition width;
- Phase-B `2 * confirm_bars` stale decay;
- Phase-C four-state mapping;
- Phase-D Regime Margin / Regime Support naming and semantics.

## Frozen v0.6 design before holdout evaluation

### Phase A

Continuous price-boundary evidence replaces the identified hard cliffs. Transition width remains `0.25 ATR` and was not selected from PnL.

### Phase B

Strong-candidate confirmation remains unchanged. An unsupported Formal state decays to Neutral after `2 * confirm_bars` (6 bars under frozen defaults). Weak challengers are never promoted directly.

### Phase C

Canonical four-state regime:

1. Accumulation family = stages 1 + 3
2. Markup = stage 2
3. Distribution family = stages 4 + 6
4. Markdown = stage 5

The six underlying stage scores remain diagnostic substructure.

### Phase D

No probability/confidence claim. Primary descriptive quantities are:

- Regime Margin = current Formal four-state weight minus strongest competitor;
- Regime Support = current Formal four-state weight.

Weight Concentration is diagnostic only.

## Implementation gate before opening the holdout

The holdout must remain unevaluated until a frozen v0.6 Pine research harness is mechanically generated and TradingView/Python implementation parity is checked closely enough for research use.

If Pine parity is blocked, Phase E ends as implementation-blocked rather than opening the holdout anyway.

## Primary holdout questions

Once the implementation gate passes, evaluate exactly once:

1. **State coverage:** does the four-state layer populate all four regimes meaningfully across the three untouched pairs?
2. **Path separation:** do canonical regimes separate 5/10/20/60-bar forward return, MFE, MAE, and realized volatility distributions?
3. **Directional sanity:** does Markup have more favorable forward return than Markdown in a majority of pair × horizon comparisons?
4. **Temporal stability inside holdout:** when each untouched pair is split chronologically into first/second halves, are occupancy and relative state behavior reasonably stable?
5. **Descriptive strength behavior:** do higher Regime Margin / Support bins correspond to greater classification persistence? They are not required or expected to predict directional return.

## Predeclared trading-utility diagnostic

Trading utility is secondary to regime robustness. If run, use this single frozen response map:

- Accumulation family: `0`
- Markup: `+1`
- Distribution family: `0`
- Markdown: `-1`

Execution assumptions:

- one-bar lag;
- primary transaction cost = 1 pip per unit turnover;
- equal-weight aggregate across the three holdout pairs.

Baselines remain transparent price-only rules:

- SMA200 trend;
- 60-bar momentum;
- 55-bar Donchian breakout;
- always-flat reference.

No response rule may be changed after the sealed holdout is evaluated.

## Operational decision rules frozen before opening

These rules are committed before any Phase-E regime output or performance statistic is computed.

- The **live window** for each pair begins at the first bar where the four canonical regime weights are finite and have positive total weight. Warm-up bars before that point are excluded from occupancy and persistence statistics.
- A canonical state is **materially populated** in a pair when it occupies at least **1%** of live-window bars.
- **Coverage passes** when every one of the four canonical states is materially populated in at least **2 of 3** holdout pairs, and every pair has at least **3 of 4** materially populated states.
- **Directional sanity passes** when Formal Markup has a higher mean forward return than Formal Markdown in **more than 50%** of comparable pair × horizon cases across 5/10/20/60 bars.
- For **temporal stability**, each pair's live window is split chronologically into equal first/second halves. Occupancy stability passes when the median pair total-variation distance between half-state shares is **<= 0.30**. Relative-behavior stability passes when the sign of each state's mean forward return agrees between halves in at least **50%** of comparable pair × state × horizon cases. Both are required.
- For **Regime Support / Margin**, tertile cut points are estimated from the first half of each pair only and applied unchanged to the second half. The strength check passes when at least one of the two fields has high-bin classification persistence greater than low-bin persistence in **more than 50%** of comparable field × pair × horizon cases. This is a persistence check, not a directional-return claim.
- Forward-path eta-squared for return/MFE/MAE/realized volatility is reported as descriptive effect size and is **not** given an after-the-fact pass threshold.
- **Cross-market regime robustness passes only if coverage, directional sanity, temporal stability, and the descriptive-strength persistence check all pass.**
- Trading utility is **incremental** only when the equal-weight frozen Wyckoff response beats at least **2 of the 3 active baselines** (`SMA200`, `momentum60`, `Donchian55`) on both net annualized return and zero-cash Sharpe under the frozen one-bar lag and 1-pip turnover cost.

Verdict mapping is mechanical:

- any implementation/seal/checksum/data failure -> `implementation_or_data_blocked`
- any required regime-robustness gate fails -> `unstable_on_independent_fx_pairs`
- regime robustness passes but incremental trading utility fails -> `descriptive_but_not_incremental`
- regime robustness and incremental utility both pass -> `validated_cross_market_robustness`

## Holdout decision boundary

The cross-market gate will be reported without tuning as one of:

- `validated_cross_market_robustness`
- `descriptive_but_not_incremental`
- `unstable_on_independent_fx_pairs`
- `implementation_or_data_blocked`

A positive cross-market result is still not a substitute for a later-date independent sample; it only earns the right to proceed.
