# Issue #174 — 9-sleeve Macro Asset Outcome Map — Preregistration (frozen)

- Issue: [#174](https://github.com/eddy121384-ui/tradingview-indicators/issues/174)
- Branch: `research/issue-174-nine-sleeve-macro-asset-map`
- Base (pre-prereg) HEAD: `f8eed2c5fa7086c0359a11360ce36cf33936afac` (Issue #171 final)
- This prereg is the FIRST Issue #174 commit on that branch.
- Status: PREREGISTRATION — frozen before any state-conditioned asset return is computed or viewed.
- `outcome_data_loaded=false` (at prereg commit; no macro x asset join exists)
- `production_authorized=false`
- `revised_macro_history=true`
- `real_time_vintage_claim=false`

## 0. Non-contamination attestation (ordering mandate)

This prereg is written from the CURRENT GitHub Issue #174 body plus the frozen
Deep-History lineage (#158/#160/#161/#166/#167/#169/#171) alone.

At the moment this file is committed:

- no 3x3 Growth x Inflation state-conditioned asset return has been computed;
- no state x asset table, episode-conditioned return, era-conditioned return,
  tail-conditioned return, or Cash-relative conditioned return has been viewed;
- only the frozen Issue #160 macro series has been read (coverage/columns only);
- only the frozen Issue #166 return files have been referenced by path/hash
  (their unconditional contents are already on record from Issue #166; no new
  conditional join has been formed);
- new-sleeve source feasibility was limited to transport checks
  (first/last observation, frequency, unit) with NO macro join and NO
  state-conditioned inspection.

Sequence (mandatory):

1. write this prereg;
2. commit it;
3. record the prereg commit SHA in the finding;
4. only then fetch/build new backbone files;
5. only then join macro x assets.

Any later change to any frozen quantity below requires a NEW issue.

## 1. Research lineage (frozen inputs — do not alter)

### 1.1 Macro source — Deep-History v0.1 (Issue #160)

- Frozen model commit: `cc331bf11591ab49c6f5a5023cfee39b2cf09fde`
- Frozen monthly macro CSV:
  `indicators/macro-pressure-map/research/generated/issue-160/deep-history-v01-monthly.csv`
- Frozen SHA256 (canonical git blob):
  `42516418ec8d1ce981d1b4bc05e2ae86809d6acbf5de63dccbad515db507dcfc`
  (Windows CRLF working-tree hash differs; evaluator MUST verify the git blob.)
- Columns used: `date`, `growth_dh` (=Growth_DH), `inflation_dh` (=Inflation_DH).
  Components `g1..g5`, `i1..i5` are NOT used.
- Observed macro coverage (macro only): both-axes-valid months = 723,
  first `1966-03-01`, last `2026-08-01`.
  Known frozen holes (macro-invalid): `2025-10-01`, `2025-11-01`, `2026-01-01`.
- Frozen usage: do NOT alter components, weights, axes, scaling, smoothing,
  thresholds, or trajectory. Do NOT use the #165 v0.2 turn layer.

### 1.2 Reused outcome backbone (Issue #166) — declared

- Issue #166 final: `9c7598bffaacda6d70264a83b42dca7e3a8dfb7e`
- Equity file:
  `indicators/macro-pressure-map/research/generated/issue-166/equity-monthly-total-returns.csv`
  (Fama-French US market monthly TR, `Mkt-RF+RF`, 202608 CRSP vintage;
  file SHA recorded in finding after prereg; methodology UNCHANGED.)
- Treasury file:
  `indicators/macro-pressure-map/research/generated/issue-166/treasury-monthly-total-returns.csv`
  (frozen synthetic ~10Y CMT coupon-inclusive monthly TR; methodology UNCHANGED.)
- Do NOT modify #166 methodology to improve rankings.

## 2. Frozen 3x3 Growth x Inflation state (PRIMARY)

For each macro-valid month `t`:

```
G_t = Growth_DH_t
I_t = Inflation_DH_t
```

Bands (inclusive to Neutral, identical both axes):

- Low: score < -10
- Neutral: -10 <= score <= +10
- High: score > +10

Nine states: `G_L/I_L`, `G_L/I_N`, `G_L/I_H`, `G_N/I_L`, `G_N/I_N`,
`G_N/I_H`, `G_H/I_L`, `G_H/I_N`, `G_H/I_H`
(shorthand e.g. `Low-Low`, `Neutral-High`).

A **state episode** = maximal run of consecutive calendar months in the same
3x3 state. A month belongs to the same episode only if the immediately
preceding calendar month was macro-valid AND in the same state. Frozen holes
break episodes. No minimum episode length.

Primary analysis = STATE. Trajectory (`d3G`, `d3I`) may be reported
descriptively only (counts/means by quadrant); it MUST NOT create a new
allocation rule, gate, or classification input in this issue.

## 3. Frozen 9-sleeve return semantics (Phase A)

Monthly frequency. Month label = first-of-month date `YYYY-MM-01` for the
calendar month whose return accrued during that month. All returns are decimal
(e.g. 0.01 = +1%). No annualization in stored backbone files.

| sleeve | exact definition | source | price/TR status | treatment | first return (expected) | eligibility prior |
|---|---|---|---|---|---|---|
| sp500 | US large-cap total return proxy = Fama-French US market monthly TR (`Mkt-RF+RF`), 202608 vintage; reuse #166 equity file verbatim | French Data Library (CRSP underlying) | TOTAL return (dividends included via CRSP holding-period) | dividends included; no coupon/carry/roll | 1960-01 (usable 1966-03) | eligible_primary w/ limitation (CRSP value-weight != S&P500 exactly; MAE ~2pp/yr vs Damodaran) |
| nasdaq | Nasdaq Composite price return = P_t/P_{t-1}-1 from FRED NASDAQCOM daily month-end last available close | FRED:NASDAQCOM (daily) | PRICE return (dividends excluded) | no dividend adj; USD; month-end last-available-daily sampling | 1971-03-01 | eligible_with_limitation (price-only; NOT technology sector) |
| russell | Russell 2000 price return = P_t/P_{t-1}-1 from Yahoo ^RUT monthly close | Yahoo ^RUT (Chicago Options, Russell 2000 index) | PRICE return (dividends excluded) | no dividend adj; USD; month-end sampling | 1987-10-01 | eligible_with_limitation (price-only; genuine history, no backfill, no IWM) |
| cash | 3M T-bill accrual proxy: cash_t = TB3MS_{t-1}/1200 where TB3MS is FRED monthly % p.a. | FRED:TB3MS (monthly) | TOTAL return (interest accrual) | simple accrual y/12; separate asset AND benchmark; NOT combined with 2Y | 1934-02-01 (usable 1966-03) | eligible_primary |
| treasury2y | synthetic ~2Y CMT coupon-inclusive TR (frozen formula S2 below) from FRED DGS2 daily month-end yields | FRED:DGS2 (daily) + frozen par-bond repricing | TOTAL return (coupon-inclusive) | semiannual coupons; dirty-price accrual; monthly roll; S2 | 1976-07-01 | eligible_primary (synthetic; validated vs SHY) |
| treasury10y | reuse #166 frozen synthetic ~10Y CMT TR verbatim | FRED DGS10 via #166 | TOTAL return (coupon-inclusive) | per #166; UNCHANGED | 1966-03-01 | eligible_primary |
| longtreasury | synthetic ~20Y CMT coupon-inclusive TR (frozen formula S20 below) from FRED DGS20 daily month-end yields | FRED:DGS20 (daily) + frozen par-bond repricing | TOTAL return (coupon-inclusive) | semiannual coupons; dirty-price accrual; monthly roll; S20 | 1962-02-01 (usable 1966-03) | eligible_primary w/ limitation (single-yield approx; DGS20 continuity disclosed) |
| gold | gold spot price return = P_t/P_{t-1}-1 from World Bank Pink Sheet monthly avg USD/oz (via datahub monthly.csv) | World Bank Commodity Price Data Pink Sheet (CC BY 4.0), mirror datahub.io/core/gold-prices | PRICE return (no coupon/div; economically complete for gold) | USD/oz; monthly-average convention; fixing continuity documented | 1960-02-01 (usable 1966-03) | eligible_primary w/ limitation (monthly-avg vs PM fix; pre-1971 fixed parity acknowledged) |
| oil | WTI spot price return = P_t/P_{t-1}-1 from FRED MCOILWTICO monthly | FRED:MCOILWTICO (monthly USD/bbl) | PRICE proxy ONLY | spot; NO roll/collateral; labeled `oil_price_proxy`; NOT investable futures TR; kept separate, never stitched | 1986-02-01 | eligible_with_limitation (short + spot-only) |

ETF QA ONLY (modern validation, never backbones): SPY, QQQ, IWM, SHY, IEF,
TLT, GLD, USO (Yahoo monthly adjclose-derived TR where applicable).

FORBIDDEN: SPY/QQQ/IWM/TLT/GLD/USO as deep history; price-as-TR without label;
yield-change-as-return; WTI-spot-as-futures-TR; silent stitching; backfilling
Nasdaq/Russell with modern constituents; common-start-date fabrication.

### 3.1 Frozen synthetic bond formulas (S2 / S20 — same structure as #166 S10)

For maturity M years (M=2 or M=20), month-end par yield y_t (decimal p.a.):

- Initiate M-year par bond at t: face 100, annual coupon c=100*y_t,
  semiannual payments c/2, N=2M coupons + principal.
- Hold one month (1/12 year). Reprice remaining M-1/12-year flows at single
  next-month yield y_{t+1} with fractional-period discounting: for coupon k
  (k=1..N) at time tau_k years from t+1 (tau = k/2 - 1/12), PV = (c/2)/(1+y_{t+1}/2)^{2*tau}
  with half-year compounding extended to fractional exponents; principal
  100 discounted at tau_N. Dirty price includes accrual (no double-counted
  coupon cash). One-month TR = PV_{t+1}/100 - 1. Roll into fresh par bond.
- Day count: 1/12-year steps. Single-yield curve approximation. Par-coupon
  simplification. Month-end timing = last available daily yield in calendar
  month. Missing month-end yield => return missing (no interpolation); zero
  month-skips expected (gaps reported, not filled).
- Cash has NO duration/repricing; 2Y/10Y/Long remain DISTINCT sleeves.

Validation (unconditional, no macro join): vs Damodaran annual T.Bond where
maturity-appropriate (10Y/Long), vs Yahoo SHY (2Y, 2002+), IEF (10Y), TLT
(Long) for sign/correlation sanity only (duration mismatch disclosed).

## 4. Frozen coverage rule (TWO views)

- Maximum-history view: each sleeve from its genuine first return through
  `2026-08-01`, joined to macro-valid months only. Do NOT backfill.
- Common-sample panels (deterministic, NOT tuned to results):
  - Core panel = intersection of sleeves with expected first return <=1976-07
    (sp500, cash, treasury10y, longtreasury, gold, treasury2y) => expected
    start 1976-07-01.
  - Full-universe panel = intersection of all 9 sleeves => expected start
    1987-10-01 (Russell binding).
  Actual starts recorded from built files; if a fetch shifts a start by <=2
  months, panels follow the ACTUAL intersection (rule unchanged).
- Do NOT truncate the study to the youngest asset as the only result.
- Macro holes excluded from every view.

## 5. Frozen eras (chosen BEFORE conditional results; do not move)

- E1 Pre-Volcker / inflationary history: `1966-03-01`–`1979-12-01`
- E2 Post-Volcker / Great Moderation: `1980-01-01`–`2007-12-01`
- E3 Post-GFC / QE era: `2008-01-01`–`2019-12-01`
- E4 Post-2020 regime: `2020-01-01`–`2026-08-01`

Era assignment by macro month `t`. Report per state x asset whether
sign/ranking is broadly persistent, mixed, or era-dependent. Do NOT require
identical magnitude.

## 6. Frozen month-weighted metrics (per state x asset)

For months where BOTH macro state and sleeve return exist:

- n_months
- mean monthly return (arithmetic)
- median monthly return
- compounded return: prod(1+r)-1 over those months; annualized =
  (prod(1+r))^(12/n)-1 where meaningful (n>=12 else N/A for ann)
- annualized volatility = biased std (ddof=0) of monthly r * sqrt(12)
- downside volatility = sqrt(mean(min(r,0)^2)) * sqrt(12) (target 0)
- positive-month fraction P(r>0)
- Cash excess: mean(r_sleeve - r_cash) monthly; compounded geometric excess =
  (1+R_s)/(1+R_c)-1; median excess; excess positive fraction P(excess>0)
- worst monthly return
- lower-tail metric (FROZEN): 10th percentile of monthly r (linear interpolation;
  NOT expected shortfall). Also report 10th percentile of monthly excess.
  Choice frozen here; ES is FORBIDDEN as substitute.

## 7. Frozen episode-weighted metrics (per state x asset)

Episodes per §2. For each episode compute sleeve compounded return
Rs_ep = prod(1+r)-1, cash compounded Rc_ep, geometric excess
Re_ep = (1+Rs_ep)/(1+Rc_ep)-1, duration in months.

- n_episodes
- mean episode compounded return (arithmetic mean of Rs_ep)
- median episode compounded return
- positive-episode fraction P(Rs_ep>0)
- Cash-relative: mean Re_ep; median Re_ep; positive-excess-episode fraction
  P(Re_ep>0)
- worst episode (min Rs_ep + its dates/duration)
- best episode (max Rs_ep + its dates/duration)
- duration distribution: min / median / mean / max months
- concentration: if sum of positive Rs_ep > 0 then
  concentration = max(Rs_ep) / sum_{ep:Rs_ep>0}(Rs_ep) else N/A.
  (Share of total episode gains in the single best episode.)

## 8. Frozen drawdown / danger metrics (per state x asset)

- worst monthly loss (min r)
- worst episode loss (min Rs_ep)
- max state-associated drawdown (FROZEN convention): within each state episode,
  cumulative return from episode start C_k = prod_{j<=k}(1+r_j)-1;
  episode drawdown = min_k(C_k) (trough from start, start=0 peak);
  reported value = min over episodes in that state (most negative).
- lower-tail loss = 10th percentile monthly (§6)
- P(underperform Cash) = P(monthly excess < 0)
- P(materially underperform Cash) monthly = P(monthly excess < -0.02)
  (-2.0pp, FROZEN) ; episode-material = P(Re_ep < -0.05) (-5.0pp, FROZEN).
  Thresholds frozen here before conditional results.

## 9. Frozen evidence-classification rules (deterministic; BEFORE conditional)

Inputs per state x asset (maximum-history view): n_m, n_e, mean_ex (mean
monthly sleeve-cash), pos_m_frac = P(excess>0 monthly), ep_hit =
P(Re_ep>0), p10_ex = 10th pct of monthly excess, worst_m = worst monthly
sleeve r, p_under = P(excess<0), era signs: mean_ex computed within each era
with >=12 months for that state x asset; persistent_positive = >=3 eras
evaluable and all evaluable mean_ex>0 (or >=3 positive where >=3 evaluable);
persistent_negative = mirror.

```
if n_m < 24 or n_e < 4:
    evidence = insufficient_sample
elif (mean_ex > 0.001
      and pos_m_frac >= 0.55
      and ep_hit >= 0.60
      and p10_ex >= -0.04
      and worst_m > -0.20
      and not persistent_negative):
    evidence = historically_favored
elif (mean_ex < -0.0005
      and (pos_m_frac <= 0.45 or ep_hit <= 0.40)
      and (p10_ex <= -0.03 or worst_m <= -0.10 or p_under >= 0.60)
      and not persistent_positive):
    evidence = historically_unfavorable
else:
    evidence = mixed
```

Uses excess + consistency + tail + era + sample. NOT mean alone. Labels are
evidence descriptors, NOT investment recommendations, NOT portfolio weights.

## 10. Frozen future-zero-weight-candidate rules (BEFORE conditional)

`future_zero_weight_candidate` is a boolean evidence flag, NOT a weight.
`true` requires ALL of:

1. eligibility in (eligible_primary, eligible_with_limitation);
2. evidence == historically_unfavorable (§9);
3. n_m >= 60 and n_e >= 6;
4. ep_hit <= 0.40 and mean_ex < 0;
5. tail/danger: (p10_ex <= -0.04) or (worst episode Rs_ep <= -0.15) or
   (P(monthly excess < -0.02) >= 0.10);
6. not persistent_positive (§9);
7. not single-episode-driven: mean_ex computed excluding the worst episode's
   months is still < 0.

Otherwise `false`. Do NOT set weights to zero here. Record any allocation
idea only as `future_allocation_policy_candidate` (text, untested).

## 11. Frozen eligibility gate (Phase A, BEFORE conditional interpretation)

Per sleeve: eligible_primary / eligible_with_limitation / qa_only /
not_eligible, based on return semantics + coverage + validation (unconditional
only). A sleeve may appear descriptively if limited but MUST NOT be treated
as equally reliable. If a sleeve fails, DO NOT fabricate it; continue with
valid sleeves. ETFs are qa_only by construction.

## 12. Frozen evaluator, outputs, and flags

Deliverables (all paths contain `issue-174`):

- `research/issue-174-nine-sleeve-map-prereg.md` (this file)
- `research/issue_174_nine_sleeve_backbone.py` (frozen pure-stdlib builders/metrics/classifiers)
- `research/test_issue_174_nine_sleeve_backbone.py` (stdlib unittest)
- `research/issue_174_build.mjs` + `research/issue_174_map.mjs` (Node fetch/build/map executors; Python has no runtime on this machine — every numeric vector cross-checked via Node)
- `research/generated/issue-174/nine-sleeve-source-matrix.csv`
- `research/generated/issue-174/nine-sleeve-provenance.json`
- `research/generated/issue-174/nine-sleeve-monthly-returns.csv` (backbone)
- `research/generated/issue-174/nine-sleeve-coverage.json`
- `research/generated/issue-174/state-month-counts.csv` (9 states: months/episodes)
- `research/generated/issue-174/month-weighted-outcomes.csv`
- `research/generated/issue-174/episode-weighted-outcomes.csv`
- `research/generated/issue-174/era-stability.csv`
- `research/generated/issue-174/downside-danger.csv`
- `research/generated/issue-174/evidence-classification.csv`
- `research/generated/issue-174/future-zero-candidates.csv`
- `research/generated/issue-174/panel-comparison.json` (max-history vs core vs full)
- `research/generated/issue-174/summary.json` (machine-readable)
- `research/decisions/issue-174-nine-sleeve-map-finding.md`

Evaluator MUST verify the macro git-blob SHA256 and the two #166 file hashes
before any join, abort on mismatch, record every source hash/URL/bytes,
never overwrite other issues' artifacts, never change Pine, never optimize
weights.

## 13. Anti-tuning firewall

After this prereg commit and the first conditional inspection, do NOT change:
macro thresholds/construction; trajectory use; sleeve definitions/sources;
synthetic formulas (S2/S20/cash); month-end conventions; state/episode rules;
eras; metric definitions; tail choice (10th pct); materiality thresholds
(-2pp/-5pp); classification or zero-candidate rules; panels rule; eligibility
mapping. Any such change requires a new issue. Forbidden: weight optimization
(any form), forcing weights >0, regime redefinition from returns, trajectory
horizon search, ETF substitution, price/TR conflation, yield-change-as-return,
spot-as-futures-TR, silent stitching, constituent backfill, dropping poor
periods/assets, altering #166 to improve rankings, production allocation rules,
merging.

## 14. Product boundary

Research only. This issue ends BEFORE allocation percentages. Even strong
evidence does NOT authorize production. Final finding MUST contain
`production_authorized=false`. Do not merge.
