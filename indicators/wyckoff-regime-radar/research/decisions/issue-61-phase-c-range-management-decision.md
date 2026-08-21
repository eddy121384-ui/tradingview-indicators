# Issue #61 — Phase C range-management decision

Status: **REJECTED AS A CORE LIFECYCLE RULE**.

The Phase-C rule was frozen before PnL inspection:

- keep the Phase-B stage lifecycle unchanged;
- define Strong Trend Consolidation with the existing full range gate, `rangeScore >= 70`;
- reduce exposure from 1.0 to 0.5 when that substate first appears;
- do not restore automatically when rangeScore falls;
- restore 0.5 to 1.0 only on a new matching fresh structural break while Formal remains Stage 2 / Stage 5;
- no stop, target, trailing stop, leverage, or fraction optimization.

## Result

Median-pair metrics changed only marginally in return and worsened in risk-adjusted / drawdown terms:

| Variant | Gross ann return | Gross Sharpe | Gross max DD | Net 2bp ann return | Net 2bp Sharpe | Net 2bp max DD | Avg abs exposure |
|---|---:|---:|---:|---:|---:|---:|---:|
| Base lifecycle | -1.72% | -0.271 | -16.41% | -1.88% | -0.298 | -17.07% | 43.43% |
| Range-managed | -1.67% | -0.284 | -18.12% | -1.85% | -0.315 | -18.76% | 40.45% |

Cross-pair consistency versus the base lifecycle was **1/4** for gross return, gross Sharpe, gross max drawdown, net return, net Sharpe, and net max drawdown.

Per-pair gross return:

- EURUSD: +0.40% → +0.18%;
- USDJPY: -3.10% → -3.50%;
- GBPUSD: -2.90% → -3.33%;
- AUDUSD: -0.54% → -0.02%.

The rule generated 61 reductions and only 17 re-adds. Lower average exposure did not translate into consistent risk improvement.

## Interpretation

`rangeScore >= 70` is useful as a descriptive trend-consolidation substate, but the specific action **"cut to half and stay half until another fresh break"** does not survive this reused-data development comparison.

Do not tune the 70 threshold, 50% fraction, or re-add behavior on these same samples to rescue the result. The rule is rejected rather than optimized.

This does **not** reject the user's broader lifecycle idea. Phase B still showed that observe → fresh-break / trend-stage entry → trend-family hold is materially better behaved than binary color mapping. It only rejects this particular range-based partial-profit implementation.

## Next research step

Move to a semantically cleaner risk-exit test: if a trade exists because an effective fresh breakout / breakdown established the setup, test whether **breakout invalidation** can act as an early stop/exit before the slower Formal regime exit.

The invalidation rule must be frozen before PnL and should reuse the structural level that armed the trade rather than introducing a new ATR multiple or optimized threshold.

All Issue #61 samples remain reused development evidence; no validation claim is allowed.