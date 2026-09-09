# Issue #76 — Nine-Market Pine Log Intake QC

## Status

**INPUT QC PARTIAL PASS — ONE PREDECLARED TRUNCATION GATE REMAINS**

This note records only ingestion/data-quality checks. No forward-behavior result cell, pooled edge, stage comparison, or strategy conclusion was inspected before the data gate was resolved.

## Received universe

All nine frozen feeds are now represented across the user-provided Pine Log exports:

| Feed | Marker rows | Event range (UTC event date) | Representation | Duplicates | QC |
| --- | ---: | --- | --- | ---: | --- |
| TVC:FR10Y | 8,303 | 1988-12-01 → 2026-08-11 | YIELD_LEVEL | 0 | PASS |
| TVC:US10Y | 9,832 | 1980-03-26 → 2026-08-09 | YIELD_LEVEL | 0 | PASS |
| TVC:DE10Y | **10,000** | 1984-06-08 → 2026-08-11 | YIELD_LEVEL | 0 | **HOLD — exactly-10,000 gate** |
| TVC:GB10Y | 9,722 | 1982-11-24 → 2026-08-10 | YIELD_LEVEL | 0 | PASS |
| TVC:AU10Y | 9,957 | 1986-01-01 → 2026-08-10 | YIELD_LEVEL | 0 | PASS |
| TVC:JP10Y | 4,148 | 2009-03-12 → 2026-08-10 | YIELD_LEVEL | 0 | PASS with measurement-artifact note below |
| OANDA:EURUSD | 5,397 | 2005-04-07 → 2026-08-10 | PRICE_LOG | 0 | PASS |
| OANDA:GBPUSD | 5,454 | 2005-04-18 → 2026-08-10 | PRICE_LOG | 0 | PASS |
| OANDA:USDJPY | 5,305 | 2005-04-06 → 2026-08-10 | PRICE_LOG | 0 | PASS |

All files use the TradingView Chinese CSV envelope `日期,訊息`, contain only the intended frozen feed, and use 1D bars with the expected Auto representation outcome.

## DE10Y truncation gate

The preregistered parser explicitly treats a file containing exactly 10,000 Issue-76 marker rows as a possible Pine Logs export cap and requires another time-window export before the nine-market matrix is run.

The received `TVC:DE10Y` file contains exactly **10,000** marker rows. Therefore the full Phase-A matrix remains blocked even though its visible event range spans 1984–2026.

Required human re-export, same logger / 1D / Auto / feed, split at 2005-01-01:

1. DE10Y window A: Event start = 1970 / all; Event end = 2004-12-31 23:59.
2. DE10Y window B: Event start = 2005-01-01 00:00; Event end = 2100 / all.

The currently received DE10Y file implies roughly 4,730 / 5,270 rows on those two sides, so both split files should remain comfortably below 10,000 if the export is complete.

## Zero-RMS Pine numerical artifact

A second, smaller measurement-layer artifact was found:

- DE10Y: 8 rows where `rv5` and `rvn5` serialize as `NaN`.
- JP10Y: 2 rows where `rv5` and `rvn5` serialize as `NaN`.

For **all 10 cases**, the same ticker has five consecutive event bars and each corresponding one-bar close-to-close move is exactly zero. Therefore the mathematically defined five-bar RMS close change is exactly zero. The `NaN` is a numerical artifact of the Pine measurement expression, not a classifier defect and not missing market data.

This will be handled deterministically in the measurement pipeline only: zero-RMS repair is allowed only when the five consecutive one-bar moves can be proven to be zero; otherwise parsing fails closed. No classifier, gate, stage weight, representation routing, or lifecycle logic may change because of this artifact.

## Outcome boundary

Until the split DE10Y exports are received and the zero-RMS handling is codified/tested, do **not** inspect or publish:

- per-stage forward-return summaries;
- fresh-entry comparisons;
- canonical-transition results;
- pooled symmetry results;
- any candidate trading edge.

This preserves the preregistered operational order and avoids learning from a partially validated nine-market sample.
