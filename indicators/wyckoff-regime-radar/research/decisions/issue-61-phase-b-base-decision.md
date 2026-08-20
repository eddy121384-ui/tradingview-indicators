# Issue #61 — Phase B base lifecycle decision

Status: **BASE LIFECYCLE SURVIVES AS DEVELOPMENT CANDIDATE; NOT VALIDATED**.

The Phase-A lifecycle semantics were frozen before PnL was inspected. Phase B then compared the frozen unit-exposure lifecycle against the historical failed `binary_color` comparator on the four already-burned static FX D1 fixtures.

No stop, target, partial-profit fraction, add sizing, leverage, or new breakout threshold was used.

## Result

Median-pair metrics:

| Variant | Gross ann return | Gross Sharpe | Gross max DD | Net 2bp ann return | Net 2bp Sharpe | Net 2bp max DD | Exposure | Turnover / yr |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| binary_color | -3.06% | -0.427 | -21.48% | -3.35% | -0.465 | -22.41% | 77.16% | 14.56 |
| stage_lifecycle_base | -1.72% | -0.271 | -16.41% | -1.88% | -0.298 | -17.07% | 43.43% | 8.28 |

Cross-pair consistency for the lifecycle versus binary color:

- gross return better: 3/4;
- gross Sharpe better: 2/4;
- gross max drawdown better: 4/4;
- net 2bp return better: 3/4;
- net 2bp Sharpe better: 2/4;
- net 2bp max drawdown better: 4/4.

Per-pair gross annualized return:

- EURUSD: -1.05% → **+0.40%**;
- USDJPY: -3.51% → **-3.10%**;
- GBPUSD: -2.61% → **-2.90%**;
- AUDUSD: -4.46% → **-0.54%**.

The lifecycle used materially less exposure and turnover while improving drawdown in every pair.

## Interpretation

### What survived

The user's original stage-action semantics are materially more coherent than treating every bullish-colored stage as continuously long and every bearish-colored stage as continuously short.

The strongest evidence is not immediate profitability; it is **risk/exposure efficiency**:

- observe states remove substantial low-information exposure;
- fresh-break + trend-stage entry reduces turnover;
- holding only inside the trend/consolidation family reduces drawdown in 4/4 pairs;
- returns improve in 3/4 pairs despite much lower market exposure.

Therefore the stage-aware lifecycle is worth continuing as a development candidate.

### What did not survive yet

The base lifecycle is still negative on the median pair and Sharpe improvement is only 2/4. It is **not** a profitable or validated trading system.

This result does not justify adding arbitrary stops, targets, partial-profit fractions, or optimized sizing. Those would create too many degrees of freedom before the core state machine is established.

## Frozen next step

The next comparison is the already-predeclared third variant:

`stage_lifecycle_plus_early_damage`

It must keep every Phase-A/Phase-B base lifecycle rule unchanged and add only the previously frozen Issue #57 **Early Damaged** transition-health risk warning as an exit/block overlay.

No new magnitude threshold is allowed. Healthy +3 remains confirmation only and is not used as a delayed primary entry.

Only after the Early-Damaged overlay result is recorded may Issue #61 consider a separately preregistered risk-management phase for partial profit, stops/trailing stops, or add sizing.

## Boundary

All Phase-B observations are reused development evidence. Any favorable result still requires a future untouched sample before validation or production trading claims.
