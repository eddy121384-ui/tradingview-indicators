# Issue #160 — Deep-History Growth/Inflation v0.1 — Preregistration (frozen)

- Issue: [#160](https://github.com/eddy121384-ui/tradingview-indicators/issues/160)
- Parent feasibility: Issue #158, frozen commit `88b1fa134d30fea60ea046db35e920ca1c968ee3`
- Branch: `research/issue-160-deep-history-v01`
- Status: PREREGISTRATION — frozen before any overlap metric was computed or viewed
- `outcome_data_loaded=false`
- `production_authorized=false`

This file was created and committed BEFORE loading the frozen Issue #133 exact V6.6
monthly signal and BEFORE computing any Deep-History v0.1 vs V6.6 overlap metric.
No overlap result is reported here. Any redesign after results requires a new
issue/version; nothing in this file may be edited in response to results.

## 1. Frozen v0.1 architecture (no redesign after this commit)

### Growth roles (equal 20% each, no fitted weights)

- G1 Output: `ECONOMICS:USIPYY` — Industrial Production YoY. Positive = stronger growth. No transform.
- G2 Labor slack: `ECONOMICS:USUR` — Unemployment Rate. INVERTED (lower unemployment = stronger growth). Inversion applied to the final component score.
- G3 Housing: `ECONOMICS:USBP` — Building Permits level → causal 12-month percent change: `100 * (BP_t - BP_{t-12}) / BP_{t-12}`. Positive = stronger growth. Requires 12 prior months; first usable 12 months after raw start.
- G4 Real household resource growth: `ECONOMICS:USDPI / ECONOMICS:USPCEPI` → real disposable-income index, then causal 12-month percent change: `100 * (R_t - R_{t-12}) / R_{t-12}` where `R = USDPI / USPCEPI`. Do NOT use nominal DPI YoY directly. Requires 12 prior months of the ratio.
- G5 Forward manufacturing demand: `ECONOMICS:USMNO` — ISM Manufacturing New Orders diffusion level, used directly as X. Rolling normalization captures high/low relative to recent history. Centered-at-50 diagnostics may be reported separately, but 50 is NOT subtracted before normalization.

### Inflation roles (equal 20% each, no fitted weights)

- I1 Headline: `ECONOMICS:USIRYY` — CPI YoY. No transform.
- I2 Persistent core: `ECONOMICS:USCPCEPIAC` — Core PCE annual change. No transform.
- I3 Upstream: `ECONOMICS:USPPIYY` — Producer Prices YoY. No transform.
- I4 Wage pressure: `ECONOMICS:USWG` — Wage Growth YoY. No transform.
- I5 Energy shock: `ECONOMICS:USEI` — Energy Inflation. No transform.

### Prohibited substitutions

No source swaps, no role additions/removals, no weight changes after this commit.

## 2. Frozen monthly pressure-score formula (identical for all 10 roles)

For each economically signed monthly role series X (G2 signed pre-inversion; inversion
applied at the end):

1. `level_z_t` = `(X_t - mean60_t) / sd60_t`, where `mean60_t` and `sd60_t` are the mean
   and biased standard deviation (`ddof=0`) over the latest 60 valid (non-missing)
   observations up to and including month `t`. No future data.
2. `d1_t` = `X_t - X_{t-1}` (1-month absolute change; NOT percentage ROC).
3. `d3_t` = `X_t - X_{t-3}` (3-month absolute change; NOT percentage ROC).
4. `mom_raw_t` = `0.6 * d1_t + 0.4 * (d3_t / 3)`.
5. `mom_z_t` = z-score of `mom_raw` over the latest 60 valid observations (same
   causal rolling rule, `ddof=0`).
6. `dir_raw_t` = `(SMA3(X)_t - SMA12(X)_t) / sd60_t`, with simple moving averages over
   the latest 3 / 12 valid observations and the same rolling `sd60_t` from step 1.
7. `direction_t` = `tanh(dir_raw_t)`.
8. `raw_t` = `0.5 * level_z_t + 0.3 * mom_z_t + 0.2 * direction_t`.
9. `score_t` = `100 * tanh(raw_t / 2)`.

Additional frozen rules:

- Rolling statistics use the latest required non-missing observations; months with
  insufficient history yield missing scores (no forward-fill, no interpolation).
- G2 unemployment: invert the FINAL component score (`score_G2 = -score`).
- G5 New Orders: use the observed diffusion level directly as X.
- A component score is finite only when all of `level_z`, `mom_z`, `direction`
  are finite.
- Primary composite requires all 5 components finite on that axis (no reweighting
  around missing roles for the primary analysis).

## 3. Frozen composite axes

- `Growth_DH = mean(G1..G5)` — equal mean, only when all five are finite.
- `Inflation_DH = mean(I1..I5)` — equal mean, only when all five are finite.

Expected start (not hand-picked): raw sources begin 1960-01; G3/G4 need 12-month
warmup; 60-month normalization pushes the first full-composition month to the
mid-1960s/1970s computationally. The ACTUAL first full-composition month will be
determined automatically from the built series and reported in the finding; it
must not be hand-picked.

## 4. Frozen modern exact anchor (signal only, no outcomes)

- Frozen Issue #133 exact monthly V6.6 snapshot, SHA256
  `1d03923503e7fe82a69b033897484c48aa646279ecf70164d090ed62a5a70719`.
- Candidate artifact paths (branch `origin/research/issue-133-state-trajectory`):
  `indicators/macro-pressure-map/research/data/issue-133-exact-monthly.csv.gz.b64`
  with manifest
  `indicators/macro-pressure-map/research/data/issue-133-exact-monthly-manifest.json`.
- Load ONLY: `date` / `GPI` / `IPI` / `regime`.
- Do NOT load any associated asset-return outcome panels. Do NOT join any
  historical asset-return outcome at any stage.

At prereg time, the contents (values, date range, regime labels) of the #133
monthly snapshot have NOT been opened in this session, and no overlap metric
has been computed or viewed.

## 5. Frozen overlap sample (repeated robustness, NOT untouched holdout)

- Primary overlap: intersection of full-composition Deep-History v0.1 months and
  exact V6.6 months; expected roughly 2007/2008 through 2026-08.
- Fixed subperiods (report all; select none): `2008-2016`, `2017-2019`,
  `2020-2022`, `2023-2026-08`.
- Monthly sampling: one observation per calendar month; Deep-History month-end
  causal construction; V6.6 snapshot months as frozen.
- This overlap sample is NOT an untouched holdout. Every durable summary must
  describe it as repeated robustness validation.

## 6. Frozen overlap metrics

### Per-axis (Growth_DH vs GPI; Inflation_DH vs IPI)

- Pearson correlation of monthly composite levels.
- Spearman correlation of monthly composite levels.
- Monthly direction sign agreement: fraction of overlap months (after the first)
  where `sign(DH_t - DH_{t-1}) == sign(V66_t - V66_{t-1})`, with changes computed
  on consecutive overlap months; a month pair with both changes exactly zero
  counts as agreement, otherwise zero-vs-nonzero counts as disagreement.
- 3-state agreement using ±10 on both normalized composite axes. State function,
  applied identically to all four series: `negative` if score < −10, `neutral`
  if −10 ≤ score ≤ +10, `positive` if score > +10. Agreement = fraction of
  overlap months with equal states.
- Slope-sign agreement using 1-month change: identical definition to direction
  sign agreement; reported as the same statistic (no separate tuning).

### Joint

- Exact 3×3 regime agreement: joint cell = (Growth state × Inflation state),
  9 cells; agreement = fraction of overlap months where the DH joint cell equals
  the V6.6 joint cell exactly.
- R7 precision and R7 recall: reference R7 months are defined by the frozen
  Issue #136 R7 definition applied to the frozen #133 `regime` field; predicted
  R7 months are defined by applying the IDENTICAL rule function to the DH joint
  states. Precision = P(V6.6 R7 | DH R7); Recall = P(DH R7 | V6.6 R7). The #136
  rule parameters will be read from the frozen #136 artifacts AFTER this prereg
  commit, applied without modification, and recorded verbatim in the finding.
- Asynchronous-turn trigger precision / recall / F1 using the Issue #136 frozen
  turn rule, applied identically to DH and V6.6 composite paths: reference
  triggers from V6.6, predicted triggers from DH, greedy chronological matching
  within ±3 months (each trigger matched at most once). Precision, recall, F1
  on matched triggers; trigger-count ratio = #predicted / #reference; median
  absolute matched-trigger lag in months (matched pairs only).

## 7. Frozen minimum gates (ALL must pass; no near-pass rescue)

1. Common full-composition months ≥ 180.
2. Growth Spearman ≥ 0.50.
3. Inflation Spearman ≥ 0.50.
4. Growth direction agreement ≥ 0.60.
5. Inflation direction agreement ≥ 0.60.
6. Exact 3×3 regime agreement ≥ 0.55.
7. R7 precision ≥ 0.60.
8. R7 recall ≥ 0.60.
9. Trigger F1 ≥ 0.60 with ±3-month matching.
10. Trigger count ratio in [0.50, 2.00].
11. Median absolute matched-trigger lag ≤ 2 months.
12. Each fixed subperiod regime agreement ≥ 0.45.

Formal verdict (exactly one):

- `deep_history_v01_overlap_passed`
- `deep_history_v01_overlap_failed`
- `deep_history_v01_overlap_inconclusive_sample`

Gate 1 failure (insufficient common months) maps to
`deep_history_v01_overlap_inconclusive_sample`. Otherwise any gate failure maps
to `deep_history_v01_overlap_failed`. Pass requires all 12 true. No
discretionary rescue, no retuning, no threshold adjustment after seeing results.

## 8. Frozen source-data and build protocol (post-prereg)

1. Pull required source history through TradingView Official MCP
   (`mcp-tv-get-economic-data`, `date_from=1960-01-01` to present) for:
   `USIPYY, USUR, USBP, USDPI, USPCEPI, USMNO, USIRYY, USCPCEPIAC, USPPIYY, USWG, USEI`.
2. Freeze source metadata: first/last observation, count, unit, and a SHA256 hash
   of the normalized fetched series per ticker; record coverage in the finding.
3. Build monthly DH Growth/Inflation series with the frozen formula (§2–§3);
   determine the first valid full-composition month automatically.
4. Load ONLY the frozen #133 `date/GPI/IPI/regime` fields; verify the snapshot
   SHA256 before use.
5. Run ONLY the preregistered metrics (§6); apply ALL gates exactly (§7).
6. Do not rescue or retune after seeing the result; any redesign needs a new issue.

## 9. Anti-tuning and firewall (frozen)

- Do not replace sources, add/remove roles, change the 60-month lookback, change
  0.5/0.3/0.2 score weights, change equal composite weights, change ±10 regime
  thresholds, change the turn definition, or change overlap gates after this commit.
- Forbidden: SPY/TLT forward returns, equity-minus-duration outcomes, Issue #136
  payoff results, historical asset-return joins, optimizing sources/weights
  against future returns, changing production V6.6/V6.7 Pine, swapping components
  after viewing overlap results.
- Allowed: TradingView Official MCP source data, frozen #133 exact monthly
  GPI/IPI/regime signal only, source transformations, component scores,
  level/direction/regime/turning overlap diagnostics.

## 10. Required deliverables (issue number 160, not 159)

- `indicators/macro-pressure-map/research/issue-160-deep-history-v01-prereg.md` (this file)
- `indicators/macro-pressure-map/research/issue_160_deep_history_v01.py`
- `indicators/macro-pressure-map/research/test_issue_160_deep_history_v01.py`
- `indicators/macro-pressure-map/research/generated/issue-160/deep-history-v01-monthly.csv`
- `indicators/macro-pressure-map/research/generated/issue-160/deep-history-v01-overlap.json`
- `indicators/macro-pressure-map/research/decisions/issue-160-deep-history-v01-finding.md`

Research only. No production Pine change. No asset-return outcome test.
No merge unless explicitly requested.
