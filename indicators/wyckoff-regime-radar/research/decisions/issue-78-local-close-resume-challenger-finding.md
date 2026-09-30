# Issue #78 — Local Close Resume Challenger Finding
## Frozen retest-segment CLOSE boundary vs R1 full close extreme

## Scope

This finding executes the preregistered final definition-only Resume challenger in
`issue-78-local-close-resume-challenger-preregistration.md`.

The eligible population is unchanged from Resume Trigger Stage 1:

- P1 Wick Retest / Hold: 110;
- P2 Close Re-entry / Reclaim: 126;
- total: 236.

Both R1 and R5 are one-shot rules with anchors frozen once at t+3. No later pullback may reset the level.

## Definitions

### R1 — Full Close Extreme baseline

First later close beyond the best favorable close observed from breakout bar t through t+3.

### R5 — Local Close Structure challenger

Let r be the first boundary-touch bar inside t+1 ... t+3.

Freeze only the favorable closes in the retest segment r ... t+3.

Trigger on the first later close beyond that frozen local close boundary.

This differs from rejected R3, which used retest-segment high/low wicks.

## Result 1 — R5 does what it was designed to do: trigger slightly earlier and slightly more often

Equal-market trigger coverage:

- R1: **82.38%**
- R5: **84.86%**

No-trigger:

- R1: 17.62%
- R5: **15.14%**

Equal-market median delay from t+3:

- R1: **1.78 bars**
- R5: **1.50 bars**

Mean delay:

- R1: 3.54 bars
- R5: **3.31 bars**

Share of all eligible P1/P2 states triggering within:

### 3 bars

- R1: 59.52%
- R5: **64.44%**

### 5 bars

- R1: 69.36%
- R5: **71.93%**

### 10 bars

- R1: 76.88%
- R5: **79.78%**

So the local-close definition genuinely addresses part of the “full new extreme may be too late” concern.

## Result 2 — The timing advantage is extremely consistent across markets

On the 194 episodes where both R1 and R5 trigger:

R5 minus R1 equal-market paired differences:

- delay: **-0.228 bars**
- confirmation-tax fraction: **-3.52 pp**
- remaining formal-regime life: **+0.228 bars**

Most importantly:

- R5 is earlier on the paired mean in **9/9 markets**;
- R5 consumes less favorable close-path excursion before confirmation in **9/9 markets**.

This is a small effect, but it is not a pooled-sample artifact.

## Result 3 — R5 pays for earlier entry with slightly dirtier post-trigger behavior

Equal-market full-population post-trigger health:

### R1

- re-expand within 5 moves: **79.60%**
- re-expand within 10: **86.24%**
- old-box failure next 3 closes: **12.45%**
- remaining formal life >=20: **70.78%**

### R5

- re-expand within 5 moves: **77.69%**
- re-expand within 10: **84.79%**
- old-box failure next 3 closes: **15.04%**
- remaining formal life >=20: **68.99%**

R5 therefore gives up approximately:

- **-1.91 pp** 5-move re-expansion;
- **-1.44 pp** 10-move re-expansion;
- **+2.59 pp** more old-box failure;
- **-1.79 pp** remaining-life >=20.

This is the expected price of a less demanding confirmation rule.

## Result 4 — On the exact same triggered episodes, health is nearly identical

Restricting to the 194 episodes where both rules eventually trigger:

R5 minus R1 paired equal-market differences:

- 5-move re-expansion: **-0.04 pp**
- 10-move re-expansion: **-0.53 pp**
- old-box failure: **+0.85 pp**

So most of the full-population health deterioration comes from R5 admitting additional / earlier cases that R1 either delays or never admits.

This is important:

> **R5 is not intrinsically producing much worse entries on common episodes; its tradeoff comes mainly from broader / earlier coverage.**

## Result 5 — R5 reduces confirmation tax modestly

Equal-market mean ATR progress consumed before trigger:

- R1: **0.851 ATR**
- R5: **0.738 ATR**

Equal-market median fraction of eventual favorable close excursion consumed:

- R1: **22.5%**
- R5: **20.8%**

So R5 saves roughly:

- 0.11 ATR of close-path confirmation distance on average;
- about 1.7 percentage points of median favorable-excursion tax in the full population.

On paired episodes, the tax reduction is larger at roughly 3.5 pp.

## Result 6 — The benefit is larger in P1 than P2

### P1 Wick Retest / Hold

Coverage:

- R1: 83.64%
- R5: **87.85%**

Median delay:

- R1: 2.50 bars
- R5: **2.22 bars**

But R5 is visibly dirtier in P1:

- re-expand 5: 77.2% -> **73.1%**
- re-expand 10: 84.9% -> **81.1%**
- old-box failure: 9.0% -> **12.9%**

### P2 Reclaim

Coverage:

- R1: 82.29%
- R5: **82.98%**

Health is much closer:

- re-expand 5: 78.3% vs 78.0%
- re-expand 10: both ~85.5%
- old-box failure: 18.0% vs 18.8%

Interpretation:

> R5's main incremental coverage comes from clean-hold P1 states, and that extra early admission is somewhat noisier.

This is diagnostic only. No P1/P2-specific trigger is created.

## Result 7 — Temporal robustness is acceptable, but R5 is consistently the slightly looser rule

### 2010–2014

Coverage is identical at ~81.7%.

Re-expansion is essentially identical.

R5 old-box failure is about +1.9 pp higher.

### 2015–2019

Coverage:

- R1: 88.1%
- R5: **90.3%**

Re-expand 5:

- R1: 76.5%
- R5: 74.3%

Re-expand 10 is effectively identical.

Old-box failure:

- R1: 13.8%
- R5: 18.3%

### 2020–2026

Coverage:

- R1: 79.8%
- R5: **84.0%**

Median delay:

- R1: 4.17 bars
- R5: **2.89 bars**

This is the largest practical timing gain.

But re-expansion becomes somewhat weaker:

- 5 moves: 76.9% -> 73.2%
- 10 moves: 90.2% -> 85.2%

There is no 2015–2019 collapse. The tradeoff is instead stable in form:

> **R5 is earlier / broader and slightly dirtier.**

## Result 8 — Direction robustness is also acceptable

### Markdown

Coverage:

- R1: 81.4%
- R5: 83.4%

Re-expand 10 is effectively identical.

Old-box failure rises from 11.2% to 13.1%.

### Markup

Coverage:

- R1: 83.1%
- R5: 85.8%

Median delay improves from 2.17 to 1.61 bars.

Re-expand 10 falls from 89.0% to 85.8%.

Old-box failure rises from 12.4% to 14.9%.

No direction-specific rule is justified.

## Research decision

### R5 passes as a genuine frontier challenger

R5 succeeds at its narrow intended objective:

- slightly higher coverage;
- slightly earlier trigger;
- lower confirmation tax;
- consistent timing advantage across 9/9 markets;
- no temporal or direction collapse.

It therefore deserves to remain on the Resume frontier.

### R5 does NOT dominate R1

R5's earlier / broader confirmation comes with:

- modestly lower re-expansion rates;
- modestly higher old-box failure;
- slightly lower remaining-regime durability.

So the correct conclusion is not:

> “R5 is better.”

It is:

> **R1 and R5 define a real confirmation frontier.**

- **R1** = more conservative, slightly later, slightly cleaner.
- **R5** = slightly earlier, slightly broader, slightly noisier.

### Stop definition-only Resume research here

The preregistered stop rule is now reached.

The local-close challenger added a meaningful but modest frontier point. There is no justification to continue inventing more swing / close / wick definitions on the same discovery sample.

Resume-definition research should stop.

## Implication for the eventual second-entry policy

The next research question is no longer “what is Resume?”

It is economic:

> **Does the earlier R5 timing create enough additional captured trend to compensate for its slightly higher false-resume / lower continuation quality, compared with the cleaner R1 confirmation?**

That requires a separately preregistered add-risk / economic-policy study.

At minimum, that study should retain:

- R0 — act immediately once P1/P2 is known at t+3;
- R5 — local-close Resume;
- R1 — full favorable close Resume;

with R4 +0.5 ATR retained only as a conservative momentum benchmark if needed.

No production sizing conclusion is made here.

Refs #78, #80, #76.
