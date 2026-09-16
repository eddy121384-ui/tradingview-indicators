# Issue #87 — Responsiveness Bonus Overlay finding

Date: 2026-09-16

## Executive conclusion

Using Market Responsiveness as an additive bonus is economically much healthier than using it as a hard participation gate, but the preregistered bonus overlays do **not** establish a superior universal sizing rule.

The first E5 bonus tier produces a real raw-return lift and favorable Large-vs-Failed asymmetry, but its drawdown rises almost one-for-one with return and its incremental gains occur in only 5/9 markets. The second E10 tier adds still more raw return, but worsens return-to-drawdown efficiency relative to both B1 and the baseline.

Therefore:

- **B1 E5 bonus: WEAK / DESCRIPTIVE SURVIVOR.** Interesting asymmetry, but not enough cross-market and risk-adjusted improvement to promote.
- **B2 second E10 tier: REJECT as an additional universal bonus tier.** The extra return does not justify the extra drawdown / turnover.
- **Persistence + Gentle remains the production-candidate baseline.** Market Responsiveness remains useful state/confidence information, but no automatic bonus overlay is promoted from this same sample.

## Data gate

The exact accepted Issue #76 sample reproduced:

- event rows: **68,118**;
- completed known-start formal trend episodes: **1,624**;
- Failed: **1,058**;
- Middle: **258**;
- Large: **308**.

No classifier change, label change, threshold search, or post-outcome bonus-size change was made.

## Policies

- **B0:** existing Persistence + Gentle baseline.
- **B1:** B0 plus one `+0.25` bonus tier earned at E5 when `cum >= +0.5 ATR` and `dir_eff >= 0.50`; bonus can only be active while the Gentle damage latch is fully healthy; max exposure `1.25`.
- **B2:** B1 plus a second `+0.25` tier earned at E10 only if the first tier was earned, `cum >= +1.0 ATR`, `dir_eff >= 0.50`, and `new_high_rate >= 0.50`; max exposure `1.50`.

The baseline position is never reduced by responsiveness.

## Universal economics

### B0 — Persistence + Gentle

- equal-market mean episode return: **+0.3322 ATR**;
- positive markets: **8/9**;
- median PF: **1.260**;
- equal-market mean MDD: **37.35 ATR**;
- return / MDD: **0.008895**;
- turnover per episode: **1.984**.

### B1 — E5 bonus

- equal-market mean episode return: **+0.3620 ATR**;
- positive markets: **8/9**;
- median PF: **1.257**;
- MDD: **40.64 ATR**;
- return / MDD: **0.008907**;
- turnover per episode: **2.261**.

Relative to B0:

- mean return: **+8.97%**;
- MDD: **+8.83%**;
- return / MDD: only **+0.13%**;
- turnover: **+13.99%**.

So B1's raw-return lift is real, but almost exactly matched by the increase in drawdown. This is not a meaningful universal risk-efficiency improvement.

### B2 — E5 + E10 bonus

- equal-market mean episode return: **+0.3694 ATR**;
- positive markets: **8/9**;
- median PF: **1.275**;
- MDD: **42.05 ATR**;
- return / MDD: **0.008784**;
- turnover per episode: **2.342**.

Relative to B0:

- mean return: **+11.19%**;
- MDD: **+12.60%**;
- return / MDD: **-1.26%**;
- turnover: **+18.07%**.

Relative to B1, the second tier adds only about **2.0%** more mean return while adding about **3.5%** more MDD. The second tier therefore does not improve the frontier.

## Large-vs-Failed economics

The responsiveness conditions are genuinely selective:

- E5 first tier is earned by about **44.5% of Large** episodes but only **11.5% of Failed** episodes.
- E10 second tier is earned by about **19.5% of Large** episodes but only **0.7% of Failed** episodes.

That selectivity does create favorable asymmetry.

### Failed trends

- B0: **-1.026 ATR**;
- B1: **-1.062 ATR** — about **3.5% more damage**;
- B2: **-1.064 ATR** — about **3.7% more damage**.

### Large trends

- B0: **+5.853 ATR**;
- B1: **+6.193 ATR** — about **5.8% more harvest**;
- B2: **+6.276 ATR** — about **7.2% more harvest**.

This is a better asymmetry than the Issue #85 hard-gate architecture: the bonus adds proportionally more to Large winners than it adds to Failed losers.

However, the Middle bucket deteriorates:

- B0: **+0.051 ATR**;
- B1: **+0.007 ATR**;
- B2: **-0.039 ATR**.

So the bonus does not simply amplify good trades; it also converts some middling trends into worse economic outcomes.

## Direction diagnostics

Both Markup and Markdown remain positive on average.

Markup:

- B0 **+0.145**;
- B1 **+0.158**;
- B2 **+0.156**.

Markdown:

- B0 **+0.496**;
- B1 **+0.541**;
- B2 **+0.558**.

Thus the overlay does not require a direction-specific rule, but most of the incremental economic gain is stronger on Markdown than Markup.

## Temporal diagnostics

The overlay does not show broad temporal improvement.

### 2010–2014

- B0 **+0.727**;
- B1 **+0.723**;
- B2 **+0.698**.

Both bonus variants are worse than baseline.

### 2015–2019 stress slice

- B0 **-0.098**;
- B1 **-0.093**;
- B2 **-0.083**.

The bonuses make the bad era slightly less negative, but do not rescue it. MDD rises.

### 2020–2026

- B0 **+0.098**;
- B1 **+0.088**;
- B2 **+0.094**.

Again, neither bonus beats baseline return.

The all-sample gain therefore does not appear as a clean improvement across the three common eras.

## Cross-market heterogeneity

Incremental mean return versus B0 is positive in only **5/9 markets** for both B1 and B2.

Positive deltas occur in:

- AU10Y;
- DE10Y;
- FR10Y;
- GB10Y;
- US10Y.

Negative deltas occur in:

- EURUSD;
- GBPUSD;
- USDJPY;
- JP10Y.

This concentration is an important warning. It is a post-hoc diagnostic, **not** permission to create separate FX / rates rules. Under the preregistered guardrails the universal overlay must stand or fall without asset-specific rescue.

## Friction

At friction `0.05 ATR per unit turnover`:

- B0: **+0.2330 ATR**, 8 positive markets;
- B1: **+0.2489 ATR**, 7 positive markets;
- B2: **+0.2523 ATR**, 7 positive markets.

At friction `0.10`:

- B0: **+0.1339**, 6 positive markets;
- B1: **+0.1359**, 5 positive markets;
- B2: **+0.1352**, 5 positive markets.

The small net-return advantage survives numerically, but breadth deteriorates as friction rises.

## Research decision

### B1 E5 bonus — WEAK / DESCRIPTIVE SURVIVOR

The first bonus tier has a sensible mechanism and favorable Large-vs-Failed asymmetry. It raises all-sample return without destroying the baseline, unlike the hard-gate experiment.

But the increase in return is almost exactly matched by the increase in MDD, turnover rises materially, only 5/9 markets improve incrementally, and neither 2010–2014 nor 2020–2026 improves.

Do **not** promote B1 to production from this sample.

### B2 E10 second tier — REJECT as an incremental universal tier

The second tier adds little return beyond B1 while adding more drawdown and turnover. Return / MDD falls below the original baseline.

Do not rescue it by changing the E10 threshold, new-high-rate threshold, or bonus size.

## What this means conceptually

The sequence of Issues #81, #85, and #87 now gives a useful separation:

1. **Market Responsiveness is real information.** It helps distinguish trajectories that later become Large from those that fail.
2. **Using it as a hard permission gate is too costly.** You miss too much of the trend.
3. **Using it as a bonus is better, but still does not produce a clearly superior universal return/risk frontier on this same sample.**

The correct response is not to keep tuning the same 68,118 rows until a prettier rule appears.

The next scientifically clean step is **validation on genuinely new information** — an unseen time period, additional markets, or another predeclared holdout — while freezing the B0 baseline and, if desired, the B1 E5 bonus exactly as tested here.

Refs #87 #85 #81 #78 #76 #68.
