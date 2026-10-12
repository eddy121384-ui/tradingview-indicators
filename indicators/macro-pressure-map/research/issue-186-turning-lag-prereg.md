# Issue #186 — Deep-History equity turning-point lag — Preregistration (frozen)

- Issue: [#186](https://github.com/eddy121384-ui/tradingview-indicators/issues/186)
- Branch: `research/issue-186-deep-history-equity-turning-lag`
- Base (pre-prereg) HEAD: `a3c6dbbdbcdbaf25129caf9bd5008b08947605e3` (#184 final)
- This prereg is the FIRST Issue #186 research commit on this branch.
- Status: PREREGISTRATION — frozen before any peak/trough-vs-allocation lag,
  missed-move, slope-diagnostic, or stress result is computed or viewed.
- `outcome_data_loaded=false` (at prereg commit; no event/lag output exists)
- `production_authorized=false`
- `revised_macro_history=true` (DH inputs are reconstructed, NOT vintage PIT)
- `real_time_vintage_claim=false`

## 0. Ordering attestation (firewall)

The CURRENT GitHub Issue #186 body was read in full (authoritative).
Pre-prereg work was limited to UNCONDITIONAL input work (no outcomes):

- parent artifact presence + frozen-policy code reading (matrix, B-2, #183 outputs);
- S&P 500 price source selection on provenance/coverage grounds + continuity
  check (month counts only; NO peak/trough extraction, NO allocation join);
- Yahoo-vs-Shiller validation on returns correlation/sign agreement (input
  validation only; §2);
- E_t construction METHOD reading (no E_t-vs-price lag computed).

No event table, lag, missed fraction, slope timestamp, or stress number was
computed or viewed. Sequence: read issue → verify inputs → freeze §§1–14 →
commit → record SHA → ONLY THEN run event/lag calculation. Any later
definition change requires a NEW issue.

## 1. Frozen parents and inputs (verified pre-prereg)

- #177 tiers/zeros `bc652bd615f2c5e9137050d01c666dbcd9528cd3`
- #178 weight matrix `10dcdce0ec86b0493d6df6b916b720eba46dcbe6`
- #180 ETF map `ac251ad5149d9f550d82dfb34b3551fe01032367`
- #183 corrected lineage `411835cc9e3a00d0f5d998df9fb2058d8a917e96`
- #184 final `a3c6dbbdbcdbaf25129caf9bd5008b08947605e3` (required base)
- Allocation source: corrected #183 lineage ONLY (matrix-as-truth). The buggy
  #178 backtest return stream is NEVER used. #182 V6.6 overlay is EXCLUDED
  from primary results (#184: timing specificity not supported).
- Frozen files: `generated/issue-178/weight-matrix.csv` (9 rows sum 100.00;
  zeros Low-Low/oil, Neutral-High/russell, High-Low/gold),
  `generated/issue-160/deep-history-v01-monthly.csv` (growth_dh/inflation_dh),
  `generated/issue-183/corrected-structural-monthly.csv` (B-2 applied states).
- Policy: ±10 bands, 9 states, B-2 confirmation (allocation month m from DH
  states through m−1; hold on unconfirmed), NO look-ahead in decisions.

## 2. Market price source (frozen; selected on provenance, not outcomes)

- PRIMARY monthly: Yahoo Finance ^GSPC daily closes → month-end LAST
  available daily close (repo NASDAQCOM precedent). Unadjusted close = price
  index (^GSPC has no splits; dividends excluded by construction = PRICE).
- Coverage verified pre-prereg: daily 15,275 rows 1966-01-03 → 2026-09-14;
  monthly 728/728 calendar months 1966-01 → 2026-08, 0 missing; no incomplete
  2026-09 month in the monthly file. Fetcher + raw + SHA:
  `research/issue_186_fetch_spx.mjs`, `generated/issue-186/spx-daily.csv`,
  `generated/issue-186/spx-monthly.csv`, `generated/issue-186/spx-provenance.json`.
- DAILY supplement: same Yahoo daily source; 2020-01 → 2020-06 window
  (COVID) + 1987-09 → 1987-12 spot check. Daily events do NOT imply monthly
  allocation could transact intramonth (disclosed).
- SECONDARY validation only: Shiller/datahub monthly AVERAGES
  (`spx-shiller-monthly-raw.csv`). Pre-prereg check: same index (calm-month
  levels match, e.g. 1987-08 329.8 vs 329.4; crash-month gaps exactly as
  averaging predicts), return-sign agreement 75.2%, logret corr 0.66 —
  consistent with the theoretical ≈0.71 for average-vs-point sampling under a
  random walk, i.e. NO data-join bug. Shiller NEVER enters primary events
  (average ≠ month-end semantics).
- If a named episode fails the primary extractor, state the reason; never
  force-include. 2020 monthly is EXPECTED to miss 20% (Feb→Mar −12.5%) and is
  carried ONLY via the predeclared daily supplement.

## 3. Applied Equity timeline E_t (frozen definition; computed post-prereg)

- `E_t = w_SP500 + w_Nasdaq + w_Russell` from the frozen matrix row of the
  B-2 APPLIED state for month t, verbatim (availability-independent: targets
  are full-matrix rows; availability governed returns only).
- 721 months, 1966-05 → 2026-08. Range 22.50 (Low-High) → 60.00 (High-Neutral).
- A change ΔE_t = E_t − E_{t−1} is attributed to the decision knowable by end
  of t−1 (B-2 uses DH through t−1... wait, parent engine: allocation month m
  from DH states through m−1). Lags are reported in whole calendar months
  between event month and E-change month; ±1mo alignment uncertainty is
  disclosed for intramonth daily turning dates. NO daily trade timestamps
  are fabricated.
- Only EXECUTED target changes count (not raw macro moves, not B-2 internals,
  not holdings drift). Significant move: |ΔE| ≥ 5pp (primary, diagnostic not a
  rule). Sensitivity: ≥ 10pp (single preregistered). Diagnostic: any nonzero Δ.

## 4. Primary monthly peak/trough extractor — 20% bear rule (frozen)

Deterministic, ex-post (labels evaluate the frozen policy; never enter it):

1. Scan monthly closes 1966-01 → 2026-08 with running peak (start = first month).
2. When P_t ≤ 0.80 × P_peak: confirm bear; PEAK = earliest month attaining the
   running-peak max; search TROUGH = month of minimum close in [peak, recovery),
   where recovery = first later month with close ≥ P_peak (full retracement).
3. If no recovery by 2026-08: trough = minimum over [peak, end], censored flag;
   stop (no further events).
4. Else record (peak, trough, recovery, severity = trough/peak − 1 ≤ −20%),
   resume running-peak search at the recovery month (strictly non-overlapping;
   months ≤ recovery never start a new event).
5. Ties for peak max → earliest month. Trough = global min in window (V-shapes
   NOT split; 1980/1982 handled as the algorithm finds, disclosed).
6. Event dates = actual peak/trough months, never confirmation months.
7. Peak without −20% follow-through = no event (uncounted). All confirmed
   cycles since ~1966 are tested (no cherry-picking); ongoing/censored and
   overlap handling reported explicitly (overlap impossible by construction §4.4).

## 5. Secondary extractors (frozen)

- 10% CORRECTION sensitivity: §4 verbatim with 0.90 threshold (same code path,
  parameter only). Lags/matching recomputed independently; reported alongside.
- DAILY COVID primary supplement: §4 20% rule on daily closes 2020-01 → 2020-06
  (expected ≈ 2020-02-19 peak → 2020-03-23 trough; NOT hardcoded — whatever the
  algorithm finds is reported). Monthly-vs-daily comparison table (detection,
  dates, severity). 1987-09 → 1987-12 daily intramonth-depth spot check.
  Daily signal months are labelled at monthly resolution for matching
  (event month = calendar month of daily peak/trough; ±1mo uncertainty noted).

## 6. Event-to-allocation matching (frozen; ±12mo windows)

For PEAK at month T (E = applied targets, ΔE = month-to-month change):

- Candidates: months m in [T−12, T] with ΔE_m ≤ −5pp AND still-in-effect at T:
  E_T ≤ E_{m−1} − 5pp (a later reversal above this bar disqualifies m).
  Pick the LAST qualifying m → `early_protection`, lag = m − T (≤ 0).
- Else first m in (T, T+12] with ΔE_m ≤ −5pp → `late_protection`, lag = m − T (> 0).
- Else if E_T ≤ 27.5 → `already_defensive` (E range 22.5–60; cutoff frozen,
  arbitrary-by-design, disclosed).
- Else if T within 12mo of timeline start (1966-05) or end (2026-8) →
  `censored_edge`. Else `no_action`.
- Robustness column (separate, never the primary lag): first POST-event month
  with ANY nonzero ΔE in (T, T+12], sign reported (unconditional reallocation).
- A position held > 12mo is NEVER reported as newly timely (only window
  actions count). Reversals judged on target levels only.
- TROUGH mirror: +5pp increases; `already_exposed` iff E_T ≥ 52.5 (frozen,
  disclosed); `early_re-risk` / `late_re-risk` / `no_action` / `censored_edge`.
- 10pp sensitivity reruns matching with ±10pp; any-action diagnostic reruns
  with nonzero threshold. At most these two — no tuning.

## 7. Per-event measures (frozen denominators)

PEAK: peak/trough dates+prices, severity; matched action month + signed lag;
E at −6/−3/−1/+1/+3/+6mo, at peak, at trough; if late, price return
peak→action and % drawdown before action = (P_peak − P_action)/(P_peak − P_trough)
(negative when early); action counts/signs in [T−12, T+12]; matched-state label.
TROUGH: trough date/price; recovery refs: R20 = first close ≥ 1.20 × trough
(primary) and Rfull = first close ≥ prior peak (secondary, may be censored);
action lag; E at ±1/3/6mo and trough; if late, recovery fraction =
(P_action − P_trough)/(P_R20 − P_trough) (negative when early; NaN if censored);
same window counts/labels. NEVER equate "did not add" with "zero equity":
E_T level is always reported alongside the action label.

## 8. Summaries (frozen; matches + coverage, never matches-only medians alone)

Per peak/trough sample (primary 20%, 10% sensitivity, daily supplement
separately): eligible N; matched/unmatched/censored counts; lag median/p25/p75/
range AMONG MATCHES + match coverage %; shares (reduced-before / reduced-after /
never; increased-before / increased-after / never); post-hit rates at +3/+6/+12mo
(first qualifying post action ≤ X) + pre-positioned share; median drawdown
before late de-risking; median rebound fraction before late re-risking;
whipsaws = pre-window ≥5pp actions failing remains-in-effect at event;
state churn counts. Survivorship-style conditioning is banned: every median is
shown with its coverage denominator.

## 9. Growth/Inflation early-improvement diagnostic (frozen; descriptive ONLY)

Per trough (monthly primary + daily COVID at monthly resolution), within
[T, T+12]: g1 = first month ΔGrowth_DH > 0; i1 = first month ΔInflation_DH ≥ 0
(non-declining; REPORT the inflation LEVEL band at i1 to separate low-level
from acceleration); x1 = first 3×3 (Growth,Inflation) band-state change vs the
trough-month state; b1 = first B-2 applied-state change after T; e1 = first
≥5pp Equity increase (reuse §6 match, never a second rule). False start =
g1/i1 signal followed within 6mo by a new market low (close < trough) OR an
E reversal ≥ 5pp down within 6mo. Count false starts AND successes. This
diagnostic MUST NOT become a combined timing rule; no lookback optimization.
Expected mechanism note (frozen hypothesis, tested descriptively): the
level/band policy waits for recovery to appear in macro LEVELS and therefore
lags price troughs.

## 10. Data-availability stress + PIT integrity (frozen)

- Report TWO concepts: (1) RECONSTRUCTED lag (§§6–8 on #183 timeline);
  (2) REAL-WORLD actionability UNKNOWN without true vintage/release dating —
  never call #183 PIT.
- Preregistered NONOPTIMIZED stress: shift the WHOLE E_t timeline +1/+2/+3mo
  (actionable month = reconstructed + k), rerun §6–§8 matching verbatim;
  report shifted medians + extra missed drawdown/rebound. A bound, NOT vintage.
- State exactly what remains unresolved (vintage release dates, intramonth
  execution, transaction frictions) + propose separately-scoped follow-up.

## 11. Eras, cases, verdict (frozen)

- Eras (frozen #183 bounds): E1 1966-03–1979-12, E2 1980-01–2007-12,
  E3 2008-01–2019-12, E4 2020-01–2026-08. Events assigned by peak (peaks) /
  trough (troughs) month. Era lag medians + coverage.
- Named walkthroughs: 1969–70, 1973–74, 1980–82, 1987, 2000–02, 2007–09
  (trough Mar 2009), Mar 2020 (daily), 2022. Non-qualifiers keep a card stating
  the algorithm reason (never silently dropped).
- Verdict thresholds (frozen BEFORE outcomes; raw distributions shown regardless):
  `deep_history_timing_materially_late` iff median peak lag (matches) ≥ +4mo
  OR median trough lag ≥ +6mo OR median drawdown-before-action ≥ 60%;
  `..._acceptable_with_limitations` iff median peak lag ≤ +2 AND median trough
  lag ≤ +4 AND median rebound fraction ≤ 60% AND match coverage ≥ 60%;
  `..._mixed_by_cycle` iff peak/trough or era medians straddle the above
  (one side late, other acceptable); else `..._not_assessable`
  (< 4 primary events or overlap < 20y). Debatable by design; numbers rule.

## 12. Deliverables (all paths contain `issue-186`)

- `research/issue-186-turning-lag-prereg.md` (this file)
- `research/issue_186_fetch_spx.mjs` (frozen fetcher; already run pre-prereg)
- `research/generated/issue-186/spx-{daily,monthly,provenance,shiller-monthly-raw}.csv/json`
- `research/issue_186_primitives.py` + `research/test_issue_186_primitives.py`
  (+ executed Node mirror test)
- `research/issue_186_build.mjs` (E_t timeline, extractor, matching, diagnostics, stress)
- `research/generated/issue-186/` manifest, equity-timeline, event tables
  (20% monthly, 10% sensitivity, daily supplement), lag distributions,
  missed-move, slope diagnostic, +1/+2/+3 stress, era splits, case cards
  (JSON), chart-ready CSVs, summary
- `research/decisions/issue-186-turning-lag-finding.md` (with the 5 plain-Chinese answers)
- Builder MUST pin parent SHAs, assert E_t integrity (gross 100, E range),
  evaluate ALL qualifying events, never touch Pine/parents/main.

## 13. Firewall

After this prereg commit and the first lag result, do NOT change: inputs,
E_t definition, extractor, thresholds, windows, matching, metrics, slope
definitions, stress, eras, verdict thresholds, or any frozen parent. Failure
is REPORTED, never repaired here. Forbidden: threshold tuning, cherry-picked
dates, V6.6 in primary results, new rules, optimization, Pine changes, merging.

## 14. Product boundary

Research only. Verdict ∈ (`deep_history_timing_acceptable_with_limitations`,
`deep_history_timing_materially_late`, `deep_history_timing_mixed_by_cycle`,
`deep_history_timing_not_assessable`). Finding MUST contain
`production_authorized=false` and the five plain-Chinese answers. Do not merge.
