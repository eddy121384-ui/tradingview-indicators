# Issue #189 Phase 1B — evidence correction addendum (standalone; originals frozen)

- Branch: `research/issue-189-deep-history-pit` (same worktree/branch as Phase 1)
- Prereg: `190f3a64d38d8f857c349ba9abf041f83266d517` (UNCHANGED; this addendum
  changes no frozen definition — it corrects two evidence claims inside the
  prereg's own rules)
- Phase 1 finding: `decisions/issue-189-pit-feasibility-finding.md` (UNCHANGED)
- Phase 1 outputs: `generated/issue-189/*` (UNCHANGED; corrections live under
  `generated/issue-189/phase1b/` only)
- Trigger: GPT-6 independent check surfaced two evidence items; both VERIFIED
  below against public sources. Scope: macro sources ONLY — no asset returns
  read, no backtests, no model/threshold/weight changes, no merge.
- `production_authorized=false`

## Correction 1 — G5 ISM: scattered contemporary vintages EXIST (status stays `unavailable` as a database)

Original judgment (Phase 1): G5 has no public vintage archive in any month.
GPT-6 claim: Mar-2008 and Feb-2009 contemporary releases preserve New Orders;
a 2013 table revises 2009–2012 seasonals. VERIFIED:

- Mar-2008 New Orders **46.5** (Feb 49.1), 4th straight sub-50 month.
  Sources: Manufacturing.net 2008-04-01; USA Today 2008-04-01 (Reuters).
  Mar-2008 response mix 25/50/25 (third-party republication of ISM table).
- Feb-2009 New Orders **33.1 first-reported** (Jan 33.2, Dec-2008 23.1 SA).
  Sources: Calculated Risk 2009-03-01; FT Portfolios 2009-03-02; full
  % table (15/33/52) via January-2009 release text.
- Jan-2013 Commerce PR (PR Newswire 2013-01-28): X12-ARIMA revisions to
  2009–2012 SA indexes + 2013 projected factors; revised Feb-2009 = **32.8**
  (revision −0.3pp — direct evidence that SA New Orders vintages revise).
- Jan-2012 Commerce PR: 2005–2011 revisions (7 years, not customary 4) after
  2008-outlier handling changes — vintage sensitivity is real, both directions.
- Method note (Jan-2013 report PDF): SA index = (unadjusted diffusion ÷
  seasonal factor); raw % responses "never changed"; factors recomputed yearly.
- Licensing/boundary: ISM data proprietary; full history paywalled since
  2014-03-01 (PR Newswire 2014-02-12 notice); contemporary values survive ONLY
  as scattered third-party republication (© publishers). Citable spot values:
  YES. Redistributable vintage database: NO. Continuous 2006–2026 monthly
  vintages: NOT constructible from this evidence.

Revised G5 judgment: status remains **`unavailable`** for five-finite PIT
scoring in every month (a database cannot be built from press clippings), BUT
the record now shows bounded spot-checkable months (2008-03, 2009-02, plus the
2009–2012 revision table span) usable ONLY for episode-level sanity checks in
Phase 2 — never as a vintage series. Lawful remedy path added: targeted
contemporary-release collection per episode (labor-intensive, still not a
database) or licensed ISM history (terms unverified). Data: `phase1b/ism-spot-evidence.csv`.

## Correction 2 — ALFRED vintage-start ≠ observation-start (warmup caveat STRUCK)

Original judgment (Phase 1 finding §C): G4/I2 "warmup truncated at window
start" because PCEPI/PCEPILFE vintages begin 2000-08. GPT-6 claim: the initial
vintage already contains full history, so 2006 decisions have their 72-month
window. VERIFIED against ALFRED's own documentation
(https://alfred.stlouisfed.org/help/downloaddata):

- "a single column contains ALL OBSERVATIONS ACTUALLY AVAILABLE ON A SPECIFIC
  DATE IN HISTORY" — each vintage carries full known history, not just new rows.
- "vintage dates closely correspond to the release dates."
- All vintage/realtime parameters are DATE-only (YYYY-MM-DD); no intraday
  timestamp field exists — the prereg's conservative next-session rule stands.
- PCEPILFE: first vintage 2000-08-01 already spans Jan-1959–Oct-2003
  observations (catalog-level evidence; value-level confirmation needs an API
  key in Phase 2).

Consequence (mechanical, no new data): for a 2006-06 decision, the 60-month
window (≈2001-06→2006-06) plus 12-month transform tail (≈2000-06) falls
entirely inside months covered by Aug-2000+ monthly vintages. The warmup
truncation caveat is WITHDRAWN for G4/I2 (and was never applicable to
G1/G2/G3/I1/I3/I4/I5 whose vintages start 1962–1999). ETF-window 10/11
coverage is therefore COMPLETE for all of 2006–2026, not "truncated at window
start". The year-grid coarseness note stays (manifest keeps month precision:
G4d/I2 usable from 2000-08, not 2000-01).

## Correction 3 — confirmation ladder (how much is catalog-only?)

New explicit ladder (frozen here for Phase 2 entry criteria):

- L1 catalog: official ID + SA + units/frequency confirmed from public FRED
  pages. Reached by: all 10 non-G5 roles.
- L2 definition: TV concept matches the counterpart (native-vs-computed YoY,
  index concept, universe). Reached by: G1/G2/G3/G4/I1/I2. TBD by:
  I3 (which PPI index), I4 (which wage concept), I5 (which energy concept),
  G3-PSN-vs-SAAR (immaterial for YoY — L2 accepted with note).
- L3 value/vintage-tested: actual vintage pulls vs TV values. Reached by:
  NONE (requires API key + Phase 2 engine; expressly not claimed).
- L0 no counterpart: G5 (bounded spot evidence per Correction 1 only).

So "10/11" = L1×10 (of which L2×6 + L2-TBD×4), L3×0. The Phase 1 headline is
restated without softening: catalog-confirmed, value-untested. Data:
`phase1b/confirmation-ladder.csv`. This also fixes the coverage-grid reading
error the task names: year cells were never "observation-available" claims —
they are vintage-start-boundary cells, and the manifest's month-precision
`vintage_start` governs.

## Revised feasibility verdict: UNCHANGED label, narrowed gaps

- Label stays **partially_feasible** (full five-finite PIT identifiable in
  ZERO months 1960–2026 — G5 blocks every month; pre-2000 full PIT not
  verifiable — unchanged).
- What changed: (a) ETF-window partial case is now complete-10/11 without the
  warmup-truncation asterisk; (b) G5 has documented spot evidence + a bounded
  lawful remedy path instead of a bare "unknown"; (c) every 10/11 claim is now
  explicitly L1/L2-only, L3 expressly pending Phase 2 with a key.
- Remaining gaps (unchanged + two refinements): G5 database absence; pre-2000
  vintage absences per manifest; I3/I4/I5 TV-definition TBD; G1 data-vintage
  list; G2 1960-01/02; SA-factor revision depth for G5 spot months
  (2009–2012 table shows ±0.5pp-scale moves — PIT must use first-reported,
  not revised, values).
- No Phase 2/3 work started. No returns read (tests below gate this).

## Maintenance note (test-only, no design change)

`test_issue_189_feasibility.mjs` received a two-line maintenance fix (skip
subdirectories in its determinism loop) because `generated/issue-189/phase1b/`
now exists beside the Phase 1 files; all 7 original assertions are unchanged
in meaning and still pass. Prereg, Phase 1 finding, and all Phase 1 output
bytes are untouched (gated by Phase 1B test §1).

`production_authorized=false`
