# Issue #59 — Macro Pressure Map V6.6 first historical diagnostics

Status: **DESCRIPTIVE FIRST PASS COMPLETE**

This report begins the actual historical validation only after default-path Pine ↔ Python parity passed.

## Evidence / sample

TradingView Pine Logs export supplied by the user:

- SHA-256: `c0220d4974b2fd0154c4cf8f33b4b3effb27a58e21ee96a1b0109011ce638e3d`
- source history: 4,935 unique daily rows, 2007-01-03 through 2026-08-14
- parity/research warmup excluded: first 355 rows
- first-pass research sample: **4,580 daily rows**, 2008-06-02 through 2026-08-14
- V6.6 parameters: **frozen / unchanged**

Forward horizons examined: 5, 10, 20, and 60 trading days. This note emphasizes the 20-day and 60-day results for readability.

Unconditional SPY averages over the research sample:

- forward 5d: +0.22%
- forward 20d: +0.87%
- forward 60d: +2.67%

## 1. Static axis levels are not clean directional equity signals

### GPI

The static GPI labels do not form a monotonic forward-SPY ranking.

Examples (mean forward SPY):

- Growth Euphoria: +2.45% over 20d; +6.85% over 60d (43 daily observations)
- Mild Growth: +0.98% over 20d; +2.98% over 60d
- Growth Neutral: +0.78% over 20d; +1.86% over 60d
- Mild Slowdown: +0.56% over 20d; +2.43% over 60d
- Severe Slowdown: +3.45% over 20d; +6.77% over 60d (136 daily observations)

Both extremes outperform the middle in this naive daily-state view. That is consistent with episode concentration / mean reversion and is strong evidence **not** to treat GPI level as a simple long/short equity score.

### IPI

IPI level shows more coherent rates/inflation fingerprints than equity direction.

Mean forward 20d:

- Stable Inflation: SPY +1.25%, IEF +0.08%
- Inflation Rising: SPY +0.78%, IEF -0.06%
- Inflation Shock: SPY +0.35%, IEF -1.10%, real yield +17.3 bp
- Inflation Cooling: SPY +0.93%, IEF +0.05%
- Deflation Pressure: SPY +0.21%, IEF +1.17%, real yield -7.7 bp

This is directionally sensible for bonds: inflation shock states are followed by weaker IEF / higher real yields, while deflation states are followed by stronger IEF / lower real yields. Equity separation is much weaker.

### FCPI

Static FCPI stress is primarily a **state-of-crisis** label, not an entry-timing signal.

Daily-state means:

- Neutral Conditions: SPY +0.87% over 20d; +2.85% over 60d
- Conditions Tightening: SPY +0.81% over 20d; +3.13% over 60d
- Conditions Easing: SPY +1.02% over 20d; +2.01% over 60d
- Financial Stress: SPY +0.76% over 20d; **-2.25% over 60d** (117 daily observations)

However, looking only at the **first day entering** Financial Stress gives +0.08% over 20d and +1.72% over 60d across 25 episodes. This gap shows why daily-state rows cannot be read as independent trading signals: long crisis episodes heavily weight the naive state average.

## 2. Axis change / transition looks more informative than static level

To test the user's transition hypothesis without changing V6.6, each axis's trailing 20-day change was divided into descriptive quintiles. These quintiles are **research diagnostics only**, not proposed production thresholds.

### GPI 20-day change

Sharp Rise (top 20%) → next 20d average:

- SPY +1.24%
- oil +3.37%
- HY OAS **-19.5 bp**
- 10Y breakeven **+4.1 bp**
- IEF -0.19%

Sharp Fall (bottom 20%) → next 20d average:

- SPY +1.12%
- oil **-2.71%**
- HY OAS **+9.0 bp**
- 10Y breakeven **-3.9 bp**
- IEF +0.51%

The equity difference is small. The macro/cross-asset continuation is much clearer: rapid GPI strengthening is followed by stronger commodities, tighter credit, and firmer breakevens; rapid weakening shows the opposite.

### IPI 20-day change

Sharp Rise → next 20d average:

- SPY +0.91%
- oil +1.65%
- 10Y breakeven **+2.8 bp**
- IEF -0.24%

Sharp Fall → next 20d average:

- SPY +0.41%
- oil **-2.07%**
- 10Y breakeven **-5.4 bp**
- IEF +0.43%

Again, the strongest first-pass signal is inflation-pressure persistence, not equity timing.

### FCPI 20-day change

Sharp Rise (stress tightening quickly) → next 20d average:

- SPY +0.71%
- oil -2.36%
- HY OAS **+17.9 bp**
- 10Y breakeven -3.0 bp

Sharp Fall (conditions easing quickly) → next 20d average:

- SPY +0.85%
- oil +1.78%
- HY OAS **-12.8 bp**
- 10Y breakeven +1.8 bp

The credit/inflation continuation is economically coherent. SPY separation remains modest.

## 3. Core regimes do create different cross-asset fingerprints — but the names must not be read as forecasts

Daily-state forward 20d means:

| Core Regime | Days | SPY | Gold | Oil | DXY | IEF | HY OAS change |
|---|---:|---:|---:|---:|---:|---:|---:|
| Benign Expansion / Stable Inflation | 363 | +1.64% | +0.71% | +3.17% | -0.65% | ~0.00% | -31.6 bp |
| Disinflationary Drift | 338 | +1.31% | +0.74% | +1.46% | -0.30% | +0.11% | -0.3 bp |
| Goldilocks / Disinflationary Expansion | 381 | **-0.28%** | +0.82% | +1.46% | +0.04% | -0.31% | **+22.5 bp** |
| Growth Slowdown / Stable Inflation | 295 | +1.05% | +1.06% | +0.16% | +0.14% | +0.14% | -7.3 bp |
| Inflation Pressure without Growth Confirmation | 469 | +0.27% | +0.22% | -1.19% | +0.48% | -0.01% | +6.1 bp |
| Neutral / Range-bound Macro | 299 | +0.98% | +1.04% | +0.09% | +0.13% | +0.11% | -12.3 bp |
| Reflation / Inflation Rising | 1,018 | +1.29% | +0.39% | +2.26% | +0.33% | -0.18% | -11.0 bp |
| Slowdown / Disinflation | 1,064 | +1.04% | +1.38% | -1.65% | +0.22% | +0.46% | +4.0 bp |
| Stagflation Pressure | 353 | **-0.20%** | +0.66% | -0.90% | +0.50% | -0.22% | +13.1 bp |

There is real separation, especially across oil, bonds, dollar, and credit. But some prospective behavior is counterintuitive relative to the regime name. Example: the static `Goldilocks` state is followed by weak average SPY and wider HY OAS in the full sample. `Stagflation` is followed by weaker SPY, but not by rising oil.

Interpretation: these names describe **what the market has recently priced**, not guaranteed forward asset returns. They should not be presented as self-executing trade calls.

## 4. Robustness across eras is mixed

Three broad eras were checked: 2008–2012, 2013–2019, 2020–2026.

Transition persistence is strongest in high-volatility / macro-active eras and weaker in the quiet 2013–2019 period.

Examples:

- GPI Sharp Rise → future HY OAS compression: strong in 2008–2012 and 2020–2026, but not in 2013–2019.
- FCPI Sharp Rise → future HY OAS widening: strong in 2008–2012 and 2020–2026, but not in 2013–2019.
- IPI Sharp Fall → future breakeven decline: present in all three eras; Sharp Rise continuation is strong in 2008–2012 and 2020–2026, near-flat/slightly negative in 2013–2019.

Regime forward-SPY behavior is also not stable enough to support universal trading rules. Examples:

- Goldilocks mean forward 20d SPY: -7.31% (2008–2012), +1.22% (2013–2019), +0.26% (2020–2026)
- Stagflation mean forward 20d SPY: +0.18%, +0.86%, -0.82% across the same eras

## 5. Preliminary simple-baseline pre-check

This is not yet the full incremental-value study, but it gives an early answer to whether the composite axes beat obvious one-line proxies on **out-of-component** outcomes.

### GPI vs Copper/Gold momentum → future oil

Top-vs-bottom 20% signal spread in forward 20d oil return:

- GPI 20d change: **+6.08 percentage points**
- Copper/Gold 20d momentum: **+3.36 percentage points**

The GPI separation is larger in all three broad eras:

| Era | GPI spread | Copper/Gold spread |
|---|---:|---:|
| 2008–2012 | +5.79% | +3.35% |
| 2013–2019 | +3.60% | +2.06% |
| 2020–2026 | +9.15% | +4.84% |

This is the strongest preliminary evidence that the GPI composite may add value beyond a single cyclical proxy.

### IPI vs 10Y breakeven momentum → future IEF

Top-vs-bottom 20% signal spread in forward 20d IEF return:

- IPI 20d change: **-0.67 percentage points**
- 10Y breakeven 20d momentum: **-0.59 percentage points**

IPI is only modestly stronger in the full sample and the advantage is not stable across all eras. Early verdict: **possible incremental value, not demonstrated yet**.

### FCPI vs HY OAS momentum → future oil / IEF / SPY

For forward 20d oil return, top-vs-bottom 20% stress-change spread:

- FCPI 20d change: **-4.14 percentage points**
- HY OAS 20d momentum: **-7.12 percentage points**

For forward SPY, both are weak separators. For IEF, HY OAS momentum also separates more strongly than FCPI in this first pass.

Early verdict: **the FCPI composite has not yet earned incremental-value status over a simple credit-spread proxy**. This does not mean FCPI is useless; it means the burden of proof is now higher for this axis.

## First-pass verdict

### KEEP

The three-axis architecture appears to contain useful information as a **macro-state compression / transition monitor**. The cleanest evidence so far is not static level and not direct SPY prediction; it is the persistence and cross-asset coherence of **axis changes**.

Preliminary axis ranking by evidence so far:

1. **GPI — strongest**: clear transition coherence and early incremental advantage over Copper/Gold on an out-of-component oil outcome.
2. **IPI — promising but modest**: coherent inflation/rates behavior; only small early advantage over simple breakeven momentum.
3. **FCPI — useful descriptively, incremental value unproven**: stress persistence is coherent, but simple HY OAS momentum can outperform it on tested out-of-component outcomes.

### DO NOT CLAIM YET

- Do not claim V6.6 is a profitable trading signal.
- Do not claim `Goldilocks`, `Reflation`, `Stagflation`, etc. imply fixed future returns.
- Do not claim final incremental value: the baseline pre-check is deliberately simple and not yet a full robustness study.

## Next gate

The next research stage should formalize the incremental-value comparison and use more independent outcomes:

- nominal UST yields / TY (not just real yield or IEF)
- USDJPY / EURUSD (not just DXY)
- potentially gold / oil depending on which axis is being tested, while avoiding direct component circularity

For each axis, compare V6.6 against its strongest simple baseline across eras and de-overlapped transition events. Only after that should Issue #59 decide KEEP / SIMPLIFY / RECALIBRATE for each axis.

No V6.6 parameter changes are justified by this first pass.
