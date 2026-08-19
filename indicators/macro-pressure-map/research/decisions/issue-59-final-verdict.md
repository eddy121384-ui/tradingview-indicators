# Issue #59 — Final Research Verdict for Macro Pressure Map V6.6

Status: **FINAL SYNTHESIS COMPLETE — POST-REVIEW REPRODUCIBILITY AUDIT**

Final verdict category: **`descriptive_but_little_incremental_information`**

## Executive decision

Macro Pressure Map V6.6 should be **kept as the frozen benchmark and descriptive macro-state dashboard**, but Issue #59 does **not** establish robust incremental predictive value.

The final evidence supports:

- engineering-valid Pine ↔ Python parity;
- coherent growth / inflation / financial-stress state compression;
- transition / impulse information being more informative descriptively than static regime names;
- keeping GPI, IPI, and FCPI as interpretable state axes;
- keeping GPI+IPI interaction as exploratory research / context.

The final evidence does **not** support:

- a standalone trading signal;
- a universal regime-to-return map;
- robust standalone GPI / IPI / FCPI out-of-component predictive superiority;
- a validated incremental predictive benefit from adding the second axis to GPI or IPI;
- treating 2020–2026 as an untouched holdout for the synchronized-transition hypothesis;
- optimal weights, thresholds, lookbacks, or regime boundaries.

Practical architecture decision:

- **GPI — KEEP as descriptive growth/cyclical state + transition axis**
- **IPI — KEEP as descriptive inflation state + transition axis**
- **FCPI — KEEP as financial-stress / risk-context overlay**
- **GPI+IPI alignment — KEEP as descriptive / exploratory interaction; predictive incrementality NOT demonstrated**
- **Static 3x3 regime labels — KEEP as descriptive UI, not deterministic forward calls**
- **V6.6 parameters — DO NOT RETUNE on Issue #59 data**

---

## 1. Engineering validity — PASS

The Python research mirror was verified against the user-supplied TradingView Pine Logs covering 2007–2026.

After correcting Pine-compatible `na` rolling semantics around zero-crossing real-yield ROC, the default market-only Python mirror reproduces the Pine V6.6 plotted axes to effectively machine precision after warmup.

Therefore the historical diagnostics test the intended V6.6 calculation rather than a materially different Python approximation.

Evidence:
- `issue-59-tradingview-parity.md`
- `issue-59-tradingview-parity.json`

---

## 2. Review-driven statistical and reproducibility audit

Successive Codex reviews materially narrowed the claims and improved the evidence pipeline.

Corrections now in the research code:

1. weekend / holiday public-data observations are preserved before anchor-calendar forward-fill;
2. event studies apply horizon-length shared embargoes so accepted forward windows do not overlap;
3. the final 20 development rows are purged before forward-20d evaluation so late-2019 events cannot use 2020 prices;
4. 2020–2026 is explicitly classified as **exploratory reused-era evidence**, not an untouched holdout;
5. raw joint-vs-single spread comparisons are not interpreted as incremental information;
6. matched conditional inference fixes one anchor-event universe at a time;
7. machine-generated matched evidence is separated from curated decision memos so rerunning a script cannot silently overwrite the research interpretation.

Reproducibility contract:
- `research/REPRODUCIBILITY.md`
- generated matched outputs default to `research/generated/issue-59-matched-incremental.generated.{json,md}`
- curated synthesis remains under `research/decisions/`

No V6.6 production parameter changed.

---

## 3. Axis verdicts

### GPI — KEEP AS DESCRIPTIVE AXIS

GPI remains economically coherent as a growth / cyclical pressure summary, but stricter de-overlapped OOC testing does not establish robust external predictive superiority over simpler proxies.

### IPI — KEEP AS DESCRIPTIVE AXIS

IPI remains economically coherent as an inflation-pressure summary. The earlier apparent EURUSD and 60d rates/TLT single-axis edges disappeared after non-overlapping event windows were enforced and are withdrawn.

### FCPI — KEEP AS RISK CONTEXT

FCPI remains useful as a compression of credit, rates/dollar, and volatility stress, but Issue #59 does not establish stable incremental predictive value over simple HY OAS / VIX baselines.

---

## 4. Static Core Regime verdict — DESCRIPTIVE, NOT PREDICTIVE

The 3x3 regime labels create understandable historical macro-state fingerprints, but they are not reliable deterministic forward-return rules.

Keep them for communication / state compression, while emphasizing:

> current state + direction of change + context

rather than:

> regime name = future trade

---

## 5. Joint GPI + IPI historical pattern — INTERESTING, BUT EXPLORATORY

The corrected non-overlapping joint event study still shows a notable post-2019 Treasury association:

- Reflation impulse = GPI high + IPI high
- Slowdown / disinflation impulse = GPI low + IPI low

Post-2019 exploratory Reflation minus Slowdown/Disinflation forward-20d spread:

- US10Y: **+18.81 bp**
- US02Y: **+17.68 bp**
- ZN1!: **-1.18%**
- TLT: **-2.03%**

But this period had already been inspected before the joint hypothesis was selected. It is therefore retained only as an **exploratory historical association**, not untouched OOS validation.

Evidence:
- `issue-59-joint-holdout.md` — historical filename retained; interpretation corrected
- `joint_holdout_validation.py` — generator now emits exploratory reused-era semantics

---

## 6. Matched conditional incremental test — NO INCREMENTAL CLAIM EARNED

The matched study fixes one de-overlapped anchor-event universe at a time and asks whether same-direction confirmation from the second axis improves the high-minus-low spread.

The statistics below are synchronized to the actual script-generated evidence. Display values are rounded from `research/generated/issue-59-matched-incremental.generated.json`.

### GPI anchor; add IPI confirmation — post-2019 exploratory era

| Outcome | Anchor-only | Confirmed | Confirmation lift | Generated 95% CI |
|---|---:|---:|---:|---:|
| US10Y | +11.10 bp | +12.48 bp | +1.38 bp | [-17.98, +23.78] |
| US02Y | +11.62 bp | +8.05 bp | -3.58 bp | [-25.17, +18.80] |
| ZN1! | -0.64% | -0.74% | -0.11% | [-1.40%, +1.08%] |
| TLT | -1.20% | -1.01% | +0.18% | [-2.80%, +2.77%] |

### IPI anchor; add GPI confirmation — post-2019 exploratory era

| Outcome | Anchor-only | Confirmed | Confirmation lift | Generated 95% CI |
|---|---:|---:|---:|---:|
| US10Y | +10.79 bp | +8.51 bp | -2.28 bp | [-22.50, +15.20] |
| US02Y | +5.53 bp | +12.60 bp | +7.07 bp | [-11.67, +25.52] |
| ZN1! | -0.59% | -0.61% | -0.02% | [-1.16%, +1.26%] |
| TLT | -1.65% | -1.28% | +0.37% | [-2.65%, +3.64%] |

The principal confirmation-lift confidence intervals also cross zero in the development sample.

### Decision

**Issue #59 does not demonstrate that adding the second axis provides incremental predictive information beyond the anchor axis.**

Synchronized GPI+IPI movement may identify a distinctive historical subset, but the predictive-incrementality claim is withdrawn.

Evidence:
- `issue-59-matched-incremental.md`
- `issue-59-matched-incremental.json`
- generated evidence under `research/generated/`

---

## 7. Final KEEP / SIMPLIFY / RECALIBRATE decision

### KEEP

- GPI as growth/cyclical state compression
- IPI as inflation-state compression
- FCPI as stress/risk context
- GPI+IPI alignment as descriptive / exploratory context
- V6.6 as the frozen benchmark

### SIMPLIFY / REFRAME

A future version may improve communication by:

- making transition velocity / impulse easier to see;
- treating static regime names as secondary descriptors;
- presenting FCPI clearly as risk context;
- separating **descriptive state** from **prospective evidence** in the UI.

This is a UX / interpretation improvement, not evidence of predictive alpha.

### DO NOT RECALIBRATE YET

Do not optimize on Issue #59 data:

- axis or component weights;
- +/-10 / +/-30 / +/-60 thresholds;
- 20 / 63 / 252 lookbacks;
- smoothing;
- regime boundaries.

Any parameter redesign would turn this already-inspected sample into training data and requires a separately pre-registered future evaluation.

---

## 8. Claims V6.6 has earned

V6.6 can defensibly be described as:

- an engineering-verified macro market-state compression dashboard;
- a three-axis growth / inflation / financial-stress framework;
- a descriptive tool where changes / transitions often reveal more context than static labels;
- a framework that generates interesting historical cross-asset patterns worth prospective study.

## 9. Claims V6.6 has NOT earned

Do not claim:

- profitable standalone trading strategy;
- universal regime-to-return mapping;
- reliable SPY timing;
- robust standalone GPI / IPI / FCPI external predictive edge;
- validated incremental predictive value from GPI+IPI synchronization;
- an untouched 2020–2026 holdout for the joint hypothesis;
- FCPI superiority over simple stress proxies;
- stable FX edge;
- optimal parameters;
- causal macro forecasting.

---

## 10. Recommendation after Issue #59

After PR #60 receives a clean review and lands on `main`, close Issue #59.

Two separate follow-ups are appropriate:

1. **Prospective OOS validation** — freeze the GPI+IPI confirmation hypothesis now and evaluate only genuinely unseen future observations after the current 2026-08-14 evidence cutoff.
2. **V6.7 UI / interpretation redesign** — if desired, improve how transition velocity, regime context, and FCPI risk state are displayed, without claiming the redesign creates predictive edge.

Do not merge those two goals into one optimization exercise.

---

## Final conclusion

Macro Pressure Map V6.6 is **not validated as a predictive trading model**, and the final matched audit does not prove incremental information beyond simpler / single-axis signals.

It is nevertheless useful as a coherent, engineering-verified **descriptive macro-state map**.

Therefore the final Issue #59 classification is:

**`descriptive_but_little_incremental_information`**

with the practical product decision:

**KEEP V6.6 as the frozen descriptive benchmark; REFRAME claims around state/context; DO NOT RECALIBRATE on this sample; prospectively test any future predictive hypothesis on genuinely unseen data.**
