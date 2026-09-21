# Issue #78 — Resume Trigger Challenge Stage 1 Finding
## Frozen one-shot resume definitions after P1/P2 retest states

## Scope

This finding executes the frozen preregistration in `issue-78-resume-trigger-stage1-preregistration.md`.

The purpose was to compare four causal, one-shot resume definitions after a valid P1/P2 retest state is known at t+3, while explicitly preventing recursive anchor resets.

Eligible population:

- P1 Wick Retest / Hold: 110;
- P2 Close Re-entry / Reclaim: 126;
- total: 236.

Every resume anchor was frozen once at t+3 and never updated after later pullbacks.

## Resume definitions

- **R1 Close Extreme** — first later close beyond the best favorable close known through t+3.
- **R2 Price Extreme** — first later bar whose high/low exceeds the best favorable intrabar extreme known through t+3.
- **R3 Retest Structure** — first later close beyond the favorable high/low of the frozen retest segment from first touch through t+3.
- **R4 +0.5 ATR Progress** — first later close 0.5 ATR beyond close[t+3].

No threshold or lookback search was performed.

## Result 1 — The feared “never enters” problem is real but not catastrophic for R1

Equal-market trigger coverage:

- R1 Close Extreme: **82.4%**
- R2 Price Extreme: **80.7%**
- R3 Retest Structure: **76.9%**
- R4 +0.5 ATR Progress: **75.5%**

No-trigger rates:

- R1: **17.6%**
- R2: **19.3%**
- R3: **23.1%**
- R4: **24.5%**

So any confirmation rule leaves some valid P1/P2 states without a later trigger.

However the frozen-anchor design prevents infinite recursion.

R1 in particular triggers in more than four-fifths of valid retest/reclaim episodes.

## Result 2 — R1 is the best coverage / timing frontier among the tested close-based rules

Equal-market delay from t+3:

- R1 median: **1.78 bars**, mean 3.54;
- R2 median: 1.50, mean 3.81;
- R3 median: 2.28, mean 4.98;
- R4 median: 2.78, mean 4.81.

Share of all eligible P1/P2 states triggering within 3 bars:

- R1: **59.5%**
- R2: 58.1%
- R3: 46.7%
- R4: 44.3%

Within 5 bars:

- R1: **69.4%**
- R2: 66.4%
- R3: 58.5%
- R4: 58.2%

Within 10 bars:

- R1: **76.9%**
- R2: 74.9%
- R3: 68.3%
- R4: 68.1%

Despite being conceptually conservative, R1 is not the slowest rule.

## Result 3 — R3 does not solve the recursive-wait concern under the preregistered high/low definition

The intended intuition for R3 was:

> break the local retest structure rather than waiting for a full new favorable extreme.

But the preregistered implementation froze the retest segment’s favorable **high / low** and required a later **close** through it.

That makes the retest wick itself part of the hurdle.

Paired episodes where both R3 and R1 trigger:

- R3 triggers **1.34 bars later** than R1;
- consumes about **+7.4 percentage points** more of eventual favorable close-path excursion;
- leaves 1.34 fewer formal-regime bars;
- only improves re-expansion by ~+3.4 pp over 5 moves and ~+0.6 pp over 10;
- old-box failure improves by only ~1.4 pp.

Decision:

> **This R3 definition fails its specific admission objective.**

It is not an earlier local-structure resume trigger.

Do not reinterpret it post hoc.

## Result 4 — R2 price/wick extreme is not clearly earlier or better than R1

R2 coverage is slightly lower than R1:

- 80.7% vs 82.4%.

On episodes where both trigger:

- R2 is about **0.24 bars later on average** at the bar level;
- trigger-bar close confirmation tax is ~2.7 pp lower because the wick can cross before the close;
- future re-expansion improves only ~+2.5 pp / +1.7 pp;
- old-box failure is ~+2.0 pp worse.

Equal-market post-trigger old-box failure:

- R1: **12.4%**
- R2: **13.2%**

So wick-based new-price-extreme confirmation does not dominate close confirmation.

## Result 5 — R4 +0.5 ATR buys cleaner immediate failure behavior by refusing more episodes

R4 has:

- lowest trigger coverage: **75.5%**;
- no-trigger: 24.5%;
- median delay: 2.78 bars;
- median confirmation-tax fraction: **31.8%** of eventual favorable close excursion;
- old-box failure after trigger: **7.0%**, lowest of the four.

Post-trigger re-expansion:

- 5 moves: 84.8%;
- 10 moves: 88.5%.

But this should not be read as a free improvement.

R4 is materially more selective and later.

Compared with R3 on paired trigger episodes:

- R4 is only ~0.2 bars earlier;
- has ~1.4 pp higher confirmation tax;
- has ~2.5 pp lower 5-move re-expansion and ~1.9 pp lower 10-move re-expansion;
- old-box failure is ~0.6 pp lower.

No structural reason exists to promote R4 over R1 or R3 from this stage.

## Result 6 — Stricter triggers improve conditional health mainly through selection

Equal-market post-trigger metrics:

### R1 Close Extreme

- re-expand 5: **79.6%**
- re-expand 10: **86.2%**
- old-box failure next 3 closes: **12.4%**
- remaining life >=20: **70.8%**
- mean remaining life: 36.2 bars
- median confirmation-tax fraction: **22.5%**

### R2 Price Extreme

- re-expand 5: 82.9%
- re-expand 10: 87.7%
- old-box failure: 13.2%
- remaining >=20: 72.7%
- median tax: 20.7%

### R3 Retest Structure

- re-expand 5: 85.2%
- re-expand 10: 89.0%
- old-box failure: 10.3%
- remaining >=20: 72.8%
- median tax: **29.7%**

### R4 +0.5 ATR

- re-expand 5: 84.8%
- re-expand 10: 88.5%
- old-box failure: **7.0%**
- remaining >=20: 74.0%
- median tax: **31.8%**

The apparent quality improvement from R3/R4 must therefore be interpreted together with lower coverage and higher confirmation tax.

## Result 7 — R1 works similarly across P1 and P2

### P1 Wick Hold

R1:

- coverage: **83.6%**
- median delay: 2.5 bars
- re-expand 5 / 10: 77.2% / 84.9%
- old-box failure: 9.0%
- remaining >=20: 71.3%

### P2 Reclaim

R1:

- coverage: **82.3%**
- median delay: 1.5 bars
- re-expand 5 / 10: 78.3% / 85.5%
- old-box failure: 18.0%
- remaining >=20: 67.3%

The same definition remains usable in both path states.

P2 carries more post-trigger old-box failure risk, consistent with its weaker semantics from the prior study.

No path-specific threshold is justified.

## Result 8 — The main trigger families do not collapse in 2015–2019

2015–2019 equal-market trigger coverage:

- R1: **88.1%**
- R2: 88.7%
- R3: 81.1%
- R4: 82.5%

2015–2019 post-trigger re-expansion 5 / 10:

- R1: 76.5% / 87.7%
- R2: 80.8% / 91.8%
- R3: 85.6% / 91.2%
- R4: 90.1% / 93.1%

No required stress-era inversion is observed.

2020–2026 has longer delays for all definitions, especially R3/R4, which reinforces the need to measure confirmation tax rather than only conditional hit rates.

## Result 9 — Direction robustness is broadly acceptable

R1 trigger coverage:

- Markdown: 81.4%
- Markup: 83.1%

R1 post-trigger re-expand 5:

- Markdown: 81.2%
- Markup: 77.3%

R1 post-trigger re-expand 10:

- Markdown: 84.7%
- Markup: 89.0%

No direction-specific rule is justified.

## Research decision

### Retain R1 Close Extreme as the clean baseline frontier

Among the preregistered candidates, R1 offers the best balance of:

- highest trigger coverage;
- low confirmation delay;
- moderate confirmation tax;
- strong post-trigger re-expansion;
- acceptable false-resume behavior;
- cross-path / cross-direction usability;
- no 2015–2019 collapse.

This is **not** yet a production selection or sizing rule.

It is the strongest baseline for a later economic-policy test.

### Do not promote R2 over R1

The wick/price-extreme trigger does not provide a compelling earlier-entry or lower-failure advantage.

### Reject the preregistered R3 definition for its intended purpose

R3 using retest-segment high/low plus close confirmation is mechanically too strict and often later than R1.

This does not invalidate the general concept of a local retest-structure trigger.

A materially different definition, such as a **frozen retest-segment close boundary**, would require a new preregistration.

### Keep R4 as a momentum benchmark only

It filters immediate old-box failure well but pays a larger confirmation tax and refuses more valid P1/P2 episodes.

## Direct answer to the recursive-wait concern

The research supports two separate conclusions:

1. **Do not reset the resume anchor after every new pullback.**
   Freeze it once at t+3.
2. Under that one-shot design, waiting for a new favorable close extreme does **not** usually create an endless loop:
   R1 triggers in ~82% of valid retest/reclaim states, with a median delay under two bars equal-market.

The remaining ~18% no-trigger rate is real confirmation cost and should be treated as such, not hidden by recursive re-anchoring.

## Next gate

Before any sizing backtest, there are two defensible routes:

### Route A — Carry R1 forward

Treat R1 as the simplest frozen resume baseline and test the economic value of adding risk at that event.

### Route B — One final definition challenger

Preregister a genuinely earlier local trigger:

> **Frozen retest-segment close-structure break**

using only closes inside the retest segment, not high/low wicks.

This would directly test whether the local-structure idea can address the user’s “full new extreme may be too late” concern without the mechanical strictness discovered in R3.

No post-hoc replacement is made in this finding.

Refs #78, #80, #76.
