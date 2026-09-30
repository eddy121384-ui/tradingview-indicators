# Issue #78 — Local Close Resume Challenger Preregistration
## Frozen retest-segment close boundary vs R1 full close extreme

## Purpose

Resume Trigger Stage 1 retained R1 — first new favorable close extreme beyond all closes known through t+3 — as the clean baseline.

The preregistered high/low-based local-structure challenger R3 failed its intended purpose because retest wicks mechanically raised the hurdle and often made it later than R1.

This study tests one materially different, structurally motivated challenger:

> **Freeze the favorable CLOSE boundary of the retest segment itself, then trigger on the first later close beyond it.**

The purpose is not to search for a better threshold. It is to test whether a genuinely local close-structure break confirms resume earlier / more broadly than R1 without a material loss in post-trigger quality.

## Frozen base population

Reuse exactly the Resume Trigger Stage 1 eligible population:

- P1 Wick Retest / Hold;
- P2 Close Re-entry / Reclaim;
- path known at close of t+3;
- same first genuine post-entry breakout;
- same causal five-bar pre-breakout box;
- same frozen three-bar acceptance window;
- same nine-market daily discovery sample.

Expected eligible population:

- P1 = 110;
- P2 = 126;
- total = 236.

No P0 / P3 events enter this challenger.

## One-shot / non-recursive rule

All reference levels are frozen once at t+3.

No later pullback may reset or replace any anchor.

Each episode gets at most one trigger per definition.

If no trigger occurs before formal-regime end, record no-trigger.

## Frozen baseline — R1 Full Close Extreme

Unchanged from Resume Trigger Stage 1.

Freeze best favorable close from breakout bar t through t+3.

Markup:

`r1_anchor = max(close[t:t+3])`

Trigger:

`first later close > r1_anchor`

Markdown:

`r1_anchor = min(close[t:t+3])`

Trigger:

`first later close < r1_anchor`

## Challenger — R5 Retest-Segment Close Structure

Let `r` be the first boundary-touch bar inside t+1 ... t+3.

Freeze only the closes from the retest segment:

`r ... t+3`

Markup:

`r5_anchor = max(close[r:t+3])`

Trigger:

`first later close > r5_anchor`

Markdown:

`r5_anchor = min(close[r:t+3])`

Trigger:

`first later close < r5_anchor`

Interpretation:

> once the retest episode is known, price must close beyond the strongest favorable CLOSE created during the retest itself.

Important distinction from rejected R3:

- R3 used retest-segment high/low wicks;
- R5 uses retest-segment closes only.

Important distinction from R1:

- R1 may include a much stronger breakout-bar / pre-touch close;
- R5 ignores those earlier closes and asks only whether the retest structure itself has been broken.

## Why this is a legitimate challenger

This definition is not chosen from outcome search.

It follows directly from the failure mode diagnosed in R3:

> wick-defined local structure was too strict because the wick itself raised the confirmation hurdle.

The close-only variant tests the same local-structure idea while removing that mechanical problem.

No alternate local-close variants will be searched in this stage.

# Primary metrics

Reuse the exact Resume Trigger Stage 1 metrics.

## T1 — Trigger coverage

Share of P1/P2 episodes triggering before formal-regime end.

Report no-trigger rate.

## T2 — Confirmation delay

Bars from t+3 to trigger.

Report:

- median;
- equal-market mean;
- fraction of all eligible states triggering within 3 / 5 / 10 bars.

## T3 — Confirmation tax

Directional favorable close-path movement consumed before trigger:

- ATR-normalized trigger close progress;
- fraction of eventual favorable close-path excursion already consumed.

## T4 — Remaining runway

At trigger:

- mean remaining formal-regime life;
- share with >=10 bars remaining;
- share with >=20 bars remaining.

# Post-trigger health

Measured strictly after trigger bar.

## H1 — Re-expand within next 5 moves

## H2 — Re-expand within next 10 moves

## H3 — Old-box failure within next 3 closes

Adverse outcome.

## H4 — Remaining formal-regime life >=10 moves

## H5 — Remaining formal-regime life >=20 moves

## H6 — Remaining formal-regime life

Same definitions as Resume Trigger Stage 1.

# Primary comparison — paired R5 vs R1

The main inference uses only episodes where both R5 and R1 trigger.

For each market compare:

- trigger timing difference;
- confirmation-tax difference;
- remaining-life difference;
- H1 / H2 difference;
- H3 difference.

Also report full-population coverage differences so a rule cannot win only by refusing more episodes.

## Admission logic

R5 improves the resume frontier only if it shows most of the following:

1. **higher or at least non-inferior coverage** versus R1;
2. **earlier trigger** on paired episodes;
3. **lower confirmation tax**;
4. no material deterioration in 5/10-move re-expansion;
5. no material increase in old-box failure;
6. useful remaining runway;
7. broad market consistency;
8. no material 2015–2019 collapse;
9. similar behavior in Markup / Markdown;
10. no path-specific tuning.

No single metric is sufficient.

## Interpretation rules

### If R5 is earlier and equally healthy

Retain R5 as a genuine local second-entry challenger alongside R1.

### If R5 is earlier but materially dirtier

Retain the tradeoff frontier; do not call R5 superior.

### If R5 is not earlier / broader

Reject the local-close challenger and stop resume-definition search.

Carry R1 forward to the later economic-policy test.

### If R5 wins only through a subset

Do not create market / direction / P1-vs-P2-specific rules.

# Temporal robustness

Repeat coverage / delay / H1–H5 for:

- 2010–2014;
- 2015–2019;
- 2020–2026.

2015–2019 remains the required stress era.

# Direction robustness

Report Markup / Markdown separately.

# Path diagnostics

Report P1 and P2 separately, but do not change the rule.

# Guardrails

- no new lookback;
- no new ATR threshold;
- no alternate definition of “retest segment”;
- first touch remains frozen from the prior path study;
- no anchor reset after t+3;
- no wick / close hybrid search;
- no minimum breakout distance added;
- no market-specific / direction-specific / path-specific thresholds;
- no post-hoc trigger horizon;
- no PnL / Sharpe;
- discovery-sample result remains in-sample.

## Stop rule

This is the **final definition-only Resume challenger** planned before an economic-policy study.

If R5 does not materially improve the frontier versus R1, resume-definition research stops and R1 is carried forward as the baseline.

## Intended answer

> **Can breaking the frozen retest segment’s favorable CLOSE structure give a genuinely earlier second-entry confirmation than waiting for a full new favorable close extreme, without materially increasing false resumes?**

Refs #78, #80, #76.
