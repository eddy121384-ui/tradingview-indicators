# Issue #78 — Current Research Summary

## Purpose

This is the one-page checkpoint for the current Issue #78 trend-capture research program.

It is not a new hypothesis, a new backtest, or a production specification. It summarizes the already-preregistered studies and their frozen findings so future work can resume without reopening settled questions.

PR #80 remains Draft / open / unmerged.

---

## 1. Current architecture

The working research architecture is:

`Wyckoff Regime -> Initial Small Risk -> Breakout / Expansion -> Acceptance / Follow-through -> Retest Hold / Reclaim -> Resume -> Add Risk -> Deterioration / Giveback -> Reduce Risk / Exit`

Current policy semantics:

- fresh formal Markup / Markdown starts at **25% Probe**;
- first usable post-entry five-bar-box breakout defines the B3 event;
- the next three bars define the causal acceptance / retest state:
  - P0 No-touch / immediate expansion;
  - P1 Wick Hold;
  - P2 Reclaim;
  - P3 Failed Acceptance;
- under the current R0 policy:
  - P0 / P1 / P2 promote to **100% Full at t+3**;
  - P3 and episodes without usable B3 remain at Probe;
- optional Warning-First deterioration management:
  - giveback <2 entry ATR: no reduction;
  - 2–4 ATR: reduce earned exposure by 25 percentage points;
  - 4+ ATR: reduce by 50 percentage points;
  - minimum positive exposure remains 25%;
  - reductions latch;
  - a new favorable close-path extreme clears the latch.

ATR remains the normalizer / risk ruler. No option overlay is part of the research.

---

## 2. What the evidence chain established

### Breakout / acceptance

Three-bar acceptance / follow-through remains useful evidence.

Compression was rejected as a universal gate.

Retest is not inherently weakness:

- P1 Wick Hold and P2 Reclaim are materially healthier than P3 Failed Acceptance;
- P3 behaves like failed acceptance and should not earn Full risk;
- P0 No-touch remains a legitimate healthy path.

### Resume research

No new Resume trigger should currently be invented.

The frozen comparison established:

- R5 Local Close is earlier / broader;
- R1 Close Extreme is later / cleaner;
- R4 +0.5 ATR is a conservative benchmark;
- neither R5 nor R1 justified replacing immediate t+3 participation.

Resume remains useful as diagnostic evidence, not as the current add-risk gate.

---

## 3. Second-entry / add-risk economics

Primary result:

> **R0 Immediate is the current gross-harvest baseline.**

For P1 / P2, waiting for R5 / R1 / R4 protects some failed-trend damage but gives up too much large-trend harvest.

Original discovery-universe whole-system equal-market results:

| Policy | Annualized return |
|---|---:|
| R0 Immediate | 1.4623 |
| R5 Local Close | 1.3915 |
| R1 Close Extreme | 1.3692 |
| R4 +0.5 ATR | 1.4062 |

MFE <4 ATR:

- R0: -1.4509
- R5: -1.1265
- R1: -1.0964
- R4: -0.9855

MFE >=8 ATR:

- R0: +5.5406
- R5: +4.8303
- R1: +4.6806
- R4: +4.7685

Interpretation:

> confirmation helps when the trend fails, but its confirmation tax is paid most heavily on the trends we most want to harvest.

The 2015–2019 stress era did not support replacing R0 with a delayed confirmation rule.

---

## 4. R0 + Warning-First composition

Warning-First is **not** the universal default.

Original discovery-universe comparison:

| Metric | R0 No De-risk | R0 + Warning-First |
|---|---:|---:|
| Annualized return | 1.4623 | 1.2984 |
| Annualized vol | 11.8544 | 9.4771 |
| Max DD | 58.03 | 40.39 |
| ES5 | -1.8556 | -1.4458 |
| Avg exposure | 0.4862 | 0.4109 |
| Annual turnover | 5.14 | 6.21 |

Warning-First:

- reduces failed / small-trend damage;
- reduces volatility;
- reduces drawdown;
- improves tail risk;
- costs raw return;
- costs large-trend harvest;
- increases turnover.

Discovery-universe MFE slices:

- MFE <4: -0.9538 -> -0.8708;
- MFE 4–8: -0.9142 -> -0.5398;
- MFE >=8: +6.1524 -> +5.1812.

Decision:

> keep R0 No De-risk as the simple gross-harvest baseline and R0 + Warning-First as the optional defensive / risk-budget challenger.

Do not create Warning-First v2 from these results.

---

## 5. Heterogeneous OOS1

A genuinely different historical OOS challenge was run outside the discovery FX / sovereign-yield universe.

Frozen six-market cohort:

- TVC:SPX
- NASDAQ_DLY:NDX
- OANDA:XAUUSD
- OANDA:XAGUSD
- BITSTAMP:BTCUSD
- BITSTAMP:ETHUSD

Integrity:

- accepted forward-log rows: **45,182**;
- completed trend episodes: **1,039**;
- usable B3 events: **624**;
- P1 + P2: **202**;
- OHLC reconstruction error: approximately **2.22e-16**.

### R0 portability

Mean normalized episode return:

| Market | R0 No De-risk |
|---|---:|
| BTCUSD | +2.079 ATR |
| ETHUSD | +0.355 |
| NDX | +0.281 |
| SPX | +0.597 |
| XAUUSD | +0.179 |
| XAGUSD | -0.002 |

R0 is positive in **5/6 markets**.

Equal-market / equal-class mean episode return:

- R0 No De-risk: **+0.582 ATR**;
- R0 + Warning-First: **+0.473 ATR**.

R0 by asset class:

- Crypto: **+1.217 ATR**;
- Equity indices: **+0.439 ATR**;
- Precious metals: **+0.088 ATR**.

All **3/3 asset classes** are positive.

This is meaningful portability evidence and reduces the plausibility that the architecture works only because it was tuned to the original FX / sovereign-yield sample.

### Why this is not Strong portability

The preregistered Strong-Portability gate was not fully met.

Among positive market means, BTCUSD contributes about **59.5%** of summed positive mean return.

Direction is also asymmetric:

- Markup R0 equal-class mean: **+1.220 ATR**;
- Markdown R0 equal-class mean: **-0.115 ATR**.

XAGUSD is approximately flat.

Formal classification:

> **Mixed portability, positive / encouraging.**

Do not tune the six-market cohort to improve that label.

---

## 6. Warning-First transported more cleanly than the raw return edge

Across the six heterogeneous OOS markets, Warning-First improves:

- bar volatility in **6/6**;
- maximum drawdown in **6/6**;
- 5% expected shortfall in **6/6**;
- MFE <4 failed / small-trend harvest in **6/6**.

But it also trails R0 on MFE >=8 ATR large-trend harvest in **6/6**.

Equal-class MFE >=8 ATR:

- R0: **+5.906 ATR**;
- Warning-First: **+5.104 ATR**.

Large-trend retention under Warning-First:

- Crypto: **86.9%**;
- Equity indices: **83.8%**;
- Precious metals: **87.6%**.

Therefore the most portable finding is not a free-lunch return improvement. It is a stable risk-shaping mechanism:

> Warning-First pays for lower failed-trend / drawdown / tail damage by surrendering part of genuine large-trend harvest.

---

## 7. Current interpretation

The current evidence is consistent with a real cross-market trend-harvest effect, but **not** with a demonstrated risk / return free lunch.

The two surviving architectures occupy different risk profiles:

### R0 No De-risk

- higher raw expectancy / gross trend harvest;
- higher volatility;
- larger drawdown / tail exposure;
- better participation in very large trends.

### R0 + Warning-First

- lower raw expectancy;
- lower volatility;
- smaller drawdown / tail exposure;
- better failed-trend damage control;
- gives back roughly 12–16% of large-trend harvest by asset class in the heterogeneous OOS1 sample.

This makes the current choice primarily a **risk-preference / risk-budget problem**, not a winner-takes-all strategy-selection problem.

A formal utility / break-even risk-aversion study has **not yet** been preregistered or accepted as a finding. Do not treat the informal risk-preference discussion as a frozen research conclusion.

---

## 8. What is currently frozen / rejected

Do not reopen without genuinely new evidence:

- no universal compression gate;
- no market-specific threshold tuning;
- no direction-specific Markup / Markdown thresholds;
- no BTC down-weight rule;
- no metals rescue rule;
- no new Resume trigger;
- no Warning-First v2;
- no reintroduction of delayed R5 / R1 / R4 as the default add-risk gate.

Current frozen survivors:

1. **R0 No De-risk** — gross-harvest / simple baseline.
2. **R0 + Warning-First** — defensive / risk-budget challenger.

---

## 9. What is still unknown

The research has **not** yet established:

- prospective forward performance;
- production readiness;
- executable futures / cash PnL after real transaction costs;
- live slippage / market-impact behavior;
- whether the Markup / Markdown asymmetry persists prospectively;
- whether BTC concentration persists prospectively;
- whether the current historical OOS performance survives a genuinely future sample;
- the investor-specific utility point where Warning-First becomes preferable to R0.

---

## 10. Next legitimate gates

Primary historical next step:

> **Cross-Sectional OOS2 on a large, previously unused U.S. individual-equity universe.**

The frozen R0 No De-risk and R0 + Warning-First policies must be applied without stock-, sector-, direction-, or era-specific retuning.

Before any OOS2 economic outcome is inspected:

- freeze the stock eligibility rule, historical window, liquidity filter, corporate-action treatment, survivorship / delisting treatment, weighting, breadth / concentration metrics and interpretation gates;
- complete a Pine -> Python classifier parity gate on calibration instruments that are excluded from formal OOS2.

In parallel:

- begin prospective / forward shadow collection of the same frozen survivors;
- optionally preregister a separate **Break-even Risk Aversion / Utility Study** to ask at what penalty on volatility / drawdown / tail loss Warning-First becomes preferable to R0.

The utility study compares frozen policies only and must not become a backdoor optimizer for new thresholds.

---

## Current decision

The research has moved beyond “does this only work in the discovery markets?”

Current evidence says:

> **Probably not. The architecture shows meaningful cross-market portability, while its risk / return trade-off remains economically normal rather than magical.**

That is encouraging evidence, not production authorization.

PR #80 stays Draft until a later explicit production / architecture gate is passed.

Refs #78, #80, #76.
