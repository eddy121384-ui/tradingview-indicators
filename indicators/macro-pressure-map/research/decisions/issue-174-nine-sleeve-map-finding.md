# Issue #174 — 9-sleeve Macro Asset Outcome Map — Finding

- Issue: [#174](https://github.com/eddy121384-ui/tradingview-indicators/issues/174)
- Branch: `research/issue-174-nine-sleeve-macro-asset-map`
- Base (pre-issue) HEAD: `f8eed2c5fa7086c0359a11360ce36cf33936afac` (Issue #171 final)
- Prereg commit (FIRST on branch, BEFORE any conditional return):
  `2703368f952927a77df7e6c998c53f63370b6c96`
- Formal result: `nine_sleeve_outcome_map_complete_with_limitations`
- `outcome_data_loaded=true` (post-prereg join only)
- `production_authorized=false`
- `revised_macro_history=true`
- `real_time_vintage_claim=false`
- Research only. No allocation weights optimized. No Pine changed. Do not merge.

## 1. Bottom line

A trustworthy historical monthly backbone was built for all 9 sleeves with
genuine starts preserved, and joined to the frozen Deep-History 3×3
Growth×Inflation states (723 macro-valid months, 362 episodes, 1966-03–2026-08).

- Month-weighted AND episode-weighted results reported for every eligible pair.
- Cash-relative, downside/tail, era-stability, and concentration reported.
- Evidence classification (frozen §9): 10 `historically_favored`, 9
  `historically_unfavorable`, 62 `mixed`, 0 `insufficient_sample`
  (fragmented 1-month episodes keep n_e≥4; era evaluability is the binding
  small-sample constraint).
- Future-zero-weight candidates (frozen §10, strong evidence only): 2 pairs.
- No portfolio weights produced. Two allocation-policy candidates recorded as
  text only (untested).

The hypotheses are NOT confirmed as blanket rules:

- Oil is disastrous in Low-Low (mean -4.06pp/mo, ep_hit 0.22) but the BEST
  mean in Low-High (+5.43pp/mo) and High-High (+2.50pp/mo). Verdict: state-dependent,
  not uniformly zero.
- Long Treasury dominates disinflationary collapse (Low-Low mean +1.50pp/mo,
  favored) but is unfavorable in stagflationary Low-High and Neutral-High.
  Verdict: state-dependent, not uniformly dominant.
- Cash never wins on mean, but its danger profile (zero drawdown) makes it the
  implicit benchmark; sleeve danger is measured against it throughout.

## 2. Frozen macro (unchanged)

- Source: `generated/issue-160/deep-history-v01-monthly.csv`,
  git-blob SHA256 `42516418ec8d1ce981d1b4bc05e2ae86809d6acbf5de63dccbad515db507dcfc` (verified).
- Axes: Growth_DH / Inflation_DH exactly as stored. Thresholds ±10
  (Low <-10, Neutral [-10,+10], High >+10). No redesign, no retuning.
- Episodes: contiguous same-state calendar months; frozen holes
  2025-10/2025-11/2026-01 break episodes. 362 episodes total.
- State months/episodes: Low-Low 62/25; Low-Neutral 45/28; Low-High 83/31;
  Neutral-Low 116/57; Neutral-Neutral 91/57; Neutral-High 112/57;
  High-Low 62/25; High-Neutral 80/40; High-High 72/42.

## 3. Backbone (Phase A) — semantics, provenance, coverage, eligibility

| sleeve | definition | source | TR/price | first–last (n) | eligibility |
|---|---|---|---|---|---|
| sp500 | US large-cap TR proxy = French market TR (Mkt-RF+RF), reuse #166 verbatim | French/CRSP via #166 equity file (wt SHA `ff75a22a…`, blob `9b0ff8ae…`) | TOTAL | 1966-03–2026-08 (726) | eligible_primary w/ limitation (CRSP≠S&P500 exactly) |
| nasdaq | NASDAQCOM month-end price return | FRED:NASDAQCOM daily (sha in provenance) | PRICE | 1971-03–2026-08 (666) | eligible_with_limitation (price-only; not tech sector) |
| russell | ^RUT month-end price return | Yahoo ^RUT (sha in provenance) | PRICE | 1987-10–2026-08 (467) | eligible_with_limitation (price-only; genuine; no IWM/backfill) |
| cash | TB3MS_{t-1}/1200 accrual; sleeve AND benchmark | FRED:TB3MS | TOTAL (interest) | 1966-03–2026-08 (726) | eligible_primary (separate from 2Y) |
| treasury2y | synthetic 2Y par/semiannual/dirty-price roll (S2) from DGS2 month-ends | FRED:DGS2 | TOTAL | 1976-07–2026-08 (602) | eligible_primary (synthetic; SHY r=0.985) |
| treasury10y | reuse #166 frozen 10Y verbatim (UNCHANGED) | #166 treasury file (wt `afb62d50…`, blob `69f505e9…`) | TOTAL | 1966-03–2026-08 (726) | eligible_primary |
| longtreasury | synthetic 20Y par/semiannual/dirty-price roll (S20) from DGS20 month-ends; 82-mo gap 1987-01–1993-10 (20Y discontinued), no interpolation | FRED:DGS20 | TOTAL | 1966-03–2026-08 (644; gap disclosed) | eligible_primary w/ limitation (single-yield; gap; TLT r=0.987) |
| gold | Pink Sheet monthly-avg USD/oz price return | World Bank Pink Sheet via datahub (CC BY 4.0; sha in provenance) | PRICE (complete for gold) | 1966-03–2026-08 (726; 1966-71 zeros = fixed $35 parity) | eligible_primary w/ limitation (monthly-avg vs fix; pre-71 parity) |
| oil | WTI spot MCOILWTICO price return, labeled `oil_price_proxy` | FRED:MCOILWTICO | PRICE proxy ONLY | 1986-02–2026-08 (487) | eligible_with_limitation (spot-only; short; NOT futures TR; never stitched) |

QA ONLY: SPY/QQQ/IWM/SHY/IEF/TLT/GLD/USO (modern overlap only).
Dividends: sp500 TR includes; nasdaq/russell price-only missing (~1-2pp/yr
understatement) — disclosed, not treated as equivalent for levels; excess vs
cash reported with caveat. Cash≠2Y; 2Y/10Y/Long distinct (duration ordering
verified: same shock long loses more). No ETF as deep history. No yield-change
as return. No spot-as-futures. No stitching. No constituent backfill.
Source hashes/URLs/bytes in `nine-sleeve-provenance.json`; semantics in
`nine-sleeve-source-matrix.csv`.

QA (unconditional, no macro join; `qa-validation.json`):
2Y-SHY r 0.985 MAE 0.06pp; 10Y-IEF r 0.893; Long-TLT r 0.987;
SP500-SPY r 0.987; Nasdaq-QQQ r 0.983; Russell-IWM r 0.999;
Gold-GLD r 0.628 (monthly-avg vs fund timing; disclosed limitation);
Oil-USO r 0.759 (spot vs futures+roll; disclosed).
Spot plausibility sign-correct: 10Y 1981-08 -3.0%, 2008-12 +4.4%,
2022-10 -2.4%; Long 2008-12 +10.1%, 2022-10 -4.4%; Gold 1980-01 +48.4%;
Oil 1986-03 -18.4%, 2008-12 -28.2%, 2020-04 -43.3%; SP500 1987-10 -22.6%.

## 4. Frozen analysis choices (from prereg, unchanged after conditional)

- Eras: E1 1966-03–1979-12; E2 1980-01–2007-12; E3 2008-01–2019-12;
  E4 2020-01–2026-08.
- Lower-tail metric: 10th percentile (linear interp). ES forbidden.
- Material underperformance: monthly excess <-2.0pp; episode geometric excess
  <-5.0pp.
- Drawdown convention: within-episode cumulative from episode start,
  min cumulative; reported worst across episodes in state.
- Panels: maximum-history (genuine starts) + Core (1976-07+, 6 long sleeves,
  599 macro months) + Full (1987-10+, all 9, 464 macro months). Never truncate
  to youngest as only result.
- Classification §9 and zero-candidate §10 applied EXACTLY as preregistered
  (code in `issue_174_nine_sleeve_backbone.py`; thresholds -2pp/-5pp, 24mo/4ep,
  60mo/6ep, ep_hit 0.60/0.40, p10 -4pp/-3pp, etc.).

## 5. Outcome map (maximum-history view)

Best/worst by monthly mean (ex-cash; cash mean 0.02–0.47pp/mo by state):

- Low-Low: best Long +1.50%, worst Oil -4.06%.
- Low-Neutral: best Russell +1.34%, worst Oil -0.14%.
- Low-High: best Oil +5.43%, worst Nasdaq -0.71%.
- Neutral-Low: best Russell +1.82%, worst Oil -0.14%.
- Neutral-Neutral: best Oil +1.69%, worst Gold +0.04%.
- Neutral-High: best Oil +1.33%, worst Russell -0.30%.
- High-Low: best SP500 +0.99%, worst Oil -1.44%.
- High-Neutral: best Russell +2.56%, worst Long +0.12%.
- High-High: best Oil +2.50%, worst Long +0.09%.

Cash-relative (mean excess; full table in `month-weighted-outcomes.csv`):
Favored (10): Low-Low 2Y/10Y/Long; Neutral-Low SP500/2Y/Long;
High-Low Long; High-Neutral SP500/Nasdaq/Russell.
Unfavorable (9): Low-Low Oil; Low-High SP500/Long; Neutral-Low Oil;
Neutral-High Russell/Long; High-Low Gold/Oil; High-High 2Y.
All others mixed. No pair insufficient_sample (fragmented episodes).

Episode consistency (`episode-weighted-outcomes.csv`): favored pairs have
ep_hit 0.60–0.91; unfavorable 0.22–0.47. Concentration (best-episode share)
flags single-episode dominance where present (table column `concentration`).

Downside/danger (`downside-danger.csv`): worst monthly Oil -43.3%
(Low-Low), Russell -21.9% (Low-Low), Nasdaq -22.4% (Low-Neutral),
SP500 -22.6% (1987 crash in High-High? worst -22.6% overall);
worst episode Oil -43.5% (Low-Low); max state-DD Oil -67.3% (Low-Low),
Russell -42.8% (Low-Low). P(material monthly <-2pp) highest Oil Low-Low
0.61, SP500 Low-High 0.37.

Era stability (`era-stability.csv`): persistent_positive where noted
(e.g. Low-Low bonds; High-Neutral equities); persistent_negative
(Low-Low Oil; Low-High Long; High-High 2Y/10Y); most others mixed or
insufficient_era (short sleeves in High-Low lack ≥12mo in ≥2 eras).

## 6. Panels: max-history vs common-sample

Core (1976-07+) unconditional means: SP500 1.05%, Nasdaq 1.13%, Cash 0.35%,
2Y 0.42%, 10Y 0.53%, Long 0.55%, Gold 0.66%, Oil 0.74% (Russell/Oil n smaller).
Full (1987-10+) means: SP500 0.96%, Nasdaq 1.07%, Russell 0.77%, Cash 0.25%,
2Y 0.31%, 10Y 0.46%, Long 0.42%, Gold 0.51%, Oil 0.77%.
Long mean drops in Full (missing 1987-93 gap + 2022 drawdown weight rises);
2Y/Cash means fall post-2008 low-rate era. State rankings are broadly stable
across panels; magnitudes shift with era weights (documented, not tuned).

## 7. Future-zero-weight candidates (frozen §10; evidence flags, NOT weights)

TRUE (2):

- `G_Neutral/I_High × russell` — unfavorable, n 75/40, mean_ex -0.56pp/mo,
  ep_hit 0.40, p10_ex -8.67pp, worst -11.37%, ex-worst mean still negative.
- `G_High/I_Low × gold` — unfavorable, n 62/25, mean_ex -0.65pp/mo,
  ep_hit 0.40, p10_ex -5.13pp, worst -14.46%, ex-worst mean still negative.

All other 79 pairs FALSE (including Low-Low Oil and Low-High SP500/Long,
which fail the ep_hit≤0.40 + n≥60 + tail + ex-worst conjunction despite
unfavorable labels — correctly NOT promoted on single-crash or small-sample
grounds).

Future allocation-policy candidates (text only, UNTESTED):

- `future_allocation_policy_candidate: allow 0% Russell in Neutral-High if
  later policy confirms small-cap stagflation fragility out-of-sample.`
- `future_allocation_policy_candidate: allow 0% Gold in High-Low if later
  policy confirms disinflationary-boom gold drag out-of-sample.`
- No weights tested here.

## 8. Limitations

- Revised (not vintage) macro; t+1 availability unvalidated.
- sp500 = CRSP market, not S&P500 exactly; nasdaq/russell price-only.
- Bonds synthetic single-yield/par-coupon/month-end; Long 82-mo gap.
- Gold monthly-avg vs fix timing (GLD r 0.63); pre-71 zeros are fixed parity.
- Oil spot-only, 1986+, NOT investable; USO r 0.76 with roll drag.
- Episodes median 1 month (whipsaw states); episode stats are short-horizon.
- No insufficient_sample by frozen 24mo/4ep rule; era sparsity is the real
  small-sample flag (many insufficient_era for young sleeves).
- DGS20 gap, Yahoo month timestamps, datahub mirror licensing (CC BY 4.0),
  FRED vintage revisions, CRSP revisions — all disclosed.

## 9. Artifacts (+ provenance)

- `research/issue-174-nine-sleeve-map-prereg.md` (prereg `2703368`)
- `research/issue_174_nine_sleeve_backbone.py` (frozen stdlib)
- `research/test_issue_174_nine_sleeve_backbone.py` (stdlib unittest)
- `research/test_issue_174_mirror.mjs` (executed Node mirror: ALL PASS)
- `research/issue_174_build.mjs`, `research/issue_174_map.mjs`,
  `research/issue_174_qa.mjs` (Node executors)
- `research/generated/issue-174/nine-sleeve-source-matrix.csv`
- `research/generated/issue-174/nine-sleeve-provenance.json`
- `research/generated/issue-174/nine-sleeve-monthly-returns.csv` (726 rows)
- `research/generated/issue-174/nine-sleeve-coverage.json`
- `research/generated/issue-174/state-month-counts.csv`
- `research/generated/issue-174/month-weighted-outcomes.csv`
- `research/generated/issue-174/episode-weighted-outcomes.csv`
- `research/generated/issue-174/era-stability.csv`
- `research/generated/issue-174/downside-danger.csv`
- `research/generated/issue-174/evidence-classification.csv`
- `research/generated/issue-174/future-zero-candidates.csv`
- `research/generated/issue-174/panel-comparison.json`
- `research/generated/issue-174/qa-validation.json`
- `research/generated/issue-174/summary.json`
- This finding.

## 10. Tests / validation evidence; bugs found and fixed

- Python stdlib suite (13 tests: bands/eras/returns/bond-duration/stats/
  episodes/classification/zero) — committed; no Python runtime on machine,
  every vector cross-checked via executed Node mirror (`test_issue_174_mirror.mjs`:
  ALL PASS, 12 assertions).
- Node build/map rerun determinism: evidence 62/10/9 and 2 zero-candidates
  identical across reruns; joined months 723; macro blob verified.
- Bugs fixed pre-final: (1) `tbM` vs `tb3` ReferenceError (caught on first
  build run); (2) 1966-03 cash/gold/long empty from missing prev-month window
  (fixed by building from 1966-02, filtering output to 1966-03+; coverage
  cash/gold 725→726, long 643→644); (3) QA month-key `ym+"-01"` mismatch
  zeroing all ETF overlaps (fixed to `ym`; correlations 0.76–0.999 recovered,
  gold 0.63 disclosed).

## 11. Explicit confirmations

- Frozen Deep-History boundaries unchanged; no asset-conditioned threshold,
  trajectory, or construction change.
- #166 10Y methodology unmodified (reuse verbatim; blob hashes recorded).
- No mean-variance / Sharpe / risk-parity / min-var / diversification / grid /
  dynamic / regime-optimizer / CAGR / MaxDD weight fitting of any kind.
- No weights forced >0; 0% remains possible via future policy.
- No production Pine changed.
- `production_authorized=false`.
- Do not merge.
