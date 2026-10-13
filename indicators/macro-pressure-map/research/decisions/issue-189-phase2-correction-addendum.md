# Issue #189 Phase 2 — correction addendum (independent file; originals frozen)

- Branch: `research/issue-189-deep-history-pit`; Phase 2 scope only (no Phase 3).
- Prereg `190f3a6`, Phase 1/1B/1C design docs: UNCHANGED (no rule, threshold,
  model, or gate touched in this correction).
- Trigger: GPT-6 independent review reproduced two bugs. Both CONFIRMED below
  with mechanism, evidence, and corrected figures. `production_authorized=false`.

## Bug 1 — analyzer snapshot aliasing (CONFIRMED, fixed, re-verified)

Mechanism: `issue_189_phase2_analyze.mjs` stored `snap[r] = cum[r]` — a live
reference to the cumulative map. As the decision loop advanced, every earlier
snapshot silently absorbed later vintages. Result on the committed run:
**2420/2430** staleness role-records carried `vintage_as_of > decision_at`
(i.e. future revised values labeled as as-of).

Fix: per-decision deep copy of the cumulative map (dict + [date,value] pairs).
Re-verified on rerun: **0/2430 violations** (gated by test).

Contamination analysis (honest bounds): the lag gate (`month_end+lag ≤ D`)
filtered out future-dated obs months, so most commons were numerically
identical (2006-06-30→2006-04 and 2026-08-31→2026-06 confirmed unchanged), but
every decision adjacent to a genuine data gap received a contaminated common
month: confirmed case 2019-02 (2018-12→**2018-11**; Dec-2018 BEA values came
from Mar-2019+ vintages under aliasing). Same class: 2025-11/2025-12 and
2026 frontier months near shutdown gaps. The exact old list is unrecoverable
(the contaminated ledger was an uncommitted working artifact, replaced not
versioned) — stated here explicitly rather than reconstructed.
Affected downstream: staleness legs vintage/value fields (ages recomputed,
medians unchanged: monthly ~1.0mo, BEA ~2.0mo; maxes grew — G3 4.07,
G4/BEA 3.07 — as gap-pulled commons now show); engine commons (rebuilt);
confusion/pairing (recomputed §3). Revision-impact, YoY spreads, definition
checks never touched snapshots — unaffected.

## Bug 2 — five null-I months mislabeled scored (CONFIRMED, taxonomy fixed)

Cause: genuine federal-shutdown vintage gaps, not code logic — 2018-12 BEA
(2018–19 shutdown) and 2025-09/10 multi-agency (2025 shutdown) observations
absent from all vintages ≤ decision date, leaving roles non-finite at common.
New frozen taxonomy: `scored` = all 9 non-G5 roles finite at common;
`partial` = warmup/count OK with ≥1 role non-finite (missing roles listed);
`gap-*` = warmup/count/grid failures (0 in this panel).
Corrected ledger: **241 scored + 2 partial** (2026-01: G2+I1+I5; 2026-03:
G2+I1+I5) + 0 gaps. Pairing for I-confusion is months with finite as-of I
AND a revised band: **184/241 = 76.3%** (was: 182/240 = 75.8% on mislabeled
rows). mean|dI| 8.549 (was 8.588). G1–G4 finite: 241/243.

## Development bugs fixed en route (were never in any committed output)

G3 double-YoY (as-of pre-transformed what frozen `build_roles` transforms —
found because G3 scores came out all-NaN; fixed to level passthrough);
contiguity warmup gate misfiring on shutdown months (count gate +
finiteness-authoritative, matching frozen `last_valid` semantics);
non-JSON NaN in ledger (sanitized to null); empty-string parser crash
(NaN-placeholder grid, zero information). All were pre-finding development
fixes toward prereg compliance, disclosed per Phase 2 practice.

## Verdict effect

Phase 2 verdict (No-Go full replay) UNCHANGED — it rests on G5 absence, which
no correction touches. All six finding answers stand with the corrected
figures in finding-v2 (this addendum's companion file).

`production_authorized=false`
