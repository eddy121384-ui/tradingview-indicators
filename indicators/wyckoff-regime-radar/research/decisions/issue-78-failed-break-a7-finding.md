# Issue #78 — A7 failed-break rejection finding (OOS3 mechanism study)

Date: 2026-10-07. Mechanism discovery on recovered OOS3 (45,279 F0 events /
300 stocks; 47,876 non-reclaimed breaks). A0–A6 calculations, thresholds,
findings, conclusions untouched (F0 reproduces A6 T3 exactly on all 300
stocks — enforced by a per-stock abort gate). No scans/ML/weights/sign-flips,
no OOS4 mining, no OOS5 contact, no production/Pine. PRs #80/#148 unmerged.

## 1. Prereg / integrity

Prereg `decisions/issue-78-failed-break-a7-preregistration.md` committed as
`68cb244` before outcomes. Analyzer + 17/17 passing tests (levels,
future-invariance, exact T3 reproduction, frozen L, 3-bar window,
first-reclaim, knowable timestamps, append-invariance, exact mirrors,
ATR math, speed/CLV strata, mutual exclusivity, post-confirmation timing,
Core-2 reuse, deterministic OOS3 rebuild). Snapshot audit pass; blob
frozen. Unit = EVENT, one-stock-one-vote, next-bar primary h10.

## 2. F0 headlines h10 ALL (aligned)

Bull failed breakdown +0.148 (296 stocks, median +0.250, pos 54.7% bars /
69.3% stock-means); bear failed breakout −0.071 (median −0.162, 46.2% /
41.4%). Strongly one-sided: bull carries the mechanism, bear does not.

## 3. Controls — rejection itself adds information

- vs raw break: bull +0.105 (58.1%, 296 stocks); bear +0.057 (60.0%).
- vs non-reclaimed break: bull +0.464 (82.7%); bear +0.270 (77.3%), positive
  in all 5 blocks for both sides. Non-reclaimed breaks continue hard
  against (bull −0.320, bear −0.341); the reclaim is the difference.
- H1 SUPPORTED for bull, WEAK for bear.

## 4. Mechanism descriptors h10 ALL

- M1 speed: bull flat (s1 +0.131 / s2 +0.132 / s3 +0.157); bear flat. H2
  contradicted — faster rejection is NOT stronger.
- M2 depth: bull flat (deep +0.140 / medium +0.176 / shallow +0.176,
  shallow n=18 inadequate); bear ordered deep −0.054 > medium −0.285 >
  shallow −0.313 (deeper break → stronger bear reversal; shallow n=21
  inadequate). Only coherent ordering in the study, on the weak side.
- M3 reclaim: bull weak −0.365 (n=11 inadequate) vs medium +0.274 /
  strong +0.147; bear flat. Mixed; H3 unresolved.
- M4 CLV: expectations contradicted both sides (bull high-CLV weakest at
  +0.122 vs mid +0.199; bear high-CLV "best" at −0.274 vs expected low).
- M5 follow-through: null both sides (yes ≈ no); no confirmation tax issue.
- H6: bull F0 positive across ALL Core-2 splits (structbull +0.172,
  structbear +0.125, exthigh +0.202, extlow +0.053) — information exists
  independently of context.

## 5. Blocks / breadth / tails

Bull F0 positive all 5 blocks (+0.08…+0.32) with 53–58% positive
fractions; bear negative everywhere. Sleeves: bull majority-positive in
all sleeves (63–76% stock-means); bear weak everywhere. Tails symmetric —
broad, not tail-driven. Block-level paired deltas mostly inadequate
(<30 stocks: triple-conditioning thins cells), so the ≥4/5-blocks gate is
structurally unreachable for paired contrasts.

## 6. Classification — FAILED_BREAK_MECHANISM_PARTIAL

Bull F0 is robust (69% stocks positive-mean, all blocks/sleeves positive,
beats both controls) but decomposition is mixed (only bear-depth ordered;
speed/CLV contradicted, reclaim/follow null) and the result is strongly
one-sided (bear F0 weak, −0.071/41%). Not STRONG (block-adequacy and
descriptor gates fail); not WEAK/CONTRADICTED (bull effect too broad and
control-beating). Asymmetry retained explicitly (H5).

## 7. Next step

Do NOT touch OOS5. Recommend a SEPARATE frozen validation issue for the
bullish failed-breakdown mechanism ONLY (exact A7 F0-bull definition,
preregistered gates), explicitly excluding bear-side and descriptor
refinements. No new trigger variants.

## 8. Artifacts / ops

`research/artifacts/issue78_failed_break_a7/` (9 files + `.zip`, SHAs
recorded); analyzer + tests + prereg + this finding. Shared-worktree
caveat stands (branch verified each step).

Refs #78 #175 #173 #170 #168 #162 #159 #156 #153 #148 #147 #138 #119 #80.
