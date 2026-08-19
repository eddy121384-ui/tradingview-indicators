# Issue #59 — Out-of-component incremental-value validation

Status: **OOC STUDY COMPLETE — NON-OVERLAPPING EVENT WINDOWS**

This stage tests frozen Macro Pressure Map V6.6 against outcomes that are not direct default-path inputs, using the user-supplied TradingView Pine Logs.

## Evidence / sample

- Parity log SHA-256: `c0220d4974b2fd0154c4cf8f33b4b3effb27a58e21ee96a1b0109011ce638e3d`
- OOC log SHA-256: `192151f5cf90c7ac067ec63b2aad62749c11766fa7775268bb1ee01fd3b39363`
- OOC rows: **4,936** daily rows, 2007-01-03 through 2026-08-17
- Overlap with frozen parity history: **4,935** rows through 2026-08-14
- Research sample after frozen 355-row warmup: **4,580** rows, 2008-06-02 through 2026-08-14
- OOC helper wiring check: GPI/IPI/FCPI plotted values match the parity helper on all overlapping dates with **0.0 max absolute error**
- No V6.6 parameters were changed.

Outcome set:
- TVC US 10Y / 2Y nominal yields
- FRED DGS10 / DGS2 feed-sensitivity checks
- USDJPY
- EURUSD
- CBOT ZN1! 10Y Treasury futures
- TLT

Signal definition remains frozen: trailing 20-trading-day axis change versus simple proxy baselines.

## Review correction — overlapping event windows

The first OOC report counted first entries into top/bottom 20% signal buckets, but a signal could clear briefly and re-enter before the previous 20d or 60d forward window ended. Those overlapping outcomes were then resampled as if independent.

The corrected study applies a **shared horizon-length embargo across high and low entry events**:

- 5d outcome -> 5-trading-row embargo
- 20d outcome -> 20-trading-row embargo
- 60d outcome -> 60-trading-row embargo

An accepted event suppresses later events of either sign until the corresponding forward window no longer overlaps.

Bootstrap confidence intervals are calculated only after that de-overlap step.

## Feed-sensitivity check

The TVC and FRED Treasury yield feeds remain close enough that broad conclusions are not a feed artifact:

- 10Y level correlation: **0.99915**
- 2Y level correlation: **0.99966**
- forward-20d yield-change correlation: **0.9712** for 10Y, **0.9722** for 2Y

## Corrected 20-day non-overlapping entry-event comparison

High-signal minus low-signal forward outcome spread:

### GPI vs Copper/Gold 20d momentum

| OOC outcome | GPI spread | Copper/Gold baseline | GPI 95% CI |
|---|---:|---:|---:|
| US10Y | +4.26 bp | +6.64 bp | [-3.58, +11.83] |
| US02Y | +3.58 bp | +1.20 bp | [-2.71, +10.20] |
| USDJPY | +0.64% | -0.15% | [-0.33%, +1.60%] |
| EURUSD | +0.29% | +0.27% | [-0.54%, +1.16%] |
| ZN1! | -0.30% | -0.18% | [-0.84%, +0.26%] |
| TLT | -0.73% | -0.53% | [-1.96%, +0.52%] |

No main corrected GPI 20d OOC confidence interval excludes zero.

Era-stability also remains weak. Corrected GPI -> US10Y spread:
- 2008–2012: **-5.31 bp**
- 2013–2019: **+4.46 bp**
- 2020–2026: **-1.16 bp**

**Verdict: KEEP as a growth/cyclical state axis, but standalone OOC incremental prediction is not demonstrated.**

### IPI vs 10Y breakeven 20d change

| OOC outcome | IPI spread | Breakeven baseline | IPI 95% CI |
|---|---:|---:|---:|
| US10Y | +4.58 bp | +3.08 bp | [-3.27, +12.53] |
| US02Y | +4.38 bp | +4.51 bp | [-2.30, +11.31] |
| USDJPY | -0.37% | -0.10% | [-1.25%, +0.50%] |
| EURUSD | +0.47% | -0.05% | [-0.37%, +1.31%] |
| ZN1! | -0.24% | -0.00% | [-0.79%, +0.30%] |
| TLT | -0.54% | -0.32% | [-1.93%, +0.80%] |

The previous headline IPI-EURUSD result of about `-0.82%` with a CI excluding zero **does not survive** the non-overlapping-event rule. It becomes about `+0.47%` with a wide CI crossing zero.

The previous 60d IPI rate / TLT evidence also does not survive:
- US10Y: **+7.92 bp**, CI `[-14.59, +31.06] bp`; breakeven baseline +7.63 bp
- TLT: **-1.21%**, CI `[-4.84%, +2.44%]`; breakeven baseline -1.50%

Corrected IPI -> EURUSD era spread:
- 2008–2012: **-0.46%**
- 2013–2019: **+0.15%**
- 2020–2026: **+0.58%**

**Verdict: KEEP as an inflation-pressure axis and as part of the joint GPI+IPI architecture, but no robust standalone OOC incremental edge is demonstrated.**

### FCPI vs HY OAS / VIX baselines

| OOC outcome | FCPI spread | HY OAS baseline | VIX baseline | FCPI 95% CI |
|---|---:|---:|---:|---:|
| US10Y | +1.74 bp | -3.10 bp | -1.53 bp | [-7.16, +10.45] |
| US02Y | -1.12 bp | -0.02 bp | -0.65 bp | [-9.01, +6.90] |
| USDJPY | -0.21% | +0.40% | +0.49% | [-1.17%, +0.71%] |
| EURUSD | +0.37% | +0.75% | -0.24% | [-0.36%, +1.11%] |
| ZN1! | -0.07% | -0.09% | -0.20% | [-0.62%, +0.51%] |
| TLT | -0.84% | +0.21% | -0.23% | [-2.09%, +0.45%] |

No corrected main FCPI 20d OOC confidence interval excludes zero.

**Verdict: DESCRIPTIVELY USEFUL; standalone incremental predictive value not demonstrated.** FCPI remains justified as a financial-stress / risk-context compression layer.

## Corrected project-level interpretation

After removing overlapping event windows, the earlier ranking of single-axis predictive strength is withdrawn.

The conservative conclusion is now:

1. **GPI — KEEP for state / transition information, not as a validated standalone external predictor.**
2. **IPI — KEEP for inflation state and joint alignment, not as a validated standalone external predictor.**
3. **FCPI — KEEP as stress / risk context; standalone incremental prediction remains unsupported.**

No individual axis has earned a robust general-purpose OOC predictive claim from this study.

That makes the separate joint-axis holdout test more important: if the full architecture has incremental value, it must come from **cross-axis alignment / synchronized transition**, not from pretending one axis is a universal signal.

## Current project-level verdict

**KEEP V6.6 frozen. Do not tune thresholds or weights.**

What this OOC study supports:
- reducing circular self-validation by using external outcome markets;
- retaining the axes as macro-state descriptors;
- downgrading all standalone single-axis predictive claims;
- using the corrected joint holdout as the main test of incremental architecture value.

What it does not support:
- direct trading profitability;
- universal single-axis directional rules;
- stable FX edge;
- FCPI superiority over simple stress proxies;
- any parameter optimization on Issue #59 data.
