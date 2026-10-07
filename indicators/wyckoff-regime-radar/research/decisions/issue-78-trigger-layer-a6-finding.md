# Issue #78 — A6 trigger-layer discovery finding (frozen Core-2 context, OOS3)

Date: 2026-10-07. Discovery only, OOS3 snapshot, 218,487 deduped events /
300 stocks. A0–A5 calculations, thresholds, findings, conclusions untouched.
No Core-2 changes, no new axis, no SD revival, no scans/optimization/ML,
no OOS4 mining, no OOS5 contact, no production/Pine. PRs #80/#148 unmerged.

## 1. Prereg / integrity

Prereg `decisions/issue-78-trigger-layer-a6-preregistration.md` committed
as `86ecd68` before outcomes. Analyzer + 12/12 passing tests (levels,
no-lookahead, frozen-L, T1 3-bar/majority+final, T2 order, T3 3-bar window,
knowable timestamps, dedup, exact mirroring, Core-2 reuse, deterministic
real-data rerun). Snapshot audit pass; classifier blob frozen; OOS4
untouched. Unit = EVENT, one-stock-one-vote; primary = next-bar actionable
h10, same-close descriptive.

## 2. Standalone triggers h10 ALL (aligned, primary)

T0 bull +0.044 (52.3%) / bear −0.128; T1 bull +0.044 (52.7%) / bear −0.086;
T2 bull +0.047 (52.6%) / bear −0.154; T3 bull **+0.146** (median +0.251,
54.7% bars / 69.2% stock-means positive, 295 stocks, positive in ALL 5
blocks +0.11…+0.20) / bear −0.071. Confirmation tax ≈ 0 (T1≈T0 bull);
same-close ≈ next-bar. Sleeve gradient large>mid>small throughout; T3 bull
positive-mean majority in all sleeves (63–76%).

## 3. Incremental vs frozen context (h10 ALL combos)

No combo meets the survivor bar. Adequate combos: bull_high_T1 +0.050
(168 stocks, 53.0% incremental-positive), bear_low_T0 +0.150 (69, 50.7%),
bull T0s ≈ 0. Per-stock incremental majorities peak at 53% (adequate) —
below the frozen 55% leg. Block incrementals: at most 1 adequate block per
combo (triple-conditioning thins cells), so the ≥4/5-blocks leg is
structurally unreachable. T3 combos are structurally near-absent
(bull-side failed breakdowns don't occur inside bull contexts: 0–24
stocks) — the T3 standalone strength cannot be conditioned as preregistered.

## 4. Family classifications

- **T0 — WEAK.** Adequate sample, near-zero increment, slim majorities.
  Raw-breakout control behaves as expected: nothing beyond context.
- **T1 — WEAK.** Closest (bull_high +0.050/53%) but fails majority and
  block legs; acceptance adds nothing over raw (tax ≈ 0).
- **T2 — WEAK.** Combo sample thin (16–48 stocks); standalone mirrors T0
  (+0.047). Pullback-reclaim adds no measurable edge.
- **T3 — WEAK.** Bullish failed breakdown is the sole positive-mean anomaly
  (+0.146, 69% stocks, 5/5 blocks, all sleeves) — documented hypothesis-only.
  Bearish mirror fails (−0.071); combos structurally absent. One-sided,
  context-free: cannot KEEP under the frozen rule.

## 5. OOS5 survivors: NONE

No family meets KEEP_FOR_OOS; nothing is frozen for OOS5. The T3-bull
standalone anomaly is the only candidate worth re-examining, and only in a
future preregistered standalone-trigger study — explicitly not frozen now.

## 6. Artifacts / ops

`research/artifacts/issue78_trigger_layer_a6/` (5 files + `.zip`, SHAs
recorded); analyzer + tests + prereg + this finding. Shared-worktree
caveat stands (branch verified each step).

Refs #78 #173 #170 #168 #162 #159 #156 #153 #148 #147 #138 #119 #80.
