# Issue #95 Phase 3 finding

## Verdict

`no_material_overlay_value`

The Phase 2 structural finding survives conceptually — high absolute inflation does change Treasury-vs-cash behavior — but the preregistered portfolio translation is too weak.

The tested rule was intentionally simple:

> when lagged HMRA state-year CPI inflation is >=4%, redirect 50% of the selected Treasury sleeve to T-bills.

Everything else in the #89 3×3 policy remained unchanged.

## Full 1975–2025 result

At 5bp one-way turnover cost:

- inflation overlay CAGR: **9.589%**
- unchanged #89 base policy CAGR: **9.562%**
- difference: **+0.027 percentage point/year** (~2.7bp)

Sharpe improves only from 0.588 to 0.596, and max drawdown is unchanged at about **−16.04%**.

That is not a material portfolio improvement.

The realized-exposure-matched static control has:
- CAGR 9.452%
- Sharpe **0.609**
- max drawdown **−12.98%**
- Calmar **0.728**

The overlay has slightly higher CAGR than matched static, but worse Sharpe, a roughly 3.1pp worse max drawdown, and much worse Calmar. The evidence does not support a robust switching/timing claim.

## Earlier versus recent inflation history

The rule is **not** merely a post-COVID rescue.

1975–1984:
- overlay CAGR 10.23%
- base CAGR 10.15%
- matched static CAGR 11.36%

2020–2025:
- overlay CAGR 8.93%
- base CAGR 8.65%
- matched static CAGR 10.48%

So the overlay is slightly positive versus the base policy in both high-inflation eras, but materially worse than matched static in both.

## Fragility

There are 16 overlay-active years grouped into only four contiguous episodes.

The largest positive overlay-vs-base episode is **2009 alone**, contributing about **52.8%** of all positive episode contribution.

Removing that one positive episode changes the primary overlay-vs-base result to:
- ΔCAGR **−0.029pp/year**
- cumulative active log return **−1.31%**

The sign of the overlay's incremental value is also not stable under leave-one-era-out analysis.

## Sensitivities do not rescue the result

At 5bp:
- 25% Treasury redirect: ΔCAGR vs base about +1.5bp/year
- 50% primary: +2.7bp/year
- 75% diagnostic: +3.6bp/year

The larger haircut produces a somewhat larger return difference, but those variants were preregistered as diagnostics only. There is no basis to promote 75% after seeing the result.

Transaction-cost sensitivity from 0 to 10bp also does not change the conclusion.

## Interpretation

This is an important negative result.

Phase 2 said:

> high absolute inflation changes the economic payoff of duration versus cash.

Phase 3 says:

> a binary 4% threshold plus a fixed 50% Treasury haircut is too crude to turn that structural fact into material portfolio value.

That does **not** invalidate HMRA, V6.6, or the Phase 2 structural finding.

It does mean we should not rescue the idea by moving the threshold to 3% or 5%, changing the haircut to 75%, or rewriting the #89 matrix inside this issue.

Any next mechanism must be a new preregistered hypothesis.
