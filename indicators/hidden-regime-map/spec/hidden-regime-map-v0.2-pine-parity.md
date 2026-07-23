# Hidden Regime Map v0.2 Pine Parity Specification

## Decision

Proceed with a Pine v6 **reference parity spike** for the frozen `SPY 1D` model.

This is not approval for a universal indicator. The research results show persistent, interpretable states, but their meanings are asset-specific:

- SPY separates two advancing regimes from a high-volatility two-sided stress regime.
- TLT separates one advancing regime from two declining regimes and shows one out-of-sample contradiction.
- The remaining v0.1 gate is whether Pine can reproduce the Python causal filter on a shared data contract.

## Frozen profile

The only supported profile in this spike is:

- profile: `spy-1d-v0.1`
- symbol: `SPY`
- timeframe: `1D`
- price basis: dividend-adjusted standard OHLC
- features: 20-bar standardized log return, 20-bar ATR percentage, 20/100 SMA spread divided by ATR
- model: three-state diagonal-covariance Gaussian HMM
- inference: fixed-parameter causal forward filtering

The authoritative parameters live in `models/spy-1d-v0.1.json`. Pine values must be copied from that file without manual reinterpretation.

## Data contract

Pine must request standard daily OHLC with dividend adjustment explicitly. It must not rely on the chart's visible candle type or the user's chart adjustment setting.

The script is unsupported when:

- the chart symbol is not SPY;
- the chart timeframe is not one day;
- the required adjusted series is unavailable;
- the chart does not contain the exact anchored feature-start bar.

Unsupported use must produce a visible warning rather than silently calculating a misleading regime.

Vendor differences remain possible. Yahoo-adjusted and TradingView-adjusted prices must be compared at the fixture dates before any posterior tolerance is accepted.

## Feature contract

On confirmed daily bars, calculate exactly:

1. `log_return = log(close / close[1])`
2. `standardized_return = log_return / stdev(log_return, 20)` using population standard deviation
3. `true_range = max(high - low, abs(high - close[1]), abs(low - close[1]))`
4. `atr = sma(true_range, 20)`
5. `atr_pct = atr / close`
6. `trend_strength = (sma(close, 20) - sma(close, 100)) / atr`

Then standardize each feature with the frozen training mean and scale.

No future values, secondary smoothing, confirmation delay, clipping, or feature substitutions are allowed.

## Forward-filter contract

Initialize once on the frozen feature-start bar. The first posterior is the normalized product of:

- exported start probabilities; and
- that bar's diagonal Gaussian emission likelihood.

For each subsequent confirmed bar:

1. project the prior posterior through the transition matrix;
2. calculate diagonal Gaussian log-likelihood for each state;
3. add log prior and log likelihood;
4. normalize with log-sum-exp;
5. store posterior A, B, and C.

Requirements:

- all three probabilities are finite and non-negative;
- their sum is 1 within normal floating-point tolerance;
- persistence comes only from the transition matrix;
- state descriptions are display labels, not extra inference rules.

## Display

The spike should show:

- posterior A, B, and C;
- dominant state;
- optional dominant-state background;
- profile ID;
- supported/unsupported status;
- a compact parity/debug view that can expose feature values and posterior values for chart-data export.

Use the asset-specific labels:

- A: two-sided stress
- B: advance
- C: calm advance

The UI must still identify them as posterior states A/B/C so the labels are not mistaken for universal meanings.

## Verification fixture

`research/fixtures/spy-1d-parity-checkpoints.json` contains a small set of checkpoints covering:

- first initialization;
- A→B and B→C transitions;
- 2011, 2018, 2020, and 2022 stress;
- recovery;
- train/OOS boundary;
- a recent out-of-sample bar.

Verification occurs in two layers:

### Layer 1 — feature parity

Compare Pine-exported close and the three raw features with the fixture.

Any material feature mismatch is a data or formula mismatch. Do not diagnose it as an HMM bug.

### Layer 2 — posterior parity

Only after feature parity is acceptable, compare posterior A/B/C.

`research/compare_pine_export.py` resolves the exported plot columns, checks all fixture dates, and writes JSON and Markdown parity reports.

The first report must publish:

- per-checkpoint absolute feature errors;
- per-checkpoint absolute posterior errors;
- maximum probability-sum error;
- dominant-state agreement;
- the chosen tolerance and why it is defensible.

## Acceptance outcomes

The spike must end in one explicit result:

1. **Parity passed** — proceed to a reviewable SPY 1D research indicator.
2. **Feed mismatch** — obtain a TradingView-adjusted OHLC export and refit the profile from that feed.
3. **Inference mismatch** — fix Pine math or initialization before continuing.
4. **Not reliable** — stop the Pine path and revisit the model design.

## Non-goals

- automatic per-symbol retraining;
- a TLT profile;
- cross-asset claims;
- strategy, PnL, alerts, MTF, regime smoothing, volume, divergence, or Wyckoff integration;
- public-release copy or visual polish.

## Implementation sequence

1. Commit the frozen profile and checkpoint fixture.
2. Implement `pine/hidden-regime-map-spy-parity.pine`.
3. Export TradingView chart data on SPY 1D with dividend-adjusted prices.
4. Run `research/compare_pine_export.py` against the export.
5. Record the parity decision before any release work.
