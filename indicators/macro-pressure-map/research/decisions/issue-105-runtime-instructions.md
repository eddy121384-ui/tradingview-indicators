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
