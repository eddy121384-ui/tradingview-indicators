# Issue #68 Phase B3.4R — EURUSD 1D Human Semantic Gate

Status: **EURUSD FIRST GATE COMPLETE / C PROVISIONAL FRONT-RUNNER / CROSS-MARKET CONFIRMATION REQUIRED**

## Review setup

Market: EURUSD
Timeframe: 1D
Artifact: `indicators/wyckoff-regime-radar/research/generated/wyckoff-issue68-phase-b34r-ac-resume-audit.pine`

Visible lanes used for the active comparison:

- CORE — frozen B3.3 directional memory
- A — Formal trend-family exposure
- C — stateful Flat Action entry/re-entry + Pace defensive-flat exposure

Candidate B remained implemented but hidden by default. No PnL or Strategy Tester information was used.

## Human visual observations

### 1. Sustained trend participation

Candidate C preserves materially more continuous aligned exposure inside long-lived Core Bias runs.

The clearest example is the large 2021–2022 EURUSD bearish regime. CORE remains bearish for a long interval. A repeatedly falls back to Flat as Formal leaves the active trend family, while C stays short through much more of the directional run and uses narrower defensive Flat intervals.

The 2025–2026 bullish regime shows the same structural difference: A is more willing to drop to Flat when Formal weakens, while C can remain Long as long as the same Core Bias survives and Pace does not force defensive observation.

### 2. Flat / Observe behavior

C is not permanently sticky. Genuine Flat intervals remain visible during ambiguous/range periods, including parts of 2019–2020 and 2023–2024. Therefore the stateful hold rule does not eliminate the Observe state.

A creates more Flat intervals, but many of them visually look like fragmentation of an otherwise coherent Core regime rather than a distinct lifecycle decision.

### 3. Churn / fragmentation

A appears more tightly coupled to the current Formal stage and therefore re-imports some classifier stage churn into Exposure. This weakens the intended architectural separation between slow regime memory and executable lifecycle.

C is visibly less fragmented and behaves more like a separate position-state layer.

### 4. Current-right-edge stress case

At the review endpoint:

- CORE = LONG
- A = FLAT
- C = LONG

EURUSD is trading near the upper part of the post-2025 range after a large prior rally. This is a useful unresolved stress case: A interprets current Formal weakness as a reason to stand aside, while C treats it as insufficient to abandon the existing bullish lifecycle.

This prevents declaring C final from EURUSD alone. The same distinction must be checked on cross-market controls to see whether C's persistence becomes excessive outside this example.

## EURUSD gate decision

**Candidate C is the provisional front-runner on EURUSD 1D.**

Reason:

- better sustained aligned participation;
- fewer apparently unnecessary Flat interruptions;
- still recovers genuine Observe periods;
- more faithfully preserves the intended separation of Core Bias from Exposure state.

Candidate A is not yet rejected. It remains the simpler control because its greater willingness to Flat may prove useful on rates markets where directional Core regimes can coexist with long consolidation periods.

## Next gate

Proceed to **FR10Y 1D** using the same frozen B3.4R artifact and judge only conditional lifecycle behavior under the same Core Bias.

No classifier reversal-latency judgment, parameter tuning, new exposure candidate, or PnL interpretation is allowed.

PR #73 remains Draft / Open. Issue #68 remains Open.
