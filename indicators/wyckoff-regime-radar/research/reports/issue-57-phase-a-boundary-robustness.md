# Issue #57 — v0.6 Phase A boundary robustness

Status: **diagnostic_complete_pending_phase_review**

This report measures local price-boundary continuity only. It does **not** evaluate PnL or reuse the burned Issue #55 Final OOS as an independent test.

## Preservation / design boundary

- Frozen v0.5 Python mirror blob: `b7d1c7e02194e46e162c999854aff6907bd5be3d`
- Frozen v0.5.2.1 Pine source: unchanged.
- Soft transition width: **0.25 ATR**; fixed as an engineering width, not selected from trading PnL.
- Formal-state persistence, state count, witnesses, HMM, and trading response remain unchanged in Phase A.

## 50-bar structural boundary counterfactual

| Metric | v0.5 | v0.6 |
|---|---:|---:|
| Median six-weight L1 jump | 26.092328 | 0.005560 |
| Median Distribution+Markdown jump | 9.849172 | 0.000215 |
| Named no-break primitive jump | 100.000000 | 0.036222 |

- Median six-weight discontinuity reduction: **99.979%**.
- v0.6 lower/equal/higher cases: **8 / 0 / 0**.
- Worst remaining v0.6 case: **GBPUSD high 2017-12-06**, L1 jump **0.028210**.

## 20-bar breakout / breakdown counterfactual

| Metric | v0.5 | v0.6 |
|---|---:|---:|
| Median six-weight L1 jump, all cases | 18.832590 | 0.004469 |
| Max v0.6 jump among actual event toggles | — | 0.028210 |

- Event toggles: **8 / 8**; isolated from the 50-bar transition band: **4**.
- Median six-weight discontinuity reduction: **99.976%**.
- Worst remaining toggled case: **GBPUSD high 2017-12-06**, L1 jump **0.028210**.

## Interpretation boundary

A lower local discontinuity is evidence of improved numerical/feed robustness only. It is not evidence of predictive utility, profitability, calibrated confidence, or successful independent OOS validation.

Phase A should be accepted or expanded based on the residual discontinuity shown above. Do not infer trading improvement from this report.
