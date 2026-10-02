# Issue #78 — Equity Trendability / Broad-Oscillation Autopsy preregistration

Date: 2026-10-01

## Purpose

OOS3 independently confirmed that the frozen stock architecture loses broad expectancy while early directional proof still contains information about eventual trend size.

The next mechanism question is:

> Are the weak / failed stock episodes concentrated in a **slow broad-oscillation environment** — i.e. large higher-timeframe ranges in which local directional legs repeatedly look valid but fail to extend?

This study is a **post-outcome mechanism diagnostic** on the already-inspected OOS3 cohort. It is not a new policy OOS and cannot validate a production filter.

No policy, threshold, or stock is changed in this pass.

---

## Frozen cohort and data

Reuse the already-frozen OOS3 cohort and snapshot:

- universe SHA-256:
  `9d4a14d163ed308238737647b94e722c62fd023b641e1015e6d97679f9ba3b44`
- 300 stocks;
- zero FIGI overlap with the first OOS2 cohort;
- Bloomberg raw history through 2026-08-31;
- same classifier blob:
  `1eec08e791403453853b589373bb2270c508c3bb`;
- same fresh Markup / Markdown episode and entry-eligibility contract.

No failed / short-history security may be replaced.

---

## Primary slow-context metric: TrendabilityScore

Reuse the **already-preregistered Issue #78 Trendability / Oscillation family** without changing its horizons or bucket thresholds.

For PRICE_LOG model price:

`ER(L) = abs(price[t] - price[t-L]) / sum(abs(price[i]-price[i-1]), i=t-L+1..t)`

Frozen horizons:

- 63 bars;
- 126 bars;
- 252 bars.

Interpretation:

- ER near 1 = travelled path mostly became net displacement;
- ER near 0 = much travel, little net displacement = oscillation / mean reversion.

For each ER series, compute TradingView-style rolling percent rank against the **previous 756 observations**:

`percent_rank = 100 * count(previous_756 <= current) / 756`

Then:

`TrendabilityScore = mean(ER63_rank, ER126_rank, ER252_rank)`

Fixed descriptive buckets:

- Low: <33.33
- Neutral: 33.33–66.67
- High: >66.67

The value observed on the fresh formal entry bar is used. It is causal for the next move.

No alternate horizon, rank length, weighting, or bucket boundary may be searched.

---

## Secondary direct test of the user's “big box” hypothesis

Low Trendability alone measures oscillation, not the amplitude of the containing range.

Therefore freeze one secondary **range-amplitude** diagnostic before inspecting results:

`RangeWidth252ATR = (highest log-high over 252 bars - lowest log-low over 252 bars) / entry ATR`

Convert this series to a rolling percent rank against its previous 756 observations using the same formula.

Fixed width buckets:

- Narrow: <33.33
- Medium: 33.33–66.67
- Wide: >66.67

Primary 2D descriptive grid:

`Trendability bucket × Width bucket`

The cell of greatest conceptual interest is:

> **Low Trendability + Wide Range**

This is the preregistered proxy for a slow **broad oscillation / large box** environment.

For contrast, Low Trendability + Narrow Range tests whether merely being “stuck” in a tight range explains the damage.

No width cutoff is optimized.

---

## Frozen outcomes

At each completed eligible episode report:

- final MFE;
- MFE <4 ATR;
- MFE >=8 ATR;
- B3 path:
  - NoUsableB3
  - P0
  - P1
  - P2
  - P3
- bad-structure flag:
  `NoUsableB3 or P3`;
- policy harvest under the already-frozen OOS3 policies.

Primary policy for mechanism interpretation:

`R0_NoDerisk`

Other frozen OOS3 policies are reported only to understand whether proof-scaling damage is environment-dependent.

---

## Primary diagnostics

### A. Trendability monotonicity

For Low / Neutral / High, one-stock-one-vote where applicable, report:

- episode count;
- stocks;
- equal-stock mean harvest;
- median stock harvest;
- positive-stock fraction;
- MFE <4 share;
- MFE >=8 share;
- bad-structure share.

Working prediction:

`Low < Neutral < High` for R0 expectancy, with Low having more MFE<4 and more bad-structure episodes.

### B. Broad-box interaction

For the fixed 3×3 Trendability × Width grid report the same outcome family.

Working prediction:

`Low Trendability + Wide`

should be worse than both:

- Low Trendability + Narrow;
- Low Trendability + Medium.

This directly tests whether the problem resembles a **large oscillating box**, rather than simply narrow compression.

### C. Temporal robustness

Repeat by frozen entry eras:

- 2010–2014
- 2015–2019
- 2020–2026

The broad-oscillation story is considered structurally supported only if the Low-vs-High direction is present overall and in at least **2 of 3** frozen eras.

The 2000–2004 and 2005–2009 rows may be reported descriptively, but long lookback/rank warm-up means coverage is mechanically lower in early history.

### D. Direction / size diagnostics

Repeat Trendability bucket summaries for:

- Markup / Markdown;
- large / mid / small sleeve.

These are diagnostics only. No subgroup-specific policy may be created from this pass.

---

## Interpretation

This diagnostic can support:

> “slow broad oscillation is a plausible mechanism behind repeated local trend failure.”

It cannot support:

> “filter Low Trendability in production.”

Any production filter requires a new preregistered policy study on a new untouched cohort.

---

## Guardrails

After seeing the result, do not:

- change 63 / 126 / 252;
- change rankLen 756;
- change 33.33 / 66.67;
- change the 252-bar range-width horizon;
- optimize a Trendability cutoff;
- optimize a Width cutoff;
- make Markup-only / large-only / sector-only rules;
- delete short-history names;
- retrofit the OOS3 policy result with this filter and call it validated.

Refs #78, #135, #132, #131, #80.
