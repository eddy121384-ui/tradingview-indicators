# Issue #78 — A5 untouched OOS4 validation finding (causal Core-2)

Date: 2026-10-07. First OOS4 outcome contact, under A5 preregistration
(`decisions/issue-78-oos4-validation-a5-preregistration.md`, committed as
`310cd71` before any OOS4 output). Frozen verbatim A4 translation, reused
by import — no thresholds, weights, formulas, or gates changed for OOS4.
No SD revival, ML, sign-flips, Pine, production. PRs #80/#148 unmerged.

## 1. Provenance (gate 1 PASS)

- Universe frozen `8c3ded9` BEFORE download/outcomes: universe SHA
  `b8e4275dd993ec659c252eda4d538c80bbeef3e0e4b3455b298d9114bc9d5316`,
  FIGI-set SHA `b0c9423a6e3e5cbd61dcd17dc1a9c5a0fc50b8bc00286ba3a5b86f560209ca49`,
  300/300, 100/100/100 sleeves, zero OOS2/OOS3 overlap (asserted by builder
  and re-asserted by analyzer), no calibration tickers.
- Bloomberg Desktop API snapshot 300/300, 0 failures; audit PASS (byte-
  identical universe, 1998-01-02→2026-08-31, normalization v2, repairs
  consistent); raw manifest SHA recorded in snapshot.
- No OOS4-driven tuning, replacement, or source/window change (gate 8 PASS).

## 2. Hard 80/20 h10 ALL (primary)

bull_low +0.082 (247 stocks, median +0.204, pos 53.2%); bull_high −0.012
(median +0.097, pos 50.8%); bear_low −0.172 (median −0.270, pos 44.2%);
bear_high −0.212 (median −0.384, pos 42.1%). Bull avg (+0.035) > bear avg
(−0.192): gate 3 PASS. bear_high worst at h1/h5/h10/h20: gate 4 PASS.
Coverage min 247 adequate stocks: gate 2 PASS (≥200).

## 3. Temporal / relaxed / breadth / tails

- Ordering bull>bears in 5/5 fixed blocks, hard and relaxed: gate 5 PASS.
  Relaxed never reverses interpretation (bear_high worst relaxed ALL too):
  gate 6 PASS. bull_low mean positive 4/5 blocks (only 2020–26 −0.032),
  medians positive everywhere.
- 235 complete stocks; large 78%/mid 64% ordering, small 48% (~coin flip);
  8/11 sectors ≥50% (Comm Services n=4, Utilities n=8 thin; Energy 40%,
  Staples 47% soft). Tails symmetric — broad, not tail-driven: gate 7 PASS
  with small-cap/2-sector caveats.
- Fidelity replicates OOS3: percentile Spearman 0.963/0.998, Jaccard
  0.77–0.81.

## 4. bull_low secondary verdict — NEUTRAL (frozen rule)

Paired low-minus-high h10 ALL +0.052 with 54.1% positive and 5/5 blocks
positive: mean ✓ and blocks ✓, but 54.1% < 55% breadth leg → NEUTRAL
(same classification as OOS3's +0.023/51.3% — consistent, not a reversal).

## 5. Primary verdict — CORE2_OOS4_VALIDATED

All 8 gates hold with no rescue or reinterpretation. Validated scope (per
prereg boundary): transport of the causal Structure × Extension context
ordering — bear_high weakest, bull states relatively better, across eras,
sleeves, and sectors. NOT a profitable-strategy claim; no entry/exit/sizing
work follows inside A5.

## 6. Artifacts / operational notes

`research/artifacts/issue78_oos4_validation_a5/` (8 files + `.zip`, SHAs
recorded); analyzer `analyze_issue78_oos4_validation_a5.py` + tests;
A0–A4 untouched. Shared-worktree caveat stands (branch verified each step).

Refs #78 #170 #168 #162 #159 #156 #153 #148 #147 #138 #119 #80.
