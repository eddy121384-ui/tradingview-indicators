# Issue #55 — Final-OOS response map, baselines, lag, and costs

Status: **FROZEN BEFORE FINAL OOS**

Frozen on: 2026-08-10

This document is the execution contract for the Issue #55 trading-utility comparison. It is intentionally fixed after Development + Exploratory diagnostics and **before any model output or future path is computed on Final OOS**.

The choices below are semantic and conventional; they are not selected by optimizing Exploratory OOS performance. Once this file is committed, no mapping, lookback, lag, or primary cost may be changed for the existing Final-OOS sample.

## 1. Primary Wyckoff response map

Use the frozen **formal state** only. Do not trade candidate state, stage weights, Evidence, or Top Gap.

| Formal state | Stage | Target position |
|---:|---|---:|
| 0 | No formal state | 0 |
| 1 | Accumulation | 0 |
| 2 | Markup | +1 |
| 3 | Re-accumulation | +1 |
| 4 | Distribution | 0 |
| 5 | Markdown | -1 |
| 6 | Redistribution | -1 |

Rationale:

- Accumulation and Distribution are transition / preparation states; stay flat rather than anticipate the break.
- Markup and Re-accumulation are treated as bullish continuation states.
- Markdown and Redistribution are treated as bearish continuation states.
- No confidence threshold is used. Pre-final confidence diagnostics showed poor calibration, so adding a threshold now would be post-hoc tuning.

## 2. Execution lag

All strategies use a **one-bar lag**.

A signal calculated from daily bar `t` becomes the held position for the return from close `t` to close `t+1` only after shifting the signal by one observation. There is no same-bar execution.

## 3. Primary transaction cost

Primary cost assumption: **1.0 pip per unit of position turnover**.

Pip size:

- EURUSD: 0.0001
- GBPUSD: 0.0001
- AUDUSD: 0.0001
- USDJPY: 0.01

For each position change, cost in simple-return units is:

`abs(position_t - position_{t-1}) * pip_size / close_t`

Examples:

- flat → long: 1 unit turnover = 1 pip
- long → flat: 1 unit turnover = 1 pip
- long → short: 2 units turnover = 2 pips

The cost model is deliberately simple and transparent. It is not intended to reproduce a specific broker's spread/commission schedule.

A separate robustness table may report 0.5-pip and 2.0-pip sensitivity, but **1.0 pip is the primary decision cost and may not be changed after Final OOS is opened**.

## 4. Baselines

All baselines use the same one-bar lag and the same turnover-cost model.

### B0 — Always flat

Target position = 0 at all times.

Purpose: transparent zero-risk / zero-return reference.

### B1 — 200-day simple moving-average trend

- `+1` when close > SMA(200)
- `-1` when close < SMA(200)
- `0` while SMA(200) is unavailable or when equal

The 200-day lookback is conventional and fixed, not optimized on this sample.

### B2 — 60-day close momentum

- `+1` when close / close[60] - 1 > 0
- `-1` when close / close[60] - 1 < 0
- `0` while the 60-day lookback is unavailable or when exactly zero

The 60-day lookback is a simple medium-term FX momentum benchmark and is fixed, not optimized on this sample.

### B3 — 55-day Donchian breakout with position carry

Use the **previous** 55 completed bars only:

- set target to `+1` when close > highest(high[1], 55)
- set target to `-1` when close < lowest(low[1], 55)
- otherwise carry the previous target position
- remain `0` until the 55-bar lookback is available

This is a simple price-only breakout benchmark. The 55-day lookback is conventional and fixed.

## 5. Utility metrics

Report separately by FX pair and in aggregate. At minimum:

- cumulative net return
- annualized net return
- annualized volatility
- annualized Sharpe ratio using zero cash rate for this relative research comparison
- maximum drawdown
- average absolute exposure
- total turnover
- number of position changes
- gross return and transaction-cost drag

Do not allow a single pair to carry the final conclusion.

## 6. Exploratory-OOS use after this freeze

After this document is committed, the same exact rules may be run on Exploratory OOS as a pre-final diagnostic.

**No result from that run may change this document.** If the rules look poor, they remain poor and Final OOS still uses the same frozen rules.

## 7. Final-OOS opening rule

Final OOS may be opened only after:

1. this decision file exists in the research branch;
2. canonical input manifest still says `SEALED_DO_NOT_EVALUATE`;
3. CI verifies the frozen input checksums;
4. the trading evaluator has tests for one-bar lag, turnover cost, and Final-OOS boundary selection;
5. the Exploratory-OOS utility report is committed without modifying the response map.

Opening Final OOS is a one-shot evaluation. Any rule change after that requires a new independent sample.

## Boundary

This response map is not a claim that the Wyckoff semantics are empirically validated. It is the predeclared executable interpretation required to test whether the frozen indicator adds decision value versus simple FX baselines.
