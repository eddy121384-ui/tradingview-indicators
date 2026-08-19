# Issue #59 — Joint-axis walk-forward holdout

Status: **JOINT-AXIS HOLDOUT COMPLETE — NON-OVERLAPPING EVENTS**

Purpose: test whether the frozen V6.6 **GPI+IPI combination** adds information beyond either individual axis, without retuning V6.6 and without treating overlapping forward windows as independent evidence.

## Corrected design after review

Threshold-definition period:
- 2008-06-02 through 2019-12-31

Training outcome evaluation:
- ends 2019-12-02
- the final **20 trading rows of the threshold-definition period are purged** so no forward-20d training outcome can use 2020 holdout prices

Holdout:
- 2020-01-02 through 2026-08-14

Frozen training cuts:
- GPI d20: low `-21.06`, high `+19.53`
- IPI d20: low `-21.20`, high `+22.51`

Joint states:
- **Reflation impulse** = GPI d20 high AND IPI d20 high
- **Slowdown / disinflation impulse** = GPI d20 low AND IPI d20 low

True state entries are detected on the complete chronological frame before train/holdout slicing, so an already-active state at the boundary is not misclassified as a fresh holdout event.

A shared **20-trading-row embargo** is then applied across positive and negative entry events inside each evaluation period. Once one event is accepted, no event of either sign is accepted until its forward-20d window no longer overlaps.

Non-overlapping joint event counts:
- training: **23** reflation vs **33** slowdown/disinflation
- holdout: **15** reflation vs **15** slowdown/disinflation

## Corrected result

Reflation minus Slowdown/Disinflation forward-20d spread:

| Outcome | Training joint | Training 95% CI | Holdout joint | Holdout 95% CI | Holdout GPI-only | Holdout IPI-only |
|---|---:|---:|---:|---:|---:|---:|
| US10Y yield | +5.87 bp | [-3.88, +15.69] | **+18.81 bp** | **[+2.19, +35.60]** | +11.10 bp | +10.79 bp |
| US02Y yield | +3.30 bp | [-3.38, +10.11] | **+17.68 bp** | **[+2.80, +33.19]** | +11.62 bp | +5.53 bp |
| ZN1! | -0.44% | [-1.11%, +0.24%] | **-1.18%** | **[-2.15%, -0.21%]** | -0.64% | -0.59% |
| TLT | -1.35% | [-3.23%, +0.42%] | -2.03% | [-4.29%, +0.40%] | -1.20% | -1.65% |
| USDJPY | +0.57% | [-0.92%, +2.17%] | +0.62% | [-1.30%, +2.59%] | +0.72% | +0.12% |
| EURUSD | -0.25% | [-1.83%, +1.39%] | +0.31% | [-1.19%, +1.86%] | -0.40% | +0.66% |

## What changed from the first version

The earlier study counted first entries but did not prevent a state from clearing briefly and re-entering within the same 20-day outcome horizon. Those forward-return windows overlapped, so the simple bootstrap treated dependent observations as if they were independent.

It also allowed training events in the final 20 trading rows of 2019 to use forward returns extending into the 2020 holdout.

Both defects are now removed.

Consequences:

- event counts fall materially;
- **training confidence intervals now cross zero** for US10Y, US02Y and ZN;
- therefore the previous statement that Treasury intervals excluded zero in both training and holdout is withdrawn;
- the **holdout result survives** the stricter methodology and is larger than either individual-axis contrast for US10Y, US02Y and ZN.

## Interpretation

The corrected evidence is narrower but cleaner.

What is supported:
- thresholds defined on 2008–2019 and frozen into 2020–2026 still identify a joint GPI+IPI transition contrast with meaningful holdout separation in nominal Treasury yields and ZN;
- aligned growth+inflation acceleration is followed, in the holdout sample, by higher nominal yields / weaker ZN relative to aligned deceleration;
- the joint contrast is larger than GPI-only and IPI-only in the holdout for the strongest Treasury outcomes.

What is **not** supported:
- a claim that the joint effect was statistically precise in the training sample after de-overlap;
- a universal cross-asset rule;
- a stable FX edge;
- TLT statistical significance;
- causal independence merely because forward windows no longer overlap.

The simple bootstrap is retained only after the 20-row embargo and remains descriptive.

## FCPI role

Nothing in this correction upgrades FCPI. Its justified role remains financial-stress / risk context rather than a validated standalone predictive filter.

## Joint-axis verdict

**KEEP the GPI+IPI joint transition architecture, but narrow the claim to holdout-supported Treasury / ZN discrimination.**

The main evidence is now the 2020–2026 frozen-threshold holdout, not a claim of significance in both training and holdout.

This still supports emphasizing **transition / alignment** over static regime labels in a future V6.7, while keeping V6.6 frozen and avoiding parameter optimization on Issue #59 data.
