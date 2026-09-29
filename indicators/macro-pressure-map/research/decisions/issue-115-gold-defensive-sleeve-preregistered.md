# Issue #115 preregistration — Gold > Cash defensive sleeve robustness

Status: **PREREGISTERED BEFORE ISSUE #115 PORTFOLIO RESULTS**

## Research status

This is an explicitly post-hoc follow-up to Issue #113.

Issue #113 attribution showed that most of the sparse Action Layer's gross historical contribution came from the Gold-vs-Cash sleeve. That observation is already inspected and cannot be treated as new evidence.

Issue #115 therefore asks only whether the already-observed Gold sleeve survives a stricter fixed robustness gate.

All history is reused development evidence, not untouched OOS confirmation.

## Frozen neutral portfolio

- SPY 0.40
- TLT 0.40
- GLD 0.10
- SHV 0.10

No leverage. No shorts.

## Frozen Gold-only rule

Active states:

- Regime 7 — Slowdown / Disinflation
- Regime 8 — Growth Slowdown / Stable Inflation
- Regime 9 — Stagflation Pressure

In any active state:

- SPY 0.40
- TLT 0.40
- GLD 0.15
- SHV 0.05

Regimes 1–6 remain neutral.

The Issue #113 Equity-vs-Duration sleeve is fully removed.

No +/-2 tier.

## Frozen timing

Exactly reuse Issue #113:

1. strict common finite SPY/TLT/GLD/SHV calendar;
2. first common eligible trading row of each calendar month;
3. signal state from the previous common eligible trading row;
4. target weights held until the next monthly origin;
5. final origin excluded if no next monthly origin exists;
6. no state forward-fill beyond frozen cutoff 2026-08-14.

## Frozen data

Reuse only committed hash-frozen inputs:

- Issue #64 SPY/TLT/GLD adjusted-price snapshot:
  `3a7f590c146f9eda5920b6968fe86c9c3cc1887db35597f2d639a1c76b6e5a57`
- Issue #109 SHV/GSG adjusted-price snapshot:
  `7dbfe3cff58be172098aa09b9c86fd70a23672834f5829e4b650c94cf72d6833`
  - only SHV is used here
- Issue #64 frozen exact V6.6 transitions:
  `80446bbcb91be8b18eb0b95e62466edf892e4c04087696a04532f0fe214698af`

No live data.

## Tactical turnover and cost

Same as Issue #113.

`turnover_t = 0.5 * sum(abs(target_w_t - target_w_t-1))`

Primary cost:

`turnover_t * 0.0005`

Initial establishment cost excluded.

Diagnostics only:

- 0bp
- 10bp

## Controls

### C0 — neutral static

40 / 40 / 10 / 10.

### C1 — exposure-matched static

Arithmetic mean of the Gold-only monthly target weights, held statically through the sample.

C1 is descriptive because it uses full-sample realized average exposure.

Gold-only passes the C1 gate only if:

- Gold-only CAGR > C1 CAGR; and
- Gold-only Sharpe > C1 Sharpe.

### C2 — frozen Issue #113 full sparse overlay

Use the exact Issue #113 rule as already committed:

- Regime 8:
  - SPY 0.45
  - TLT 0.35
  - GLD 0.15
  - SHV 0.05
- Regimes 7/9:
  - SPY 0.40
  - TLT 0.40
  - GLD 0.15
  - SHV 0.05
- Regimes 1–6:
  - neutral

C2 is a simplification comparator only and is not a gate.

## Metrics

Use the exact Issue #113 metric definitions:

- CAGR
- annualized volatility
- Sharpe using SHV monthly return as cash benchmark
- max drawdown
- Calmar
- terminal wealth
- annualized tactical turnover
- total tactical cost
- annualized cost drag

## Temporal validation

By monthly origin:

- pre-2020
- 2020-01 through 2022-12
- 2023+

Each segment restarts wealth at 1.0.

Because the hypothesis is post-hoc selected, all three segments must have positive Gold-only CAGR advantage versus C0.

If any segment has fewer than 24 completed months, verdict is inconclusive.

## Active episodes

An active episode is a consecutive monthly run with the same non-neutral Gold-only target.

Since Regimes 7/8/9 share the same Gold-only target, direct transitions among 7/8/9 remain the same episode.

Episode contribution:

`sum(GoldOnly_net_return - C0_return)`

Strongest-positive-episode leaveout:

1. identify the active episode with largest positive contribution;
2. revert every month in that episode to C0;
3. recompute tactical turnover including boundaries;
4. recompute 5bp net results.

Required:

`leaveout Gold-only CAGR - C0 CAGR > 0`

Report top-positive episode share.

## Leave-one-state-out robustness

Run exactly three counterfactuals:

- L7: remove Regime 7 tilt; keep 8/9
- L8: remove Regime 8 tilt; keep 7/9
- L9: remove Regime 9 tilt; keep 7/8

Everything else remains fixed.

Each counterfactual must retain:

`CAGR advantage vs C0 > 0`

The result may not be used to select a preferred subset.

## State contribution diagnostic

For Regimes 7, 8, and 9 separately, report:

- active months;
- gross arithmetic contribution:
  `sum(0.05 * (GLD_return - SHV_return))`
- annualized mean contribution:
  `mean(monthly contribution over the full sample) * 12`

This diagnostic cannot change the rule.

## Stricter eight-part gate

All must pass:

1. full-sample Gold-only net CAGR advantage vs C0 >= +0.0025;
2. full-sample Sharpe advantage vs C0 >= +0.05;
3. max drawdown difference Gold-only minus C0 >= -0.015;
4. all 3/3 temporal segments have positive CAGR advantage;
5. minimum temporal CAGR advantage >= 0;
6. strongest-positive-episode leaveout keeps positive CAGR advantage;
7. Gold-only beats C1 on both CAGR and Sharpe;
8. L7, L8, and L9 all retain positive CAGR advantage vs C0.

## Deterministic verdict

- if any temporal segment has <24 completed observations:
  `gold_defensive_sleeve_inconclusive`
- else if all eight gates pass:
  `gold_defensive_sleeve_robust_candidate`
- else if full-sample Gold-only CAGR advantage vs C0 > 0:
  `gold_defensive_sleeve_economically_positive_but_posthoc_not_robust`
- else:
  `gold_defensive_sleeve_no_material_value`

No discretionary override.

## Interpretation boundary

Even a full pass is not independent confirmation.

A pass means only:

> Among the already-inspected state-only ideas, this is the cleanest surviving candidate worth preserving while genuinely new data accumulate.

It does not prove future outperformance.

## Forbidden rescue paths

Do not:

- change 5pp;
- change neutral weights;
- change 5bp;
- add Equity-vs-Duration back;
- remove Regime 7/8/9 after state diagnostics;
- use the best leave-one-state-out subset;
- add Reflation;
- add trajectory;
- add FCPI;
- add commodities;
- optimize Gold weight;
- change monthly timing;
- weaken the +0.05 Sharpe gate;
- change the all-3-era requirement.

No Issue #115 portfolio result had been viewed when this document was committed.
