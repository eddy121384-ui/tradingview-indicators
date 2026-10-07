# Issue #78 — Factorized classifier A0 discovery finding (OOS3)

Date: 2026-10-05

Scope: first-pass A0 architecture discovery on the already-inspected OOS3
300-stock Bloomberg cohort, per the 2026-10-05 discovery amendment. This is
**architecture discovery, not fresh OOS validation**. No result below is OOS
evidence. Historical OOS2/OOS3 findings are unchanged. PRs #80 / #148 untouched
(unmerged).

## 1. Data integrity confirmation

- Cohort: 300 securities / 300 raw Bloomberg files / 0 failures.
- FIGI-set SHA-256: `017e9360402afa002dc0970088649e7c411c4f02333dec550f2432be3c0dd701` (exact frozen cohort).
- Recovered snapshot byte SHA: `f6753c46788accf4a90e8d917fe2863a96e2c70006355ee5fdd1c326d4cb7712`
  (original `9d4a14d1…` byte identity unrecoverable after the local-artifact
  loss; see `issue-78-oos3-local-artifact-recovery-note.md`. Cohort identity is
  by FIGI set, as the recovery protocol requires.)
- Snapshot audit: **pass** (300/300, checksums clean, 372 OHLC repairs / 38
  securities recomputed = manifest, 1998-01-02 → 2026-08-31).
- Frozen classifier blob: `1eec08e791403453853b589373bb2270c508c3bb`.
- Coverage: 926,982 eligible bars → 859,207 factor-ready bars; 281 stocks
  contribute to headline cells (282 to correlations; 18 short-history names
  have zero ready bars and are retained as fixed members).
- Horizons 1/5/10/20; within-stock quintiles; min 5 bars per stock-cell;
  min 30 stocks per aggregate (descriptive otherwise).
- Untouched A0 outputs (formulas frozen before run):
  `research/artifacts/issue78_factorized_classifier_discovery_a0/`
  (10 files + `.zip`; per-file SHA-256 recorded in the run log).
  Primary horizon below is 10 bars unless stated.

## 2. Exact A0 formulas used (unchanged)

- `direction = clip(mean(2*speed_rank-100, ma_bull_spread-ma_bear_spread), ±100)`
- `range_factor = range_score`; `expansion_factor = 100 - range_factor`
- `sd = clip(mean(downside_exhaustion,support_holding) - mean(upside_exhaustion,resistance_holding), ±100)`
- `emerging = breakout_score` (direction>=0) else `explicit_breakdown_score`
- `established = mean(range_cont_direction, ma_direction_spread)`
- `deteriorating = supply` (direction>=0) else `demand`
- Old six-stage raw/effective/probability/formal labels are NOT factor inputs.

## 3. Headline results (10-bar, one-stock-one-vote)

| Test | Result (equal-stock mean) | Breadth |
|---|---|---|
| Direction up-extreme (aligned) | **-0.080 ATR** (pos 50.9%, median-stock median +0.117) | 281 stocks |
| Direction down-extreme (aligned) | **-0.145 ATR** (pos 43.2%, median -0.345) | 281 stocks |
| Direction Q1→Q5 signed | +0.145 → +0.027 → +0.010 → -0.007 → **-0.079** (monotonic decreasing; repeats at 1/5/20 bars) | Q5-Q1 spread mean -0.224, pos 34.2% |
| Lifecycle up delta (good-minus-bad) | **-0.180** (pos 38.8%, med -0.285) | 134 stocks |
| Lifecycle down delta | **-0.043** (pos 45.7%, med -0.072) | 210 stocks |
| Range×SD paired deltas | **unevaluable** (opposite legs missing) | — |
| Emerging durability | **unevaluable** (high-det leg absent; low-det leg 1 stock) | — |
| Expansion-minus-Range abs move | **-0.327** (pos 10.0%, med -0.296; high-Range moves MORE) | 281 stocks |
| Strongest correlation | direction–sd **+0.770** (med +0.772) | 282 stocks |

Both preregistered central gates fail: Test A lifecycle delta is negative in
**both** directions; Test B cannot be formed.

## 4. Factor-by-factor classification

- **Direction — SEMANTICALLY INVERTED.** Clean monotonic inversion at every
  horizon (h20: Q1 +0.318 → Q5 -0.258). Aligned means negative both sides and
  worsen with horizon (h20: down -0.318, up -0.259). Inversion holds in all
  sleeves (small strongest: Q5-Q1 -0.497). Median-stock median stays positive
  while means go negative → adverse left tail dominates, matching the audit's
  "trend intensity ≠ remaining continuation" diagnosis. The score behaves like
  an extension/exhaustion gauge, not a continuation bias.
- **Range/Expansion — SEMANTICALLY INVERTED (as named).** High-Range bars are
  followed by *larger* absolute moves than high-Expansion at all horizons
  (h10 2.002 vs 1.674; h20 3.098 vs 2.344; only 10% of stocks go the intended
  way). Signed range quintiles are flat. As an *unsigned absolute-move sorter*
  the score separates strongly — but with the opposite sign to its name.
- **Supply/Demand (sd) — SEMANTICALLY INVERTED.** Supply quintile (Q1) beats
  demand quintile (Q5) monotonically at 5/10/20 bars (h10 +0.068 vs -0.070;
  h20 +0.141 vs -0.135; spread pos 36.1%, negative in all sleeves). High
  "demand" predicts negative signed forwards.
- **Emerging — DROP (as defined).** Degenerate distribution: one quintile bin
  holds 278 stocks / 547k bars (tie mass from mostly-zero breakout scores),
  Q5 is a single stock (inadequate at every horizon), Q3 (41 stocks) prints
  -0.302 at h10 / -0.907 at h20. No usable quintile signal; Test C joints are
  empty.
- **Established — DROP (as defined).** Hump-shaped, non-monotone quintiles
  (h10: -0.037 / +0.031 / +0.041 / +0.018 / -0.045); Q5-Q1 spread -0.005 with
  39.7% positive. Adds nothing conditional on direction (Test A negative).
- **Deteriorating — SEMANTICALLY INVERTED.** Higher "deterioration" predicts
  *better* signed forwards (h10 Q1 -0.019 → Q5 +0.054; spread +0.073, pos
  55.5%), consistent with the negative lifecycle deltas. The label means the
  opposite of what it says in this cohort.
- **Redundancy — WARNING (no formal breach).** No pair exceeds the 0.85
  mean-|Spearman| gate, but **direction–sd at +0.770** (96.8% of stocks
  |rho|>0.70, only 1.4% >0.85) is near-redundant: the two headline "separate"
  dimensions share most of their cross-sectional rank information.
  Secondary: range–deteriorating +0.566, emerging–deteriorating -0.495.

## 5. Strongest useful interaction

High-Range vs high-Expansion absolute forward movement: -0.327 ATR at h10
(median -0.296, 90.0% of stocks move more after high-Range), stable across
horizons, sleeves, and sectors. The effect is real and consistent — but it
says Range predicts movement and Expansion predicts calm, i.e. the reverse of
the factor's name. Only sector nuance: Energy is near-flat (-0.074, pos 38%).

## 6. Weakest / broken factor

**Emerging**: degenerate quintile distribution (Q5 n=1), empty Test C joints,
and a 41-stock middle bin with deeply negative means. It cannot be evaluated
as formulated, let alone used.

## 7. Semantic-inversion evidence (summary)

Four of six A0 dimensions point the wrong way simultaneously — direction,
range, sd, deteriorating — all with monotone quintile profiles and
cross-sleeve consistency. This systematic pattern (plus the audit's Finding 4:
score magnitude ≈ already-moved extension) suggests the frozen primitives
themselves load on *extension/heat* rather than *remaining continuation*, so
any formula averaging them inherits the flip. A blind sign-flip is NOT
recommended (drift contamination, tail asymmetry, and costless-reversal
assumptions are unverified).

## 8. Redundancy warnings

1. direction–sd +0.770: treat as one shared axis until A1 disentangles them
   (test demand/supply legs separately by direction side; test
   dir_short vs dir_structure separately — `speed_rank` velocity is the prime
   inversion suspect).
2. range–deteriorating +0.566: range position and "deterioration" overlap;
   redefining either must check the other.
3. Structural sparsity: Up+HighRange+Supply, Down+HighRange+Demand, and both
   Emerging×Deteriorating joints are nearly empty — A0 intersections are too
   demanding to estimate paired effects. A1 needs relaxed joints or
   continuous interaction models.

## 9. Recommendation for A1 (exploratory only; A0 preserved above)

Keep the factorized separation principle (it diagnosed cleanly what the
six-way contest could not), but redefine ingredients: (a) split direction
into short-velocity vs structural components and test each alone;
(b) rename/recast range_factor as an absolute-movement sorter with corrected
semantics; (c) rebuild sd orthogonal to direction; (d) replace emerging
(de-generate breakout evidence) and established (flat) with non-degenerate
durability measures; (e) add **temporal-block** robustness to the analyzer
(A0 outputs have no time splits — noted limitation); (f) pre-specify
sparser-joint handling. Freeze any A1 candidate before touching OOS4, which
remains deferred and untouched.

## 10. Operational notes (no research logic changed)

- The auto-runner initially found 0 manifests because it required the original
  universe byte SHA `9d4a14d1…`, unrecoverable post-artifact-loss. Fixed
  (`run_issue78_factorized_classifier_discovery_auto.py`): original byte
  identity first; fallback to FIGI-set cohort identity `017e9360…` with
  manifest↔universe byte-consistency check and explicit warnings. Also added
  the `snapshot/raw/` subdirectory candidate to raw-dir resolution.
- CRLF trap: `git checkout` with `core.autocrlf=true` rewrites the stashed
  LF-byte CSVs (`f6753c…` → `6af3c3…`) and fails the snapshot audit. Restore
  byte-exact (raw `git show`) before running.
- Runner discovery verified function-level to the exact A0 paths (300 raws);
  the A0 outputs above come from the untouched analyzer with identical args.

Refs #78 #153 #148 #147 #138 #135 #132 #131 #80.
