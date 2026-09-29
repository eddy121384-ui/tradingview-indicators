# Issue #117 finding — Long-history Gold vs Cash concept validation

Status: **COMPLETE — NO MATERIAL LONG-HISTORY GOLD-vs-CASH RELATIONSHIP UNDER THE PREREGISTERED HMRA ANALOGUE**

Formal preregistered verdict:

`long_history_no_material_gold_cash_relationship`

This finding does **not** invalidate the exact modern V6.6 result. The diagnostic modern-overlap bridge shows that the long-history HMRA proxy and exact V6.6 defensive-state selection overlap poorly.

## Research question

Does the Gold > Cash relationship observed in exact modern V6.6 Regimes 7/8/9 survive roughly fifty years of concept-equivalent macro history?

This is a concept-equivalent long-history study, not a retroactive reconstruction of V6.6.

## Frozen long-history design

Primary source coverage:

- 1975-01 through 2026-08
- 619 common monthly source observations
- 51.58 years of common source coverage

Monthly HMRA analogue:

- Fed Industrial Production
- BLS CPI-U
- 12-month growth / inflation rates
- 12-month acceleration
- prior 60-month normalization
- 70% level + 30% acceleration
- score = 100 × tanh(raw / 2)
- ±10 state thresholds
- decision month uses macro source month t-2

Pooled defensive states:

- Slowdown / Disinflation
- Growth Slowdown / Stable Inflation
- Stagflation Pressure

Outcome:

- World Bank Pink Sheet monthly Gold price through a pinned mirror
- Kenneth French monthly RF as one-month Treasury-bill return
- primary horizon = forward 3 months
- primary inference uses a pooled 3-month non-overlap selector

The source and state rules were frozen before conditioned Gold-vs-Cash payoffs were computed.

## Primary result

The defensive-state opportunity span is **48.25 years**.

Primary non-overlapping observations:

- n = **79**
- mean 3M Gold − Cash spread = **+0.13%**
- median = **−2.53%**
- positive fraction = **39.2%**
- standard deviation = 11.89%
- 95% bootstrap CI = **−2.31% to +2.85%**

The confidence interval clearly includes zero.

Therefore the preregistered long-history structural-support gate fails.

## Era validation

### 1975–1989

- n = 28
- mean 3M spread = **−1.10%**
- median = −4.99%
- positive fraction = 32.1%
- 95% CI = −7.02% to +6.05%

### 1990–2006

- n = 24
- mean = **−0.36%**
- median = −1.68%
- positive fraction = 33.3%
- 95% CI = −2.81% to +2.45%

### 2007–2019

- n = 20
- mean = **+1.83%**
- median = +0.70%
- positive fraction = 50.0%
- 95% CI = −1.32% to +5.06%

### 2020–latest

- n = 7
- mean = **+1.88%**
- median = +0.49%
- positive fraction = 57.1%
- 95% CI = −2.83% to +6.74%

Descriptively, the sign changes around the modern era:

- 1975–2006: negative mean Gold − Cash spread
- 2007 onward: positive mean spread

However no individual era CI excludes zero, and only 2 of 4 eras have positive means.

This is a descriptive era split, not a separately validated trading rule.

## Episode robustness

Strongest positive defensive episode:

- 2019-05 through 2021-02
- 22 months
- top-positive episode share = **25.74%**

The concentration share itself passes the frozen <=35% gate.

But after removing that episode from the primary sample:

- n = 71
- mean 3M spread = **−0.29%**
- 95% CI = −2.92% to +2.77%

The leaveout mean reverses negative.

Therefore strongest-episode robustness fails.

## Leave-one-substate-out robustness

All three fixed counterfactual means remain slightly positive:

- remove Slowdown / Disinflation: **+0.078%**
- remove Growth Slowdown / Stable Inflation: **+0.029%**
- remove Stagflation Pressure: **+0.477%**

All associated confidence intervals include zero.

This says no single sub-state mechanically creates the tiny positive pooled mean, but it does not establish a structural edge.

## Individual sub-states

### Slowdown / Disinflation
- n = 36
- mean = +0.10%
- CI = −2.52% to +2.84%

### Growth Slowdown / Stable Inflation
- n = 8
- mean = +0.84%
- CI = −6.37% to +7.15%

### Stagflation Pressure
- n = 35
- mean ≈ 0.00%
- CI = −4.45% to +5.50%

No individual long-history sub-state shows a statistically clear Gold > Cash effect.

## Horizon diagnostics

All-monthly defensive observations:

### 1M
- n = 218
- mean ≈ **0.00%**
- CI = −0.75% to +0.80%

### 6M
- n = 217
- mean = **−0.58%**
- CI = −2.31% to +1.15%

There is no hidden strong 1M or 6M relationship under the frozen analogue.

## Frozen verdict gates

PASS:

1. defensive opportunity span >=45 years
2. primary n >=30
4. at least 3 evaluable eras
6. no evaluable era mean below −5%
8. strongest positive episode share <=35%
9. all leave-one-substate-out means remain positive

FAIL:

3. full pooled 95% CI excludes zero positively
5. at least 3 evaluable eras have positive means
7. strongest-positive-episode leaveout remains positive

Formal deterministic verdict:

`long_history_no_material_gold_cash_relationship`

## Modern overlap bridge — important interpretation limit

A preregistered diagnostic bridge compared the monthly HMRA analogue with the exact frozen V6.6 Regime 7/8/9 indicator over 2007–2026.

Overlap:

- months = 230
- true-positive overlap = 29
- HMRA-only defensive months = 42
- exact-V6.6-only defensive months = 57
- neither = 102
- agreement rate = **57.0%**
- HMRA precision vs exact defensive = **40.8%**
- HMRA recall vs exact defensive = **33.7%**
- defensive Jaccard overlap = **22.7%**

This is low overlap.

In the same modern window, 3M non-overlapping Gold − Cash means were:

- HMRA defensive: **+1.75%** (n=27)
- exact V6.6 defensive: **+4.85%** (n=38)
- intersection only: **+1.75%** (n=14)

All-monthly means:

- HMRA defensive: +1.96%
- exact V6.6 defensive: +3.42%
- intersection: +3.21%

Therefore the long-history analogue is **not selecting the same defensive months as exact V6.6 particularly well**.

The correct interpretation is narrower than “the V6.6 Gold signal failed over 50 years”:

> The simple long-history IP + CPI HMRA analogue does not show a material structural Gold > Cash relationship over 1975–2026.

But because its modern state overlap with exact V6.6 is poor, this study cannot establish that the exact modern V6.6 Gold > Cash relationship would have failed historically if its unavailable modern market internals had existed.

## Relationship to #115

#115 remains valid for the exact modern implementation-era evidence:

- 2007–2026 frozen exact V6.6 states
- Gold-only overlay CAGR advantage +0.37pp/year
- positive CAGR advantage across all three modern eras
- strongest-episode leaveout remained positive
- post-hoc and not production-authorized

#117 weakens the claim that this is a **generic macro law** of weak-growth / inflation defensive states.

It does not erase the narrower modern V6.6 association.

## Research conclusion

The evidence now supports a more precise statement:

> Gold > Cash is a promising **modern V6.6-specific association**, but we do not have evidence that a simple Growth × Inflation defensive analogue produces the same Gold preference across the full post-Bretton-Woods era.

That means the next step should **not** be to claim a fifty-year structural Gold rule or to tune the HMRA proxy until it works.

Any further work must answer a genuinely different question, such as why exact V6.6's market-implied defensive states differ so much from the IP+CPI historical analogue.

## Reproducibility note

A post-payoff reproducibility amendment replaced a flaky raw floating HMRA CSV byte gate with an exact ordered **state-semantic hash** over:

- date
- growth_state
- inflation_state
- regime
- defensive_gold_state

All upstream source hashes, Gold, and Cash remain byte-exact gates.

No source, state, payoff rule, threshold, or verdict changed in that amendment.
