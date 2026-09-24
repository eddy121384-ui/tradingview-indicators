# Issue #109 A2 — exact V6.6 trajectory export transport

Status: **FROZEN BEFORE ANY A2 TRAJECTORY PAYOFF RESULT**

## Purpose

Obtain a durable daily exact-V6.6 raw GPI/IPI history from TradingView so the preregistered A2 trajectory test can be run without substituting public-feed axes.

This transport does **not** compute any asset payoff, model fit, portfolio result, or Action Layer verdict.

## Source relationship

The helper reads the plotted V6.6 main-axis series from the already-frozen production indicator through `input.source()`.

Required chart setup:

- symbol: `SPY`;
- chart timeframe: `1D`;
- production indicator: `Macro Pressure Map V6.6 [Tiered GPI/IPI/FCPI]`;
- production V6.6 must retain the same settings used by the frozen #59/#64 research configuration;
- main pressure-line smoothing must be **enabled**;
- smoothing length must be **5**.

Do not change V6.6 weights, symbols, lookbacks, thresholds, optional component toggles, or macro-data toggles for this export.

## Raw-axis reconstruction

Production V6.6 publishes the main GPI/IPI lines as EMA(5) when smoothing is enabled.

For EMA length 5:

```
alpha = 2 / (5 + 1) = 1/3
plot_t = alpha * raw_t + (1-alpha) * plot_(t-1)
```

Therefore:

```
raw_t
= (plot_t - (1-alpha) * plot_(t-1)) / alpha
= 3 * plot_t - 2 * plot_(t-1)
```

This is the same exact reconstruction used and cross-checked in Issue #64.

The prior #64 parity audit found maximum raw-axis reconstruction discrepancies versus independently recomputed V6.6 axes of approximately:

- GPI: 2.51e-08
- IPI: 2.45e-08
- FCPI: 2.49e-08

Those differences were attributable to exported decimal rounding.

## Frozen A2 trajectory features

From reconstructed raw axes only:

```
fast_slope_GPI = (raw_GPI_t - raw_GPI_t-20) / 20
mid_slope_GPI  = (raw_GPI_t - raw_GPI_t-63) / 63
acceleration_GPI = fast_slope_GPI - mid_slope_GPI

fast_slope_IPI = (raw_IPI_t - raw_IPI_t-20) / 20
mid_slope_IPI  = (raw_IPI_t - raw_IPI_t-63) / 63
acceleration_IPI = fast_slope_IPI - mid_slope_IPI
```

No alternate lookback is permitted.

## Export columns

The helper must expose at least:

- selected smoothed GPI plot;
- selected smoothed IPI plot;
- reconstructed raw GPI;
- reconstructed raw IPI;
- GPI 20-row slope;
- GPI 63-row slope;
- GPI acceleration;
- IPI 20-row slope;
- IPI 63-row slope;
- IPI acceleration;
- reconstructed 3x3 regime id.

The exported CSV date/time column comes from the SPY 1D chart.

## 3x3 audit mapping

Using raw axes and frozen ±10 thresholds:

- GPI > +10 / IPI < -10 => 1
- GPI > +10 / |IPI| <= 10 => 2
- GPI > +10 / IPI > +10 => 3
- |GPI| <= 10 / IPI < -10 => 4
- |GPI| <= 10 / |IPI| <= 10 => 5
- |GPI| <= 10 / IPI > +10 => 6
- GPI < -10 / IPI < -10 => 7
- GPI < -10 / |IPI| <= 10 => 8
- GPI < -10 / IPI > +10 => 9

The regime id is an audit column only. A2 still uses the already-frozen Issue #64 exact regime transition history for the state baseline.

## Acceptance gate after user export

Before any A2 payoff model is run:

1. freeze the user-exported CSV by SHA-256;
2. verify unique increasing daily dates;
3. verify reconstructed regime id against Issue #64 frozen transitions over their common historical window;
4. compare reconstructed raw GPI/IPI against the committed Issue #64 axis audit checkpoints;
5. reject the export if settings/source selection are inconsistent;
6. only after the exact-axis gate passes may A2 trajectory payoff evaluation begin.

## Forbidden

Do not:

- reconstruct trajectory from regime ids alone;
- substitute public-feed GPI/IPI and call it exact V6.6;
- alter smoothing length from 5;
- use smoothed GPI/IPI as the A2 trajectory axes;
- change 20/63 after payoff inspection;
- add FCPI as an A2 directional feature;
- modify production V6.6;
- compute any asset payoff inside the Pine helper.

No A2 trajectory payoff result had been viewed when this transport contract was committed.
