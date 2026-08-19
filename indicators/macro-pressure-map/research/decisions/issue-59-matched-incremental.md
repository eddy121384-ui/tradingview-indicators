# Issue #59 — Matched conditional incremental test

Status: **EXPLORATORY MATCHED TEST COMPLETE**

This study was added after Codex review identified that comparing independently embargoed joint, GPI-only, and IPI-only event samples does not establish incremental information.

## Evidence boundary

The 2020–2026 era is **not an untouched holdout**. Earlier Issue #59 diagnostics had already inspected that period and helped motivate the synchronized-transition hypothesis. Therefore every result below is exploratory.

Thresholds remain frozen from the 2008-06-02 through 2019-12-31 definition sample:

- GPI d20: low `-21.06`, high `+19.53`
- IPI d20: low `-21.20`, high `+22.51`

No V6.6 production parameter is changed.

## Matched method

The test fixes one de-overlapped **anchor-event universe** at a time:

1. GPI high/low entry events, with one shared 20-trading-row embargo; then tag whether IPI is already in the same-direction extreme bucket on that exact event date.
2. IPI high/low entry events, with the same method; then tag GPI confirmation.

For each anchor universe, compare:

- `anchor-only spread` = high minus low outcome across all accepted anchor events;
- `confirmed spread` = high minus low outcome only where the second axis confirms;
- `confirmation lift` = confirmed spread minus anchor-only spread.

Bootstrap draws resample the same positive/negative anchor events and recompute both nested statistics from each draw. This directly tests the incremental-lift claim without comparing unrelated event dates or sample sizes.

## Development sample

Development outcome evaluation ends 2019-12-02 after the existing 20-row training-tail purge.

Event counts:

- GPI anchor: **93** events, **21** with IPI same-direction confirmation.
- IPI anchor: **79** events, **34** with GPI same-direction confirmation.

For the principal Treasury outcomes, every confirmation-lift 95% interval crosses zero.

Examples:

| Anchor | Outcome | Confirmation lift | 95% CI |
|---|---:|---:|---:|
| GPI | US10Y | +5.85 bp | [-9.25, +21.02] |
| GPI | US02Y | +2.41 bp | [-7.38, +12.75] |
| GPI | ZN1! | -0.49% | [-1.56%, +0.56%] |
| GPI | TLT | -1.72% | [-4.02%, +0.59%] |
| IPI | US10Y | +5.88 bp | [-4.18, +16.61] |
| IPI | US02Y | +1.58 bp | [-5.77, +8.95] |
| IPI | ZN1! | -0.73% | [-1.60%, +0.09%] |
| IPI | TLT | -0.21% | [-2.29%, +1.72%] |

## Post-2019 exploratory era

Evaluation era: 2020-01-02 through 2026-08-14.

Event counts:

- GPI anchor: **45** events, **17** with IPI confirmation.
- IPI anchor: **51** events, **10** with GPI confirmation.

### GPI anchor; add IPI confirmation

| Outcome | GPI anchor-only | GPI + IPI confirmed | Confirmation lift | Lift 95% CI |
|---|---:|---:|---:|---:|
| US10Y | +11.10 bp | +12.48 bp | **+1.38 bp** | **[-17.88, +22.49]** |
| US02Y | +11.62 bp | +8.05 bp | **-3.58 bp** | **[-24.86, +18.47]** |
| ZN1! | -0.64% | -0.74% | **-0.11%** | **[-1.33%, +1.04%]** |
| TLT | -1.20% | -1.01% | **+0.18%** | **[-2.80%, +2.95%]** |

### IPI anchor; add GPI confirmation

| Outcome | IPI anchor-only | IPI + GPI confirmed | Confirmation lift | Lift 95% CI |
|---|---:|---:|---:|---:|
| US10Y | +10.79 bp | +8.51 bp | **-2.28 bp** | **[-22.19, +15.56]** |
| US02Y | +5.53 bp | +12.60 bp | **+7.07 bp** | **[-12.43, +26.94]** |
| ZN1! | -0.59% | -0.61% | **-0.02%** | **[-1.18%, +1.23%]** |
| TLT | -1.65% | -1.28% | **+0.37%** | **[-2.62%, +3.62%]** |

FX outcomes also fail to produce a confirmation-lift interval excluding zero.

## Verdict from the matched test

**The second axis does not demonstrate incremental predictive information beyond the anchor axis in this sample.**

The earlier joint Reflation-vs-Slowdown Treasury contrast remains an interesting descriptive / exploratory association, but two stronger claims are withdrawn:

1. 2020–2026 cannot be described as an untouched decision-grade holdout because the era had already been inspected before the joint hypothesis was selected.
2. A larger raw joint spread cannot be interpreted as incremental information because the matched confirmation-lift test does not reject zero.

This does not prove GPI+IPI interaction is useless. It means Issue #59 has **not earned** the claim that synchronized movement predicts external assets better than the individual axes.

## Implication for the final Issue #59 verdict

The evidence now fits the category:

**`descriptive_but_little_incremental_information`**

V6.6 remains:

- engineering-valid;
- coherent as growth / inflation / financial-stress state compression;
- useful as descriptive market context.

But Issue #59 does not establish robust standalone or joint incremental predictive value beyond simpler / single-axis information.

Any future predictive claim for GPI+IPI alignment should be pre-registered now and tested only on genuinely unseen future data.
