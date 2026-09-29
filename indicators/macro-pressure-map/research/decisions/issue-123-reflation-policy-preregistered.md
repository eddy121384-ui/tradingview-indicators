# Issue #123 preregistration — Reflation Equity > Treasury Phase 2 policy rematch

Status: **PREREGISTERED BEFORE ISSUE #123 POLICY PERFORMANCE RESULTS**

## Role

Issue #121 already selected exactly one long-history revived pairwise mapping:

> Reflation / Inflation Rising -> Equity > Treasury

Issue #123 tests only whether that already-known relative relationship survives a minimal fixed portfolio translation.

This is an implementation / policy robustness test, not untouched discovery.

## Frozen data backbone

Reuse the frozen Issue #91 pipeline exactly:

- HMRA-v0.1 states
- Damodaran annual S&P 500 total returns
- Damodaran annual 10Y Treasury total returns
- Damodaran annual 3M T-bill returns
- strict-causal state_t -> full-calendar-year return_t+2 timing

All source and HMRA freeze validators must pass before policy calculation.

No ETF data.

## C0 neutral sleeve

Every eligible return year:

- Equity 0.50
- Treasury 0.50

## Action target

If signal state_t is exactly:

Reflation / Inflation Rising

then for return year t+2:

- Equity 0.55
- Treasury 0.45

Otherwise:

- Equity 0.50
- Treasury 0.50

No other state gets any tilt.

No leverage.
No shorts.
No Gold.
No Cash allocation.
No Commodities.
No second tilt size.

## Tactical turnover and cost

For annual target vectors:

turnover_t = 0.5 * sum(abs(target_w_t - target_w_t-1))

Initial target establishment cost is excluded.

Primary cost:

turnover_t * 0.0005

This is 5bp one-way per dollar of tactical target turnover.

Common annual rebalancing / drift turnover of the 50/50 base is excluded from both Action and C0.

## Annual portfolio returns

Before tactical cost:

Action gross return =
w_equity * equity_return + w_treasury * treasury_return

Action net return =
Action gross return - tactical_cost

C0 =
0.50 * equity_return + 0.50 * treasury_return

C1 exposure-matched static:
- arithmetic mean of Action target weights across all eligible years
- same fixed weights used every year
- no tactical target-turnover cost

## Metrics

For Action, C0, and C1 report:

- number of annual return observations
- CAGR = terminal wealth^(1/n) - 1
- arithmetic mean annual return
- sample annual volatility
- Sharpe versus annual T-bill return:
  mean(portfolio_return - cash_return) / sample_std(portfolio_return - cash_return)
- year-end max drawdown from cumulative annual wealth
- Calmar = CAGR / abs(max drawdown), if defined
- terminal wealth

Action additionally reports:
- annualized tactical target turnover = mean annual turnover
- cumulative tactical cost = sum annual tactical cost

No intra-year drawdown claim is permitted.

## Broad temporal validation

Assign by signal state year t:

1. 1928–1945
2. 1946–1979
3. 1980–1999
4. 2000–2023

Each broad era is evaluable when it contains >=8 eligible causal policy rows.

For each era:
- subset rows by signal year
- restart wealth at 1.0
- treat the first target in the segment as initial establishment, so first-row tactical turnover/cost = 0
- compute Action, C0, and C1 metrics
- report Action-minus-C0 CAGR and Sharpe differences

Required:
- >=3 evaluable eras
- >=3 evaluable eras have positive Action-minus-C0 CAGR
- no evaluable era CAGR disadvantage < -0.0025

Era boundaries are frozen before outcome inspection.

## Fine-era leave-one-out

Reuse the original Issue #91 fine-era label attached to signal year t.

A fine era is evaluable for this diagnostic only if it contains at least one active 55/45 Reflation target.

For each evaluable fine era:
- revert every Action target whose signal year belongs to that era to 50/50
- recompute tactical turnover over the entire full-sample path, including entry/exit boundaries
- recompute full-sample policy metrics

Required:
- every evaluable fine-era leaveout has Action CAGR > C0 CAGR

Do not select favorable eras.

## Active episodes

An active episode is a consecutive run of return years whose target is 55/45.

Episode gross contribution is:

sum(0.05 * (equity_return - treasury_return))

over active years in that episode.

Use gross contribution only to identify / rank episodes.

Report:
- episode start/end return year
- signal-year start/end
- active years
- gross contribution
- strongest positive episode share =
  strongest positive contribution / sum(all positive episode contributions)

Primary leaveout:
- identify strongest positive episode
- revert that whole episode to 50/50
- recompute the complete full-sample target path, tactical turnover, costs, and metrics

Required:
- leaveout Action CAGR > C0 CAGR
- strongest positive episode share <=0.50

## Exposure-matched C1 gate

Action must beat C1 on both:
- CAGR
- Sharpe versus T-bill

C1 is descriptive full-sample exposure control, not deployable OOS.

## Ten-part candidate gate

All must pass:

1. Action CAGR > C0 CAGR
2. Action Sharpe > C0 Sharpe
3. Action max-drawdown difference vs C0 >= -0.010
4. >=3 broad eras evaluable
5. >=3 evaluable broad eras have positive CAGR advantage
6. no evaluable broad-era CAGR disadvantage < -0.0025
7. strongest-positive-episode leaveout CAGR advantage >0
8. strongest positive episode share <=0.50
9. Action beats C1 on both CAGR and Sharpe
10. every evaluable fine-era leaveout retains positive CAGR advantage vs C0

## Deterministic verdict

- if fewer than 3 broad eras are evaluable:
  `inconclusive_policy_sample`
- else if all ten gates pass:
  `long_history_reflation_policy_candidate`
- else if Action full-sample CAGR > C0 CAGR:
  `economically_positive_but_policy_robustness_failed`
- else:
  `no_material_policy_value`

No discretionary override.

## Interpretation boundary

A full pass would mean:

> The frozen long-history HMRA Reflation analogue supports a minimal 5pp Equity-over-Treasury sleeve tilt as a portfolio-policy candidate.

It would not prove:
- exact V6.6 Reflation is identical to HMRA Reflation
- 5pp is optimal
- production trading is authorized

Production authorization remains false in Issue #123 regardless of verdict.

## Forbidden rescue paths

Do not:
- change 5pp
- change 50/50 base
- add Disinflationary Drift
- add any other state
- change t+2 timing
- add Gold / Cash / Commodity sleeves
- optimize transaction costs
- optimize era boundaries
- weaken exposure-control gate
- weaken leaveout gates
- add alternate weighting after seeing results

No Issue #123 policy performance result had been computed when this file was committed.
