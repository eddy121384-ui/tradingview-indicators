# Issue #76 — FR10Y Real TradingView Pine Log Smoke Finding

## Input

Human-exported TradingView Pine Logs CSV from the generated Issue #76 Forward Behavior Logger on:

- symbol: `TVC:FR10Y`
- timeframe: `1D`
- representation: production `Auto`, resolved by the logger to `YIELD_LEVEL`
- uploaded file name: `pine-logs-#76 Forward Logger.csv`

The TradingView CSV envelope is localized and uses two columns:

- `日期`
- `訊息`

This is compatible with the preregistered parser design because the parser scans every CSV cell for the `ISSUE76|schema=1` marker rather than depending on a specific header name.

## Schema / feed validation

Observed marker rows: **8,303**.

Validation replay against the frozen parser contract:

- marker schema: `ISSUE76|schema=1`
- ticker: all `TVC:FR10Y`
- timeframe: all `1D`
- representation: all `YIELD_LEVEL`
- formal stage: all in S1…S6
- previous stage: all in 0…6
- fresh flag: all internally consistent with `stage != prev`
- transition label: all internally consistent with `prev>stage`
- event-time `symATR` scale: finite and positive
- all 1 / 5 / 10 / 20 horizon `move`, `norm`, `mfe`, `mae`, `mfen`, `maen`, `rv`, `rvn` fields present and finite
- duplicate event keys `(ticker, event_time, event_bar)`: **0**
- parser validation errors: **0**
- 10,000-row Pine Log truncation warning: **not triggered**

Event-time coverage after the fixed 20-bar forward observation lag:

- first event: `1988-12-01T07:00:00Z`
- last event: `2026-08-11T06:00:00Z`

## Independent arithmetic cross-check

A second check used only contiguous logged formal-stage bars so the next event row is also the next chart bar.

For each eligible starting event, the logged multi-bar forward move was compared with the sum of its subsequent logged one-bar moves:

- horizon 5: 8,168 checks, max absolute discrepancy `5.68e-14` bp
- horizon 10: 8,033 checks, max absolute discrepancy `5.68e-14` bp
- horizon 20: 7,770 checks, max absolute discrepancy `1.14e-13` bp

These are floating-point noise only.

Future RMS-volatility fields were also reconstructed from one-bar yield changes on contiguous sequences. Maximum absolute discrepancy was approximately `5.0e-11` bp, consistent with logger string rounding.

Normalized forward moves were checked against the event-time `symATR` scale. Maximum absolute discrepancy across frozen horizons was below `1.72e-7` normalized units.

## Descriptive event inventory — not a trading result

Formal-stage occupancy rows in this FR10Y export:

- S1: 687
- S2: 3,025
- S3: 32
- S4: 487
- S5: 4,072
- S6: 0

Fresh formal-stage entries: **263**.

Primary canonical transitions observed in this one market:

- S1 → S2: 20
- S2 → S3: 1
- S3 → S2: 2
- S4 → S5: 21
- S5 → S6: 0
- S6 → S5: 0

These counts are descriptive only. They are not grounds to alter the classifier, universe, horizons, or transition definitions. Absence of S6 in FR10Y is a sample characteristic, not a repair request.

## Decision

**FR10Y REAL TRADINGVIEW LOG SMOKE + CSV ENVELOPE = PASS.**

The logger compiles/runs in TradingView, the real localized Pine Logs CSV envelope is compatible with the parser contract, the frozen feed/representation metadata is correct, and the forward arithmetic is internally coherent.

Proceed to the remaining eight preregistered markets using the same generated logger and default classifier settings. Keep PR #77 Draft while data collection and the nine-market Phase-A study remain incomplete.
