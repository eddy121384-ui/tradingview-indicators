# Issue #180 — Tradable implementation reality check — Preregistration (frozen)

- Issue: [#180](https://github.com/eddy121384-ui/tradingview-indicators/issues/180)
- Branch: `research/issue-180-tradable-implementation-reality-check`
- Base (pre-prereg) HEAD: `10dcdce0ec86b0493d6df6b916b720eba46dcbe6` (#178 final)
- This prereg is the FIRST Issue #180 research commit on this branch.
- Status: PREREGISTRATION — frozen before any implementation-adjusted
  portfolio result is viewed.
- `outcome_data_loaded=false` (at prereg commit; no implementation backtest)
- `production_authorized=false`
- `revised_macro_history=true`
- `real_time_vintage_claim=false`

## 0. Non-contamination attestation (ordering mandate)

The CURRENT GitHub Issue #180 body was read in full via webfetch
(authoritative; no cached copy). Issue #178 final artifacts were read as
frozen POLICY inputs only (weight matrix, policy.json, backtest mechanics,
performance baselines). Pre-prereg work was limited to UNCONDITIONAL proxy
feasibility (Yahoo monthly availability per ticker, inception dates, expense
ratio documentation). No implementation-adjusted portfolio return was computed
or viewed. Proxy choice below rests on semantics/liquidity/history, never on
portfolio performance (unseen at this commit).

Sequence (mandatory):

1. read Issue #180;
2. read #178 final artifacts as frozen inputs;
3. audit proxy availability (unconditional only);
4. freeze §§1–12 below;
5. commit this prereg;
6. record prereg SHA;
7. ONLY THEN build implementation returns, tracking study, backtests.

Any later parameter change requires a NEW issue.

## 1. Frozen primary implementation map (all-ETF for uniformity)

Returns = Yahoo monthly ADJCLOSE-derived total returns (net of fund expenses
by construction; no separate ER subtraction — documented, not double-counted).
Month label = first-of-month for the calendar month whose return accrued.
No backfill before a fund's genuine first monthly bar.

| sleeve | research concept | primary proxy | inception (first bar) | ER (doc only) | type |
|---|---|---|---|---|---|
| sp500 | S&P 500 TR | SPY | 1993-01 | 0.0945% | ETF |
| nasdaq | Nasdaq Composite (price/TR) | QQQ, LABELED Nasdaq-100 proxy (issue option 2) | 1999-03 | 0.20% | ETF |
| russell | Russell 2000 price | IWM | 2000-05 | 0.19% | ETF |
| cash | 3M T-bill accrual | IDENTICAL T-bill series (no tracking diff) | 1934+ | — | bills |
| treasury2y | synth 2Y CMT TR | SHY | 2002-07 | 0.15% | ETF |
| treasury10y | synth 10Y CMT TR | IEF | 2002-07 | 0.15% | ETF |
| longtreasury | synth 20Y CMT TR | TLT | 2002-07 | 0.15% | ETF |
| gold | Pink Sheet price | GLD | 2004-11 | 0.40% | ETF |
| oil | investable CL+collateral | USO (front-month WTI fund; 2020 ladder shift disclosed) | 2006-04 | 0.60% | commodity pool |

Alternate (sensitivity only): ONEQ genuine Nasdaq Composite ETF (2003-10+,
ER 0.21%) for the Nasdaq sleeve. No other alternates. No futures implementation
(Yahoo continuous roll opaque; ETF set is uniform, transparent, reproducible).

## 2. Nasdaq special rule (frozen choice: issue option 2)

Primary QQQ is Nasdaq-100, NOT Nasdaq Composite. It is NEVER renamed.
Tracking study quantifies QQQ vs Composite price AND vs official TR (^XCMP
2003+). Classification expected `implementation_acceptable_with_limitation`
pending frozen rules; mismatch stays visible in every artifact.

## 3. Oil special rule (frozen)

Investable economics preserved: USO holds near-month WTI futures (laddered
since Apr-2020 prospectus leeway), ER 0.60%, commodities-pool structure.
Documented vs #176 investable sleeve (CL excess + TB3MS collateral): fee drag,
roll-calendar differences, 2020 regime shift. NO spot substitution anywhere.

## 4. Cost model (PRIMARY — frozen)

ETF adjclose returns are NET of expenses; no ER layer is added.
cost[m] = oneway_turnover[m] × 0.0002 (2bp per 100% one-way turnover),
one-way turnover = 0.5 × Σ_sleeves |w_target(new) − w_target(old)| at switch
months (frozen #178 target-based definition), else 0. post-cost[m] =
pre-cost[m] − cost[m]. Conservative, deterministic, disclosed. Turnover (hence
cost timing) is IDENTICAL to research by construction (same weights/timeline).
Alternate cost scenario (sensitivity only): rate 0.0010 (10bp).

## 5. Execution timing (PRIMARY — frozen)

Month-end close execution: allocation confirmed through month m−1 close
(frozen B-2) is filled at the m−1 close and earns month-m proxy returns.
No look-ahead (identical timing to #178 research). Alternate execution
(sensitivity only): 1-month implementation lag (confirmed allocation effective
one month later — conservative bound; monthly granularity cannot resolve
next-session effects honestly).

## 6. Missing-history treatment (frozen)

Proxy unavailable in month m → sleeve EXCLUDED that month (weight 0 via the
frozen §7-style exclusion; same caps; Cash absorbs). No backfill. Panels:
(A) research-backbone history 1966-05+; (B/C) tradable from first month all
primary proxies have genuine returns; STRICT full-implementation panel starts
2006-06-01 (USO binds; requires two full monthly bars per proxy; assert 0
drops, else STOP and report). Partial-sleeve overlaps reported as QA only.

## 7. Benchmarks (frozen, same cost/timing framework)

Static Neutral (ETF basket, same proxies/costs), Cash 100%, broad equity
(SPY TR), 60/40 (SPY/IEF, monthly rebalanced). Static targets → zero turnover
→ zero turnover cost; ETF returns net of ER as usual. No post-hoc benchmarks.

## 8. Tracking study + classification rules (frozen; unconditional)

Per sleeve over genuine overlap: n, corr, mean monthly diff, ann ret diff,
ann vol diff, tracking-error vol (std(diff)×√12), worst monthly diff, cum
ratio, top disagreement months, structural reason. Classification (applied
after computation, thresholds frozen here):
- `implementation_faithful`: overlap ≥120mo AND |ann ret diff| ≤0.5pp AND
  TE ≤1.5% AND corr ≥0.99 AND no unresolved semantic mismatch.
- `implementation_acceptable_with_limitation`: overlap ≥60mo AND corr ≥0.95
  AND TE ≤4% (mismatch labeled where present).
- `implementation_materially_different`: corr <0.95 OR TE >4%.
- `implementation_not_ready`: overlap <60mo.
Cash (identical series) → faithful by construction, documented.

## 9. Preservation + pass/fail decision rules (frozen; evaluated on strict panel)

Preserved (`tradable_implementation_candidate_complete`) iff ALL hold
(B vs A, post-cost unless noted): |CAGR gap| ≤1.0pp/yr; TE ≤2.5%/yr;
MaxDD gap ≥ −5pp; cost drag ≤0.4%/yr; best/worst state rank unchanged;
no high-cash-bias state vol worse by >2pp.
`..._complete_with_limitations`: ≤2 fail and none is unresolved-semantic or
TE>4%. `..._not_ready`: any not_ready sleeve >10% weight in any state, or
TE>4% with drag>1%/yr, or 3+ fails incl. semantic. Report all six gauges
regardless of verdict. Thresholds never move post-result.

## 10. Metrics/report set (frozen)

Sleeve tracking table; A/B/C portfolio metrics (CAGR, vol, Cash excess,
Sharpe-like, MaxDD, worst month, pos frac, turnover, cost drag ann +
cumulative, reallocations, avg Cash/family weights); preservation audit
(corr, TE, gaps, |diff|>1pp fraction, largest months, state-rank stability,
defensive-state risk); 9-state implementation table; era split (frozen E1–E4;
tradable-live eras reported separately); benchmarks; sensitivity (ONEQ /
10bp costs / 1-mo lag — descriptive only, primary never replaced).

## 11. Deliverables (all paths contain `issue-180`)

- `research/issue-180-implementation-prereg.md` (this file)
- `research/issue_180_policy.py` (frozen stdlib: costs/timing/tracking/classify/decision primitives)
- `research/test_issue_180_policy.py` (+ executed Node mirror test)
- `research/issue_180_build.mjs` (proxy fetch + tracking study + audit)
- `research/issue_180_backtest.mjs` (A/B/C, preservation, state/era/benchmarks/sensitivity)
- `research/generated/issue-180/proxy-map.csv`
- `research/generated/issue-180/tracking.csv`
- `research/generated/issue-180/implementation-monthly.csv`
- `research/generated/issue-180/performance.json`
- `research/generated/issue-180/preservation.json`
- `research/generated/issue-180/state-implementation.csv`
- `research/generated/issue-180/era-live.json`
- `research/generated/issue-180/benchmarks.json`
- `research/generated/issue-180/sensitivity.json`
- `research/generated/issue-180/policy.json`
- `research/generated/issue-180/summary.json`
- `research/decisions/issue-180-tradable-implementation-finding.md`

Builders MUST pin frozen input SHAs (#178 weight-matrix/policy.json,
backbone returns, macro states), reproduce #178 research series A exactly
(0 mismatches) before interpreting B/C, never overwrite other issues'
artifacts, never touch Pine, never optimize.

## 12. Firewall

After this prereg commit and the first implementation result, do NOT change:
proxies, return construction, costs, timing, missing-data rule, benchmarks,
classification/decision thresholds, #178 weights, #177 tiers/zeros, macro
states/thresholds, B-2. Worse-than-expected implementation is REPORTED, never
repaired here. Forbidden: optimizers, weight/cap/parameter tuning, trajectory,
V6.6, leverage, shorts, backfilled ETF history, QQQ-renaming, spot oil,
hidden costs/turnover, Pine changes, merging.

## 13. Product boundary

Research implementation candidate only. Verdict ∈
(`tradable_implementation_candidate_complete`,
`tradable_implementation_candidate_complete_with_limitations`,
`tradable_implementation_not_ready`).
Finding MUST contain `production_authorized=false`. Do not merge.
