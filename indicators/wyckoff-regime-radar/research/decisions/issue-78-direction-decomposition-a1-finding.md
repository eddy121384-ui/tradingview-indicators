# Issue #78 — A1 direction decomposition finding (velocity vs structure)

Date: 2026-10-06

Scope: decompose the rejected A0 Direction average into short-term velocity
(`speed_rank`) and slow MA structure on the already-inspected OOS3 cohort, per
Issue #156. **Architecture discovery, not fresh OOS validation.** No result is
OOS evidence. A0 artifacts and findings are preserved unchanged (verified:
A0 analyzer + finding have zero diff; A0 committed outputs intact in
`5ff4882`). No composite A1 score is proposed here — decomposition evidence
first. OOS4 untouched. PRs #80 / #148 unmerged.

## 1. Data integrity

- Same recovered OOS3 snapshot as A0: 300 stocks / 300 raw files / 0 failures;
  FIGI-set `017e9360…`; classifier blob `1eec08e7…`; snapshot audit pass.
- A1 coverage: 926,982 eligible bars → 859,256 ready bars (A0: 859,207; the
  +49-bar difference is bars where range/emerging/established primitives are
  NaN but all decomposition scores are finite — negligible, 0.006%).
- A1 frame verified bar-identical to A0 on real data for
  date/eligible/ready/forwards/direction/sd/deteriorating, and
  `clip(mean(velocity, structure))` reproduces A0 direction exactly.
- Horizons 1/5/10/20; within-stock quintile ranks; min 5 bars per stock-cell;
  min 30 stocks per aggregate. Fixed calendar blocks frozen before inspection:
  2000–2004 / 2005–2009 / 2010–2014 / 2015–2019 / 2020–2026 (+ ALL full sample).
- A1 outputs: `research/artifacts/issue78_direction_decomposition_a1/`
  (12 files + `.zip`; per-file SHA-256 recorded). Primary horizon is 10 bars.

## 2. Exact formulas (decomposition only, nothing redefined)

- `dir_velocity = 2*speed_rank - 100` (signed velocity)
- `ma_bull` / `ma_bear` = frozen A0 bullish/bearish MA-structure scores
  (0..100, same four-component formulas as the A0 module; recombine exactly)
- `dir_structure = ma_bull - ma_bear` (signed slow structure)
- `extension = abs(dir_velocity)` (unsigned extension magnitude)
- Controls (comparison only, unchanged): A0 `direction`, `sd`, `deteriorating`.
- No six-stage label is an input. No sign-flip of A0 anywhere.

## 3. Velocity alone — behaves as extension/exhaustion, not continuation

ALL-sample signed forwards tilt negative with velocity but middle quintiles
are noisy (h10: Q1 +0.089, Q2 -0.017, Q3 +0.029, Q4 +0.044, Q5 -0.046; h20:
Q1 +0.229 → Q5 -0.114). Aligned extremes, both sides negative: up-extreme
-0.047 (h10) / -0.114 (h20); down-extreme -0.089 / -0.229. High positive
velocity does not earn continuation; strongly negative velocity
mean-reverts against the bearer (median-stock median -0.286 at h10).

## 4. MA structure alone — no directional continuation either

Structure quintiles (signed fwd, ALL): h10 Q1 (most bearish) **+0.178** →
Q5 (most bullish) **-0.081**; h20 +0.368 → -0.273. The structure axis is
itself inverted as a signed predictor: bearish structure is followed by
rising prices, bullish structure by flat-to-falling prices. Aligned: structure
up-extreme -0.081 (h10) / -0.273 (h20); down-extreme -0.178 / -0.368.
MA-bull and MA-bear legs are exactly complementary (Spearman ∓1.000 in 100%
of stocks — one degree of freedom by construction); keep only the signed
`dir_structure`, drop separate legs.

## 5. Structure × extension interaction — the only working split, asymmetric

- **Bear side (hard 80/20): low-minus-high extension = +0.048 (h10, 263
  stocks, 56.3% positive; h20 +0.120).** By block (h10): 2000–04 +0.438,
  2005–09 +0.161, 2010–14 +0.435, 2015–19 +0.144, 2020–26 -0.037. Relaxed
  median-split version is positive in every block including 2020–26.
- **Bull side: no interaction** (hard low-minus-high: h10 -0.010, 46.5%;
  h20 +0.032; relaxed ≈ 0). Extension does not differentiate bullish-structure
  outcomes at hard thresholds.
- **Within bull structure, low velocity beats high velocity at every horizon**
  (vel_low-minus-vel_high aligned: h1 +0.015, h5 +0.032, h10 +0.054,
  h20 +0.183; 249 stocks, 53–57% positive). Within bear structure the same
  contrast is ≈0/negative. Extension penalty is real where structure is
  bullish, and bear-side high-extension is where damage concentrates.
- Continuous check is weak: per-stock Spearman(extension, aligned fwd) is
  -0.023 (bear, 60.2% negative) and +0.006 (bull) — the effect is
  threshold/nonlinear, not linear; binned diagnostics stand, continuous does
  not replace them.

## 6. Temporal robustness

The inversion pattern is regime-dependent, identically for velocity and
structure (Q5–Q1 per-stock spread, h10): strong inversion in 2000–04
(vel -0.321, struct -0.401), 2010–14 (-0.353, -0.446), 2015–19 (-0.246,
-0.354); **absent in 2005–09** (vel -0.039, struct -0.031) and faded for
velocity in 2020–26 (-0.047) while structure stays inverted there (-0.288).
The 2005–09 crisis block is the exception for both components — consistent
with the old R0 finding that only early blocks were positive, and a warning
that any directional use is era-dependent.

## 7. Sleeve / sector breadth (h10 ALL)

Bear-side hard interaction: mid +0.034 / small +0.169 positive, large -0.035
≈ 0 (medians +0.02/+0.16/+0.11 — directionally consistent, large-cap muted).
Bull interaction ≈ 0 in all sleeves. Sector cuts are mixed with small-n
(Staples -0.500 on bear-hard at n=21 vs mid/small positive) — no sector may
carry a rule; one-stock-one-vote primacy holds.

## 8. Tail diagnosis — inversion is broad, not tail-driven

Down/bear cells: only 33–45% of stocks positive, median-stock medians deeply
negative (velocity down-extreme -0.286, structure down-extreme -0.330).
neg_share is modestly elevated (53–57% vs ~50% in up cells), so tails lean
against, but the bulk of the inversion is broad cross-sectional negativity,
not a few disasters. Up-side cells sit near 50/50 with positive medians and
negative means — there the mean/median gap IS tail-driven (adverse left tail),
matching A0.

## 9. Redundancy — two severe findings

- **`dir_velocity` vs A0 `sd`: +0.944** (median +0.948) — severe. A0
  supply-demand is essentially velocity in disguise, which explains why both
  inverted together. Any sd reuse must be rebuilt orthogonal to velocity.
- **ma_bull vs ma_bear: -1.000** (100% of stocks beyond both thresholds) —
  severe by construction; dir_structure (±1.000 with each leg) already
  contains all of it. Structure = one signed axis.
- A0 direction loads on both children (velocity +0.772, structure +0.829;
  97.5% of stocks structure–direction |rho|>0.70) — averaging them blended two
  different failures. Velocity–structure cross-correlation is only +0.308, so
  the decomposition itself is clean.
- Deteriorating is uncorrelated with everything here (|rho| ≤ 0.09) — its A0
  inversion comes from elsewhere (out of scope for this issue).

## 10. Conclusion — C. BOTH USEFUL BUT SEPARATE

Neither component works as direction (both inverted as signed predictors),
so A and B are rejected; the interaction evidence is too consistent to call
both useless, so D is rejected. **C: keep structure as the conditioning side
axis and velocity as the extension-magnitude gauge — strictly separate,
never averaged.** Explicitly: YES, `speed_rank` behaves mainly like
extension/exhaustion (high velocity predicts worse aligned forwards;
low-beats-high inside bullish structure at all horizons; sd ≡ velocity at
+0.944 proves the loading is in the primitive itself).

## 11. Recommendation for the next Issue #78 research step

Next factor study: rebuild supply-demand orthogonal to velocity (it is
currently a velocity proxy), then test the only surviving directional
hypothesis from this issue — bullish-structure + low-extension as a
probe-state conditioner — with temporal-block gates, frozen before any new
data contact. Still no OOS4, no production use, no sign-flips.

## 12. Operational notes

- A0 files untouched (analyzer + finding diff empty; committed A0 outputs
  intact). New files only: `analyze_issue78_direction_decomposition_a1.py`,
  `test_issue78_direction_decomposition_a1.py` (6/6 pass, incl. real-data
  A0-parity), A1 artifacts + this finding.
- Workstation caveat: a second process is concurrently using this worktree on
  another branch (observed mid-session branch flips); all commits below were
  verified on the correct branch before push. Future parallel work should use
  separate worktrees.

Refs #78 #156 #153 #148 #147 #138 #80.
