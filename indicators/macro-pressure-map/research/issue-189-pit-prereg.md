# Issue #189 — Deep History PIT vintage & publication-lag validation — Preregistration (frozen)

- Issue: [#189](https://github.com/eddy121384-ui/tradingview-indicators/issues/189)
- Branch: `research/issue-189-deep-history-pit`
- Base (pre-prereg) HEAD: `5864f6852042c22594529d8d96d02d73d42c6130` (#188 OC final)
- `origin/main` at launch: `cf659e0ebe8604a25fcbd2b43c7a122deee738fa` (must stay untouched)
- Parent HEADs at launch: #177 `bc652bd615f2c5e9137050d01c666dbcd9528cd3`,
  #178 `10dcdce0ec86b0493d6df6b916b720eba46dcbe6`,
  #180 `ac251ad5149d9f550d82dfb34b3551fe01032367`,
  #183 `411835cc9e3a00d0f5d998df9fb2058d8a917e96`,
  #184 `a3c6dbbdbcdbaf25129caf9bd5008b08947605e3`,
  #186 `a83836ce0453d890c4d00667d50c36767aa9278b`,
  #187 `e61b9a31feb08ab757d34d77cc841fda70c77bcc`,
  #188 `5864f6852042c22594529d8d96d02d73d42c6130` (all verified `commit` objects)
- This prereg is the FIRST Issue #189 research commit on this branch.
- Status: PREREGISTRATION — frozen before ANY vintage fetch beyond
  public-catalog checks, before ANY as-of recomputation, and before ANY
  asset-return inspection for source selection.
- `outcome_data_loaded=false` (at prereg commit; no PIT result exists)
- `production_authorized=false`
- `revised_macro_history=true`, `real_time_vintage_claim=false`

## 0. Ordering attestation (firewall)

Issue #189 was read in full (authoritative). Parent findings (#158 source
feasibility as TV-ticker inventory, #160 frozen 60-month construction,
#177/#178/#180/#183/#188 policy lineage) were read as frozen INPUTS.
Pre-prereg work was limited to: parent SHA existence checks, file-presence
checks, and reading #158/#160 docs (no network vintage pulls, no return-file
reads for decisions). No vintage value, coverage percentage derived from a
fetch, as-of score, or payoff number was computed or viewed. Sequence: read
issue → verify parents → freeze §§1–9 → commit → record SHA → ONLY THEN run
Phase 1 catalog/fetch audit. Any later design change requires a NEW issue.
Phase 1 scripts MUST NOT import asset-return files (enforced by review; the
coverage/record logic operates on macro/source calendars only).

## 1. Hypotheses and verification questions (frozen)

- H1: each of the 11 raw TV feeds has an exact official counterpart whose
  historical vintages reproduce the frozen #160 role semantics.
- H2: for every decision month, the 60-month version history visible THEN
  suffices to recompute level/momentum/direction without future information.
- H3: publication timestamps permit month-end tradability decisions as the
  frozen engine assumes (or a conservatively delayed clock documented here).
- Phase 1 verdict criteria (§7) decide whether Phase 2 (as-of rebuild) and
  Phase 3 (P-ETF replay) are identifiable. Failure is REPORTED (stopped),
  never patched with revised values.

## 2. The 11 feeds and their allowed exact counterparts (frozen; audit tests THESE)

| Role | TV symbol (frozen) | Frozen transform (#160) | Counterpart hypothesis UNDER TEST (not assumed) |
|---|---|---|---|
| G1 | `ECONOMICS:USIPYY` | native YoY | FRED `INDPRO`, monthly SA index → computed 12m % |
| G2 | `ECONOMICS:USUR` | level, sign inverted | FRED `UNRATE`, monthly SA rate → inverted |
| G3 | `ECONOMICS:USBP` | level → causal 12m % | FRED `PERMIT` (units) → 12m %; units/SA must match TV PSN |
| G4n | `ECONOMICS:USDPI` | level ÷ PCEPI → 12m real % | FRED `DSPI` (nominal DPI) + `PCEPI` (chain price) |
| G4d | `ECONOMICS:USPCEPI` | deflator level | FRED `PCEPI` level |
| G5 | `ECONOMICS:USMNO` | diffusion level, 50 NOT subtracted | ISM New Orders DI history incl. pre-1980 backfill method |
| I1 | `ECONOMICS:USIRYY` | native YoY | FRED `CPIAUCSL`, monthly SA → 12m % |
| I2 | `ECONOMICS:USCPCEPIAC` | native annual % | FRED `PCEPILFE` (core PCE idx, SA) → 12m % |
| I3 | `ECONOMICS:USPPIYY` | native YoY (index definition TBD in audit) | FRED PPI all-commodities (`PPIACO`) or stage-based successor; definition must match history |
| I4 | `ECONOMICS:USWG` | native YoY (definition TBD in audit) | BLS CES earnings (production/nonsupervisory pre-2006); FRED `AHETPI` starts 2006 — NOT sufficient alone |
| I5 | `ECONOMICS:USEI` | native % (definition TBD in audit) | CPI energy component (FRED `CPIENGSL` or `CPIENG`); definition must match history |

"Exact" means: same measured concept, same seasonal adjustment, same
native-vs-computed YoY basis, same units. Anything else is at best
`proxy_not_equivalent` (audited, never silently substituted). G4 MUST keep
nominal÷deflator→real→YoY order (no nominal-DPI shortcut).

## 3. Vintage判定 principles (frozen)

- Source priority per feed: (1) ALFRED vintage history, (2) Philadelphia Fed
  RTDSM complete vintages, (3) official agency release archives with dated
  vintages, (4) dated release PDFs/schedules (supports date-only status max).
- `observation_period` ≠ release date ≠ vintage date. A series starting 1960
  proves NOTHING about 1960 vintages. An ALFRED vintage date proves existence
  that day, NOT availability before that day's month-end close / trading.
- Status taxonomy (frozen, one per feed): `exact_verified_PIT`
  (timestamp-verified intra-month availability), `date_only_conservative_PIT`
  (day-granular only → conservative rule §4), `partial_PIT` (sub-period or
  sub-definition only, bounds recorded), `proxy_not_equivalent`, `unavailable`.
- Evidence per feed (frozen requirement): URLs, query method + extraction time,
  record counts, raw checksums, license/redistribution note. No credentials or
  API keys committed. No non-redistributable raw data committed (fetchers +
  hashes instead).

## 4. Conservative rules for imprecise dates (frozen)

- Unknown intraday time → eligible at the NEXT trading session's close at the
  earliest; month-end decisions require eligibility ≤ last trading close of
  the decision month, else the observation is NOT usable that month.
- Day-granular vintage dates → `date_only_conservative_PIT`, shifted by the
  rule above; NEVER labeled timestamp-exact.
- Holiday/weekend releases → next trading session. Timezone: US Eastern for
  agency releases; UTC-normalized `eligible_at` stored alongside.
- Same-day ambiguity (release day == month-end close) → next eligible session
  (conservative), month tradability labeled honestly.
- Backfilled diffusion history (G5 pre-1980), harmonized indexes, or modeled
  back-history → NOT true PIT (at best `partial_PIT` with bounds, or
  `proxy_not_equivalent`).

## 5. 60-month version rebuild (frozen method for Phase 2)

- At decision date D, each role value uses ONLY vintage values with
  `vintage_date ≤ D` (ALFRED realtime semantics), latest-vintage-wins per
  observation; rolling 60-observation means/sds, SMA3/SMA12, d1/d3 momentum
  recomputed ENTIRELY inside that vintage-visible history (internal revision
  contamination documented, never mixed with later vintages).
- Warmup: ≥72 months of vintage-visible history before the first scored month
  (60 + 12 for G3/G4 YoY + SMA/momentum edges); insufficient → no-signal gap
  (five-finite rule preserved; gaps NEVER filled with revised values).
- Common-month rule: Growth/Inflation composites use the most recent common
  fully-available observation month; staleness recorded per leg/month.
- Frozen formula reuse: level_z 0.5 / mom_z 0.3 (0.6·d1+0.4·d3/3) / direction
  0.2, `100·tanh(raw/2)`, all-five-finite, ±10 bands, B-2 in calendar time,
  100% gross/caps/zeros. Decision ledger fields: `observation_period`,
  `published_at`, `vintage_as_of`, `eligible_at`, `signal_observed_at`,
  `decision_at`, `trade_effective_at`.

## 6. Stop conditions (frozen)

- Any role with status `proxy_not_equivalent`/`unavailable` for month M →
  no PIT score/state/weight for M (labeled, counted, never imputed).
- `partial_PIT` bounds recorded per role; months outside bounds are gaps.
- Phase-level: PIT_not_identifiable for any span where <90% of its months are
  fully five-finite-identifiable, or where ANY of G1–G5/I1–I5 lacks an exact
  counterpart for >10% of months. ETF 2006–2026 verdict needs the same bar
  (else partial/non-primary at best).
- Blocked Phase 1 → STOP, report coverage failure (finding §7), no synthetic
  vintages, no revised-value gap fill, no threshold loosening.

## 7. Phase 1 feasibility criteria (frozen; finding answers A–D against THESE)

- A (exact mapping count): of 11 feeds, how many reach `exact_verified_PIT`
  or `date_only_conservative_PIT` with definition match.
- B (year-by-year 1960–2026): months fully / partially / not reconstructible
  for Growth_DH+Inflation_DH jointly (five-finite rule); coverage table frozen
  schema (§9).
- C (ETF 2006–2026): full-PIT-replay verdict needs 11/11 roles identifiable
  for ≥90% of months incl. 72-month warmup history (i.e. vintage-visible
  history effectively from ~2000); else partial-only with exact missing pieces.
- D (gaps): enumerated missing data + ONLY definition-preserving,
  future-free remedies (e.g. documented conservative carry of last ELIGIBLE
  vintage — still labeled, never silent). No revised-value remedies, no proxy
  swaps, no requirement loosening.
- Allowed conclusions: fully feasible / partially feasible / not verifiable.
  Weakening PIT to pass is FORBIDDEN.

## 8. Phase 2/3 future validation (frozen scope; NOT executed in Phase 1)

- Phase 2: as-of engine + tests (synthetic vintage updates, in-window
  revisions, reference-vs-release months, holiday/same-day, warmup,
  anti-lookahead, B-2 boundaries, 100%/caps/zeros); three SEPARATE experiments
  (PIT-verified / date-conservative / +1/+2/+3 hypothetical lag); confusion
  matrices, crossing/switch timing, 1970s/2007–09/2020/2022 where archives permit.
- Phase 3: P-ETF 2006-06→2026-08 matched replay ONLY where identifiable
  (A revised vs A-PIT vs C vs D vs E + #188 B/F contextual); identical months,
  Yahoo adjusted ETF/T-bill streams, 2bp incl. drift-rebalance, no backfill,
  no calendar compression; metrics + paired bootstrap (24m, seed 188, 90%) +
  leave-one-crisis-out; timestamp-lag diagnostic. P-MAX only as
  feasibility/partial diagnostic, never verified PIT.
- Verdicts (mutually exclusive): `pit_advantage_survives_with_caveats`,
  `pit_advantage_materially_degrades`, `pit_edge_inconclusive`,
  `pit_not_identifiable`. Loose gates never equal live alpha.

## 9. Deliverables (all paths contain `issue-189`) + rules

- `research/issue-189-pit-prereg.md` (this file)
- `research/generated/issue-189/source-manifest.csv` (11 rows + evidence cols)
- `research/generated/issue-189/vintage-coverage.csv` (role×year or role×month
  grid with status + vintage-start + notes)
- `research/generated/issue-189/publication-lag-audit.csv` (per-feed release
  schedule, lag days, timezone, staleness rule)
- `research/generated/issue-189/feasibility-summary.json` (A–D answers machine-readable)
- `research/decisions/issue-189-pit-feasibility-finding.md` (A–D in Traditional
  Chinese + Phase 2 risks/data needs)
- Consistency tests (no-return-imports, schema, determinism). Parent artifacts
  untouched. Phase 1 reads NO asset-return file for any decision (attested in
  finding; audit code reviews imports).
- Firewall: after this prereg commit, no design change without a NEW issue.
  STOP at Phase 1. No main merge, no Pine/production edits, no threshold/
  weight/cap/B-2 changes, no tradable-portfolio construction.
  Finding MUST contain `production_authorized=false`.
