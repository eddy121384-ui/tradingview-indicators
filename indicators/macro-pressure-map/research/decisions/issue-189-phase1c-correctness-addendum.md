# Issue #189 Phase 1C — correctness audit addendum (standalone; originals frozen)

- Branch: `research/issue-189-deep-history-pit` (same worktree/branch)
- Prereg `190f3a6`, Phase 1 finding, Phase 1 outputs, Phase 1B addendum +
  phase1b/ files: ALL UNCHANGED (gated by test §1 below).
- Trigger: two correctness questions. Scope: macro sources ONLY — no asset
  returns read, no backtests, no model/threshold/weight changes, no Phase 2/3.
- `production_authorized=false`

## Q1 — the "2003-10 in the 2000-08-01 vintage" contradiction: STRUCK, replaced with value-verified spans

Phase 1B repeated a catalog-level claim that PCEPILFE's 2000-08-01 first
vintage already contained observations through Oct-2003. That is temporally
impossible and was WRONG — most plausibly a misreading of ALFRED units-validity
ranges. It is struck in full. What replaced it is better than what it claimed:
ALFRED's public `alfredgraph.csv` endpoint works WITHOUT an API key, so all 10
feeds' real vintage spans were pulled and recorded
(`phase1c/alfred-vintage-spans.json`, 28 pulls, SHA-pinned, 2026-10-12):

- Requested vintage dates return EXACT-date vintages (headers echo 19600101,
  20000801, 20060601 …), and every vintage ends ~1–2 months BEFORE its date
  (2000-08-01 → latest obs 2000-06; 2006-06-01 → 2006-04; 1960-01-01 →
  1959-11): correct real-time truncation, and a hard test in §4 below asserts
  no vintage in this set contains any post-date observation.
- Every 2000-08-01 vintage spans back to series origin (INDPRO 1921, UNRATE
  1948, PERMIT 1960, DSPI/PCEPI/PCEPILFE 1959, CPIAUCSL 1947, PPIACO 1913,
  AHETPI 1964, CPIENGSL 1957): the full-history-in-first-vintage convention is
  now VALUE-VERIFIED (was: catalog-level), across all 10 feeds.
- Corroborating cases: CPIAUCSL 1972-07-21 vintage holds only 19 obs
  (1970-12…1972-06) — truncated early vintages are real, and the prereg's
  truncated-YoY handling for 1972 stands. DSPI 1979-12-18 starts at 1959.
- Convention quotes (ALFRED help, fetched): "a single column contains all
  observations actually available on a specific date" / "vintage dates closely
  correspond to release dates" / date-only granularity (no intraday field) —
  the prereg conservative next-session rule stands unchanged.
- Caveats kept: (a) header-echo vs true-revision-date ambiguity noted — the
  OBS SPANS are the evidence, not the labels; (b) monthly vintage DENSITY
  2000-08→2006-06 is endpoint-sampled only, exhaustive density needs a key
  (Phase 2); (c) RTDSM PCONX page independently states the same full-history
  convention ("entire time-series history for each vintage … available … at
  the vintage date").

## Q2 — warmup is 74 raw months, not 72; ETF start still covered

Verified by importing FROZEN `issue_160_deep_history_v01.pressure_score` and
driving it with synthetic series (`issue_189_phase1c_warmup.py`, venv python):

- Score on a gapless X: first finite index **62** (60 X + momentum's X[i-3]).
- G3-style role (X needs raw t−12): first finite raw index **74** = 62+12.
- One missing raw month: first finite moves to raw+80 (extends, never fills).
- Cross-check: raw 1960-01 + 74 months = **1966-03** == the observed DH first
  valued month (1966-03-01). The frozen engine and the frozen data agree.
- Prereg §5 said "≥72 months" — corrected to **74 raw months minimum**
  (refinement to an unexecuted future method, disclosed here; nothing executed
  changes).
- 2006 ETF re-check with correct math: first 2006-06 decision needs raw
  2000-04+ with vintages ≤ decision date. Verified spans show all 10 feeds'
  first vintages (≤2000-08) already contain 2000-04 observations, and sampled
  2006-06-01 vintages span to origin. Conclusion UNCHANGED (covered), basis
  upgraded from convention to value-verified spans (density caveat per Q1).

## Verdict effect: none on labels, two upgrades in evidence

- Phase 1 `partially_feasible` and Phase 1B's unchanged-label verdict both
  stand. G5 still blocks every month; pre-2000 full PIT still unverifiable.
- Upgraded: (a) 10/11 ETF-window coverage now rests on 28 value-verified
  vintage spans, not catalog inference; (b) the only two known-wrong statements
  in prior outputs (2003-10-in-2000-vintage; 72-month warmup) are struck with
  corrected values on record.
- Remaining gaps (unchanged): G5 database; pre-2000 vintage absences;
  I3/I4/I5 TV-definition TBD; G1 data-vintage list; monthly density audit;
  SA-factor revision depth (use first-reported G5 spot values, never revised).

## Files (all new; originals untouched)

- `generated/issue-189/phase1c/alfred-vintage-spans.json` (28 pulls)
- `generated/issue-189/phase1c/warmup-verification.json`
- `research/issue_189_phase1c_pull.mjs` (fetcher; hashes+spans only, no raw commits)
- `research/issue_189_phase1c_warmup.py` (frozen-code synthetic verification)
- `research/test_issue_189_phase1c.mjs` (7 checks)
- this addendum.

`production_authorized=false`
