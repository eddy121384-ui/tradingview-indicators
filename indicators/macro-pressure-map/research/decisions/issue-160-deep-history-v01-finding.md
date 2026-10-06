# Issue #160 — Deep-History Growth/Inflation v0.1 — Overlap Finding

- Issue: [#160](https://github.com/eddy121384-ui/tradingview-indicators/issues/160)
- Branch: `research/issue-160-deep-history-v01`
- Parent feasibility: Issue #158, frozen commit `88b1fa134d30fea60ea046db35e920ca1c968ee3`
- Preregistration: `indicators/macro-pressure-map/research/issue-160-deep-history-v01-prereg.md`,
  committed as `d92f3c1b8c5e1d25a7b3c23e1291841fb6494411` BEFORE any overlap metric
  was computed or viewed.
- Formal verdict: `deep_history_v01_overlap_failed`
- `outcome_data_loaded=false`
- `production_authorized=false`
- Sample: repeated robustness validation; NOT an untouched holdout. No merge requested.

## 1. What was built (frozen, no redesign)

Deep-History v0.1 exactly as preregistered — Growth roles
`USIPYY`, `USUR` (inverted), `USBP→12m%`, `USDPI/USPCEPI→12m%`, `USMNO`;
Inflation roles `USIRYY`, `USCPCEPIAC`, `USPPIYY`, `USWG`, `USEI`;
equal 20% weights; 60-month pressure scores with absolute 1M/3M changes,
0.6/0.4 momentum blend, SMA3/SMA12 tanh direction, 0.5/0.3/0.2 blend,
100·tanh(raw/2), biased sds, no future data, all-5-finite composites.
Nominal DPI YoY was NOT used (real DPI via PCE deflation, as frozen).

## 2. Source history (TradingView Official MCP, post-prereg pull)

`mcp-tv-get-economic-data`, `date_from=1960-01-01` to `2026-10-07`.
Hashes are SHA256 of the as-fetched compact `date:value` strings.

| role | ticker | first | last | n | unit | sha256 (compact) |
|---|---|---|---|---|---|---|
| G1 | ECONOMICS:USIPYY | 1960-01-01 | 2026-08-01 | 800 | % | 3931122a07aa1c9ae33f595b444ba27bbf3394fc05a9439203fa96657b9e8199 |
| G2 | ECONOMICS:USUR | 1960-01-01 | 2026-09-01 | 800 | % | 00130f867039dc2f9a81bacead6561d3500629262878bb96beb95bed192b75a5 |
| G3 src | ECONOMICS:USBP | 1960-01-01 | 2026-08-01 | 800 | PSN | 33c87d353c1021bb1a664c3037e5e4e672e14a3f6d107b234645364bdc14b075 |
| G4 num | ECONOMICS:USDPI | 1960-01-01 | 2026-08-01 | 800 | USD | 61ebe4b28c6a700bdfd942b6bd682d8d31164642e42779c5197adb2aecd12ed7 |
| G4 den | ECONOMICS:USPCEPI | 1960-01-01 | 2026-08-01 | 800 | POINT | 095da158771fc244e2afdb74899a3f64dfbfe5408092f9d8c569ed8edff35736 |
| G5 | ECONOMICS:USMNO | 1960-01-01 | 2026-09-01 | 801 | POINT | e6c0495be1c6b70e43e011913f5c90343611972a43a48f3918e5c2cd15f046f9 |
| I1 | ECONOMICS:USIRYY | 1960-01-01 | 2026-08-01 | 799 | % | 9936e0d6202cfbf4a25909ce3e683b1c508d496f9f08f686729d0d03885e289a |
| I2 | ECONOMICS:USCPCEPIAC | 1960-01-01 | 2026-08-01 | 800 | % | 6708f3113e1d275ccfe5a8708be2fd6fcbe59be62b86ccdb9094a685aafc5d51 |
| I3 | ECONOMICS:USPPIYY | 1960-01-01 | 2026-08-01 | 800 | % | 12b53781537337a417dec020a80ff877cf7699459f7b8e482a14b288f69bab3e |
| I4 | ECONOMICS:USWG | 1960-01-01 | 2026-08-01 | 800 | % | b80f40b644a465ab053055dc7a75a1875f5b610c4b0ceecae1fbced269c58b2b |
| I5 | ECONOMICS:USEI | 1960-01-01 | 2026-08-01 | 799 | % | 6ad42a14798fc803c56ecbd75569b6ef2193c3b89f87312f02e27608f78577f2 |

Union grid: 801 calendar months (1960-01-01 → 2026-09-01). I1/I5/G2 each miss
exactly one month (2025-10, federal-shutdown release gap); all other roles are
gap-free on the grid.

Actual first full-composition month (automatic, not hand-picked): **1966-03-01**.
Last full-composition month: 2026-08-01. Full-composition months: 723 of 726
possible (1966-03 → 2026-08). The 3 non-compliant months are 2025-10, 2025-11
(missing UR/CPI/energy source months plus their positional-momentum neighbors)
and 2026-01 (3-month-change neighbor of the 2025-10 hole) — automatic
consequences of the frozen no-interpolation rule.

Monthly series: `generated/issue-160/deep-history-v01-monthly.csv`
(801 rows + header, full-precision doubles),
SHA256 `42516418ec8d1ce981d1b4bc05e2ae86809d6acbf5de63dccbad515db507dcfc`.

## 3. Modern exact anchor (signal fields only)

Frozen Issue #133 snapshot decoded from
`origin/research/issue-133-state-trajectory:.../issue-133-exact-monthly.csv.gz.b64`.
SHA256 verified: `1d03923503e7fe82a69b033897484c48aa646279ecf70164d090ed62a5a70719`
(match). 388 rows, 1994-05-31 → 2026-08-31, header exactly
`date,gpi,ipi,regime`, zero month gaps. Only `date/GPI/IPI/regime` were used.
Cross-check: `regime==7` coincides exactly with `core_regime(GPI,IPI)` yielding
"Slowdown / Disinflation" on all 233 overlap months (0 mismatches), confirming
R7 = regime 7 for both reference construction and the identical DH-side rule.

## 4. Overlap sample

Intersection of full-composition DH months with the exact window (≥ 2007-01-01):
**233 months, 2007-01-31 → 2026-08-31** (236 calendar months minus the 3 DH-gap
months above). Direction-agreement pairs use consecutive overlap rows (232 pairs);
the 3 gap-spanning pairs are included per the preregistered "consecutive
overlap months" reading — disclosed here, impact negligible.

## 5. Overlap metrics (preregistered only)

| metric | value |
|---|---|
| Growth Pearson / Spearman | 0.3351 / 0.3532 |
| Inflation Pearson / Spearman | 0.4343 / 0.4503 |
| Growth direction agreement | 0.5216 (121/232; independently re-verified) |
| Inflation direction agreement | 0.5216 (121/232; independently re-verified) |
| Growth 3-state (±10) | 0.3991 |
| Inflation 3-state (±10) | 0.4850 |
| Exact 3×3 regime agreement | 0.2446 |
| R7 months: reference / predicted / hit | 50 / 24 / 13 |
| R7 precision / recall | 0.5417 / 0.2600 |
| V6.6 first-triggers (14) | 2008-12-31, 2010-08-31, 2011-08-31, 2012-06-29, 2014-10-31, 2015-01-30, 2015-07-31, 2015-12-31, 2018-10-31, 2019-05-31, 2020-04-30, 2022-08-31, 2023-03-31, 2025-04-30 |
| DH first-triggers (5) | 2007-01-01, 2009-01-01, 2015-10-01, 2020-05-01, 2023-03-01 |
| Trigger matched / precision / recall / F1 | 4 / 0.8000 / 0.2857 / 0.4211 |
| Trigger count ratio | 0.3571 |
| Trigger median absolute lag | 1 month |
| Subperiod 3×3: 2008-2016 (n=108) | 0.2130 |
| Subperiod 3×3: 2017-2019 (n=36) | 0.3056 |
| Subperiod 3×3: 2020-2022 (n=36) | 0.3333 |
| Subperiod 3×3: 2023-2026-08 (n=41) | 0.1707 |

Full machine-readable record: `generated/issue-160/deep-history-v01-overlap.json`.

## 6. All 12 gates (frozen; no rescue)

| # | gate | result |
|---|---|---|
| 1 | common months ≥ 180 (233) | PASS |
| 2 | Growth Spearman ≥ 0.50 (0.3532) | FAIL |
| 3 | Inflation Spearman ≥ 0.50 (0.4503) | FAIL |
| 4 | Growth direction ≥ 0.60 (0.5216) | FAIL |
| 5 | Inflation direction ≥ 0.60 (0.5216) | FAIL |
| 6 | 3×3 regime ≥ 0.55 (0.2446) | FAIL |
| 7 | R7 precision ≥ 0.60 (0.5417) | FAIL |
| 8 | R7 recall ≥ 0.60 (0.2600) | FAIL |
| 9 | Trigger F1 ≥ 0.60 (0.4211) | FAIL |
| 10 | Trigger count ratio in [0.50, 2.00] (0.3571) | FAIL |
| 11 | Median matched-trigger lag ≤ 2 (1) | PASS |
| 12 | Every subperiod 3×3 ≥ 0.45 (0.2130/0.3056/0.3333/0.1707) | FAIL |

Formal verdict: `deep_history_v01_overlap_failed` (gate 1 passed, so the
sample is conclusive, not inconclusive).

## 7. Interpretation (descriptive only; no redesign)

Both DH axes correlate positively with their V6.6 counterparts but well below
structural-equivalence gates. DH triggers are usually genuine V6.6 triggers
(precision 0.80, median lag 1) yet sparse (recall 0.29, ratio 0.36); joint
regime coincidence is low (0.24). Any v0.2 architecture, weight, lookback,
threshold, or turn-rule change requires a NEW issue and a NEW preregistration.
This finding changes nothing in production and re-tunes nothing.

## 8. Workflow evidence and verification

- Prereg committed (`d92f3c1`) before the #133 snapshot bytes were decoded and
  before any overlap metric was computed or viewed.
- #133 SHA256 verified before use; #136 turn rule confirmed identical between
  its prereg text and its frozen evaluator code; R7 mapping confirmed by
  zero-mismatch cross-check.
- Implementation: `issue_160_deep_history_v01.py` (pure stdlib) is the frozen
  canonical record; results were executed through a line-for-line Node mirror
  (this machine has Node v22, no Python runtime), so the Python tests below are
  committed WITHOUT a local execution pass.
- `test_issue_160_deep_history_v01.py` (stdlib unittest): frozen-constant pins,
  exact analytic cases (biased sd, ±10 boundaries, R7 cell, turn rule incl.
  `<=0` edge and NaN safety, greedy matching), an integer-analytic sawtooth
  score case, G2-inversion wiring, all-finite gating, gap propagation,
  first-trigger-per-episode, and synthetic perfect-agreement (expects PASS) /
  inverted-axes (expects FAIL) end-to-end gate checks. All numeric test vectors
  were cross-checked through the Node mirror; one hand-derived trigger-index
  error was caught by that cross-check and corrected in the test before commit.
- One implementation bug was caught by independent verification before final:
  the first overlap run overwrote snapshot month-end dates with DH
  first-of-month dates, emptying the V6.6 trigger set. Fixed to match the
  preregistered month-key join; non-trigger metrics were re-verified identical
  before/after (pairing was always month-key based).
- `git status` shows only the six required issue-160 files as new; no
  production Pine or mirror file was modified.

## 9. Explicit confirmations

- No asset-return outcome was loaded: no SPY/TLT prices or returns, no
  equity-minus-duration spread, no Issue #136 payoff table or result summary
  (only its prereg text and evaluator source for the frozen turn rule), no
  historical asset-return join of any kind. `outcome_data_loaded=false`.
- No production code was changed: no edits under `src/`, no V6.6/V6.7 Pine
  change, no mirror change. `production_authorized=false`.
- No source, weight, lookback, threshold, turn-definition, or gate change was
  made after the prereg commit.
- This overlap is a repeated robustness sample, NOT an untouched holdout.
- Do not merge.
