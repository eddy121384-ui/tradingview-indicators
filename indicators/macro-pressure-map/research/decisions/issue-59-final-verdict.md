# Issue #59 — Final Research Verdict for Macro Pressure Map V6.6

Status: **FINAL SYNTHESIS COMPLETE — POST-REVIEW STATISTICAL AUDIT**

Final verdict category: **`partially_validated_some_axes_or_transitions_useful`**

## Executive decision

Macro Pressure Map V6.6 should be **kept as the frozen benchmark**, but the claims around it must be narrower than the first synthesis suggested.

The evidence does **not** support:
- treating V6.6 as a direct directional trading signal;
- reading static `Goldilocks`, `Reflation`, or `Stagflation` labels as deterministic forecasts;
- claiming any individual GPI / IPI / FCPI axis has a robust standalone out-of-component predictive edge;
- claiming the joint GPI+IPI effect was statistically precise in both training and holdout.

The evidence **does** support:
- V6.6 as a coherent macro-state compression framework;
- transition / impulse information being more useful than static level labels;
- retaining GPI and IPI as the two main macro-pressure axes;
- retaining FCPI as financial-stress / risk context;
- a **frozen-threshold 2020–2026 holdout result** in which synchronized GPI+IPI transitions discriminate future nominal Treasury yields and ZN better than either axis alone.

Practical architecture decision:

- **GPI — KEEP**
- **IPI — KEEP**
- **GPI+IPI synchronized transition / alignment — KEEP; strongest decision-grade result**
- **FCPI — KEEP AS STRESS / RISK OVERLAY; DO NOT PROMOTE AS STANDALONE PREDICTOR**
- **Static 3x3 regime labels — KEEP AS DESCRIPTIVE UI, but demote relative to transition/alignment information**
- **V6.6 parameters — DO NOT RETUNE in Issue #59**

A future V6.7 should be a separately specified design/research iteration, not an in-place optimization of this sample.

---

## 1. Engineering validity — PASS

The Python research mirror was verified against user-supplied TradingView Pine Logs covering 2007–2026.

After correcting Pine-compatible `na` rolling semantics around zero-crossing real-yield ROC, the default market-only Python mirror reproduces the Pine V6.6 plotted axes to effectively machine precision after warmup.

Therefore the historical diagnostics are testing the intended V6.6 calculation rather than a materially different Python approximation.

Evidence:
- `issue-59-tradingview-parity.md`
- `issue-59-tradingview-parity.json`

---

## 2. Review-driven statistical correction

A later Codex review identified two material problems in the first joint-holdout inference:

1. entry events could re-enter within the 20-day outcome horizon, producing overlapping forward returns that were bootstrapped as if independent;
2. training events in the final 20 trading rows of 2019 could use forward returns extending into the 2020 holdout.

The corrected methodology now:
- detects true entries on the complete chronological frame before sample splitting;
- applies a shared horizon-length embargo across positive and negative events so accepted forward windows do not overlap;
- purges the final 20 trading rows from training outcome evaluation;
- keeps threshold estimation frozen through 2019-12-31;
- leaves all V6.6 production parameters unchanged.

The same overlap audit was also applied to the single-axis OOC event study.

This correction materially narrows the claims below.

---

## 3. GPI verdict — KEEP, NOT STANDALONE PREDICTOR

### What works

GPI remains economically coherent as a growth / cyclical pressure axis.

Sharp strengthening and weakening correspond to sensible cyclical, commodity, credit, and breakeven behavior in descriptive diagnostics. GPI also contributes materially to the joint GPI+IPI transition state that survives the holdout audit.

### What does not work

Static GPI level is not a stable SPY long/short signal.

After applying non-overlapping event windows to the stricter out-of-component study, no main 20d GPI OOC confidence interval excludes zero. Corrected GPI -> US10Y separation is about `+4.26 bp` versus `+6.64 bp` for the Copper/Gold baseline, with a wide CI crossing zero.

### Decision

**KEEP GPI** as a growth/cyclical state and transition axis, especially as one half of joint alignment. Do not claim robust standalone external predictive superiority.

---

## 4. IPI verdict — KEEP, PREVIOUS SINGLE-AXIS EDGE WITHDRAWN

### What works

IPI remains economically coherent as an inflation-pressure axis and contributes to the strongest joint transition result.

### What changed

The first OOC report highlighted IPI-EURUSD and 60d rates/TLT as the strongest single-axis incremental evidence. Those conclusions depended on overlapping event windows.

After enforcing horizon-length embargoes:
- IPI -> EURUSD 20d spread changes from about `-0.82%` to about `+0.47%`, with CI crossing zero;
- IPI -> US10Y 60d becomes about `+7.92 bp`, CI crossing zero;
- IPI -> TLT 60d becomes about `-1.21%`, CI crossing zero.

The earlier claim that IPI had a decision-grade standalone external edge is therefore **withdrawn**.

### Decision

**KEEP IPI** as an inflation-pressure axis and as the second half of GPI+IPI alignment. Do not describe IPI as a validated standalone external predictor.

---

## 5. FCPI verdict — KEEP AS OVERLAY

FCPI remains directionally coherent as a compression of credit, rates/dollar, and volatility stress.

However, even before the overlap audit it did not beat simple HY OAS / VIX baselines consistently. After de-overlap, no main FCPI 20d OOC confidence interval excludes zero.

### Decision

**KEEP FCPI as financial-stress / risk-context overlay.**

Do not promote FCPI into a predictive gating rule based on Issue #59. Any simplification or redesign belongs in a separately pre-registered V6.7 study.

---

## 6. Static Core Regime verdict — DESCRIPTIVE, NOT PREDICTIVE

The 3x3 labels create useful historical macro descriptions and cross-asset fingerprints, but they are not reliable deterministic forward-return rules.

### Decision

Keep the labels for communication and state compression, but UI/documentation should emphasize:

> current macro state + direction of change + cross-axis alignment

rather than:

> regime name = future trade

---

## 7. Corrected joint GPI + IPI holdout — STRONGEST RESULT

Threshold-definition period:
- 2008-06-02 through 2019-12-31

Training outcome evaluation:
- purged through 2019-12-02 so no 20d training return enters 2020

Holdout:
- 2020-01-02 through 2026-08-14

Frozen 20d transition cuts:
- GPI: low `-21.06`, high `+19.53`
- IPI: low `-21.20`, high `+22.51`

Joint states:
- **Reflation impulse** = GPI high + IPI high
- **Slowdown / disinflation impulse** = GPI low + IPI low

A shared 20-trading-row embargo removes overlapping event windows.

Non-overlapping joint event counts:
- training: **23** reflation vs **33** slowdown/disinflation
- holdout: **15** vs **15**

Corrected Reflation minus Slowdown/Disinflation forward-20d spread:

| Outcome | Training joint | Training 95% CI | Holdout joint | Holdout 95% CI | Holdout GPI-only | Holdout IPI-only |
|---|---:|---:|---:|---:|---:|---:|
| US10Y | +5.87 bp | [-3.88, +15.69] | **+18.81 bp** | **[+2.19, +35.60]** | +11.10 bp | +10.79 bp |
| US02Y | +3.30 bp | [-3.38, +10.11] | **+17.68 bp** | **[+2.80, +33.19]** | +11.62 bp | +5.53 bp |
| ZN1! | -0.44% | [-1.11%, +0.24%] | **-1.18%** | **[-2.15%, -0.21%]** | -0.64% | -0.59% |
| TLT | -1.35% | [-3.23%, +0.42%] | -2.03% | [-4.29%, +0.40%] | -1.20% | -1.65% |

### What the corrected study earns

- The **training effect is directionally coherent but not statistically precise** after de-overlap.
- The **holdout effect survives** the stricter methodology for US10Y, US02Y, and ZN.
- On those strongest holdout outcomes, the joint GPI+IPI contrast is larger than GPI-only or IPI-only.
- This is the main decision-grade evidence that the combination contains information beyond either individual axis.

### What it does not earn

- significance in both training and holdout;
- a universal cross-asset rule;
- a stable FX edge;
- TLT statistical significance;
- a complete trading strategy;
- causal macro forecasting.

### Decision

**KEEP the GPI+IPI synchronized transition architecture, with the claim explicitly narrowed to holdout-supported Treasury / ZN discrimination.**

---

## 8. Final KEEP / SIMPLIFY / RECALIBRATE decision

### KEEP

- GPI calculation and role
- IPI calculation and role
- GPI+IPI joint transition architecture
- FCPI as stress/risk context
- V6.6 as the frozen benchmark

### SIMPLIFY / REFRAME IN A FUTURE VERSION

- reduce emphasis on static regime names as forecasts
- surface transition velocity / impulse more clearly
- surface GPI+IPI alignment / convergence more clearly
- present FCPI primarily as a conditioning overlay
- distinguish descriptive state from prospective signal in UI/documentation

### DO NOT RECALIBRATE YET

Do **not** optimize on Issue #59 data:
- axis or component weights
- +/-10 / +/-30 / +/-60 thresholds
- 20 / 63 / 252 lookbacks
- smoothing
- regime boundaries

Any parameter redesign requires a separately defined fresh OOS evaluation.

---

## 9. Claims V6.6 has earned

V6.6 can defensibly be described as:
- a macro market-state compression dashboard;
- a three-axis growth / inflation / financial-stress framework;
- a tool where **changes and synchronized axis transitions are more informative than static labels**;
- a framework with frozen-threshold holdout evidence that joint GPI+IPI impulses discriminate future nominal Treasury-rate / ZN behavior.

---

## 10. Claims V6.6 has NOT earned

Do not claim:
- profitable standalone trading strategy;
- universal regime-to-return mapping;
- reliable SPY timing from static GPI / regime states;
- robust standalone GPI or IPI OOC predictive edge;
- FCPI superiority over simple stress proxies;
- stable FX edge across eras;
- optimal weights / thresholds;
- causal macro forecasting.

---

## 11. Recommendation for V6.7

Open a **separate** V6.7 issue only after Issue #59 / PR #60 is reviewed and merged.

The V6.7 question should be:

> How should the indicator expose the information that Issue #59 actually validated?

Priority design hypotheses:
1. explicit GPI / IPI transition velocity or impulse state;
2. joint alignment / convergence indicator;
3. static regime labels made secondary to transition state;
4. FCPI retained as risk context unless new evidence supports more;
5. any parameter redesign pre-registered and tested on fresh OOS data.

---

## Final conclusion

Macro Pressure Map V6.6 is **not validated as a universal trading signal**, and the post-review audit removes the earlier standalone IPI edge and the claim of training+holdout significance.

It is nevertheless **not merely decorative complexity**.

The strongest surviving evidence lies in **synchronized GPI+IPI transitions**, with the clearest decision-grade result in the 2020–2026 frozen-threshold holdout for nominal US Treasury yields and ZN futures.

Therefore the final Issue #59 classification remains:

**`partially_validated_some_axes_or_transitions_useful`**

with the practical product decision:

**KEEP V6.6 as the frozen benchmark; REFRAME the next version around transition/alignment; KEEP FCPI as context; DO NOT RECALIBRATE on this sample.**
