# Issue #78 — A3 ablation finding (drop Supply-Demand, test two-axis core)

Date: 2026-10-06

Scope: ablation study per Issue #162 — does Core-2 (structure side ×
extension magnitude) lose anything when the Supply-Demand axis is dropped
entirely? **Architecture discovery, not fresh OOS validation.** A0/A1/A2
preserved unchanged. No new primitives, weights, ML, sign-flips, six-stage
rescue, OOS4, or production/Pine changes. PRs #80 / #148 unmerged.

## 1. Data integrity

- Same recovered OOS3 snapshot: 300/300, FIGI-set `017e9360…`, blob
  `1eec08e7…`, audit pass; 926,982 eligible bars.
- A3 frame IS the A2 frame (same builder by import): same eligibility,
  scores, forwards, blocks. A1 axes and A2 candidates reused, never redefined.
- Horizons 1/5/10/20; min 5 bars/cell; min 30 stocks; fixed blocks
  2000–04/05–09/10–14/15–19/20–26 + ALL; hard 80/20 first, predeclared 70/30
  relaxed second.
- Outputs: `research/artifacts/issue78_ablation_a3/` (10 files + `.zip`,
  SHAs recorded). Primary horizon 10 bars, one-stock-one-vote throughout.

## 2. Core-2 levels (structure × extension, aligned)

h10 ALL: bull_low −0.072 (258 stocks, median-stock median +0.131, pos 51.0%);
bull_high −0.033 (median +0.120, pos 52.1%); bear_low −0.157 (median −0.251,
pos 44.8%); bear_high −0.231 (median −0.416, pos 41.0%). Low-vs-high contrast
(bull −0.010, 46.5% positive; bear +0.048, 56.3%) lives on the bear side:
bear contrast positive in 2000–2019 (+0.14 to +0.44) and ~0 in 2020–26;
bull contrast ≈ 0 ALL and positive only in 2010–14 (+0.164).

## 3. Ablation: neither SD control adds incremental information

- Within-cell paired deltas (expected-good minus expected-bad), h10 ALL:
  bull cells negative for both controls (bull_high a0_sd −0.092, holding
  −0.128; bull_low holding only 3 stocks); bear cells ≈ 0 (±0.03). Expected
  ordering absent in every core, horizon, block, and sleeve.
- Within-cell rank info: |Spearman| ≤ 0.04 everywhere; wrong-signed in bull
  cells (−0.03 to −0.04: higher demand rank → worse aligned outcome),
  trivially positive in bear cells (+0.02 to +0.04, ~55% positive — noise).
- Within-cell control quintiles: flat/noisy, no monotonicity in any core.
- Relaxed 70/30 agrees (same signs, smaller magnitudes). All three drop
  gates met: (1) no stable incremental separation; (2) no breadth gain
  (sleeves disagree in sign, small-cap often opposite); (3) no temporal gain
  (early blocks deeply negative, 2020–26 weakly positive but split).

## 4. Conclusion 1 — DROP SUPPLY-DEMAND AXIS FROM CURRENT ARCHITECTURE

Both controls fail as overlays on top of Core-2 in levels, contrasts, rank
information, breadth, and time. The S/D avenue within frozen primitives is
closed (A2) and its removal costs nothing measurable (A3). No placeholder:
a placeholder would imply保留 expected future value for which there is no
evidence. If a future primitive family ever motivates S/D again, it needs a
fresh preregistration — not a placeholder axis.

## 5. Conclusion 2 — probe verdict: bull_low retained as leading conditioner,
with explicit caveats (Phase-0 correction 2026-10-07: corrected against the
committed artifact; no calculation changed)

bullish-structure + low-extension leads ONLY on median-stock median:
highest of the four cells at every horizon (h1 +0.024, h5 +0.062, h10
+0.131, h20 +0.337; positive in 4/5 blocks at h10, 2020–26 ≈ −0.001).
On equal-stock mean and positive-stock fraction, bull_high leads at h10
(−0.033 vs −0.072; 52.1% vs 51.0%) and h20 (−0.082 vs −0.134; 51.2% vs
50.9%); bull_low leads those two metrics only at h1/h5. Both bull cells
— not bull_low alone — keep positive median-stock medians at every
horizon and in every h10 block (bull_high medians: +0.009/+0.033/+0.120/
+0.180; positive in 5/5 blocks). The earlier wording claiming bull_low
the outright leader on means and hit rates "at every horizon" and the
"only" positive-median cell was factually wrong and is retracted here.
The retain-with-caveats verdict stands, resting on the median profile —
not on means or hit rates. Retain as the leading probe-state
conditioner for later work — a conditioning context, NOT a validated edge,
policy, or gate.

## 6. Temporal robustness

Core ordering (bear_high worst, bull cells least-bad) holds in all blocks;
bull_low mean positive only in 2005–09 (+0.043) and 2010–14 (+0.134).
2005–09 remains the exception block for every component (flattest contrasts).
No block overturns either conclusion.

## 7. Breadth / tails

Sleeve/sector cuts on paired deltas disagree in sign (no subgroup carries a
rule); bull_low per-stock means ~51% positive with symmetric tails — broad,
not tail-driven. Bear_high negativity is likewise broad (41% positive,
median −0.42).

## 8. Recommended next step

Preregister a frozen Core-2 translation study: exact bull_low (and relaxed)
probe-state definition, fixed horizons/blocks/gates from THIS finding, then
first contact with the untouched OOS4 cohort (deferred until that
preregistration lands). No further OOS3 mining for direction/SD.

## 9. Operational notes

- New files only: A3 analyzer + tests (6/6 pass incl. real-data A2 parity),
  A3 artifacts + this finding. A0/A1/A2 untouched.
- Workstation caveat stands: unrelated processes share this worktree;
  branch verified before every commit/push.

Refs #78 #162 #159 #156 #153 #148 #147 #138 #80.
