# Issue #76 — Frozen TradingView feed and export contract

## Status

This note freezes the Phase-A data contract before any forward-behavior result is inspected.

The classifier is not being changed here. The source remains the merged Issue #68 release candidate:

- merge commit: `d29b673857e7e2c64a67254efd398b3271b7f172`
- source: `indicators/wyckoff-regime-radar/src/chase-risk-market-regime-radar-issue68-rc.pine`
- source blob: `e5c3fd2622841a6d3f97bdda4b9d0a6378ebda55`

## Frozen TradingView feeds

All Phase-A measurements use `1D` charts.

| Market | Frozen TradingView ticker id | Representation expected under production `Auto` |
| --- | --- | --- |
| EURUSD | `OANDA:EURUSD` | Price Log |
| GBPUSD | `OANDA:GBPUSD` | Price Log |
| USDJPY | `OANDA:USDJPY` | Price Log |
| US10Y | `TVC:US10Y` | Yield Level |
| DE10Y | `TVC:DE10Y` | Yield Level |
| FR10Y | `TVC:FR10Y` | Yield Level |
| GB10Y | `TVC:GB10Y` | Yield Level |
| AU10Y | `TVC:AU10Y` | Yield Level |
| JP10Y | `TVC:JP10Y` | Yield Level |

No broker/source substitution is permitted after outcomes are inspected. If one frozen feed becomes unavailable, stop that market and document the replacement before collecting its outcomes.

## Existing repository data inventory

Issue #55 contains pinned OHLC fixtures for EURUSD / GBPUSD / USDJPY / AUDUSD. They are useful as historical fixtures, but they are **not** the primary Issue #76 measurement feed because:

1. they are not the frozen TradingView OANDA feed;
2. their provider provenance was intentionally treated as non-authoritative in Issue #55;
3. the production classifier can use feed-specific auxiliary information such as Volume Auto behavior.

Therefore Issue #76 does not silently combine those fixtures with TradingView classifier states.

## Primary export mechanism

Phase A uses a dedicated research-only Pine harness generated from the exact frozen production source. It does not reimplement the classifier.

The harness emits one Pine Log message for an event bar only after that event has a complete 20-bar future window. Each message carries the event's confirmed formal stage plus all preregistered 1 / 5 / 10 / 20 bar outcomes.

This has four important consequences:

- classifier state and forward price/yield outcomes come from the **same TradingView feed**;
- no Python replica of the classifier is required;
- the final 20 chart bars are intentionally right-censored and cannot become event rows;
- event-time normalization uses the production `symATR` value known on the event bar.

## Event row definition

An exported event row is created for an event bar `t` when:

- the chart is `1D`;
- `syminfo.tickerid` is one of the nine frozen identifiers;
- `formalId[t]` is S1…S6;
- event-time `symATR[t]` is finite and positive;
- bars through `t+20` are available and confirmed.

The row also records `formalId[t-1]`, allowing fresh-entry and direct canonical-transition labels to be reconstructed without guesswork.

## Frozen outcome definitions

For FX / Price Log:

- forward raw move = `log(close[t+h] / close[t])`;
- MFE raw = `log(max(high[t+1:t+h]) / close[t])`;
- MAE raw = `log(min(low[t+1:t+h]) / close[t])`;
- event normalization scale = `symATR[t]`, which is in log-price units.

For government yields / Yield Level:

- forward raw move = `(close[t+h] - close[t]) * 100`, reported in basis points when the TradingView series is quoted in percentage points;
- MFE / MAE raw use the same conversion from future high / low versus event close;
- event normalization scale = `symATR[t]`, in yield-level percentage-point units.

Normalized forward move / MFE / MAE divide the underlying representation-space move by `symATR[t]`.

Future realized volatility is frozen as non-annualized RMS one-bar movement over the horizon:

`sqrt(mean(delta_model^2))`

where `delta_model` is one-bar log return for Price Log and one-bar yield-level change for Yield Level. A normalized RMS version divides by `symATR[t]`. RMS is used rather than sample standard deviation so the 1-bar horizon remains defined.

## Directional labels

The parser reports positive-rate for every stage.

A separate direction-aligned hit rate is defined only for the preregistered continuation families:

- S2 / S3: positive forward move is aligned;
- S5 / S6: negative forward move is aligned;
- S1 / S4: no directional hit-rate assumption is imposed.

## Pine Logs 10,000-message limit

TradingView displays at most the most recent 10,000 historical Pine Log messages for a script. The harness therefore includes start/end time inputs. The first pass uses the full available window. If the parser receives exactly 10,000 Issue-76 marker rows or detects truncation, collect an earlier non-overlapping time window and combine the exports; the parser de-duplicates by ticker + event timestamp + event bar index.

This is a data-acquisition workaround only. It must not alter classifier settings or the outcome definitions above.

## Frozen production-input behavior

Unless a separate defect is proven, keep all production defaults unchanged, including:

- Representation = `Auto`;
- Volume mode and witness settings;
- MTF mode and settings;
- Divergence mode and settings;
- stage weights / gates / `confirmBars`;
- exact symmetric HARD current-context cap.

The research harness may add logging controls and hidden export channels only. It may not change classifier semantics.
