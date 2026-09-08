# Issue #68 — Core Semantic Validity Gate

Status: **PREREGISTERED / A-vs-C PAUSED / NO PNL / NO CLASSIFIER TUNING**

## Why this gate exists

B3.4R human review exposed a more fundamental problem than Exposure selection. On FR10Y 1D, the frozen B3.3 Core Bias remains bearish through a large portion of the 2022–2023 yield-rise regime. This is not a small entry-timing question: it challenges whether Core Bias is semantically valid as the upstream regime layer at all.

Therefore the A-vs-C Exposure decision is paused. Candidate C is **not selected**. The system must first pass a high-level regime-semantic gate.

The B3.5–B3.17 forensic work remains valid: it localized some causes of reversal latency and confirmed stale old-range memory as a local causal brake, while rejecting direct global invalidation as unsafe. This new gate does not reopen component tuning. It asks a simpler upstream question:

> Does the frozen Core Bias identify the direction of obvious, sustained major regimes well enough to serve as lifecycle navigation?

## Discovery vs validation

FR10Y 2022–2023 is a **discovery / burned** case because it triggered this gate. It may illustrate the failure but cannot by itself validate the conclusion.

Validation uses fixed, cross-market semantic windows selected from obvious historical price regimes, not from Core output and not from PnL.

## Frozen semantic windows

All charts: **1D**. Direction refers to the price/yield series shown on the chart itself.

Discovery only:

- `FR10Y 2022-01-03 -> 2023-12-29` — expected **Bull** (yield rise).

Validation windows:

1. `JGB10Y 2022-01-04 -> 2024-12-30` — expected **Bull**.
2. `US10Y 2020-08-04 -> 2023-10-19` — expected **Bull**.
3. `EURUSD 2021-06-01 -> 2022-09-28` — expected **Bear**.
4. `SPX 2020-04-01 -> 2021-12-31` — expected **Bull**.
5. `SPX 2022-01-03 -> 2022-10-12` — expected **Bear**.

No window may be moved, shortened, lengthened, or replaced after seeing Core statistics.

## What is measured

Within each fixed window, using the frozen B3.3 Core Bias only:

- total scored bars;
- aligned bars: Core direction equals expected regime direction;
- opposite bars: Core direction is opposite expected regime direction;
- neutral bars: Core = 0;
- aligned occupancy %;
- opposite occupancy %;
- first-alignment delay in daily bars from window start;
- longest continuous opposite-Core run;
- Core transition count, diagnostic only.

These are semantic classification diagnostics. They are **not** return or performance metrics.

## Window-level semantic failure rule

A validation window is a hard semantic **FAIL** if either condition is true:

1. Core is opposite the expected major-regime direction on **more than 50%** of scored bars; or
2. Core remains continuously opposite the expected direction for **more than 63 daily bars** within the fixed window.

The 63-bar rule is an acceptance criterion, not a classifier parameter. It represents roughly one trading quarter of sustained opposite-regime labeling in an already-preregistered obvious major trend. It must not be tuned after results.

A window may still be marked **CONCERN** without hard failure if first-alignment delay is long or neutral occupancy is unusually high. Concerns are recorded but do not alter the preregistered hard rule.

## Cross-market go / no-go rule

FR10Y discovery is excluded from the validation count.

- **PASS / lifecycle may resume:** 0 validation hard failures.
- **CONDITIONAL / global lifecycle remains paused:** exactly 1 validation hard failure. Record a market-domain limitation; do not tune the classifier to rescue it.
- **NO-GO / Core invalid as a general regime layer:** 2 or more validation hard failures.

A NO-GO does not authorize immediate parameter search. It means the architecture must be reconsidered at a higher level before any lifecycle or PnL work resumes.

## Visual audit artifact

A dedicated TradingView indicator will show only:

- `EXPECTED` regime band for the selected preregistered window;
- frozen `CORE` band;
- explicit opposite-Core markers inside the window;
- table with alignment %, opposite %, first-align delay and longest opposite run.

Color semantics:

- green = Bull / Long direction;
- red = Bear / Short direction;
- gray = Neutral / outside the audit window;
- red mismatch marker = Core is opposite the preregistered expected regime.

Exposure A/B/C is hidden and irrelevant during this gate.

## Hard boundary

- no Strategy Tester / PnL / returns / Sharpe / drawdown / hit-rate;
- no `breakoutBars`, Break weight, MA length, threshold or persistence tuning;
- no new classifier component;
- no new Exposure candidate;
- no Volume / MTF / Divergence / HMM rescue;
- frozen B3.3 Core and production C-2 remain unchanged;
- B3.4R A-vs-C decision stays paused until this gate resolves;
- PR #73 remains Draft / Open;
- Issue #68 remains Open.
