# Issue #68 Phase B3 — Regime-first v3 Semantic Diagnostic

Status: **burned development evidence / no PnL**

Primary reciprocal gate: **PASS**
- v3 desired-position mirror: **99.67%**
- preregistered gate: **>= 99.00%**
- mean pair flat share, rejected v2: **86.85%**
- mean pair flat share, regime-first v3: **43.72%**
- median of pair median-holds, v2: **29.0 bars**
- median of pair median-holds, v3: **23.0 bars**

## Per pair

| Pair | Formal mirror | v3 position mirror | v2 Flat | v3 Flat | v2 median hold | v3 median hold |
|---|---:|---:|---:|---:|---:|---:|
| EURUSD | 100.00% | 100.00% | 91.91% | 45.23% | 25.0 | 25.0 |
| USDJPY | 99.09% | 99.09% | 75.26% | 47.42% | 48.0 | 20.0 |
| GBPUSD | 100.00% | 100.00% | 80.55% | 44.62% | 33.0 | 21.0 |
| AUDUSD | 99.45% | 99.57% | 99.70% | 37.63% | 1.0 | 28.0 |

## v3 event counts

- **EURUSD**: `{'enter_long': 9, 'enter_short': 20, 'exit_long': 9, 'exit_short': 19, 'flip_long_to_short': 3, 'flip_short_to_long': 4, 'hold_long_reaccumulation': 0, 'hold_short_redistribution': 0}`
- **USDJPY**: `{'enter_long': 20, 'enter_short': 10, 'exit_long': 19, 'exit_short': 10, 'flip_long_to_short': 4, 'flip_short_to_long': 3, 'hold_long_reaccumulation': 0, 'hold_short_redistribution': 0}`
- **GBPUSD**: `{'enter_long': 17, 'enter_short': 16, 'exit_long': 17, 'exit_short': 15, 'flip_long_to_short': 3, 'flip_short_to_long': 2, 'hold_long_reaccumulation': 3, 'hold_short_redistribution': 0}`
- **AUDUSD**: `{'enter_long': 12, 'enter_short': 20, 'exit_long': 12, 'exit_short': 20, 'flip_long_to_short': 3, 'flip_short_to_long': 3, 'hold_long_reaccumulation': 0, 'hold_short_redistribution': 0}`

## Boundary

Semantic lifecycle diagnostic only. No return, Sharpe, drawdown, hit-rate, cost, sizing, stop, target, or Strategy Tester metric is computed.
