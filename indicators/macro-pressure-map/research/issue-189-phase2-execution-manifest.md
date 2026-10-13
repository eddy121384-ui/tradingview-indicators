# Issue #189 Phase 2 — execution manifest (frozen; prereg §5 refinement, NOT a rule change)

- Phase: **Phase 2 — genuine PIT vintage reconstruction & validation** (NO payoff
  backtests; NO Phase 3 replay in this round).
- Branch: `research/issue-189-deep-history-pit`, base `5864f68`, prereg `190f3a6`
  (unmodified; verified in history). Phase 1/1B/1C outputs frozen.
- GPT-6 independent branch `research/issue-189-gpt6-phase1c-independent`
  (`25986c9`) used as READ-ONLY review: adopted nomenclature
  (`max_raw_lookback_offsets=74`, `min_raw_observation_count=75`) and its
  residual gaps (§7) as must-address items. Test cases re-derived independently
  in our own files (never copy-pasted). NO merge between branches.
- This manifest is committed BEFORE any batch vintage pull. mechanism
  `outcome_data_loaded=false` still holds (no as-of score computed yet).
- `production_authorized=false`

## 1. Frozen vocabulary (from GPT-6 reconciliation + Phase 1C proof)

- `max_raw_lookback_offsets = 74`: score month T needs raw back to T−74m
  (60 X window + momentum X[i−3] + G3/G4 12m YoY), no-gap case, verified
  against frozen `pressure_score` + `build_roles` (Phase 1C synthetic proof;
  first-finite raw index 74; DH 1960-01+74m = 1966-03 cross-check holds).
- `min_raw_observation_count = 75`: 74 offsets inclusive of scored month.
- The prereg's "≥72 months" is SUPERSEDED by 74/75 everywhere in Phase 2
  (documented correction, same frozen formula).

## 2. Vintage sampling grid (frozen)

- Endpoint: `alfredgraph.csv?id=<SID>&vintage_date=<YYYY-MM-DD>`, single date
  (multi-date `vintage_dates=` and `output_type=` are IGNORED by this endpoint
  — verified 2026-10-13: both return the latest vintage instead).
- Sample dates: LAST CALENDAR DAY of every month 2000-08 → 2026-08
  (313 dates) × 10 feeds (G1 INDPRO, G2 UNRATE, G3 PERMIT, G4n DSPI, G4d PCEPI,
  I1 CPIAUCSL, I2 PCEPILFE, I3 PPIACO, I4 AHETPI, I5 CPIENGSL). G5 EXCLUDED —
  no endpoint exists (Part B spot plan §6 instead).
- Expected volume ≈ 3,130 pulls ≈ ~1 h at 1.0–1.5 s spacing (background job
  with resume-by-manifest; consecutive failures ≥10 abort the run, partial
  manifest kept and reported).
- Fetch discipline: User-Agent with repo contact, HTTP-status check, retry ×3
  with backoff, per-pull SHA-256 + returned-header date + obs span + row
  count recorded; raw CSVs are NOT committed (processed artifacts +
  re-pullable manifest only, per redistribution caution).
- Header-echo caveat (Phase 1C): returned column echoes the requested date;
  the OBS SPAN (latest obs ≈ 1–2 months before vintage date) is the realtime
  evidence, asserted per pull by test (latest obs month < vintage month).

## 3. Scope and missing-data rules (frozen)

- Decision months: 2006-06 → 2026-08 month-ends (243); warmup history comes
  from 2000-08+ vintages (full-history columns verified in Phase 1C).
- As-of value for observation m at decision D = value in the newest fetched
  vintage ≤ D-end (latest-wins; monthly grid ⇒ effectively the D-end vintage
  column). No interpolation, no revised-value injection, no cross-feed splicing.
- A decision month is SCORED only with 75 raw observations each carrying a
  vintage ≤ D (74 offsets); otherwise no-signal gap (five-finite rule kept).
- Months lacking any needed vintage (fetch gaps) → gap, never filled; density
  audit from the pull manifest decides whether 2006–2026 is fully covered or
  partially (reported, never smoothed over).
- Staleness/eligibility: prereg conservative clock unchanged (date-only →
  next trading session; BEA end-of-month borderline documented per leg/month
  as information age; month-label ≠ release-date discipline with
  observation_period / vintage_as_of / eligible_at fields on every used value).

## 4. Three-way split (frozen; never conflated)

1. Revised reconstruction: frozen #160/#183 values as published (inputs only).
2. Genuine as-of vintage: this round's product (§3 grid, latest-wins).
3. Hypothetical fixed lag +1/+2/+3: mechanical shift of the REVISED series
   (secondary diagnostic only, same as #188 stress).

## 5. Analyses (frozen list; methods in builder, thresholds none — descriptive)

- R1 revision impact: same-observation values across vintages (level drift,
  SA-factor/rebasing steps, 2008-outlier-type events); revision magnitude
  distribution per feed; effect on rolling means/sds via frozen recompute.
- R2 staleness: per-leg information age at each decision month-end; BEA
  borderline months flagged; common fully-available observation month.
- R3 definition checks I3/I4/I5: vintage candidate values vs frozen #160
  input semantics (native-vs-computed YoY, index concept, SA, units) —
  fail-closed: mismatch → `proxy_not_equivalent` stands.
- R4 as-of G/I scores + ±10 states + B-2-equivalent state path on genuinely
  covered months; confusion vs revised states; crossing/switch timing deltas;
  defensive/re-risk decision counts advanced/delayed/missed. (States feed NO
  return computation in this round.)
- R5 G5 Part B spots: 2008–09 (verified 2008-03: 46.5; 2009-02: 33.1/32.8),
  2020 and 2022 contemporary values (to be fetched with citations this round);
  episode-level对照 only; licensed-database feasibility/cost note.

## 6. Tests (frozen list; synthetic + frozen-code + independent mirror)

- T1 header-echo/span discipline on every pull (latest obs < vintage month).
- T2 revision propagation: synthetic raw revision changes frozen score
  (GPT-6 case re-derived independently).
- T3 74/75 warmup via REAL `build_roles`+`pressure_score` (GPT-6 stronger case
  re-derived independently; supersedes Phase 1C hand-built-X version).
- T4 reference-vs-release month separation; holiday/same-day conservative rule.
- T5 missing vintage never filled by revised values (poison-value test).
- T6 definition mismatch fail-closed (wrong-concept series rejected).
- T7 rerun determinism (manifest + processed artifacts byte-identical).
- T8 no-G5 ⇒ no complete nine-state output (engine refuses).
- T9 Phase 2 imports NO asset-return file (static import scan; Node + Python).
- T10 independent cross-check: separate Node reimplementation of
  pressure_score verified against frozen Python on shared vectors
  (no single-implementation self-validation).
- Python suite via venv python; Node mirror suite; both green before finding.

## 7. Deliverables (all under `indicators/macro-pressure-map/research/`, `issue-189` paths)

- This manifest (`issue-189-phase2-execution-manifest.md`)
- `generated/issue-189/phase2/vintage-manifest.json` (per-pull URL/hash/span/retries)
- `generated/issue-189/phase2/asof-ledger.json` (monthly role values + vintage_as_of/eligible_at)
- `generated/issue-189/phase2/revision-impact.json`, `staleness.json`, `definition-checks.json`
- `generated/issue-189/phase2/g5-spots.json`, `coverage.json`
- `research/issue_189_phase2_pull.mjs`, `research/issue_189_phase2_asof.py` (frozen-#160 import engine), `research/test_issue_189_phase2.py`, `research/test_issue_189_phase2_mirror.mjs`
- `research/decisions/issue-189-phase2-finding.md` (6繁中 answers + Phase 3 Go/No-Go)
- STOP after finding. No Phase 3 replay, no merge, no Pine.
- `production_authorized=false`
