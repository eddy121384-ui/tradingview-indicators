# Issue #78 — Equity Proof-Policy OOS3 first untouched outcome

Date: 2026-10-01

## Status

This document records the **first untouched economic outcome** from the second deterministic 300-stock OOS3 cohort.

The cohort, universe SHA, Bloomberg snapshot, classifier blob, proof thresholds, exposure states, WarningFirst semantics and interpretation gates were frozen before this result was inspected.

No rescue retuning is permitted on this cohort.

---

## Integrity

- frozen classifier blob:
  `1eec08e791403453853b589373bb2270c508c3bb`
- frozen OOS3 universe SHA-256:
  `9d4a14d163ed308238737647b94e722c62fd023b641e1015e6d97679f9ba3b44`
- raw files: **300**
- raw failures: **0**
- completed eligible episodes: **19,572**
- primary stocks: **260**
- B3 events: **11,597**
- survivorship-limited: **true**
- zero FIGI overlap with first OOS2 cohort

Path construction:

- accepted: 11,597
- no breakout: 5,313
- too short: 2,194
- B3 ineligible: 468

---

## Primary result

All six frozen policies remain **Diagnostic Weak / Failed** as standalone policies.

Equal-stock primary results:

### R0_NoDerisk

- mean expectancy: **-0.077252 ATR**
- median stock expectancy: **-0.143887 ATR**
- positive-stock fraction: **38.08%**
- profit factor: **1.0103**
- average exposure: **43.81%**

### R0_WarningFirst

- mean expectancy: **-0.077596 ATR**
- median stock expectancy: **-0.111824 ATR**
- positive-stock fraction: **35.00%**
- profit factor: **0.9716**
- average exposure: **39.89%**

### Proof1_NoDerisk

Frozen rule: 25% probe -> 100% after first +1 ATR cumulative directional proof.

- mean expectancy: **-0.105050 ATR**
- median stock expectancy: **-0.162581 ATR**
- positive-stock fraction: **37.69%**
- profit factor: **1.0047**
- average exposure: **61.31%**

### Proof1_WarningFirst

- mean expectancy: **-0.105247 ATR**
- median stock expectancy: **-0.139079 ATR**
- positive-stock fraction: **36.92%**
- profit factor: **0.9681**
- average exposure: **54.51%**

### ProgressiveProof_NoDerisk

Frozen 25 / 50 / 75 / 100% ladder at +0.5 / +1 / +2 ATR proof.

- mean expectancy: **-0.098744 ATR**
- median stock expectancy: **-0.148713 ATR**
- positive-stock fraction: **38.85%**
- profit factor: **1.0074**
- average exposure: **60.39%**

### ProgressiveProof_WarningFirst

- mean expectancy: **-0.104332 ATR**
- median stock expectancy: **-0.142717 ATR**
- positive-stock fraction: **37.69%**
- profit factor: **0.9607**
- average exposure: **52.77%**

---

## Frozen frontier decision

Neither proof policy passes the preregistered useful-transport frontier gate.

Versus R0_NoDerisk:

### Proof1_NoDerisk

- mean expectancy delta: **-0.027799 ATR**
- median stock expectancy delta: **-0.018694 ATR**
- positive-stock fraction delta: **-0.38 pp**
- MFE<4 improved-stock fraction: **1.54%**
- MFE>=8 harvest retention vs R0: **142.97%**
- useful frontier gate: **FAIL**

### ProgressiveProof_NoDerisk

- mean expectancy delta: **-0.021492 ATR**
- median stock expectancy delta: **-0.004826 ATR**
- positive-stock fraction delta: **+0.77 pp**
- MFE<4 improved-stock fraction: **1.54%**
- MFE>=8 harvest retention vs R0: **140.19%**
- useful frontier gate: **FAIL**

The proof policies capture substantially more of genuine large trends than R0, but they do so by taking materially more exposure in weak / failed episodes. The added upside does not compensate for the added false-start damage.

---

## MFE decomposition

Equal-stock mean episode harvest:

| Policy | MFE <4 | MFE 4–8 | MFE >=8 |
|---|---:|---:|---:|
| R0_NoDerisk | -0.839 | +0.063 | +4.861 |
| R0_WarningFirst | -0.779 | +0.147 | +4.415 |
| Proof1_NoDerisk | -1.301 | +0.700 | +6.950 |
| Proof1_WarningFirst | -1.196 | +0.743 | +6.244 |
| ProgressiveProof_NoDerisk | -1.249 | +0.589 | +6.814 |
| ProgressiveProof_WarningFirst | -1.136 | +0.597 | +6.068 |

This is the central OOS3 policy result:

> **proof magnitude is genuinely informative, but using proof alone as permission to scale exposure is too permissive for individual equities.**

It increases harvest in Middle / Large trends, but worsens the far more common Failed-trend population enough to reduce broad expectancy.

---

## OOS3 baseline anatomy replicates OOS2

The second untouched stock cohort reproduces the main structural findings from the first cohort.

### Direction

R0_NoDerisk:

- Markup: **+0.033711 ATR**
- Markdown: **-0.243554 ATR**

The first cohort also showed Markdown materially worse than Markup.

### Size

R0_NoDerisk:

- large: **-0.025082 ATR**
- mid: **-0.037603 ATR**
- small: **-0.192646 ATR**

The large -> mid -> small deterioration therefore replicates.

### Time

R0_NoDerisk:

- 2000–2004: **+0.100020 ATR**
- 2005–2009: **+0.100397 ATR**
- 2010–2014: **-0.178652 ATR**
- 2015–2019: **-0.095981 ATR**
- 2020–2026: **-0.102490 ATR**

Again, only the first two frozen blocks are positive.

### Sector

R0_NoDerisk has only **2 / 11** positive adequate sectors:

- Energy: **+0.233017 ATR**
- Information Technology: **+0.156468 ATR**

All other adequate sectors are negative.

The broad standalone-stock weakness is therefore independently replicated in OOS3.

---

## Descriptive post-outcome path autopsy

This section is descriptive only and cannot alter the frozen OOS3 decision.

R0 path episode shares:

- NoUsableB3: **40.75%**
- P3 FailedAcceptance: **21.08%**
- P0 NoTouch: **17.94%**
- P1 WickHold: **12.08%**
- P2 Reclaim: **8.16%**

Thus about **61.8%** of completed eligible episodes are either NoUsableB3 or P3.

Equal-stock mean harvest by path:

| Path | R0_NoDerisk | Proof1_NoDerisk | ProgressiveProof_NoDerisk |
|---|---:|---:|---:|
| NoUsableB3 | -0.538 | -1.015 | -1.013 |
| P3 FailedAcceptance | -0.005 | -0.450 | -0.391 |
| P0 NoTouch | +0.545 | +1.618 | +1.565 |
| P1 WickHold | +0.111 | +0.691 | +0.674 |
| P2 Reclaim | +0.389 | +0.791 | +0.779 |

This is the key mechanism.

Proof-only scaling is **excellent inside structurally successful B3 paths** and **harmful inside structurally rejected / never-confirmed paths**.

For Proof1_NoDerisk:

- approximately **21.7%** of NoUsableB3 episodes nevertheless earn exposure above Probe;
- approximately **76.5%** of P3 FailedAcceptance episodes earn exposure above Probe;
- approximately **92.0%** of P0/P1/P2 episodes earn exposure above Probe.

Therefore +1 ATR proof is not false; it is simply insufficient as a standalone structural admission rule.

Many ultimately rejected stock trends first travel far enough to earn proof and then reverse.

---

## WarningFirst replication

WarningFirst again transports strongly as a defensive overlay.

### R0 pair

- lower bar volatility: **99.62%**
- lower max drawdown: **89.23%**
- better ES5: **99.62%**
- better MFE<4 harvest: **86.54%**
- MFE>=8 retention: **90.84%**

### Proof1 pair

- lower bar volatility: **100%**
- lower max drawdown: **86.92%**
- better ES5: **100%**
- better MFE<4 harvest: **91.54%**
- MFE>=8 retention: **89.84%**

### ProgressiveProof pair

- lower bar volatility: **100%**
- lower max drawdown: **86.92%**
- better ES5: **100%**
- better MFE<4 harvest: **90.77%**
- MFE>=8 retention: **89.05%**

WarningFirst therefore replicates as a portable damage-control layer, but it does not turn the proof policies into positive standalone stock strategies.

---

## Research interpretation

OOS3 falsifies the simple hypothesis:

> `Probe -> price proof -> scale`

is sufficient as a standalone individual-equity participation policy.

The more precise architecture supported by the combined evidence is:

- fresh formal trend is useful only as a Probe state;
- early directional proof contains strong information about eventual trend size;
- structural B3 / acceptance evidence contains independent information about whether that proof is durable;
- WarningFirst controls damage after exposure is earned.

The strongest new mechanism is the interaction:

> **price proof says “this trend has moved”; structural acceptance says “this move has survived.”**

Proof without structural acceptance over-promotes NoUsableB3 and P3 episodes.

This interaction was not a frozen OOS3 policy and must not be optimized on this cohort.

---

## Guardrail after first OOS3 outcome

Do not rescue this cohort by:

- changing proof thresholds;
- changing exposure percentages;
- adding a timeout;
- adding directional efficiency;
- switching to Markup only;
- filtering small caps;
- filtering sectors;
- dropping NoUsableB3 / P3 ex post;
- introducing a B3 + proof hybrid and calling it validated.

A future hybrid or proof-failure brake requires a new preregistration and a third untouched cohort.

Refs #78, #135, #132, #131, #80.
