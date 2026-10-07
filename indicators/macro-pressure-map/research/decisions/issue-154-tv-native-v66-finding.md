# Issue #154 — TradingView-native V6.6 Reconstruction Finding

Status: **reconstruction failed the frozen parity gate; Issue #145 mismatch autopsy NOT authorized**

Issue: #154  
Draft PR: #155  
Branch: `research/issue-154-tv-native-v66`

## Research integrity / ordering

Issue #154 was preregistered before any reconstruction parity metric was observed.

Frozen preregistration commit:

`3e563f98b200cb36ecc0e314b27c39354acf78b8`

The TradingView source acquisition was then performed through the connected **TradingView Official MCP**, using the exact default V6.6 production symbols and `1D` historical OHLCV.

No exact V6.6 target was loaded during Phase A source acquisition.

No asset-return outcome was loaded or inspected at any point.

Phase-A source manifest:

`indicators/macro-pressure-map/research/generated/issue-154-source/issue-154-source-manifest.json`

Parity evaluator / CI head:

`dea963dd2108c22025c012efae6da133503d8a1a`

Validated workflow run:

`37290886820`

Artifact:

- id: `11336511046`
- digest: `sha256:9198abdfcab8f4c70394ac75ac52d190139c9716b44962b847427689bfedef1b`

Hard firewall:

- `outcome_data_loaded=false`
- `production_authorized=false`

## TradingView source freeze

Exact production symbols were used with no substitution.

GPI:
- AMEX:SPY
- AMEX:IWM
- AMEX:RSP
- AMEX:XLY
- AMEX:XLP
- AMEX:XLI
- AMEX:XLU
- COMEX:HG1!
- COMEX:GC1!

IPI:
- FRED:T10YIE
- AMEX:DBC
- NYMEX:CL1!
- NYMEX:RB1!

Every series returned 5,000 daily bars.

Approximate raw-history starts:
- T10YIE: 2006-10-10
- SPY / equity ETFs / DBC: 2006-11-15
- CL1! / RB1!: 2006-11-27
- HG1! / GC1!: 2006-12-03 UTC timestamp dates

The first day on which every frozen default GPI/IPI component score is finite is:

**2008-03-06**

The reconstruction reused the previously validated Issue #59 Pine-compatible `v6_6_core.py` implementation rather than reimplementing the component formula.

## Formal reconstruction verdict

**`tv_native_reconstruction_failed`**

`autopsy_authorized=false`

The formal Issue #145 mismatch autopsy was therefore **not run**.

## Primary parity window

Common exact full-composition monthly observations:

**222 months**

Period:

**2008-03 through 2026-08**

## Axis parity

GPI:
- correlation: **0.996161**
- mean absolute error: **1.45384 index points**
- max absolute error: **24.60616**

IPI:
- correlation: **0.995300**
- mean absolute error: **2.66340 index points**
- max absolute error: **13.16585**

Frozen gates:

- GPI correlation >=0.995 — PASS
- IPI correlation >=0.995 — PASS
- GPI MAE <=1.50 — PASS
- IPI MAE <=1.50 — **FAIL**

Thus the MCP reconstruction captures both axes extremely strongly in correlation terms, but IPI absolute-value parity is not tight enough to satisfy the preregistered exact-reconstruction gate.

## Regime parity

Exact 3x3 regime agreement:

**94.5946%**

Frozen gate:

>=95%.

**FAIL.**

This is a narrow miss numerically, but the preregistration intentionally provides no discretionary near-pass rescue.

## R7 parity

Across the common window:

- exact R7 months: 50
- reconstructed R7 months: 53
- true-positive R7 months: 50
- R7 precision: **94.3396%**
- R7 recall: **100.0%**

Both frozen R7 gates pass.

## Asynchronous-turn parity

Exact triggers:

**14**

Reconstructed triggers:

**17**

Matched within +/-1 month:

**14**

Trigger metrics:
- precision: **82.3529%**
- recall: **100.0%**
- F1: **90.3226%**
- reconstructed/exact trigger-count ratio: **1.21429**

Both frozen trigger gates pass.

Matched exact triggers:

Same-month matches:
- 2008-12
- 2010-08
- 2011-08
- 2012-06
- 2014-10
- 2015-01
- 2015-07
- 2015-12
- 2018-10
- 2020-04
- 2023-03
- 2025-04

Within-one-month matches:
- exact 2019-05 -> reconstructed 2019-06
- exact 2022-08 -> reconstructed 2022-07

Therefore every exact Issue #136-style turning trigger in the common reconstruction window is recovered within the frozen +/-1 month tolerance.

## Gate table

PASS:
1. common months >=180
2. GPI correlation >=0.995
3. IPI correlation >=0.995
4. GPI MAE <=1.50
7. R7 precision >=0.90
8. R7 recall >=0.90
9. async-turn trigger F1 >=0.80
10. trigger-count ratio between 0.80 and 1.25

FAIL:
5. IPI MAE <=1.50
6. regime agreement >=0.95

Thus **8 of 10** frozen parity gates pass.

Formal verdict remains:

`tv_native_reconstruction_failed`.

## Interpretation

The TradingView Official MCP is clearly usable as a high-fidelity modern MPM research input pipeline.

It reproduces:
- GPI/IPI level co-movement at >0.995 correlation;
- all 14 exact asynchronous-turn signals within +/-1 month;
- exact R7 months with 100% recall.

However, it is not yet proven to be an exact substitute for the Pine `request.security` data path.

The remaining absolute-value differences are large enough to alter roughly 5.4% of 3x3 regime classifications and create three extra reconstructed turning triggers.

Possible engineering causes include data-history boundary effects, TradingView OHLCV endpoint vs chart `request.security` bar/session alignment, and feed details around continuous futures / daily timestamps. These are hypotheses only; Issue #154 did not retune or diagnose them after the failed formal gate.

## Research boundary

Per preregistration, because parity failed:

- do not run the Issue #145 component mismatch autopsy;
- do not use this reconstruction to select a new historical inflation proxy;
- do not loosen the MAE or regime gates;
- do not hand-pick a later parity start;
- do not change symbol alignment inside Issue #154;
- do not inspect historical asset outcomes.

A future separately preregistered engineering-parity issue may investigate why the MCP OHLCV path differs slightly from Pine `request.security`.

## Product boundary

No production V6.6/V6.7 code was changed.

`outcome_data_loaded=false`

`production_authorized=false`
