# Issue #78 — A4 causal Core-2 finding (translation frozen before OOS4)

Date: 2026-10-07. Discovery, not validation. `oos4_touched=false` — no OOS4
data fetched, inspected, built, summarized, or computed; analyzer asserts on
any `oos4` path. A0/A1/A2/A3 calculations, artifacts, thresholds, and
conclusions unchanged (one documentation-only Phase-0 prose correction to
the A3 finding, committed separately as `29b3f64`). No SD, weights, ML,
sign-flips, Pine, production. PRs #80/#148 unmerged.

## 0. Phase-0 reconciliation (artifact = source of truth)

Committed `issue78_ablation_a3/core_summary.csv` hard h10 ALL re-read:
bull_low −0.0725 (258 stocks, median +0.1305, pos 51.0%); bull_high −0.0334
(median +0.1197, pos 52.1%); bear_low −0.1568; bear_high −0.2311. The A3
prose claim "bull_low highest means and positive fractions at every
horizon" was wrong (bull_high leads both at h10/h20) as was "only
positive-median cell" (bull_high medians positive every horizon and block).
Corrected doc-only in `29b3f64`; verdicts rest on the median profile.

## 1. Preregistration

`decisions/issue-78-causal-core2-a0-preregistration.md` is
`issue-78-causal-core2-a4-preregistration.md`, frozen and committed as
`78d5afc92b625a29929f1a94f1431a1733bcc21b` BEFORE any A4 outcome:
prior-only expanding percentile `pct=(less+0.5·equal)/N_prior`, 252-bar
minimum, hard 80/20 + relaxed 70/30, horizons/blocks/aggregation, fidelity
diagnostics, 8 decision gates, SUPPORTED/NEUTRAL/CONTRADICTED rule
(ALL mean>0 AND ≥55% positive AND ≥3/5 blocks positive → SUPPORTED;
ALL mean<0 AND <45% → CONTRADICTED; else NEUTRAL).

## 2. Causal percentile (frozen definition)

Per stock/bar t, over N prior READY values only (self excluded):
`pct(t) = (count_strictly_less + 0.5·count_equal) / N`. Unavailable when
N<252 or bar t not ready. Implemented with insertion-ordered prior list
(exact tie handling via bisect_left/right).

## 3. No-lookahead tests — PASS (8/8)

Prefix-vs-full and append-future rebuilds leave all pre-existing causal
ranks exactly identical; 252 boundary exact (bars 0–251 unavailable, bar
252 available; non-ready bars never counted); hard/relaxed masks exact;
A1 axes unchanged on real data; A3 artifact spot-check passes; deterministic
rebuild on real OOS3 data passes.

## 4. Causal coverage

790,629 causal-ready bars (−8% vs retrospective, the warmup price); 265
stocks with causal bars; hard-cell h10 adequate stocks: bull_low 246,
bull_high 241, bear_low 252, bear_high 250 — gate 2 (≥200) PASS.

## 5. Hard 80/20 four-cell h10 ALL (aligned)

bull_low +0.001 (median +0.186, pos 52.2%); bull_high +0.008 (median +0.150,
pos 52.4%); bear_low −0.103 (median −0.219, pos 46.0%); bear_high −0.121
(median −0.336, pos 43.1%). Bull avg (+0.005) > bear avg (−0.112): gate 3
PASS. bear_high worst at every horizon (h1/h5/h10/h20): gate 4 PASS (relaxed
variant: bear_low marginally worse, interpretation unchanged).

## 6. Temporal robustness — gate 5 PASS (5/5 blocks)

Bull-avg > bear-avg in every fixed block (hard and relaxed). bear_high
worst in 4/5 blocks (2020–26: bear_low marginally worse). bull_low mean
positive in 2000–04 (+0.216), 2005–09 (+0.079), 2010–14 (+0.134); negative
in 2015–19 (−0.044), 2020–26 (−0.058); medians positive in ALL blocks.

## 7. Sleeve/sector/tails

bull_low positivity concentrates large-cap (68.9% vs mid 53.8% vs small
35.4%); ordering holds large 85%/mid 68% but reverses small (36%); sectors
mostly 50–86% except Discretionary 43%. Tails symmetric (~0.49/0.51) —
broad, not tail-driven. Gate 7 PASS with noted small-cap caveat (ordering
holds 5/5 blocks over 226 complete stocks; not a tiny subset).

## 8. 70/30 robustness — gate 6 PASS

Relaxed preserves bull>bears ordering in all blocks and the bear-side
concentration; no interpretation reversal.

## 9. bull_low vs bull_high — NEUTRAL

Paired low-minus-high h10 ALL +0.023 with 51.3% positive (rule needs ≥55%),
positive in 4/5 blocks. NEUTRAL per frozen rule — not required for
readiness; the probe-context role (best levels/medians) is unaffected.

## 10. Fidelity (diagnostic): causal tracks retrospective closely

Percentile Spearman 0.963 (structure) / 0.997 (extension); MAE 0.042/0.015;
cell Jaccard 0.75–0.79; ZERO cross-side migration (all disagreement is
core-vs-noncore margin).

## 11. A4 verdict — CORE2_CAUSAL_TRANSLATION_READY_FOR_OOS4

All 8 gates hold (1 tests ✓, 2 coverage ✓, 3 bull>bear ✓, 4 bear_high
worst ✓, 5 blocks 5/5 ✓, 6 relaxed ✓, 7 breadth-with-caveat ✓, 8 OOS4
untouched ✓). No rescue, no reinterpretation.

## 12. Next step

First OOS4 contact ONLY under a new preregistration reusing this frozen
translation verbatim (percentile, 252 warmup, 80/20 + 70/30, h10 primary,
same 8 gates as OOS4 pass/fail). No further OOS3 work on direction.

## 13. Operational notes

New files only: A4 analyzer + tests (8/8) + A4 artifacts + prereg + this
finding. CI status below in final report. Shared-worktree caveat stands.

Refs #78 #168 #162 #159 #156 #153 #148 #147 #138 #80.
