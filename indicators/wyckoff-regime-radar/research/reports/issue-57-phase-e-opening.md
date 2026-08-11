# Issue #57 — Phase E holdout opening record

Status: **OPENED FOR ONE-SHOT EVALUATION**

Opening date: 2026-08-11 (UTC+8).

Preconditions satisfied before opening:

- Phase A boundary redesign frozen.
- Phase B stale-Formal decay frozen at `2 * confirm_bars` (6 bars under defaults).
- Phase C canonical four-state mapping frozen.
- Phase D semantics frozen as Regime Support / Regime Margin, not probability/confidence.
- Phase-E source/pair selection and exact file checksums already sealed.
- TradingView `OANDA:EURUSD`, `1D` manually compiled and ran the generated v0.6 research harness.
- TradingView self-test values matched the frozen design invariants: `50 / 100 / 0 / 1 / 3 / 6`.
- Operational verdict rules were committed before this opening record.

Holdout markets opened exactly once:

- USDCAD
- USDCHF
- EURCHF

The frozen data files and manifest remain immutable evidence. Opening the holdout does not authorize any parameter, mapping, response-rule, lag, cost, baseline-lookback, or verdict-rule change.

After this record, all Phase-E outputs are considered consumed independent-test results and cannot be used to tune v0.6 and then be re-presented as an independent validation.
