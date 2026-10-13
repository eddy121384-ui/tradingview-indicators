# Issue #189 I3/I4/I5 re-verification — finding note

- Branch: `research/issue-189-deep-history-pit`; prereg addendum `9f78b1d`
  (before any new pull). Scope: three inflation roles only. G5 untouched,
  full PIT stays paused. No model/threshold/weight change, no payoff backtest,
  no Phase 3. `production_authorized=false`.

## Verdicts (frozen rules: C1 extreme-point Δ < 0.5pp + concept + coverage)

- **I3 UNVERIFIED.** SOP leg has no ALFRED vintages at all (10× 404; C1-SOP
  untestable); FD leg vintages start 2014-06, so the Jul-2009 extreme needs a
  nonexistent 2009 vintage (C1-FD untestable). Concept ID is now exact, though:
  FRED-current SOP YoY Nov-1974 = 19.57 = TV value to the basis point —
  TV pre-2014 history IS SOP Finished Goods (definition evidence, not PIT).
- **I4 UNVERIFIED (rule-bound).** A576RC1 (BEA payroll) values at first
  eligible vintages: Apr-2020 −8.53 vs TV −5.89 (Δ −2.64); Apr-2021 +16.36 vs
  TV +15.28 (Δ +1.08). Direction and COVID dynamics match (collapse/rebound),
  magnitudes miss the 0.5pp tolerance — first-reported-vs-revised gap is the
  documented candidate explanation, not an excuse. Concept match (BEA
  disbursements) stands; numeric confirmation fails.
- **I5 CONFIRMED.** CPIENGNS first-eligible-vintage values: Mar-1980 47.130
  vs TV 47.13 (Δ 0.000); Jul-2009 −28.093 vs TV −28.09 (Δ −0.003). NSA energy
  YoY reproduces TV extremes to 0.003pp across 29 years.

## C2 decomposition: not-identifiable (stated, not approximated)

The full-swap I-ledger needs the SOP leg, which has no vintages at any date —
recorded in `comparison.json`, no partial-swap variant (would violate the
frozen spec). Consequence for the user's question (how much of the ~24% band
disagreement is wrong-series vs genuine revision): answerable only in parts —
I5's share is genuine revision (series confirmed); I4's share is bounded but
unresolved (direction right, magnitude off, could be either); I3's share is
unknown (concept identified, values unverifiable). No number is manufactured
for the missing cells.

## C3 revision spreads (YoY units, benchmark grid)

- I3_FD 0.145/0.45pp; I4_PAY **1.233**/2.354pp (BEA payroll revises materially —
  consistent with the I4 C1 gap); I5_NSA 0/0 (NSA values immutable, as expected).

## Method anchors

- 656/656 pulls, 0 failures (scoped grids: FD 2014-06+, PAY 2010-06+, NSA
  2000-08+; boundaries probed and recorded in `no-vintage.json`).
- Analyzer rerun byte-identical; 6 phase2b checks PASS (span discipline on all
  pulls, verdict logic, C2 status, no-returns scan).
- G5/full-PIT/Phase 3 status unchanged (paused). No merge, no main/Pine/model edits.

`production_authorized=false`
