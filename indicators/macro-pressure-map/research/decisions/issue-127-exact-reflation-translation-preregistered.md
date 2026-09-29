# Issue #127 preregistration — exact V6.6 Reflation production translation gate

Status: **PREREGISTERED BEFORE ISSUE #127 PORTFOLIO RESULTS**

## Research role

This is the final modern translation / contradiction gate for the only long-history allocation rule that survived Issues #121/#123:

Reflation / Inflation Rising -> Equity > Treasury.

Known prior evidence is explicitly reused. This is not untouched discovery.

## Frozen modern portfolio

C0 neutral:
- SPY 0.40
- TLT 0.40
- GLD 0.10
- SHV 0.10

Exact V6.6 Regime 3 target:
- SPY 0.45
- TLT 0.35
- GLD 0.10
- SHV 0.10

Regimes 1/2/4/5/6/7/8/9 remain C0.

No leverage, shorts, Gold-vs-Cash overlay, second state, or alternate tilt size.

## Frozen sources

Use only:
- Issue #64 frozen SPY/TLT/GLD adjusted-price snapshot;
- Issue #109 frozen SHV/GSG snapshot, SHV only;
- Issue #64 frozen exact V6.6 transition history.

Expected hashes:
- SPY/TLT/GLD snapshot: 3a7f590c146f9eda5920b6968fe86c9c3cc1887db35597f2d639a1c76b6e5a57
- SHV/GSG snapshot: 7dbfe3cff58be172098aa09b9c86fd70a23672834f5829e4b650c94cf72d6833
- exact transitions: 80446bbcb91be8b18eb0b95e62466edf892e4c04087696a04532f0fe214698af

Exact-state signal cutoff remains 2026-08-14.

No live data.

## Monthly timing

Exactly reuse Issue #113:
1. strict common finite SPY/TLT/GLD/SHV calendar;
2. first common eligible trading row of each month;
3. state from the previous common eligible trading row;
4. target set at monthly origin;
5. return measured to next monthly origin;
6. incomplete final origin excluded;
7. no state forward-fill beyond 2026-08-14.

## Turnover and transaction cost

Tactical target turnover only:
turnover_t = 0.5 * sum(abs(target_w_t - target_w_t-1)).

Initial establishment cost excluded.
Primary cost = turnover_t * 0.0005.

No alternate-cost rescue.

## Controls

C0 = static 40/40/10/10.

C1 = arithmetic average of realized monthly Action target weights over the full eligible sample, held statically every month.

Action must beat C1 on both CAGR and Sharpe vs SHV.

## Metrics

Report:
- CAGR
- annualized volatility
- Sharpe vs SHV
- max drawdown
- Calmar
- terminal wealth
- annualized tactical turnover
- cumulative tactical cost
- gross-vs-net annualized cost drag

## Temporal validation

Frozen segments:
- pre_2020: origin < 2020-01-01
- covid_inflation_2020_2022: 2020-01-01 through 2022-12-31
- post_2023: origin >= 2023-01-01

A segment is policy-evaluable only when it contains at least 3 active Regime-3 monthly origins.

For segment metrics:
- subset the full-path realized monthly returns to that segment;
- restart wealth at 1.0 for reporting;
- preserve each row's realized tactical turnover/cost from the full path, including a segment-boundary row if a real target transition occurred there.

Required:
- at least 2 evaluable segments;
- at least 2 evaluable segments have positive Action-minus-C0 CAGR;
- no evaluable segment CAGR disadvantage below -0.0025.

Segments with fewer than 3 active months are reported but neither help nor hurt temporal gates.

## Active episodes

An active episode is a consecutive monthly run with the non-neutral 45/35/10/10 target.

Gross episode contribution:
sum(0.05 * (SPY_return - TLT_return)).

Use gross contribution only to rank episodes.

Strongest-positive-episode leaveout:
- revert that whole episode to C0;
- recompute tactical turnover across the full path including boundaries;
- recompute 5bp net returns and full-sample metrics.

Required:
- leaveout CAGR advantage vs C0 > 0;
- strongest positive episode share <= 0.50.

## Sample sufficiency

Required:
- active Regime-3 monthly origins >= 12;
- active episodes >= 5;
- policy-evaluable temporal segments >= 2.

If any of these fails, verdict is inconclusive.

## Final 11-part gate

All must pass:
1. full-sample Action CAGR > C0 CAGR
2. full-sample Action Sharpe > C0 Sharpe
3. max drawdown difference Action minus C0 >= -0.010
4. active Regime-3 months >= 12
5. active episodes >= 5
6. policy-evaluable temporal segments >= 2
7. at least 2 evaluable temporal segments have positive CAGR advantage
8. no evaluable temporal segment CAGR disadvantage below -0.0025
9. strongest-positive-episode leaveout CAGR advantage > 0
10. strongest positive episode share <= 0.50
11. Action beats C1 on both CAGR and Sharpe

## Deterministic verdict

- if gates 4, 5, or 6 fail: inconclusive_modern_translation_sample
- else if all 11 pass: exact_v66_reflation_translation_candidate
- else if full-sample Action CAGR advantage > 0: modern_direction_positive_but_implementation_not_robust
- else: modern_exact_signal_contradicts_long_history_candidate

No discretionary override.

## Interpretation boundary

A full pass means the frozen modern exact-V6.6 Regime 3 implementation is consistent with the ultra-long-history evidence and is the leading fixed-size Action Layer production candidate.

Even a full pass does not prove future outperformance and does not automatically enable live trading.

## Forbidden rescues

Do not:
- change the 5pp tilt;
- change 40/40/10/10 neutral weights;
- add Gold > Cash;
- add another state;
- change monthly timing;
- change 5bp cost;
- change temporal eras;
- lower sample sufficiency;
- change episode definition;
- weaken C1;
- optimize thresholds or weights after results.

No Issue #127 portfolio result had been computed when this file was committed.