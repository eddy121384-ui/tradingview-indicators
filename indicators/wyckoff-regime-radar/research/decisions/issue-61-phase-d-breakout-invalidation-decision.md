# Issue #61 — Phase D breakout-invalidation decision

Status: **RISK-CONTROL VALUE OBSERVED; ALWAYS-ON VERSION NOT ACCEPTED AS CORE RULE**.

The rule was frozen before PnL: each trade stored the structural range-break level that caused entry and exited if a later close crossed back through that level. No buffer, ATR multiple, target, trailing stop, or sizing rule was allowed.

## Result

Median-pair metrics:

| Variant | Gross ann return | Gross Sharpe | Gross max DD | Net 2bp ann return | Net 2bp Sharpe | Net 2bp max DD | Exposure | Turnover/yr | Median hold bars |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Base lifecycle | -1.72% | -0.271 | -16.41% | -1.88% | -0.298 | -17.07% | 43.43% | 8.28 | 22.5 |
| Always-on breakout invalidation | -1.51% | -0.360 | -13.81% | -1.75% | -0.416 | -14.48% | 24.60% | 12.26 | 3.0 |

Cross-pair consistency versus base:

- gross return better: 3/4;
- gross Sharpe better: 2/4;
- gross max drawdown better: 4/4;
- net 2bp return better: 2/4;
- net 2bp Sharpe better: 2/4;
- net 2bp max drawdown better: 4/4.

There were 132 invalidation exits and 53 new-fresh-break re-entries. Entry anchors were recovered without missing cases.

## Interpretation

The structural level clearly contains useful **early failure / risk-control information**: drawdown improved in every reused FX pair and gross return improved in three of four.

However, keeping the original breakout level as a permanent hard stop is too aggressive for a trend lifecycle:

- median holding duration collapses from 22.5 bars to 3 bars;
- exposure falls from 43% to 25%;
- turnover rises materially;
- Sharpe does not improve consistently.

Therefore the Phase-D rule is **not accepted as the final lifecycle stop**. Do not tune a price buffer or ATR multiple on these same Phase-D outcomes to rescue it.

## Next development hypothesis

A failed breakout is most semantically relevant during the **initial confirmation window**, not necessarily months later after a trend has matured.

A new Phase E may therefore preregister an `early breakout invalidation` rule that keeps the same structural anchor but allows it to stop the trade only during the already-existing `confirmBars = 3` bars after entry / re-entry. If the trade survives that window, the anchor is retired and the ordinary Formal trend-family exit resumes control.

This is a new development hypothesis informed by Phase D, not an independent validation. It must be frozen before its own PnL is inspected and may not be described as OOS evidence.