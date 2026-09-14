# Issue #78 — TradingView Visualizer Manual Smoke Checklist

Generated script:

`indicators/wyckoff-regime-radar/research/generated/wyckoff-issue78-trend-hold-visualizer.pine`

Manual gate:

1. Paste the generated Pine into TradingView Pine Editor.
2. Confirm Pine v6 compiles without modification.
3. Add to a 1D chart.
4. Confirm the original formal regime background still matches the Issue #68 RC behavior.
5. Confirm the bottom-right `Issue #78 Position Lifecycle` panel appears.
6. Default view should show one main signed target-exposure staircase, not the old two-policy clutter. Component lines should remain hidden unless explicitly enabled.
7. During formal Markup, signed target exposure should be positive; during formal Markdown, negative; outside those two primary trend regimes, zero.
8. Confirm the `Excursion-Proof` default starts a new trend at 25% (`試`).
9. In `Excursion-Proof`, participation cap should progress 25% -> 50% -> 75% -> 100% only after favorable MFE reaches 0.5 / 1 / 2 entry ATR.
10. Switch to `Persistence`; participation cap should progress 25% -> 50% -> 75% -> 100% at regime ages 0 / 5 / 10 / 20 bars.
11. Confirm regime age and MFE reset on every new formal Markup / Markdown episode.
12. Confirm Gentle / Balanced damage caps still use the frozen giveback buckets and only de-risk on deterioration.
13. Confirm damage-latch re-risking restores its cap only after a new favorable close-path extreme, not merely because giveback shrinks into a healthier bucket.
14. Confirm final target exposure always equals `min(participation cap, damage cap)`.
15. Confirm `加` / `滿` / `減` markers correspond to final target exposure changes, not future information.
16. Confirm exposure shown on the current close is interpreted as the next-bar target.
17. Do not treat the visualizer as production strategy authorization.

If TradingView reports a compiler error, record the exact error and line number in Issue #78; fix only visualization-layer syntax unless evidence shows source-lineage drift.
