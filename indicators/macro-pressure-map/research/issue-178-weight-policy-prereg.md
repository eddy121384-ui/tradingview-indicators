# Issue #178 — 9-sleeve state weight policy — Preregistration (frozen)

- Issue: [#178](https://github.com/eddy121384-ui/tradingview-indicators/issues/178)
- Branch: `research/issue-178-state-weight-policy`
- Base (pre-prereg) HEAD: `bc652bd615f2c5e9137050d01c666dbcd9528cd3` (Issue #177 final)
- This prereg is the FIRST Issue #178 research commit on this branch.
- Status: PREREGISTRATION — frozen before any state weight is generated and
  before any portfolio backtest result is viewed.
- `outcome_data_loaded=false` (at prereg commit; no weight matrix, no backtest)
- `production_authorized=false`
- `revised_macro_history=true`
- `real_time_vintage_claim=false`

## 0. Non-contamination attestation (ordering mandate)

The CURRENT GitHub Issue #178 body was read in full via webfetch
(authoritative; no cached copy). Issue #177 final artifacts were read as
policy INPUTS only (frozen tiers, zero cells, cash-bias labels, verdict
`state_allocation_policy_candidate_complete_with_limitations`). No portfolio
percentage was computed and no backtest was run before this commit.

Frozen Issue #177 inputs (verified present, byte-frozen at build time):
`generated/issue-177/policy-matrix.csv` (72 non-cash cells: 10 High /
42 Neutral / 17 Low / 3 Zero; zeros: Low-Low Oil, Neutral-High Russell,
High-Low Gold), `cash-bias.csv` (scores: LL 9/low, LN 7/neutral, LH 3/high,
NL 11/low, NN 7/neutral, NH 3/high, HL 6/neutral, HN 8/neutral, HH 5/neutral).

Sequence (mandatory):

1. read Issue #178;
2. read Issue #177 final artifacts as frozen inputs;
3. freeze §§1–11 below;
4. commit this prereg;
5. record prereg SHA;
6. ONLY THEN generate weights;
7. ONLY THEN run backtests.

Any later parameter change requires a NEW issue.

## 1. Neutral strategic baseline (PRIMARY — frozen)

One generic balanced macro portfolio (NOT user-personalized). Sums to 100%.
Chosen for simplicity and portfolio role; NOT on backtest performance
(no performance has been viewed).

| sleeve | baseline % | family | family % |
|---|---|---|---|
| S&P 500 | 25 | Equity | 45 |
| Nasdaq | 12 | Equity | 45 |
| Russell 2000 | 8 | Equity | 45 |
| 2Y Treasury | 8 | Rates | 30 |
| 10Y Treasury | 14 | Rates | 30 |
| Long Treasury | 8 | Rates | 30 |
| Gold | 6 | Real Assets | 10 |
| Oil | 4 | Real Assets | 10 |
| Cash | 15 | Cash | 15 |

Rationale: equity-led balance; S&P core, Nasdaq growth satellite, Russell
small-cap tilt; 10Y duration anchor, 2Y buffer, Long diversifier (capped);
Gold strategic diversifier 6%, Oil small tactical sleeve 4% (NOT equal-weighted:
equal 9-way would give Gold+Oil 22.2% — the failure mode the issue warns about);
Cash 15% strategic reserve. Static-neutral benchmark = this baseline,
rebalanced monthly.

## 2. Tier multipliers (PRIMARY — frozen)

- 0 = 0.0x exactly
- Low = 0.5x
- Neutral = 1.0x
- High = 1.75x

Monotonic 0 < Low < Neutral < High. Chosen for round, hand-explainable spread
(halve / keep / near-double). NOT tuned (no performance viewed).

## 3. Caps / floors (frozen, economically motivated, NOT tuned)

Sleeve max: S&P 35, Nasdaq 20, Russell 15, 2Y 15, 10Y 25, Long 15, Gold 12,
Oil 8 (all %). Single-name concentration guard; Gold/Oil kept small because
they are satellite diversifiers; Long capped on duration risk.
Family max: Equity 60, Rates 50, Real Assets 15.
Cash: min 2% (always some liquidity), max 60% (policy stays invested).
No sleeve negative. No leverage. 0% always allowed (multiplier 0 bypasses caps).

## 4. Cash rule (frozen)

Frozen #177 cash_bias → minimum residual Cash: low → 5%, neutral → 10%,
high → 20%. Cash max 60% always. Cash absorbs the residual to 100%.

## 5. Normalization algorithm (frozen exact ordering)

For a state, over AVAILABLE non-cash sleeves only (see §7):

1. raw[s] = baseline[s] × mult[tier[s]] (tier-0 sleeves = 0, skipped below).
2. Sleeve caps: w[s] = min(raw[s], cap[s]); record binds.
3. Family caps: if family sum > cap, scale that family's sleeves pro-rata
   to the cap (one pass, fixed family order Equity→Rates→Real Assets for
   reporting only; scaling is independent per family).
4. S = Σ w. cash_raw = 100 − S. min_c = bias→min (§4), max_c = 60.
5. If cash_raw < min_c: scale all non-cash w by (100−min_c)/S; cash = min_c.
   Elif cash_raw > max_c: scale all non-cash w by (100−max_c)/S; cash = max_c.
   Else cash = cash_raw.
6. Re-apply sleeve caps (shave only); any shaved remainder goes to Cash.
7. Round to 2 decimals with largest-remainder (tier-0 sleeves excluded from
   remainder allocation); rows must total exactly 100.00%.
8. Audit: assert every cap/floor, cash bounds, 100.00 total, zeros intact.

No state-specific exceptions. Cap binds reported per state.

## 6. Rebalance rule (PRIMARY — frozen)

Rule B-2 (confirmation): a new state's weights apply starting from its
SECOND consecutive completed month; during the first month of a state,
hold the previous allocation. The guard controls IMPLEMENTATION only; it
never redefines the macro state.
Timing (no lookahead): month-m return uses the allocation confirmed with
states through month m−1 close. Backtest starts 1966-05-01 (needs
state(1966-03), state(1966-04) for the first confirmation).
Turnover metric (frozen): monthly one-way turnover =
0.5 × Σ_sleeves |w_target(new) − w_target(old)| at switch months, else 0
(target-based, no drift modeling, zero transaction costs — costs frozen at 0).

## 7. Missing-data treatment (frozen)

Return series used (hardened semantics): S&P = #176 hardened recon
(1966-03–2023-06), then French broad-market TR fallback for 2023-07–2026-08
(38 months, explicitly flagged — the exact superseded series, corr 0.989,
no fabrication); Nasdaq FRED price 1971-03+; Russell ^RUT 1987-10+;
Cash/TB3MS; 2Y synth 1976-07+; 10Y frozen; Long synth (82-mo 1987–93 gap);
Gold; Oil = investable CL=F+collateral 2000-09+ (spot NEVER used as exposure;
pre-2000-09 oil months EXCLUDE oil).
Rule: a sleeve with no return in month m is EXCLUDED that month (weight 0,
algorithm §§5 runs over available sleeves, caps unchanged, Cash absorbs).
Panels: maximum-history (1966-05 start, dynamic availability) AND
full-universe (2000-09–2023-06, all used sleeves genuinely present).
No ETF history used for missing months. No silent redistribution.

## 8. Benchmarks (frozen before evaluation)

1. Static Neutral (§1), rebalanced monthly. 2. Cash 100%. 3. Broad U.S.
equity 100% (French market TR — longest genuine history). 4. Balanced 60/40
(60% French market + 40% frozen 10Y synthetic, monthly rebalanced). No weak
benchmarks invented post hoc; no benchmark weights optimized.

## 9. Metrics (frozen set)

CAGR, annualized vol (biased-sd monthly × √12), Cash excess (annualized),
Sharpe-like = ann(mean monthly excess over Cash) / ann(std monthly excess),
MaxDD on cumulative total-return index, worst month, positive-month fraction,
average Cash/family weights, turnover (monthly one-way mean ×12 annualized,
total switches, state-changes vs allocation-changes, avg weight change per
rebalance), reallocations count, avg months between changes, time per state,
per-state portfolio return, era (E1–E4 frozen bounds) policy-vs-baseline.

## 10. Sensitivity set (frozen, max 3, run separately, primary never replaced)

- S1: alternate neutral baseline — Equity 55 / Rates 25 / Real 8 / Cash 12
  (S&P 30, Nas 15, Rus 10, 2Y 6, 10Y 12, Long 7, Gold 5, Oil 3).
- S2: alternate multipliers — 0x / 0.25x / 1.0x / 2.0x.
- S3: alternate rebalance — immediate monthly (no confirmation).
Report stability only. No grid search. No best-case promotion.

## 11. Deliverables (all paths contain `issue-178`)

- `research/issue-178-weight-policy-prereg.md` (this file)
- `research/issue_178_policy.py` (frozen stdlib: baseline/mult/cap/cash/normalize/rebalance/metrics)
- `research/test_issue_178_policy.py` (+ executed Node mirror test)
- `research/issue_178_build.mjs` (matrix + audit + SHA pins)
- `research/issue_178_backtest.mjs` (panels, metrics, benchmarks, turnover, eras, sensitivity)
- `research/generated/issue-178/weight-matrix.csv` (9×9 percentages)
- `research/generated/issue-178/state-cards.md`
- `research/generated/issue-178/backtest-monthly.csv`
- `research/generated/issue-178/performance.json`
- `research/generated/issue-178/benchmarks.json`
- `research/generated/issue-178/turnover.json`
- `research/generated/issue-178/era-report.json`
- `research/generated/issue-178/sensitivity.json`
- `research/generated/issue-178/policy.json` (machine-readable policy artifact)
- `research/generated/issue-178/summary.json`
- `research/decisions/issue-178-state-weight-policy-finding.md`

Builder MUST pin frozen input SHAs, reproduce #177 tiers/zeros/cash-bias
exactly (0 mismatches) before emitting weights, never overwrite other
issues' artifacts, never touch Pine, never optimize.

## 12. Firewall

After this prereg commit and the first backtest inspection, do NOT change:
baseline, multipliers, caps, cash rule, normalization order, rebalance rule,
benchmarks, sensitivity set, missing-data rule, #177 tiers/zeros, macro
states/thresholds. Poor performance is REPORTED, never tuned. New issues only.
Forbidden: optimizers (any), percentages-to-tiers reverse-fitting, leverage,
shorts, trajectory, V6.6 overlays, hidden overrides, Pine changes, merging.

## 13. Product boundary

Research policy candidate only. Verdict ∈
(`state_weight_policy_candidate_complete`,
`state_weight_policy_candidate_complete_with_limitations`,
`state_weight_policy_not_ready`).
Finding MUST contain `production_authorized=false`. Do not merge.
