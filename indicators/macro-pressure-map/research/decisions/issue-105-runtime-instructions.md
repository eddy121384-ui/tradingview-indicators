# Issue #105 runtime instructions

The validation harness is intentionally Pine-only because ISM historical PMI data should remain inside TradingView's licensed runtime.

## Run

1. Open any symbol on a **1M / monthly** TradingView chart.
2. Add `bci10_intended_v01_fed_validation.pine`.
3. Do not change the code or source fields.
4. Read the top-right table after the chart loads.

The table reports:
- first/last usable forecast origin;
- number of evaluation rows;
- P / R_hawk / PS correlation with future six-month Fed Funds change;
- fixed-threshold balanced accuracy;
- tighten/ease accuracy;
- PS zero-crossing event-study means at +3/+6/+12 months;
- PS confusion matrix.

Hidden plots are included so TradingView's chart-data export can export the aligned validation rows if a durable CSV is needed later.

## Important

This script does not use Treasury or portfolio returns.

The sample is frozen at realized Fed Funds outcomes through December 2025, so future data releases do not silently expand this preregistered test.


## 2026-09-23 pre-outcome runtime amendment

The user's TradingView account returned `Permission denied for symbol: ECONOMICS:USCPCEPI` before any #105 validation outcome was visible.

Core PCE transport is therefore amended to:
`request.security("FRED:PCEPILFE", "M", close)`

This preserves the same monthly BEA Core PCE index construct and the same YoY transformation. No model weight, lag, threshold, horizon, or outcome definition changed.

See:
`decisions/issue-105-preoutcome-runtime-source-amendment.md`
