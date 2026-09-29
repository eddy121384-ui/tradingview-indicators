# Issue #113 preregistration — sparse state-only Action Layer sizing gate

Status: **PREREGISTERED BEFORE ISSUE #113 PORTFOLIO RESULTS**

## Frozen upstream state map

Only Issue #109 A1 stable candidates may act:

- Regime 8 — Growth Slowdown / Stable Inflation:
  - SPY +5pp / TLT -5pp
  - GLD +5pp / SHV -5pp
- Regime 7 — Slowdown / Disinflation:
  - GLD +5pp / SHV -5pp
- Regime 9 — Stagflation Pressure:
  - GLD +5pp / SHV -5pp
- Regimes 1–6:
  - no view

Trajectory, FCPI, Duration-vs-Cash, and broad commodities are excluded.

## Frozen target weights

Neutral C0:

- SPY 0.40
- TLT 0.40
- GLD 0.10
- SHV 0.10

Action Layer target:

- regime 8: SPY 0.45 / TLT 0.35 / GLD 0.15 / SHV 0.05
- regime 7 or 9: SPY 0.40 / TLT 0.40 / GLD 0.15 / SHV 0.05
- regimes 1–6: C0 weights

No leverage, shorts, or +/-2 tier.

## Frozen data

Reuse only committed/hash-frozen research inputs:

- Issue #64 SPY/TLT/GLD adjusted-price snapshot:
  - CSV SHA-256 `3a7f590c146f9eda5920b6968fe86c9c3cc1887db35597f2d639a1c76b6e5a57`
- Issue #109 SHV/GSG adjusted-price snapshot:
  - CSV SHA-256 `7dbfe3cff58be172098aa09b9c86fd70a23672834f5829e4b650c94cf72d6833`
  - only SHV is used in Issue #113
- Issue #64 exact V6.6 transition history:
  - CSV SHA-256 `80446bbcb91be8b18eb0b95e62466edf892e4c04087696a04532f0fe214698af`
  - signal cutoff 2026-08-14

Primary price calendar is the strict common finite SPY/TLT/GLD/SHV calendar.

No live data.

## Monthly timing

1. identify the first common eligible trading row in each calendar month;
2. use the frozen V6.6 state on the previous common eligible trading row;
3. set the target weights at the monthly origin;
4. compute asset returns from that origin to the next monthly origin;
5. exclude the final origin if the next monthly origin is unavailable;
6. do not forward-fill the state after the frozen signal cutoff.

This is a monthly target-weight backtest. Asset weights are treated as reset to the target vector at each monthly origin for return calculation.

## Turnover and transaction costs

Turnover is **tactical target turnover only**, exactly:

`turnover_t = 0.5 * sum(abs(target_w_t - target_w_t-1))`

It deliberately does not add drift-rebalancing turnover from the neutral portfolio.

Primary cost:

`cost_t = turnover_t * 0.0005`

Primary Action Layer return:

`R_AL_net,t = dot(target_w_t, asset_return_t) - cost_t`

C0 and C1 have constant target vectors and therefore zero tactical target turnover after initialization. Initial portfolio establishment cost is excluded for all portfolios.

Diagnostics only:

- 0bp tactical cost
- 10bp tactical cost

No cost assumption may be changed after inspection.

## C1 exposure-matched static control

C1 weights equal the arithmetic average of all monthly Action Layer target weights over the full eligible sample.

C1 uses that one constant target vector in every month.

C1 is descriptive only because its weights use realized full-sample exposure.

The Action Layer is considered **not explained solely by average-exposure drift** only if both:

- Action Layer net CAGR > C1 CAGR; and
- Action Layer net Sharpe > C1 Sharpe.

No tolerance or post-hoc exception.

## Monthly portfolio metrics

For each return stream:

- cumulative wealth = cumulative product of `1 + monthly_return`
- CAGR = terminal wealth ^ (12 / n_months) - 1
- annualized volatility = sample std(monthly return) * sqrt(12)
- Sharpe = mean(monthly portfolio return - monthly SHV return) / sample std(monthly portfolio return - monthly SHV return) * sqrt(12)
- max drawdown = minimum of wealth / running_max(wealth) - 1
- Calmar = CAGR / abs(max drawdown)
- annualized tactical turnover = mean(monthly tactical turnover) * 12
- total tactical cost = sum(monthly tactical cost)
- annualized cost drag = gross CAGR - net CAGR

For C0/C1, tactical turnover and tactical cost are zero.

## Temporal segments

By monthly origin:

- pre-2020: origin < 2020-01-01
- 2020–2022: 2020-01-01 through 2022-12-31
- 2023+: origin >= 2023-01-01

Each segment metric restarts wealth at 1.0.

If any segment has fewer than 24 completed monthly observations, final verdict is
`inconclusive_insufficient_sample`.

## Active overlay episodes

An active episode is a consecutive run of monthly origins with the **same non-neutral target weight vector**.

This is target-vector based, not regime-label based. Therefore regimes 7 and 9 are the same episode type if they occur in consecutive eligible months without a target-vector change.

Episode contribution:

`sum(ActionLayer_net_monthly_return - C0_monthly_return)`

The strongest positive-contribution active episode is the episode with the largest positive value above.

Top-positive share:

`strongest_positive_episode_contribution / sum(all positive active episode contributions)`

## Episode leaveout

For the strongest positive episode:

- revert its target weights to C0 for every month in that episode;
- recompute target turnover across the full sample, including entry/exit boundaries;
- recompute 5bp net monthly returns and full-sample metrics.

Gate condition:

`leaveout Action Layer CAGR - C0 CAGR > 0`

No alternative leaveout rule.

## Sleeve attribution

Diagnostic gross monthly contribution relative to C0:

Equity-duration sleeve:
- only regime 8
- `0.05 * (SPY_return - TLT_return)`

Gold-cash sleeve:
- regimes 7/8/9
- `0.05 * (GLD_return - SHV_return)`

Transaction costs are reported separately and not allocated to sleeves.

Attribution cannot change the frozen map.

## Production gate

Using the 5bp primary net Action Layer result, all must pass:

1. full-sample CAGR advantage vs C0 >= +0.0025
2. full-sample Sharpe advantage vs C0 >= +0.05
3. max drawdown difference `AL - C0 >= -0.015`
4. at least 2 of 3 temporal segments have positive CAGR advantage
5. minimum temporal CAGR advantage >= -0.005
6. strongest-positive-episode leaveout CAGR advantage > 0
7. Action Layer CAGR > C1 CAGR **and** Action Layer Sharpe > C1 Sharpe

## Deterministic verdict

- if any temporal segment has <24 completed months:
  `inconclusive_insufficient_sample`
- else if all seven production gates pass:
  `production_action_layer_candidate`
- else if full-sample Action Layer net CAGR advantage vs C0 > 0:
  `economically_positive_but_not_robust_enough`
- else:
  `no_material_production_value`

No discretionary override.

## Forbidden rescue paths

Do not:

- change 5pp tilt size;
- add +/-2;
- optimize base weights;
- change transaction costs;
- add Reflation;
- add Duration-vs-Cash;
- add commodities;
- add trajectory;
- add FCPI;
- change monthly frequency;
- redefine episode contribution;
- change C1 criterion;
- alter the production gate after results.

No Issue #113 portfolio result had been viewed when this document was committed.
