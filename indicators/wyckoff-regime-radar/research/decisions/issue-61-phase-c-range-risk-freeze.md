# Issue #61 — Phase C range-substate risk-management freeze

Status: **FROZEN BEFORE PHASE-C PNL**.

This rule is derived from structural occupancy only. No return, Sharpe, drawdown, or trade outcome was inspected when choosing the consolidation substate or exposure split.

## Why literal Stage 3 / 6 are not used

Formal and Candidate Stage 3 / 6 are structurally absent while the base lifecycle holds exposure, so they cannot operationalize the intended Re-accumulation / Redistribution risk-management behavior.

## Existing rangeScore audit

The v0.6 engine already defines:

- `rangeScore = 35` as the start of its existing range gate;
- `rangeScore = 70` as the point where that existing range gate is fully active.

While the frozen base lifecycle is holding:

- start gate (>=35) is active on 68.06% of long-held bars and 77.36% of short-held bars: too broad to represent a distinct consolidation substate;
- full gate (>=70) is active on 10.36% of long-held bars and 12.19% of short-held bars, with events in all four FX pairs: sufficiently selective to represent **Strong Trend Consolidation** without inventing a new threshold.

This selection is based on inherited model semantics and structural occupancy, not PnL.

## Frozen exposure semantics

The base lifecycle entry and exit rules remain unchanged.

Position size is decomposed into two equal conceptual tranches:

- **0.5 core**;
- **0.5 tactical/add tranche**.

The 50/50 split is a neutral semantic split, not an optimized fraction.

### Long

1. Enter the base lifecycle long at 1.0 exposure.
2. While the same long lifecycle episode remains valid, the first bar with `rangeScore >= 70` marks Strong Trend Consolidation and reduces desired exposure to **0.5**.
3. Once reduced, exposure stays at 0.5 even if rangeScore later falls below 70. There is no automatic re-risk merely because the range score cools.
4. Restore exposure to **1.0 only** on a later fresh `rangeBreakUp` while Formal Stage 2 is active and the base long episode remains alive.
5. A later Strong Trend Consolidation may reduce 1.0 to 0.5 again.
6. Base lifecycle family exit still closes the remaining core to 0.

### Short

Exact mirror using `rangeScore >= 70`, fresh `rangeBreakDn`, and Formal Stage 5.

## Same-bar precedence

A fresh matching structural break in the matching Formal trend stage takes precedence over the strong-range reduction on that same close. It represents the renewed-trend event and leaves / restores desired exposure at 1.0.

A newly opened base lifecycle entry also begins at 1.0. Strong-range reduction can act only from a later bar in that lifecycle episode.

## What is not added

- no stop loss;
- no profit target;
- no trailing stop;
- no time exit;
- no optimized fraction;
- no leverage above 1.0;
- no Early-Damaged rule in the primary Phase-C comparison;
- no Healthy-based entry;
- no new range threshold.

## Phase-C comparison

Primary incremental comparison:

1. `stage_lifecycle_base` — unit exposure;
2. `stage_lifecycle_range_managed` — same lifecycle, 0.5 core during/after Strong Trend Consolidation until a renewed fresh break restores 1.0.

`binary_color` may remain in the report as historical context but is not the incremental benchmark.

Report return, Sharpe, drawdown, exposure, turnover, reduction count, re-add count, and pair consistency.

## Boundary

All samples are reused development evidence. A favorable result does not validate the system and must not be used to retune the 70 boundary or the 0.5 split on the same data.
