# Issue #78 — A2 supply-demand rebuild finding

Date: 2026-10-06

Scope: rebuild the Supply/Demand axis so it is not a disguised velocity /
extension score, per Issue #159. **Architecture discovery, not fresh OOS
validation.** A0 and A1 artifacts/findings preserved unchanged (A0 analyzer +
finding zero diff; A0 committed checksums re-verified). A1 velocity/structure
formulas reused by import, never redefined. No tuned weights, regression, ML,
sign-flips, six-stage rescue, OOS4, production or Pine changes. PRs #80 / #148
unmerged. No composite beyond the two predeclared candidates.

## 1. Data integrity

- Same recovered OOS3 snapshot: 300/300, FIGI-set `017e9360…`, blob
  `1eec08e7…`, audit pass; 926,982 eligible bars.
- A2 ready bars and A1-axis parity verified on real data (same eligibility,
  forwards, velocity/structure/extension).
- Horizons 1/5/10/20; within-stock ranks; min 5 bars/cell; min 30 stocks;
  fixed blocks 2000–04/05–09/10–14/15–19/20–26 + ALL (unchanged from A1).
- Outputs: `research/artifacts/issue78_supply_demand_a2/` (12 files + `.zip`,
  SHAs recorded). Primary horizon 10 bars.

## 2. Exact formulas (all simple differences, predeclared)

- `holding_balance = support_holding - resistance_holding` (candidate H)
- `exhaustion_balance = downside_exhaustion - upside_exhaustion` (candidate E)
- `a0_sd` = A0 control, unchanged, benchmark only.
- High Demand = top quintile of candidate rank; high Supply = bottom quintile.
- Bull cells aligned +1 (demand-good), bear cells −1 (supply-good). Hard
  80/20 first, predeclared 70/30 relaxed second. No other candidate proposed.

## 3. Primitive findings (Phase A)

Distributions are healthy (median ~2,600 distinct values/stock, modal share
≈0.04%) — degeneracy is NOT the problem. Contamination is: every primitive
is velocity-loaded (|rho| vs velocity: sup_hold +0.88, down_exh +0.87,
res_hold −0.86, up_exh −0.80). Primitive cross-correlations run ±0.72–0.83
except down-vs-up exhaustion (−0.58, the cleanest pair — still velocity-bound
on both legs). Quintile endpoints (h10 ALL signed): sup_hold Q1 +0.106 →
Q5 −0.060 (inverted); down_exh +0.026 → −0.022 (weak inversion); up_exh flat;
res_hold Q1 −0.091 → Q5 +0.005 (tiny positive tilt, the mirror of velocity).
No primitive works standalone.

## 4. holding_balance result — REDUNDANT

- Orthogonality: +0.878 vs velocity (severe), +0.974 vs a0_sd, +0.891 vs
  exhaustion_balance, +0.935 vs sup_hold. Fails the 0.70 gate by distance.
- Quintiles (h10 ALL): Q1 +0.088 → Q5 −0.084, inverted in all sleeves
  (large −0.146, mid −0.068, small −0.307).
- Conditionals: bull demand-minus-supply negative at ALL horizons
  (h10 −0.128 bull-high; bull-low only 3 stocks); bear supply-minus-demand
  ≈0 ALL (+0.03 ALL, negative in early blocks, sleeve-inconsistent).
  Expected ordering absent everywhere.

## 5. exhaustion_balance result — REDUNDANT (severe)

- Orthogonality: **+0.961 vs velocity** — essentially velocity itself; +0.967
  vs a0_sd. The exhaustion terms ARE the contamination source, as suspected.
- Quintiles flat-to-weak-inverted (h10 Q1 +0.012 → Q5 −0.047).
- Conditionals mirror holding_balance at smaller magnitude (bull-high −0.054;
  bear ALL ≈ 0 with early-block negatives). Nothing independent survives.

## 6. Redundancy result (Phase C gates)

Both candidates exceed 0.70 vs velocity and are therefore rejected as
independent axes. Full gate table: candidates vs velocity/extension/structure/
direction/deteriorating all exceed caution; deteriorating stays clean (|rho|
≤ 0.09) but is out of scope here. The four primitives offer no clean linear
combination: any demand-minus-supply difference of velocity-loaded terms stays
velocity-loaded (holding +0.878 is the *best* case and still severe).

## 7. Conditional bull/bear results (Phase D)

Hard 80/20 reported first in all cases; 70/30 relaxed agrees (same signs,
smaller magnitudes). Bull-side expected ordering (demand > supply) fails for
all three candidates at all horizons (ALL deltas ≤ −0.05). Bear-side expected
ordering (supply > demand) fails ALL (≈0 to +0.09, driven by 2020–26 while
early blocks are deeply negative) and sleeves disagree in sign (large/mid
positive vs small −0.45). Tails: broad-based, not tail-driven (down-cell
positive-stock fractions 33–45%, negative medians). No candidate passes gate
2 (both orderings present) or gate 4 (temporal stability).

## 8. Temporal robustness (Phase E)

No block rescues any candidate: early-block bear cells are strongly negative
(e.g. bear-high a0_sd h10: 2000–04 −0.845, 2010–14 −0.552), 2005–09 ≈ 0,
2020–26 weakly positive but sleeve-split. Inconsistent sign across eras =
fail of gate 4 for every candidate.

## 9. Candidate classifications

- **holding_balance — REDUNDANT** (severe velocity/a0_sd/exhaustion overlap;
  inverted ordering on top).
- **exhaustion_balance — REDUNDANT** (severe; +0.961 vs velocity).
- **a0_sd (control) — REDUNDANT** (as expected; retained as benchmark only).

Verdict: **NO CLEAN SUPPLY-DEMAND FACTOR FROM CURRENT PRIMITIVES.** None of
the five A3 gates is met by any candidate (1: redundancy far above bar;
2: orderings absent/inverted; 3: sleeve sign splits; 4: era sign splits;
5: distributions pass, the only gate met — necessary but far from
sufficient).

## 10. Recommended A3 step

Stop mining these four primitives for S/D. A3 should be an **ablation study**:
freeze the surviving two-axis core (structure side × extension magnitude)
and test whether dropping the S/D axis entirely loses anything on the
bull-structure + low-extension probe conditioner — if nothing is lost, the
architecture simplifies to two factors with no S/D pretense. Any genuinely
new S/D primitive family would require a fresh preregistration and new-data
contact rules, explicitly out of scope here.

## 11. Operational notes

- A0/A1 untouched (verified by diff + checksums). New files only: A2
  analyzer, A2 tests (6/6 pass incl. real-data A1 parity), A2 artifacts +
  this finding.
- Workstation caveat: another process is concurrently using this worktree on
  unrelated branches (observed repeated branch flips, including a new
  `issue-160` branch); all work re-verified on the correct branch before
  commit/push. Parallel work should use separate worktrees.

Refs #78 #159 #156 #153 #148 #147 #138 #80.
