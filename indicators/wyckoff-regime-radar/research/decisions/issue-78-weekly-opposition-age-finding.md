# Issue #78 — Weekly opposition age / maturity diagnostic finding

Status: discovery / in-sample diagnostic only. No production sizing rule selected.

Preregistration: `issue-78-weekly-opposition-age-preregistration.md`.

## Sample

This study uses only fresh daily directional entries that begin against an already-established opposing completed-weekly directional family.

- fresh daily Markup entries against weekly bearish directional context: **238**
- fresh daily Markdown entries against weekly bullish directional context: **167**
- total opposing-context entries: **405**

Frozen age buckets:

- Young: 1–4 completed weeks
- Intermediate: 5–13 completed weeks
- Mature: 14+ completed weeks

Weekly spell age treats Markup/Reaccumulation as one bullish family and Markdown/Redistribution as one bearish family, so switching within a directional family does not reset age.

## Equal-market results

### Fresh daily Markup against bearish weekly context

| Weekly opposition age | Markets | Entries | P+G mean return | MFE | Duration | MFE >=4 | MFE >=8 | Positive return |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Young 1–4w | 8 | 22 | -0.324 | 3.865 | 29.7 | 34.4% | 19.8% | 19.8% |
| Intermediate 5–13w | 8 | 50 | -0.348 | 2.730 | 23.1 | 25.0% | 8.7% | 24.5% |
| Mature 14+w | 8 | 166 | +0.255 | 3.866 | 32.8 | 37.7% | 14.4% | 37.9% |

The most interesting pattern is that **intermediate-age weekly opposition is the weakest context for a fresh daily Markup**, while mature weekly opposition is less hostile. Mature vs Intermediate:

- return higher in 5/8 comparable markets;
- MFE higher in 7/8;
- duration is also higher in the equal-market aggregate.

This is suggestive that a very mature weekly down-regime can become more vulnerable to a daily upside takeover than a 5–13 week weekly down-regime. However return consistency is only 5/8, so this does not pass the preregistered promotion gate.

### Fresh daily Markdown against bullish weekly context

| Weekly opposition age | Markets | Entries | P+G mean return | MFE | Duration | MFE >=4 | MFE >=8 | Positive return |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Young 1–4w | 6 | 17 | +1.083 | 5.323 | 31.2 | 37.5% | 15.3% | 37.5% |
| Intermediate 5–13w | 9 | 49 | -0.328 | 3.538 | 25.4 | 26.7% | 14.2% | 30.5% |
| Mature 14+w | 9 | 101 | -0.047 | 4.114 | 29.5 | 25.4% | 15.0% | 28.9% |

The large positive Young result is **not robust evidence**. The bucket has only 17 episodes across six markets and is strongly influenced by three US10Y cases, one of which is an unusually large trend. It must not be promoted.

Mature vs Intermediate is only mildly better:

- return higher in 6/9 markets;
- MFE higher in 5/9.

That is insufficient for a universal maturity rule.

## Temporal stress

The bucket ordering is not stable across 2010–2014, 2015–2019 and 2020–2026, and many era × age cells are very thin.

For the previously weak 2015–2019 era, fresh daily Markup against mature weekly opposition does look better than Young / Intermediate in this sample, but the same clean ordering does not persist across the other eras or both directions. This therefore cannot be used as a rescue rule for 2015–2019.

## Decision

**Weekly opposition age / maturity does not pass the universal promotion gate.**

There is a useful descriptive clue:

> A fresh daily counter-trend appears most vulnerable when the opposing weekly directional regime is already established but not extremely mature; very mature weekly opposition can sometimes be more susceptible to a daily takeover.

But the evidence is asymmetric, the Young buckets are thin, and return ordering is not sufficiently consistent across markets and eras.

Do not select a 1–4 / 5–13 / 14+ exposure rule from this discovery sample.

## Research implication

The accumulated evidence now argues against using the weekly timeframe as a persistent hard gate. The more promising architecture is narrower:

> **Daily remains the trading engine. Weekly opposition can justify initial skepticism at a fresh daily counter-trend entry, but the daily trend should be allowed to earn its way out of that skepticism using causal daily evidence.**

A successor study, if pursued, should therefore test a **temporary entry brake with daily proof-based release**, rather than another static weekly level / age filter. Such a study requires a new preregistration before simulation.
