# Issue #57 — Top-2 directional-consensus semantics amendment

Status: **RECORDED BEFORE ACTION-COMPATIBLE RE-RUN**

The first Top-2 diagnostic grouped stages 1/2/3 as bullish and 4/5/6 as bearish. That grouping was intentionally simple, but inspection of the frozen v0.5.2.1 Pine shows that it does **not** match the indicator's own action semantics.

The frozen Pine explicitly defines:

- bullish actionable stages: 2 Markup and 3 Re-accumulation;
- bearish actionable stages: 5 Markdown and 6 Redistribution;
- stage 1 Accumulation: low-level accumulation / wait for confirmation;
- stage 4 Distribution: high-level supply / wait for breakdown confirmation.

Therefore the user's phrase "候選跟次要落在同向" is better represented, for this diagnostic, as:

- bullish Top-2 consensus: Top1 and Top2 are exactly the two stages {2, 3};
- bearish Top-2 consensus: Top1 and Top2 are exactly the two stages {5, 6};
- stages 1 and 4 are transition/context stages and do not by themselves create directional consensus.

The primary threshold remains unchanged at Top1 + Top2 >= 90%. This semantic correction is made from the frozen indicator's own action logic, not from backtest results.

The earlier broad-family report is preserved as a superseded diagnostic rather than overwritten.

A separate unresolved fidelity point also remains: real v0.5.2.1 defaults Volume Mode to Auto, and Volume can modify the six stage weights. The current static FX research fixtures are OHLC-only, so the action-compatible re-run remains price-only. If this corrected price-only test still fails to reproduce the user's live impression, the next fidelity step is to reproduce the default Volume-Auto dashboard path using a data source with volume/tick-volume.
