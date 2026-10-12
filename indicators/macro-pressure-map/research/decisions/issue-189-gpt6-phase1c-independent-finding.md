# Issue #189 — GPT-6 independent Phase 1C correctness finding (2026-10-13)

**Scope:** A narrow technical check of two assertions in the **Phase 1B** addendum. Not Phase 2/3; no return series, backtests, vintage value downloads, optimization or model changes.

- Base: `434ee8e680902b25283baa742719567a7f872dc9` (OC Phase 1B frozen).
- Branch: `research/issue-189-gpt6-phase1c-independent` (isolated; deliberately **not** writing to OC's `research/issue-189-deep-history-pit`).
- #189 prereg `190f3a64d38d8f857c349ba9abf041f83266d517`, Phase 1 + Phase 1B findings and all prior outputs remain untouched.
- `outcome_data_loaded=false`, `production_authorized=false`. No main merge, production Pine, weight or B-2 change.
- Main question: Did Phase 1B prove (a) the initial 2000-08 ALFRED snapshot's full observation extent and (b) the frozen #160 warmup at the 2006 ETF start? **Neither is yet proven at raw-value level.** The *mathematical* warmup requirement, however, **is independently established below**.

## A — ALFRED evidence correction (CONFIRMED documentary error; numeric data NOT pulled)

The public ALFRED category displays for `PCEPILFE`:
- `Index 1996=100 | Release Dates 2000-08-01 to 2003-12-22 | Observation Period Jan 1959 to Oct 2003`.
- The Phase 1B statement that **the first 2000-08-01 vintage already contains 1959-01 through 2003-10** is a category-aggregation fallacy: the October 2003 observation is 38 months in the FUTURE relative to the first vintage. This cannot literally be true.
- ALFRED's documentation does confirm that *each individual vintage column* contains all observations available on **that vintage date**, but the series/category's cross-vintage observation envelope is not a measurement of the FIRST column.
- The data catalog strongly suggests historical 1959 observations are available for the series, but it does **not by itself prove** the exact old-history range of the 2000-08-01 snapshot or any specific as-of 2006-06 snapshot.
- Official BEA contemporaneous release is available from 2000-08-01, reinforcing that BEA published PCE information in 2000; it is not a substitute for ALFRED as-of values.
- `exact_first_vintage_coverage = NOT_VERIFIED`; `exact_2006_decision_vintage_coverage = NOT_VERIFIED`. No authentication token is available in this audit environment, and a fabricated vintage-value table would be worse than a reported coverage uncertainty.

Sources (checked 2026-10-13):
1. https://alfred.stlouisfed.org/category?cid=9&ob=pv&od=desc&t=energy (PCEPILFE revision grouping).
2. https://alfred.stlouisfed.org/series?seid=PCEPILFE (unit/definition changes by release period).
3. https://alfred.stlouisfed.org/help/downloaddata (meaning of each vintage column).
4. https://fred.stlouisfed.org/docs/api/fred/series_observations.html (API key required; `realtime_start` / `realtime_end` / `vintage_dates`).
5. https://www.bea.gov/news/2000/personal-income-june-2000 (contemporaneous 2000-08-01 8:30 EDT BEA release).

**Consequence:** RETAIN the Phase 1B withdrawal of the blanket “a vintage begins in 2000, therefore raw historical 2000 observations are unavailable” inference. But DOWNGRADE Phase 1B's “ETF 2006 warmup is verified complete” claim to **plausible, conditional, L3 unverified**. The failure to prove raw snapshot depth is not proof that the history was unavailable.

## B — Frozen #160 warmup: 75 consecutive raw MONTHS (independently confirmed)

Canonical code: `research/issue_160_deep_history_v01.py`:
- `build_roles`: G3 `BP[t]/BP[t-12]-1`; G4 uses `(DPI/PCEPI)[t]/(DPI/PCEPI)[t-12]-1`.
- `pressure_score`: 60 **valid momentum observations**, where `mom[t] = .6*(x[t]-x[t-1]) + .4*(x[t]-x[t-3])/3`; SMA3 and SMA12 do not dominate this bound.
- At first valid G3/G4 role index `i`, the earliest of those 60 valid momentum observations is at `i-59`. Its 3-month input is at `i-62`. That derived YoY requires raw input at `i-74`. Therefore the first scored G3/G4 month requires `i >= 74` (zero-based), **75 consecutive original monthly observations including the current reference month**.
- 74 raw points → no valid score; 75 → first score at index 74; 76 → first score at index 74 (two scores). Both BP-derived and real-DPI-derived series passed an independent local Python implementation of the *frozen arithmetic*. This exactly matches #160's actual first five-factor month `1966-03` from a `1960-01` start.
- A new `test_issue_189_gpt6_phase1c.py` is committed and **imports the actual frozen #160 module**, running four test methods (constants; 74/75/76 raw periods; internal-revision propagation; 2006 month offsets). The independent arithmetic was executed locally; **the committed test's execution on a full checkout / GitHub runner has not been verified in this session**. Do not mislabel it as passed CI.
- The 75-point bound assumes no missing observations and stable nonzero variances; source gaps, as-of releases, ragged publication calendars and different native-vs-computed transform definitions can require MORE history.

### Example for ETF era (NOT a vintage claim)

For a *reference observation* month `2006-06`, the oldest necessary raw month is `2000-04`; for `2006-05`, `2000-03`; for `2006-04`, `2000-02`. This is not automatically the same as the portfolio DECISION month: real PCE/DPI reporting can make the latest jointly available reference month 1–2 months older. As-of timing and intraday eligibility must be audited separately.

The frozen #189 prereg wrote `>=72 months` as a rough warmup. This addendum documents the exact frozen-code minimum without changing the prereg or any model. Future Phase 2 should respect **the larger mechanically required 75 points**, not alter the formula to fit 72.

## C — Interpretation, stop/go

**Updated conclusion:** `partially_feasible` unchanged. G5 ISM New Orders still lacks a continuous, licensed/verified historic vintage feed, so this audit CANNOT generate the five-finite PIT portfolio. L3 tested raw vintage values remain **zero**. The 2006–2026 partial 10/11 case looks substantially more tractable than an observation-start misreading implied, but is still **unverified**.

Before any Phase 2 portfolio payoff computation:
1. Retrieve *actual* as-of `PCEPI` and `PCEPILFE` numeric observation records at `2000-08-01` and `2006-06-29/30` (ALFRED key or documented permissible historical download), calculate `min_observation_month`, `max_observation_month`, and missing counts; store query, hash, UTC retrieval time, no secret.
2. For as-of 2006-06, find the latest **jointly eligible** observation month across the eleven original roles; verify historical coverage back 74 monthly offsets from that **reference month** (not from decision month), including publication cutoff.
3. Match I3/I4/I5's actual TV statistic definition and G1 vintage data depth; remain label-L3-pending otherwise.
4. Resolve G5 licensing or retain blocked full-PIT status. ISM news excerpts and seasonal-revision tables are bounded episode checks, **not** a replacement for full scoring.

**No returns examined, no parent artifact replaced.** Finding and machine-readable synthetic audit output live only in this independent research branch.

`production_authorized=false`
