# Issue #78 — A8 failed-break cross-market symmetry finding

Date: 2026-10-08. Transport/replication on FX (4 canonical pairs) + rates
(4 Bloomberg yield series). Exact frozen A7 F0, controls, timing,
normalization path. No scans/tuning/inversions/substitutions, no OOS4
mining, no OOS5, no production/Pine. PRs #80/#148 unmerged.

## 1. Prereg / integrity

Prereg `decisions/issue-78-failed-break-cross-market-a8-preregistration.md`
committed as `8723449` before outcomes (FX list, conditional rates, timing,
aggregation, gates, 13-test list). Analyzer + 13/13 passing tests (F0
semantics, levels, future-invariance, quote orientation, rates fields,
one-vote exactness, frozen-path identity, deterministic rebuild).
Snapshot audit: FX byte SHAs verified against canonical manifest (worktree
CRLF flags carry zero content diff); rates Bloomberg snapshot 4/4, 0
failures, manifest `da0a8cea…`, universe `891bba9b…`, 1998→2026-08-31, v2
normalization. No instrument replaced after outcomes.

## 2. FX family h10 (one-instrument-one-vote, 4/4 adequate)

- Bear (upside failed break → reversal down): failed +0.289 (median +0.056)
  vs raw +0.033 vs nonreclaimed −0.105. Per-instrument failed>raw 3/4
  (only EURUSD −0.050<−0.018 misses); failed>nonreclaimed 3/4 (EURUSD
  −0.050<+0.342 misses). Temporal: advantage in 2015-19 and 2020-26,
  reversed 2010-14. Family mean tail-leaning (+0.289 vs median +0.056 on
  AUD/GBP strength) but not one-instrument-driven.
- Bull (downside failed break → reversal up): failed −0.039 vs raw −0.269
  vs nonreclaimed −0.537 — beats both controls while negative itself;
  per-instrument vs-raw majority FAILS (2/4: EURUSD +0.500 and USDJPY
  +0.517 pass; AUDUSD −0.557 and GBPUSD −0.617 fail); vs-nonreclaimed 4/4.

## 3. Rates family h10 (yield space, 4/4 adequate)

- Bear: failed −0.010 vs raw +0.296 vs nonreclaimed −0.478 (0/4 vs raw).
- Bull: failed −0.180 vs raw +0.082 vs nonreclaimed −0.795 (0/4 vs raw).
- Plain raw breaks mean-revert in yields on their own; the failed-break
  overlay adds nothing beyond raw. Representation is clean (consistent
  yield OHLC, 7.4k bars/series) — this is a transport failure, not a data
  failure.

## 4. Hypotheses

- H1 FX two-sided: NO (bull fails per-instrument majority).
- H2 rates two-sided: NO (both sides fail vs raw).
- H3 asset-class-specific asymmetry: SUPPORTED — equity bull-only,
  FX bear-leaning, rates neither; winning side differs by class with
  quotes/yields frozen throughout.
- H4 rejection-vs-nonreclaim: SUPPORTED broadly (15/16 family-side cells;
  sole exception EURUSD-bear) — reclaimed breaks behave materially
  differently from non-reclaimed ones even where directional transport
  fails.

## 5. Classifications

- FX: **FX_FAILED_BREAK_ASYMMETRIC** (bear side meets gates 1–4; bull side
  fails the per-instrument majority; temporal 2/3 eras with 2010-14
  reversal noted; tail-leaning family mean noted).
- Rates: **RATES_FAILED_BREAK_NOT_TRANSPORTED** (adequate sample, clean
  representation, fails gate 1 both sides).
- Overall: **FAILED_AUCTION_ASSET_CLASS_DEPENDENT**. No near-pass rescue.

## 6. Next step

If validation is wanted: a SEPARATE untouched-validation issue for the
exact frozen failed-break event PER ASSET CLASS (no pooling across
classes, no redefinition). Do not invent another variant inside A8. The
valid Core-2 equity track is unaffected by this result.

## 7. Artifacts / ops

`research/artifacts/issue78_failed_break_a8/` (instruments.json,
run_instruments.json, rates_universe.csv, rates_snapshot/, results/ +
`results.zip`, SHAs recorded); analyzer + tests + prereg + this finding.
Shared-worktree caveat stands (branch verified each step).

Refs #78 #179 #175 #173 #170 #168 #162 #159 #156 #153 #148 #147 #138 #119 #80.
