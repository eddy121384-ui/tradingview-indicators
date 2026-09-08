# Issue #68 Phase B3.5 — Core Bias Reversal Forensic

Status: **diagnostic only / frozen C-2 + frozen B3.3**

Primary gate: **PASS**
- Core reciprocal mirror: **100.00%**
- Formal -> Core zero-lag invariant: **True**
- Core flip events inspected: **58**
- median local TOP -> STRONG lag: **0.0 bars**
- median STRONG -> FORMAL lag: **2.0 bars**
- max STRONG -> FORMAL lag: **2 bars**
- median direct STRONG run: **3.0 bars**
- prior opposite-STRONG attempts before successful flips: **32 total**

## Per pair

| Pair | TOP mirror | STRONG mirror | FORMAL mirror | CORE mirror | Core flips |
|---|---:|---:|---:|---:|---:|
| EURUSD | 99.76% | 99.94% | 100.00% | 100.00% | 12 |
| USDJPY | 99.94% | 99.94% | 99.33% | 100.00% | 16 |
| GBPUSD | 99.82% | 99.88% | 100.00% | 100.00% | 16 |
| AUDUSD | 99.88% | 99.94% | 99.57% | 100.00% | 14 |

## Interpretation boundary

The local TOP/STRONG lags describe the classifier's immediate lead-in to an actual Core flip. They do not claim to identify the economically true reversal date. Cross-market TradingView review is required to determine whether suspected stale bias begins before TOP, between TOP and STRONG, or between STRONG and FORMAL.

Diagnostic semantics only. No strategy performance, sizing, stops, targets, or execution optimization is evaluated.
