# Issue #123 finding — Reflation Equity > Treasury Phase 2 policy rematch

Status: **COMPLETE — LONG-HISTORY POLICY CANDIDATE**

Formal preregistered verdict:

`long_history_reflation_policy_candidate`

Production authorization: **NO**

## Research role

This study translated the sole Issue #121 revived mapping:

> Reflation / Inflation Rising -> Equity > Treasury

into a minimal fixed annual sleeve rule.

It is not an untouched discovery test. The underlying pairwise relationship was selected from the same long-history evidence in #121.

The question here is narrower:

> Does a fixed 5pp implementation survive portfolio-level controls and robustness checks without retuning?

## Frozen policy

C0 neutral:

- Equity 50%
- Treasury 50%

Action:

- Reflation signal_t -> return_{t+2}: Equity 55% / Treasury 45%
- all other states: 50% / 50%

Primary tactical cost:

- 5bp one-way per dollar of target turnover

No optimizer.
No additional states.
No Gold/Cash/Commodity sleeve.

## Sample

- signal years: 1928–2023
- return years: 1930–2025
- annual policy rows: **96**
- active Reflation years: **22**
- active episodes: **15**

C1 exposure-matched static weights:

- Equity: **51.1458%**
- Treasury: **48.8542%**

## Full-sample performance

### Action

- CAGR: **7.9159%**
- arithmetic mean annual return: 8.4586%
- annual volatility: 10.6936%
- Sharpe vs T-bill: **0.46327**
- year-end max drawdown: **-31.1027%**
- terminal wealth from 1.0: **1500.38x**
- annualized tactical target turnover: **1.5625%**
- cumulative tactical cost: **0.075%**

### C0 neutral 50/50

- CAGR: **7.7778%**
- arithmetic mean annual return: 8.3011%
- annual volatility: 10.5018%
- Sharpe vs T-bill: **0.45680**
- max drawdown: **-31.1027%**
- terminal wealth: **1326.84x**

### Action minus C0

- CAGR advantage: **+0.1381 percentage point / year**
- Sharpe advantage: **+0.00647**
- max-drawdown difference: **0.00pp**
- terminal wealth difference: **+173.54x**

Over 96 years, the small annual edge compounds to approximately 13.1% more terminal wealth than C0.

## Exposure-matched C1

C1:

- CAGR: **7.8391%**
- Sharpe: **0.45673**
- max drawdown: -31.8715%
- terminal wealth: 1401.31x

Action minus C1:

- CAGR: **+0.0768pp/year**
- Sharpe: **+0.00654**

Therefore the Action result is not explained solely by carrying slightly more Equity exposure on average.

## Broad-era validation

All four frozen broad signal eras are evaluable and all four have positive Action-minus-C0 CAGR.

### 1928–1945 signal era

- n = 18
- active years = 6
- CAGR advantage: **+0.1934pp/year**
- Sharpe advantage: +0.00726

### 1946–1979

- n = 34
- active years = 5
- CAGR advantage: **+0.1284pp/year**
- Sharpe advantage: +0.01219

### 1980–1999

- n = 20
- active years = 2
- CAGR advantage: **+0.0618pp/year**
- Sharpe advantage: +0.00186

### 2000–2023

- n = 24
- active years = 9
- CAGR advantage: **+0.1691pp/year**
- Sharpe advantage: +0.00735

Result:

- 4 / 4 evaluable broad eras positive
- no era has a negative CAGR advantage
- drawdown never worsens versus C0 in these annual-data summaries

## Fine-era leave-one-out

Every fine era containing at least one active Reflation target was removed one at a time.

All full-sample CAGR advantages remain positive.

Examples:

- omit Depression / WWII Reflation years: **+0.1005pp/year**
- omit Postwar / Bretton Woods: **+0.1093pp/year**
- omit Great Inflation pre-Volcker: **+0.1212pp/year**
- omit Post-Volcker disinflation: **+0.1258pp/year**
- omit Pre-GFC 2000s: **+0.1304pp/year**
- omit GFC/QE low-inflation era: **+0.1140pp/year**
- omit 2021–22 inflation-surge era: **+0.1273pp/year**

No fine-era leaveout eliminates the positive full-sample CAGR edge.

## Episode robustness

Strongest positive active episode:

- return years: **1935–1938**
- signal years: 1933–1936
- active years: 4
- gross incremental contribution: +2.877%
- share of all positive episode contribution: **18.10%**

This is well below the frozen 50% concentration ceiling.

After removing the entire strongest episode and recomputing turnover:

- Action CAGR: 7.8976%
- C0 CAGR: 7.7778%
- CAGR advantage: **+0.1198pp/year**
- Sharpe advantage: **+0.00881**

The policy result does not depend on one winning episode.

## Ten-part preregistered gate

PASS:

1. Action CAGR > C0
2. Action Sharpe > C0
3. max-DD degradation <=1.0pp
4. >=3 broad eras evaluable
5. >=3 broad eras positive CAGR advantage
6. no broad-era disadvantage below -0.25pp/year
7. strongest-episode leaveout remains positive
8. strongest-positive-episode share <=50%
9. Action beats C1 on CAGR and Sharpe
10. every evaluable fine-era leaveout retains positive CAGR advantage

Result:

**10 / 10 gates PASS**

Formal verdict:

`long_history_reflation_policy_candidate`

## Interpretation

This is the strongest long-history allocation result in the current rematch chain.

The effect is deliberately modest:

- only a 5pp Equity-over-Treasury tilt
- active in 22 of 96 return years
- about +13.8bp/year CAGR over the full sample

That small magnitude is consistent with a sparse tactical overlay rather than a wholesale allocation regime switch.

The important evidence is robustness:

- positive across all four broad eras
- survives every fine-era leaveout
- survives strongest-episode removal
- beats exposure-matched static C1
- does not worsen annual max drawdown

## Relationship to modern V6.6

This result does not establish that exact V6.6 Reflation is identical to HMRA Reflation.

The modern exact-V6.6 #109 sample for Reflation Equity > Duration was directionally positive but statistically underpowered.

The ultra-long-history HMRA result now supports the interpretation that the modern failure to clear significance may have been a sample-size problem rather than evidence against the economic direction.

A separate exact-modern bridge / production translation is still required before any live Action Layer rule is authorized.

## Boundary

Issue #123 does not authorize:

- production trading
- a 5pp live position
- a 10pp rescue
- adding near-miss states
- optimizer-based weights
- merging this research PR into production

The correct status is:

> **Long-history policy candidate; production authorization remains false.**
