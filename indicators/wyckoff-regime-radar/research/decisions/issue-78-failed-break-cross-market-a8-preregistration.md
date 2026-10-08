# Issue #78 — A8 cross-market failed-break symmetry preregistration

Date: 2026-10-08 (frozen BEFORE any A8 forward-return outcome is computed;
before any new download; rates probe results unknown at freeze).

Status: cross-market TRANSPORT / mechanism replication — NOT fresh final
validation. Instruments below overlap earlier Issue #78/55/76 work and must
never be called fresh OOS. No OOS4 trigger mining, no OOS5 contact, no
policy/sizing/production/Pine. PRs #80/#148 unmerged.

## F0 reuse (exact, no changes)

A7 F0 verbatim: prior-20 levels (current bar excluded), 3-bar reclaim
window, first-reclaim confirmation, timestamp = reclaim close, aligned
bull +1 (downside failed break) / bear −1 (upside failed break), same
dedup (no consecutive repeats, one sequence per side-window). Controls A
(raw T0) and B (non-reclaimed, mutually exclusive) verbatim. No lookback/
window/threshold scans, no asymmetry changes, no ML.

## FX family (frozen: 4 canonical pairs)

- EURUSD, USDJPY, GBPUSD, AUDUSD — repo canonical static D1 snapshots
  `research/data/frozen/issue-55-{audusd,eurusd,gbpusd,usdjpy}-static-d1.csv`
  (date/open/high/low/close, 2012-12-04→2022-03-04, manifest SHAs pinned).
  Only 4 canonical pairs exist → "at least 4" target met, no 6th-pair
  exception crafted. Quote series preserved exactly; NOTHING inverted for
  symmetry (USDJPY etc. stay as-quoted).
- No Bloomberg FX download (frozen snapshots technically adequate).

## Rates family (conditional on representation probe)

- Primary representation: YIELD SPACE ONLY (never mixed with futures/bond
  prices). Candidates IF yield OHLC (high/low/close) is consistently
  available: US 2Y, US 5Y, US 10Y, US 30Y (exact Bloomberg identifiers
  frozen in the manifest step IF the probe passes).
- Representation probe (field-availability only, no outcomes) runs AFTER
  this commit: request PX_OPEN/PX_HIGH/PX_LOW/PX_LAST for one benchmark
  tenor. If yields lack clean daily HIGH/LOW consistently → STOP rates
  before outcomes, report exact blocker, conclude
  RATES_FAILED_BREAK_INSUFFICIENT. No futures/price substitution, ever.

## Outcome timing / normalization (frozen)

Knowable at reclaim close; primary forward clock next bar (e=tc+1);
h1/h5/h10(PRIMARY)/h20; aligned bull +1 / bear −1; no backdating.
ATR-normalized `fwd = (log close[t+h] − log close[t]) / sym_atr[t]` with
`sym_atr` from the frozen classifier blob via the same code path as A7.
Equity-only liquidity/dollar-volume eligibility gates are dropped (FX has
no volume); eligibility = valid OHLC within available history. Event math,
thresholds, and clocks are otherwise identical — the ONLY adaptation,
forced by the asset class, frozen here.

## Aggregation (frozen)

Per instrument first; then one-instrument-one-vote per family (never
event-pooled). Per instrument/side: history span, F0/raw/nonreclaim
counts, h1/h5/h10/h20 mean/median/positive-fraction/p5/p10/ES5,
failed−raw and failed−nonreclaimed deltas, fixed blocks
2000–04/05–09/10–14/15–19/2020–26/ALL (early blocks expected
inadequate/empty on 2012+ histories — reported, never redefined),
tails/concentration. Adequacy: ≥5 events per instrument-cell, ≥3 adequate
instruments per family-side for a family verdict (else INSUFFICIENT).

## Gates (frozen; H1–H4 + two-sided gate + family/overall classifications
exactly per Issue #179; no near-pass rescue; asymmetry never forced or
hidden; magnitudes need not match across sides)

## Tests (frozen = issue's 13 proofs; rates-field gate included)

Refs #78 #179 #175 #173 #170 #168 #162 #159 #156 #153 #148 #147 #138 #119 #80.
