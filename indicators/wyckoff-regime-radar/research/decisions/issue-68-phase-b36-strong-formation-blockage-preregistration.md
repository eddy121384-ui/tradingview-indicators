# Issue #68 Phase B3.6 — Strong Formation Blockage Audit Preregistration

Status: diagnostic only / no classifier changes / no performance use.

## Question

When TOP already points to a bullish or bearish trend family but `strongCandidate` is false, which existing C-2 gate blocks STRONG formation?

## Frozen lineage

- Issue #66 C-2 price-only classifier remains unchanged.
- B3.3 Core Bias remains unchanged.
- B3.4 Exposure A/B/C remain paused.
- B3.5 established that Formal -> Core lag is exactly 0 bars and STRONG -> FORMAL lag is at most 2 bars on frozen FX.

## Blocker taxonomy

For every post-warmup bar where TOP belongs to trend family 2/3 or 5/6 but `strongCandidate == false`, attribute blockers using the existing C-2 conditions only:

1. `NO_SHARP` — TOP/effective probability state is not usable/finite enough to qualify.
2. `DOMINANCE` — `top_value < dominant_min`.
3. `GAP` — `top_gap < top_gap_min`.
4. `EVIDENCE` — `evidence_strength < evidence_min`.
5. `CONFLICT` — `candidate_conflict == true`.

Blockers may overlap. No blocker threshold is changed or optimized.

## Mechanical outputs

On the already-burned four-FX fixtures and their reciprocal quotations:

- count TOP-trend bars;
- count STRONG-trend bars;
- count TOP-trend-but-not-STRONG bars;
- blocker count/share, including overlaps;
- unexplained blocked bars;
- reciprocal mirror diagnostics for TOP direction, STRONG direction, and each blocker mask.

Primary engineering gate: every blocked TOP-trend bar must have at least one blocker attribution after accounting for unusable/non-finite sharp state. No performance metric is allowed.

## TradingView audit

Generate a human-readable B3.6 Pine with horizontal bands:

1. TOP direction;
2. STRONG direction;
3. DOM/GAP gate pass;
4. EVIDENCE gate pass;
5. CONFLICT-free pass;
6. FORMAL direction;
7. CORE direction memory.

For gate bands, green means pass, red means blocked, gray means TOP is not in a trend family / gate not applicable. TOP/STRONG/FORMAL/CORE retain green=bull, red=bear, gray=neutral.

Priority human review:

- FR10Y 1D, especially 2021–2024;
- JGB10Y 1D, same period as control.

Goal: determine whether FR10Y's late STRONG formation is primarily caused by insufficient dominance/gap, insufficient evidence, candidate conflict, or repeated mixtures of these.

## Hard boundary

No PnL, return, Sharpe, drawdown, hit rate, transaction cost, sizing, stop, target, time exit, Strategy Tester optimization, Volume/MTF/Divergence/HMM rescue, or threshold shopping is permitted in B3.6.
