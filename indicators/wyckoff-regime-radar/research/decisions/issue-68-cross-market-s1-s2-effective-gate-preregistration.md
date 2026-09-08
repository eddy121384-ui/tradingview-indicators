# Issue #68 — FR10Y vs DE10Y S1/S2 Effective-Gate Attribution Preregistration

Date: 2026-09-03
Status: DISCOVERY ONLY / FROZEN C-2 / NO TUNING

## Why this phase exists

The Bull-source / S3 attribution falsified the S3-rescue hypothesis. In the shared 2022-01-03 to 2023-12-29 1D window, Bull TOP is almost entirely S2 Markup in both FR10Y and DE10Y, while S3 Reaccumulation is effectively absent. The remaining cross-market split is therefore overwhelmingly S1 Accumulation versus S2 Markup.

Observed contrast supplied by TradingView:

- FR10Y: S1 TOP ~74.1%, S2 TOP ~21.1%, S3 TOP ~0.1%; S2 TOP avg gap ~15.1, gap-pass ~58.1%; avg p2 ~33.1.
- DE10Y: S1 TOP ~58.1%, S2 TOP ~36.1%, S3 TOP ~0.1%; S2 TOP avg gap ~24.1, gap-pass ~85.1%; avg p2 ~34.1.
- S1+S2 account for roughly 94–95% of TOP outcomes in both markets.
- Prior path-geometry audit found the local 2022–2023 yield paths nearly indistinguishable, while DE could still form Bull Core and FR could not.

## Mathematical constraint

The frozen probability transform uses a positive monotonic power (`effective_score ^ gamma`) followed by division by one common positive total. This transform can enlarge or compress TOP gaps, but it cannot change stage ordering. Therefore the FR/DE difference in S2 TOP occupancy must already exist before normalization, at the effective-score ordering layer.

This phase is designed to identify whether the cross-market split is created mainly by:

1. S1 versus S2 RAW ordering;
2. gate application changing the RAW winner;
3. a specific S1 gate component;
4. a specific S2 gate path (breakout, extension, continuation);
5. another stage stealing global TOP after S2 already beats S1;
6. post-effective gamma sharpening affecting gap quality only.

## Frozen measurements

For the same 2022-01-03 to 2023-12-29 1D window, measure without changing production logic:

- S1 RAW, gate, effective score;
- S2 RAW, gate, effective score;
- S1 gate components: range, bear-background-for-accumulation, downside-exhaustion, support-holding, non-markdown-continuation;
- S2 sub-gates: breakout, extension, continuation, plus which sub-gate supplies the max gate;
- S2>S1 RAW share;
- S2>S1 effective-score share;
- RAW-S2 -> effective-S1 flip share;
- RAW-S1 -> effective-S2 flip share;
- S2-effective-leader but non-S2-global-TOP share;
- average RAW margin (S2-S1), effective margin (S2-S1), and final p2-p1;
- pairwise S1/S2 share before and after gamma sharpening as a gap-amplification diagnostic only.

## Decision logic

- If RAW leadership is similar across FR/DE but effective leadership diverges materially, the gate layer is causal.
- If gate-layer divergence is concentrated in one S1 component, repair research must target that component's semantics, not TOP-gap thresholds.
- If gate-layer divergence is concentrated in one S2 sub-gate, repair research must target that continuation/breakout/extension path.
- If effective leadership is similar but global TOP differs, another stage is the remaining competitive contaminant.
- Gamma may be studied for gap amplification only; it must not be blamed for TOP winner changes because the transform is monotonic.

## Hard boundary

No production edits in this phase. No `topGapMin`, `confirmBars`, gamma, weights, threshold, rank length, MA, range, maturity, Heat, Break, Structure, Volume, MTF, Divergence, HMM, Strategy Tester, PnL, Sharpe, drawdown, or Exposure changes. No parameter search. No merge. Keep PR #73 Draft/Open and Issue #68 open until Eddy explicitly approves a repair after causal attribution and cross-market controls.
