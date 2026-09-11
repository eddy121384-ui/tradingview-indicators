# Issue #78 — TradingView Visualizer Manual Smoke Checklist

Generated script:

`indicators/wyckoff-regime-radar/research/generated/wyckoff-issue78-trend-hold-visualizer.pine`

Manual gate:

1. Paste the generated Pine into TradingView Pine Editor.
2. Confirm Pine v6 compiles without modification.
3. Add to a 1D chart.
4. Confirm the original formal regime background still matches the Issue #68 RC behavior.
5. Confirm the bottom-right `Issue #78 Trend Hold Lab` panel appears.
6. During formal Markup, signed target exposure should be positive; during formal Markdown, negative; outside those two primary trend regimes, zero.
7. Confirm `Regime Age` resets on a new formal Markup/Markdown episode.
8. Confirm giveback is zero at a new favorable close-path extreme and rises as price moves against that extreme.
9. Confirm Gentle and Balanced exposures only de-risk when their frozen giveback buckets worsen.
10. Confirm damage-latch re-risking restores Full only after a new favorable close-path extreme, not merely because giveback shrinks into a healthier bucket.
11. Confirm exposure shown on the current close is interpreted as the next-bar target.
12. Do not treat the visualizer as production strategy authorization.

If TradingView reports a compiler error, record the exact error and line number in Issue #78; fix only visualization-layer syntax unless evidence shows source lineage drift.
