# Issue #189 — I3/I4/I5 re-verification prereg addendum (frozen)

- Branch: `research/issue-189-deep-history-pit`; base lineage Phase 2 `8511592`.
- Parent prereg `190f3a6` UNCHANGED (this addendum narrows scope, never widens).
- Status: PREREGISTRATION — frozen before ANY vintage pull for the three new
  routes and before ANY recomputed as-of comparison.
- `outcome_data_loaded=false` (for the three new routes; old-candidate numbers
  are frozen inputs). `production_authorized=false`.

## 0. Scope (frozen; the user's bound)

Re-verify ONLY I3/I4/I5 with the three new routes below. G5 untouched (full
PIT stays paused). No threshold/weight/cap/matrix/B-2 change. No allocation
payoff backtest. No Phase 3. A substitution is a NEW incomparable candidate
(per #189 prohibitions), never a silent repair of the frozen strategy.

## 1. Frozen route specs (IDs verified read-only 2026-10-13, no vintage pulled yet)

- I3 splice, YoY computed WITHIN each leg (no level splice factor):
  leg1 = `WPUSOP3000` (SOP Finished Goods, NSA, 1982=100, through Dec-2015,
  discontinued; replacement per FRED note: `WPUFD49207`) for obs < 2014-01;
  leg2 = `PPIFIS` (FD headline, SA, Nov2009=100, from Nov-2009) for obs
  ≥ 2014-01. Overlap 2009–2015: report BOTH legs' YoY as consistency diagnostic.
- I4 payroll: `A576RC1` (BEA wages & salary disbursements, monthly SAAR bn
  USD, Table 2.6/2.7B) → causal 12m%. (TV USWG page: BEA disbursements concept.)
- I5 NSA: `CPIENGNS` (CPI-U Energy, NSA, 1982-84=100, monthly) → causal 12m%.
  (TV USEI page: BLS energy concept; SA flag undisclosed.)

## 2. Vintage plan (frozen; same keyless protocol as Phase 2)

`alfredgraph.csv` single-`vintage_date` pulls, monthly month-end grid
2000-08→2026-08 per new ID, plus first-vintage span pulls
(WPUSOP3000/PPIFIS/A576RC1/CPIENGNS). Rate limit + retries + SHA/span manifest;
raws uncommitted. If an ID has no ALFRED vintages, that leg stays UNVERIFIED
(record, no fallback).

## 3. Comparison protocol (frozen; macro-only, no returns)

- C1 extreme-point match (tolerance Δ < 0.5pp): I3 SOP leg Nov-1974 (TV 19.57),
  I3 FD leg Jul-2009 (TV −6.86); I4 Apr-2020 (TV −5.89) + Apr-2021 (TV +15.28);
  I5 Mar-1980 (TV 47.13) + Jul-2009 (TV −28.09). Values from first eligible
  vintage (PIT-correct), not latest.
- C2 as-of band agreement: rebuild I-ledger with swapped roles (same frozen
  engine/clock/warmup), recompute pairing vs revised on 243 decisions.
- C3 revision spreads (YoY units) for the three new series, same benchmark grid.
- C4 decomposition of the ~24% disagreement: months where old- vs new-candidate
  bands DISAGREE with each other = selection effect (upper bound); months where
  BOTH disagree with revised = genuine revision effect (lower bound).
- Verdicts per role (frozen): CONFIRMED if C1 passes + concept match + vintage
  coverage spans recorded; else UNVERIFIED (never upgraded on names alone).
  New candidates NEVER overwrite frozen Phase 2 claims; reported side-by-side.

## 4. Stop conditions + deliverables

- Any new ID without vintages → leg UNVERIFIED, stop that leg (others continue).
- Deliverables (all `issue-189` paths): this addendum; `phase2b/` pulls manifest,
  alt-ledger, comparison JSONs; short finding note with the three verdicts +
  the decomposition; tests (span discipline, C1 asserts, no-returns scan,
  determinism). No model edits, no merge, no Pine.
- Firewall: after this commit + first new-route outcome, no spec change without
  a NEW issue. Finding MUST contain `production_authorized=false`.
