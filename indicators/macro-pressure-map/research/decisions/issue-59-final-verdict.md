# Issue #59 — Final Research Verdict for Macro Pressure Map V6.6

Status: **FINAL SYNTHESIS COMPLETE**

Final verdict category: **`partially_validated_some_axes_or_transitions_useful`**

## Executive decision

Macro Pressure Map V6.6 should be **kept as the frozen validated benchmark**, but its interpretation should change.

The evidence does **not** support treating V6.6 as a direct directional trading signal or reading static regime labels such as `Goldilocks`, `Reflation`, or `Stagflation` as deterministic forecasts.

The evidence **does** support V6.6 as a useful macro-state compression framework whose strongest information is in **transition / impulse / cross-axis alignment**, especially the interaction of GPI and IPI.

The most defensible architecture decision is therefore:

- **GPI — KEEP**
- **IPI — KEEP**
- **FCPI — KEEP AS STRESS / RISK OVERLAY; DO NOT PROMOTE AS STANDALONE PREDICTOR**
- **Static 3x3 regime labels — KEEP AS DESCRIPTIVE UI, but demote relative to transition/alignment information**
- **V6.6 parameters — DO NOT RETUNE in Issue #59**

A future V6.7 should be a separately specified research/design iteration, not an in-place optimization of this sample.

---

## 1. Engineering validity — PASS

The Python research mirror was verified against user-supplied TradingView Pine Logs covering 2007–2026.

After correcting Pine-compatible `na` rolling semantics around zero-crossing real-yield ROC, the default market-only Python mirror reproduces the Pine V6.6 plotted axes to effectively machine precision after warmup.

This means the historical diagnostics in Issue #59 are testing the intended V6.6 calculation rather than a materially different Python approximation.

Evidence:
- `issue-59-tradingview-parity.md`
- `issue-59-tradingview-parity.json`

---

## 2. GPI verdict — KEEP

### What works

GPI transition / impulse contains economically coherent information.

Sharp GPI strengthening is followed, on average, by stronger cyclical / reflationary behavior: stronger commodities, tighter credit, and firmer breakevens. Sharp weakening shows the opposite pattern.

The first component-overlapping study also found GPI transition separation materially stronger than Copper/Gold momentum for future oil behavior.

In the stricter out-of-component study, GPI retains some separation in nominal rates / Treasury futures, although the effect is episodic rather than universal.

### What does not work

Static GPI level is not a monotonic SPY long/short signal.

`Growth Euphoria`, `Growth Neutral`, and `Severe Slowdown` do not sort forward equity returns in a stable, economically clean way. Crisis concentration and mean reversion make naive daily-state averages misleading.

### Decision

**KEEP GPI.**

Its justified role is a growth / cyclical pressure axis and an input into cross-axis transition alignment, not a standalone equity timing model.

---

## 3. IPI verdict — KEEP

### What works

IPI shows coherent inflation / rates fingerprints.

Inflation-shock states are followed by weaker Treasury-price behavior / higher real yields, while deflation-pressure states show the opposite tendency.

The out-of-component study produced the strongest genuinely external single-axis result in Issue #59:

- IPI 20d transition extreme spread in future EURUSD: about **-0.82%**
- simple 10Y breakeven-momentum baseline: about **-0.06%**
- IPI bootstrap interval excluded zero

At 60 days, IPI also showed stronger separation than the breakeven baseline in US10Y and TLT in the full sample.

### What does not work

The effect is not stable across every era or asset.

The EURUSD result is strongest in macro-active eras and weak in the quiet 2013–2019 period. IPI is therefore not validated as a universal directional inflation trade signal.

### Decision

**KEEP IPI.**

IPI has earned a role as an inflation-pressure axis and, more importantly, as the second half of the GPI+IPI joint transition architecture.

---

## 4. FCPI verdict — KEEP AS OVERLAY / SIMPLIFY CLAIMS

### What works

FCPI is directionally coherent as a financial-stress summary:

- rising FCPI is associated with wider credit spreads and weaker risk behavior;
- falling FCPI is associated with easing stress;
- the composite compresses credit, rates/dollar, and volatility conditions into one dashboard variable.

This is useful descriptively and for risk context.

### What does not work

FCPI has **not** demonstrated stable incremental predictive value over simple HY OAS / VIX baselines on out-of-component outcomes.

No main 20d OOC FCPI spread in the stricter study had a bootstrap interval excluding zero, and signs changed materially across eras.

Exploratory use of FCPI as a conditioning filter on joint GPI+IPI events also failed to produce a stable enough train/holdout improvement to freeze as a rule.

### Decision

**KEEP FCPI, but only as a stress / risk-condition overlay.**

Do not describe FCPI as a superior standalone predictor. Do not add FCPI gating rules to V6.6 based on Issue #59.

A future V6.7 may investigate whether FCPI can be simplified, reweighted, or redesigned, but that must be a separate research task with new holdout evidence.

---

## 5. Static Core Regime verdict — DESCRIPTIVE, NOT PREDICTIVE

The 3x3 labels do create different historical cross-asset fingerprints, especially across oil, bonds, dollar, and credit.

However, the labels are not reliable deterministic forecasts.

Examples from the full sample include counterintuitive prospective behavior after `Goldilocks` and `Stagflation` states. This is not necessarily a defect in state description; it shows that a label describing what markets have recently priced is not the same as a forward-return rule.

### Decision

**KEEP the regime labels for communication and state compression, but demote them in interpretation.**

UI / documentation should emphasize:

> current macro state + direction of change + cross-axis alignment

rather than:

> regime name = future trade

---

## 6. Joint GPI + IPI transition verdict — STRONGEST RESULT

This is the strongest evidence supporting the full Macro Pressure Map concept.

Training period: 2008-06-02 to 2019-12-31.
Holdout: 2020-01-01 to 2026-08-14.

Training-period GPI/IPI 20d transition cuts were frozen and applied unchanged to holdout.

Joint states:

- **Reflation impulse** = GPI 20d change high + IPI 20d change high
- **Slowdown / disinflation impulse** = GPI 20d change low + IPI 20d change low

First-entry events only were counted.

Holdout Reflation minus Slowdown/Disinflation forward-20d separation:

- US10Y: **+15.90 bp**
- US02Y: **+16.63 bp**
- ZN1!: **-1.04%**
- TLT: **-1.44%**

For US10Y and ZN, the joint GPI+IPI contrast exceeded the individual GPI-only and IPI-only contrasts in holdout.

Bootstrap intervals for US10Y, US02Y, and ZN excluded zero in both training and holdout.

### Decision

**The GPI+IPI synchronized transition architecture is validated as useful for Treasury macro-state / directional-pressure discrimination.**

This is not a complete trading strategy, but it is meaningful incremental information and is the main reason V6.6 should be retained rather than collapsed into a few single proxies.

---

## 7. Final KEEP / SIMPLIFY / RECALIBRATE decision

### KEEP

- GPI calculation and role
- IPI calculation and role
- GPI+IPI joint architecture
- FCPI as stress/risk context
- V6.6 as the frozen benchmark

### SIMPLIFY / REFRAME IN A FUTURE VERSION

- reduce emphasis on static regime names as forecasts
- surface transition velocity / impulse more clearly
- surface GPI+IPI alignment / convergence more clearly
- present FCPI primarily as a conditioning overlay
- distinguish descriptive state from prospective signal in UI/documentation

### DO NOT RECALIBRATE YET

Do **not** optimize:

- axis weights
- component weights
- +/-10 / +/-30 / +/-60 thresholds
- 20 / 63 / 252 lookbacks
- smoothing
- regime boundaries

using this same Issue #59 sample.

Any such optimization would convert the current diagnostic sample into in-sample training data and would require a separately defined fresh OOS evaluation.

---

## 8. Claims V6.6 has earned

V6.6 can defensibly be described as:

- a macro market-state compression dashboard;
- a three-axis growth / inflation / financial-stress framework;
- a tool where **changes and synchronized axis transitions are more informative than static labels**;
- a framework with holdout evidence that joint GPI+IPI impulses discriminate future nominal Treasury-rate / ZN behavior.

---

## 9. Claims V6.6 has NOT earned

Do not claim:

- profitable standalone trading strategy;
- universal regime-to-return mapping;
- reliable SPY timing from static GPI / regime states;
- FCPI superiority over simple stress proxies;
- stable FX edge across all eras;
- optimal weights / thresholds;
- causal macro forecasting.

---

## 10. Recommendation for V6.7

Open a **separate** V6.7 issue only after Issue #59 / PR #60 is reviewed and merged.

The V6.7 research question should not be "how do we improve backtest performance?"

It should be:

> How should the indicator expose the information that Issue #59 actually validated?

Priority design hypotheses:

1. add explicit GPI / IPI transition velocity or impulse state;
2. add a joint alignment / convergence indicator;
3. make static regime labels secondary to transition state;
4. keep FCPI as a risk-context overlay unless new evidence supports more;
5. if any parameter redesign is proposed, pre-register the change and test on fresh OOS data.

---

## Final conclusion

Macro Pressure Map V6.6 is **not validated as a universal trading signal**, but it is also **not merely decorative complexity**.

Its strongest validated information lies in **macro pressure transitions and synchronized GPI+IPI movement**, with the clearest holdout evidence in nominal US Treasury rates and ZN futures.

FCPI remains useful as a stress-context layer but has not justified standalone predictive complexity.

Therefore the final Issue #59 classification is:

**`partially_validated_some_axes_or_transitions_useful`**

with the practical product decision:

**KEEP V6.6 as the frozen benchmark; REFRAME the next version around transition/alignment; DO NOT RECALIBRATE on this sample.**
