# Issue #78 — Bloomberg 300-Stock OOS2 Diagnostic Autopsy Finding

## Status

Descriptive post-outcome analysis only.

This finding explains the already-locked **Diagnostic Weak / Failed** result. It does not change any frozen classifier, entry eligibility rule, R0 / WarningFirst rule, primary weighting, or interpretation gate.

No rescue retuning is authorized on this cohort.

---

## Executive finding

The failure is not uniform noise.

Three structural features dominate:

1. **NoUsableB3 episodes are the main economic sink.**
2. **Markdown is materially worse than Markup.**
3. **The cross-sectional edge decays strongly after 2010 and deteriorates as stock size falls.**

At the same time, the already-frozen B3 / retest path logic contains meaningful signal, especially in Markup episodes, and WarningFirst transports strongly as a risk-shaping layer.

---

## 1. Direction

R0 equal-stock mean expectancy:

- Markup: **-0.050202 ATR**
- Markdown: **-0.293426 ATR**

WarningFirst improves both but leaves both negative:

- Markup: **-0.038158 ATR**
- Markdown: **-0.261012 ATR**

Therefore Markdown is the much larger directional drag.

However, Markup is not independently profitable at the whole-policy level because failed / short trend episodes remain costly.

---

## 2. Time decay

R0 equal-stock mean expectancy by frozen block:

- 2000–2004: **+0.448257 ATR**
  - median: **-0.054362 ATR**
  - positive-stock breadth: **44.44%**
- 2005–2009: **+0.267544 ATR**
  - median: **+0.079774 ATR**
  - positive-stock breadth: **54.76%**
- 2010–2014: **-0.050191 ATR**
- 2015–2019: **-0.109737 ATR**
- 2020–2026: **-0.200377 ATR**

Only 2005–2009 is positive on both mean and median.

The diagnostic therefore shows a clear weakening after 2010, with the most negative block in 2020–2026.

This is descriptive evidence of historical instability, not permission to retune by era.

---

## 3. Sector breadth

Only one of 11 adequately represented sectors is positive under R0:

- Energy: **+0.240844 ATR**
  - median: **+0.246761 ATR**
  - positive-stock breadth: **65.22%**

All other sectors are negative.

Largest negative sector means include:

- Utilities: **-0.391894 ATR**
- Information Technology: **-0.225132 ATR**
- Materials: **-0.180233 ATR**
- Consumer Discretionary: **-0.179407 ATR**
- Communication Services: **-0.178792 ATR**

This confirms that the full-cohort weakness is broad rather than driven by one isolated sector.

Energy is a descriptive exception, not a post-hoc approved sub-strategy.

---

## 4. Size sleeve

R0 equal-stock mean expectancy:

- large: **-0.019710 ATR**
- mid: **-0.162587 ATR**
- small: **-0.259660 ATR**

Positive-stock breadth:

- large: **44.09%**
- mid: **29.79%**
- small: **23.46%**

The deterioration is monotonic from large to small.

This supports the hypothesis that idiosyncratic noise / shorter and less stable trend persistence becomes increasingly damaging away from large caps.

That interpretation is a hypothesis for future preregistration, not a permitted filter on this cohort.

---

## 5. MFE decomposition

R0 equal-stock mean harvest:

- MFE <4 ATR: **-0.792439 ATR**
- MFE 4–8 ATR: **-0.072810 ATR**
- MFE >=8 ATR: **+4.624687 ATR**

The architecture still captures very large trends strongly.

The economic failure comes from the much more common episodes that never mature into large trends.

WarningFirst changes the slices to:

- MFE <4 ATR: **-0.738480 ATR**
- MFE 4–8 ATR: **+0.024934 ATR**
- MFE >=8 ATR: **+4.184273 ATR**

Thus WarningFirst reduces failed-trend damage and preserves about **90.48%** of >=8 ATR harvest.

---

## 6. The main structural sink: NoUsableB3

R0 path decomposition:

### NoUsableB3

- episodes: **8,288**
- share: **41.59%**
- equal-stock mean harvest: **-0.513020 ATR**
- median stock mean harvest: **-0.515567 ATR**
- positive-stock fraction: **0.00%**
- mean episode length: **11.24 bars**
- mean MFE: **0.57 ATR**

This is the dominant failure mode.

These episodes are short formal trend episodes that terminate before the frozen first usable B3 + t+3 evidence chain can mature.

Under frozen R0 they remain at 25% Probe, but the aggregate bleed is still large because the state occurs so often.

A simple episode-share-weighted decomposition of the path means gives approximately:

- NoUsableB3 contribution: **-0.213 ATR**
- P0 contribution: **+0.017 ATR**
- P1 contribution: **+0.021 ATR**
- P2 contribution: **+0.039 ATR**
- P3 contribution: **+0.002 ATR**

The approximate total is **-0.135 ATR**, close to the locked overall R0 mean of **-0.142 ATR** despite the fact that equal-stock and pooled path weights are not mathematically identical.

This makes the diagnosis robust:

> **the usable-B3 path system is not the main source of the loss; the pre-B3 / never-B3 trend population is.**

---

## 7. Usable B3 paths contain signal

R0 equal-stock path means:

- P0 NoTouch: **+0.091644 ATR**
- P1 WickHold: **+0.179386 ATR**
- P2 Reclaim: **+0.524183 ATR**
- P3 FailedAcceptance: **+0.011632 ATR**

P2 is strongest.

The key finding is that every frozen path bucket is approximately flat-to-positive in aggregate except NoUsableB3.

Therefore the B3 / acceptance / retest architecture appears economically informative even though the whole R0 policy fails.

---

## 8. Path × direction reveals an asymmetry

### Markup

- NoUsableB3: **-0.531768 ATR**
- P0: **+0.273835 ATR**
- P1: **+0.310236 ATR**
- P2: **+0.890574 ATR**
- P3: **+0.009858 ATR**

Once Markup reaches a usable B3 state, the frozen path architecture is strongly positive, especially P2.

### Markdown

- NoUsableB3: **-0.503152 ATR**
- P0: **-0.099152 ATR**
- P1: **-0.094371 ATR**
- P2: **+0.070721 ATR**
- P3: **-0.018781 ATR**

The retest / acceptance structure transports far less well in Markdown.

This is descriptive evidence for a future hypothesis:

> the current trend-harvest architecture may be much more compatible with long-side individual-equity trend persistence than with short-side individual-equity trend persistence.

That hypothesis may only be tested in a new preregistered cohort. It cannot be used to rescue this result.

---

## 9. WarningFirst survives the autopsy

Frozen defensive gate remains strongly positive:

- lower bar volatility: **100.0%**
- lower max drawdown: **91.79%**
- better ES5: **99.63%**
- better MFE<4 harvest: **85.82%**
- >=8 ATR harvest retention: **90.48%**

The strongest portable component discovered by Issue #78 is therefore still:

> **risk shaping / damage control, not broad cross-sectional alpha generation.**

---

## Research interpretation

The first Bloomberg 300-stock diagnostic does not support using the current R0 architecture as a general standalone U.S. individual-stock strategy.

But it also does not show that every component is useless.

The autopsy separates three things:

- **classifier trend declaration** is too permissive for many short-lived individual-stock trends;
- **B3 / retest / acceptance evidence** contains meaningful information after a trend survives long enough to reach it;
- **WarningFirst** is robust as a damage-control layer.

Future research should therefore start from new preregistered hypotheses around:

- why NoUsableB3 formal trends are so frequent;
- whether a pre-B3 admission / persistence gate can distinguish short-lived false trends without destroying >=8 ATR winners;
- why Markdown path economics differ so sharply from Markup;
- whether the strong size gradient reflects idiosyncratic noise, liquidity, gap risk, or trend persistence.

Those are new studies, not modifications of this frozen cohort.

Refs #78, #131, #80.
