# Issue #57 — Phase E independent validation preregistration

Status: **PREREGISTERED / HOLDOUT SEALED**

This document is committed before evaluating v0.6 on the Phase-E holdout.

## Why cross-market holdout instead of a later-date feed

Issue #55 documented material reproducibility/data-quality problems in candidate later-period free FX feeds (including Yahoo OHLC envelope defects and unstable public-feed access). Phase E therefore uses an untouched **cross-market holdout** from the same pinned static daily-data source and source commit as Issue #55.

This keeps bar construction, source versioning, and OHLC validation identical while testing three currency pairs that were never used in Issue #55 or v0.6 Phases A-D.

A later-date independent test remains desirable after this cross-market gate, but is not substituted with a lower-quality feed merely to obtain newer dates.

## Sealed holdout markets

- USDCAD
- USDCHF
- NZDUSD

Source repository: `ejtraderLabs/historical-data`

Pinned source commit: `a7c5089d96379d4de03cf0001eb5807304675f0e`

Expected source paths:

- `USDCAD/USDCAD_D1.csv`
- `USDCHF/USDCHF_D1.csv`
- `NZDUSD/NZDUSD_D1.csv`

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

## Holdout decision boundary

The cross-market gate will be reported without tuning as one of:

- `validated_cross_market_robustness`
- `descriptive_but_not_incremental`
- `unstable_on_independent_fx_pairs`
- `implementation_or_data_blocked`

A positive cross-market result is still not a substitute for a later-date independent sample; it only earns the right to proceed.
