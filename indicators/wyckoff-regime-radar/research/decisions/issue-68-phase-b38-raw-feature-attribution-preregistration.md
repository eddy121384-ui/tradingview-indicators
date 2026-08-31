# Issue #68 Phase B3.8 — Raw Feature Attribution Preregistration

Status: diagnostic only / frozen C-2 / frozen B3.3 / no performance use.

## Question

B3.7 localized most TOP-family misses to the raw-score layer. B3.8 asks what kind of raw competition is responsible and, for fresh directional trend formation, which existing mirrored Stage-2/Stage-5 inputs favor or oppose the new direction.

FR10Y and JGB10Y remain human-review counterexamples only. GB10Y remains a downstream/range-clearance control. None of these charts define a tuning target or economic reversal label.

## Symmetric target families

Bull audit:
- target trend family = Stage 2 / Stage 3;
- raw range competitors = Stage 1 / Stage 4;
- raw opposite-trend competitors = Stage 5 / Stage 6;
- fresh-trend pair = Stage 2 Markup versus Stage 5 Markdown.

Bear audit is the reciprocal mirror:
- target trend family = Stage 5 / Stage 6;
- raw range competitors = Stage 4 / Stage 1;
- raw opposite-trend competitors = Stage 2 / Stage 3;
- fresh-trend pair = Stage 5 Markdown versus Stage 2 Markup.

## Raw competitor attribution

Using the six existing smoothed C-2 raw stage scores only:

- `target_raw = max(raw scores in target trend family)`;
- `range_raw = max(Stage1 raw, Stage4 raw)`;
- `opposite_trend_raw = max(raw scores in opposite trend family)`;
- when target raw is not the maximum, record the exact raw winner stage and grouped winner family: precursor range, opposite range, or opposite trend.

No gate, probability, candidate, persistence, Core Bias, Exposure, or performance output participates in this classification.

## Fresh-trend mirrored component attribution

Current C-2 Stage-2/Stage-5 fresh-trend raw formulas are exact mirrors after Issue #66 repairs. Before the common EMA smoothing, the directional pair consists of six mirrored input edges:

1. BREAK: `breakoutScore` versus `explicitBreakdownScore`;
2. HEAT: `heatUp` versus `panicHeatDn`;
3. STRUCTURE: `structureStrong` versus `structureWeak`;
4. EXTENSION: `markupExtensionScore` versus `markdownExtensionScore`;
5. CONTINUATION: `markupContinuationScore` versus `markdownContinuationScore`;
6. TRACE: `accTraceForMarkup` versus `distTraceForMarkdown`.

Stage-2 raw0 uses effective weights 0.17 / 0.17 / 0.17 / 0.2125 / 0.1275 / 0.15 respectively; Stage-5 is the exact reciprocal mirror. B3.8 may report which weighted component contributes the largest negative directional delta, but it may not change any weight.

Stage-3/Stage-6 remain part of target-family and competitor identity accounting. Their internal formula attribution is deferred unless the B3.8 human audit shows they, rather than Stage-2/Stage-5 formation, are the dominant source of the rates reversal lag.

## Engineering checks

On already-burned FX fixtures and reciprocal quotations:

- raw competitor attribution must be exhaustive with no unexplained winner;
- Bull raw-winner classifications on P must mirror Bear classifications on 1/P apart from already-known tiny C-2 numerical/tie residuals;
- reconstructed Stage-2-minus-Stage-5 raw0 delta from the six weighted component deltas must match the direct raw0 delta to floating-point tolerance;
- no strategy-performance metric is permitted.

## TradingView human audit

Generate a direction-selectable Pine audit, default Bull for rates-yield reversals, with horizontal bands:

1. RAW ADV — target trend family beats all other raw stages;
2. TARGET > RANGE — target trend family beats Stage1/4 raw;
3. TARGET > OPP TREND — target trend family beats opposite trend-family raw;
4. BREAK EDGE — fresh-trend break evidence favors audit direction;
5. HEAT EDGE — heat favors audit direction;
6. STRUCTURE EDGE — structure favors audit direction;
7. EXTENSION EDGE — trend-extension evidence favors audit direction;
8. CONTINUATION EDGE — continuation evidence favors audit direction;
9. TRACE EDGE — predecessor Acc/Dist trace favors audit direction.

The legend/data window must also expose:
- target raw value;
- raw winning stage identity;
- Stage 2 / 3 / 1 / 4 / 5 / 6 raw values;
- current fresh-trend component values.

Priority human review:
- FR10Y 1D, especially 2021–2024;
- JGB10Y 1D as control;
- GB10Y only as a downstream/range-clearance exception control.

Interpretation:
- RAW ADV red + TARGET > RANGE red -> range-stage raw formulation is the main upstream competitor;
- RAW ADV red + TARGET > OPP TREND red -> opposite directional trend raw still dominates;
- fresh-trend component edge bands identify which mirrored Stage2/5 inputs are directionally late, without creating thresholds.

## Hard boundary

No PnL, returns, Sharpe, drawdown, hit rate, transaction costs, sizing, stops, targets, time exits, Strategy Tester optimization, Volume/MTF/Divergence/HMM rescue, threshold shopping, or raw-weight changes are allowed in B3.8.
