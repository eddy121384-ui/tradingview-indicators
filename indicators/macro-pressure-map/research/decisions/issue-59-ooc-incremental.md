# Issue #59 — Out-of-component incremental-value validation

Status: **OOC FIRST PASS COMPLETE**

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

Signal definition remains frozen for this diagnostic: trailing 20-trading-day change. Primary evidence uses the first day entering the top/bottom 20% bucket to reduce duplicated multi-day regimes.

## Feed-sensitivity check

The TVC and FRED Treasury yield feeds are close enough that the broad conclusions are not a feed artifact:

- 10Y level correlation: **0.99915**
- 2Y level correlation: **0.99966**
- forward-20d yield-change correlation: **0.9712** for 10Y, **0.9722** for 2Y

## 20-day entry-event comparison

The table reports high-signal minus low-signal forward outcome spread.

### GPI vs Copper/Gold 20d momentum

| OOC outcome | GPI spread | Copper/Gold baseline |
|---|---:|---:|
| US10Y | **-4.45 bp** | -3.46 bp |
| US02Y | **-2.45 bp** | -0.73 bp |
| USDJPY | -0.00% | +0.05% |
| EURUSD | -0.15% | **-0.30%** |
| ZN1! | **+0.36%** | +0.03% |
| TLT | +0.31% | **+0.38%** |

GPI has some incremental separation on nominal rates / ZN, but the evidence is not robust enough to call a universal edge. The TVC 10Y 95% bootstrap CI is `[-10.49, +1.42] bp`; the FRED DGS10 sensitivity result is stronger at **-6.07 bp** with CI `[-12.08, -0.22] bp`.

Era stability is the weakness. For 20d US10Y entry events, GPI spread is:
- 2008–2012: **-13.0 bp**
- 2013–2019: **-1.0 bp**
- 2020–2026: **+2.1 bp**

So the rate effect is heavily concentrated in the crisis-heavy early sample.

**Verdict: KEEP / PROMISING, but broad out-of-component incremental value is not yet proven.** The earlier strong oil result does not generalize cleanly to all external markets.

### IPI vs 10Y breakeven 20d change

| OOC outcome | IPI spread | Breakeven baseline |
|---|---:|---:|
| US10Y | -4.52 bp | **-5.83 bp** |
| US02Y | **-5.32 bp** | -5.04 bp |
| USDJPY | **+0.29%** | -0.07% |
| EURUSD | **-0.82%** | -0.06% |
| ZN1! | +0.22% | +0.22% |
| TLT | +0.43% | **+0.50%** |

The clearest unique OOC result is EURUSD: high-vs-low IPI transition entry events are followed by **-0.82%** relative EURUSD performance over 20 trading days, with a bootstrap 95% CI of **[-1.43%, -0.20%]**. The simple breakeven baseline is almost flat.

At 60 days, IPI also separates rates more than the baseline in some tests:
- US10Y: **-15.99 bp** vs breakeven baseline **-11.76 bp**, IPI CI `[-27.18, -4.73] bp`
- TLT: **+2.23%** vs baseline **+1.65%**, IPI CI `[+0.30%, +4.13%]`

However, era stability remains mixed. EURUSD 20d IPI spread is:
- 2008–2012: **-1.74%**
- 2013–2019: **+0.03%**
- 2020–2026: **-0.60%**

The effect is therefore strongest in macro-active eras, not universal.

**Verdict: KEEP / MODEST INCREMENTAL EVIDENCE.** IPI currently has the best genuinely external result, but it should not be sold as a stable directional inflation trade signal.

### FCPI vs HY OAS 20d change / VIX 20d change

| OOC outcome | FCPI spread | HY OAS baseline | VIX baseline |
|---|---:|---:|---:|
| US10Y | +2.29 bp | +2.29 bp | +2.10 bp |
| US02Y | +3.15 bp | -0.79 bp | +2.96 bp |
| USDJPY | +0.29% | -0.53% | -0.52% |
| EURUSD | +0.09% | -0.18% | +0.10% |
| ZN1! | -0.14% | +0.02% | +0.01% |
| TLT | +0.20% | -0.08% | -0.14% |

No 20d FCPI OOC spread above has a bootstrap interval excluding zero. Era signs also change frequently.

**Verdict: DESCRIPTIVELY USEFUL, INCREMENTAL VALUE NOT DEMONSTRATED.** FCPI still compresses credit/rates/volatility conditions into one dashboard variable, but the current evidence does not justify claiming it forecasts external assets better than simple stress proxies.

## What changed from the previous first-pass ranking

The earlier in-sample / partially component-overlapping study ranked GPI strongest because its transitions separated oil and credit behavior well. This stricter OOC study downgrades that claim:

1. **IPI — best external incremental clue so far**, especially EURUSD at 20d and rates/TLT at 60d, though era stability is mixed.
2. **GPI — still useful, but its strongest prior advantage was more concentrated in commodity/credit outcomes; external rates evidence is episodic.**
3. **FCPI — still the weakest on incremental value; keep as a state-compression layer unless later joint-regime tests justify the extra complexity.**

This does **not** mean IPI is now a trading strategy or that GPI/FCPI should be deleted. It means the burden of proof is different once circular component validation is removed.

## Current project-level verdict

**KEEP V6.6 frozen. Do not tune thresholds or weights yet.**

What V6.6 has already earned:
- Pine ↔ Python implementation parity
- coherent macro-state compression
- evidence that transition/change contains more information than static labels
- some cross-asset separation
- at least one meaningful out-of-component incremental result

What V6.6 has not earned:
- a claim of direct trading profitability
- stable universal regime-to-return mappings
- proof that every composite axis beats a simple proxy
- justification for parameter optimization

## Recommended next gate

The remaining question is whether the **three-axis combination itself** adds information beyond the best individual axis.

Next study should keep V6.6 frozen and test:
1. joint GPI/IPI transition alignment;
2. FCPI as a conditioning overlay rather than a standalone predictor;
3. regime-entry events versus the best single-axis / simple-proxy baseline;
4. walk-forward era holdout, so any rule selected from 2008–2019 is judged on 2020–2026 without retuning.

That is the point where we can decide whether V6.7 should preserve all three axes, simplify FCPI, or redesign the regime layer.
