# Issue #78 — Trendability / Oscillation Lab Visualizer Note

Generated Pine:

`indicators/wyckoff-regime-radar/research/generated/wyckoff-issue78-trendability-visualizer.pine`

Branch:

`research/issue-78-trend-capture-frontier`

## Purpose

Visually test the preregistered hypothesis that some formal Markup / Markdown signals occur inside a slower broad-oscillation environment where local directional legs fail to extend.

This script is mechanically generated from the frozen Issue #68 RC classifier. It does not alter formal regime semantics or Issue #78 exposure rules.

## Main line

`Trendability Composite` is the equal-weight mean of rolling within-market percentile ranks for path efficiency at:

- 63 bars;
- 126 bars;
- 252 bars.

Path efficiency is:

`abs(net displacement) / total absolute path travelled`

Interpretation:

- below 33.33: `Oscillation` diagnostic bucket;
- 33.33–66.67: `Neutral`;
- above 66.67: `Expansion` diagnostic bucket.

These are frozen descriptive terciles, not trading thresholds.

## Visual defaults

To keep the pane readable:

- the original upside-risk line is hidden in this research build;
- downside-risk line defaults off;
- original classifier Dashboard defaults off;
- Pace Guide defaults off;
- formal regime background remains available for context;
- only the composite Trendability line is shown by default;
- 63/126/252 component percentile lines can be enabled from settings.

## Entry logger

At each fresh formal Markup / Markdown entry on a 1D chart, the script emits one compact Pine Log row:

`ISSUE78TREND|schema=1|...`

Fields include ticker, event time, formal stage, raw ER63/126/252, percentile ranks and composite TrendabilityScore.

The entry-only logger is intentionally compact. It can be joined to the already accepted Issue #76 forward-behavior logs using `ticker + event_time + stage`, so no new future-outcome export is required.

## Manual smoke

First inspect US10Y visually, especially:

- 2010–2014;
- 2015–2019;
- 2020–2026.

Questions:

1. Does the composite visibly stay lower during broad range / repeated reversal environments?
2. Does it rise during genuinely directional multi-month expansion?
3. Does it avoid simply becoming another short-term momentum oscillator?
4. At fresh Markup / Markdown entries, are low-score and high-score cases visually meaningfully different?

Only after the visual behavior is sensible should the nine-market Pine Logs be collected for the preregistered quantitative test.

Refs #78, #80, #76.
