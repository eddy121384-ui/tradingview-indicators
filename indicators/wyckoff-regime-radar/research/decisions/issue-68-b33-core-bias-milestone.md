# Issue #68 Milestone — Core Bias Memory established before Exposure Layer

Status: **checkpoint / semantic architecture milestone / no PnL**

This memo freezes the current research state after the first TradingView human review of the B3.3 Core Bias audit.

## Why this is a milestone

The key architectural correction is now clear:

1. **Core Bias / trend memory** answers: what is the currently established directional regime memory?
2. **Executable Exposure** answers: should the strategy actually hold Long, Flat, or Short right now?

These two concepts must not be represented by one binary/ternary lifecycle state.

Earlier Issue #68 lifecycle variants conflated them. This caused local Stage1/4 calls and short-lived regime ambiguity to erase the directional memory itself, producing repeated washouts inside major trends.

## What has been learned

### Rejected v2

The mechanically transplanted Issue #61 human-review-v2 lifecycle restored reciprocal symmetry (~99.92%) but failed TradingView semantic review. It had drifted into a breakout-handshake / three-bar Early-Fail system that remained flat through too much established trend and exited too quickly.

### B3 regime-first v3

B3 restored trend exposure but still used one `position` state for both trend memory and executable exposure.

Human review showed:
- major trends were held better than v2;
- however, established trends were still repeatedly washed out when Formal Stage1/4 appeared;
- large ranges also produced too many Long/Short entries.

### B3.1 StrongCandidate entry gate

Null result.

Requiring Formal 2/5 plus same-direction `strongCandidate` blocked **0** entries on the burned four-FX fixtures. Formal 2/5 already inherits strong-candidate confirmation through persistence, so this condition added no information.

### B3.2 Stage1/4 range grace

Reusing existing `confirmBars=3` as a grace window before exiting on Stage1/4 produced only a small effect:
- immediate Stage1/4 exits: 96
- confirmed grace exits: 90
- washout exits suppressed: 6
- mean pair flat share: 43.72% -> 40.82%
- median of pair median-holds: 23.0 -> 27.5 bars

Conclusion: this is not a grace-window tuning problem. No 5/8/10-bar threshold search should follow.

### B3.3 Core Bias Memory

B3.3 separates directional memory from executable position logic.

Rules:
- initial bias = 0;
- Formal 2 establishes bullish bias +1;
- Formal 5 establishes bearish bias -1;
- existing bullish bias persists through Formal 0/1/2/3/4 and flips only on bearish trend family 5/6;
- existing bearish bias persists through Formal 0/1/4/5/6 and flips only on bullish trend family 2/3;
- Stage1/4 cannot erase trend memory.

No-PnL diagnostic:
- reciprocal core-bias mirror: **100.00%**;
- B3 position transitions across four FX pairs: **220**;
- B3.3 core-bias transitions: **62**;
- **158 transitions removed from the memory layer**;
- EURUSD: **50 B3 transitions -> 13 core-bias transitions**.

TradingView human review confirms the qualitative objective: major EURUSD trends are now materially better preserved and the core directional state is no longer repeatedly erased by local Stage1/4 calls.

## Important semantic boundary

**Core Bias is not an executable position.**

The B3.3 audit line is expected to spend most of its post-warmup history at +1 or -1 once a trend memory has been established. The lack of frequent 0 states is therefore not a bug in the memory layer.

The next layer must separately decide actual exposure.

## Frozen architecture going forward

The architecture after this milestone is:

### Layer 1 — Core Bias Memory

- directional regime memory;
- values: -1 / 0 / +1;
- Stage1/4/0 do not erase an established directional memory;
- only an opposite trend family can flip the directional memory.

### Layer 2 — Exposure Authorization

Still to be designed and tested.

Expected output:
- +1 = Long exposure;
- 0 = Observe / Flat;
- -1 = Short exposure.

The exposure layer may use existing Flat Action / Pace semantics to decide whether to be active or flat while preserving the underlying Core Bias.

Desired behavior:
- in a major bearish regime, Core Bias may remain -1 while Exposure alternates only between -1 and 0;
- in a major bullish regime, Core Bias may remain +1 while Exposure alternates only between +1 and 0;
- opposite executable exposure should require a genuine Core Bias reversal, not a local range fluctuation.

## Next step — B3.4

Build and review **Core Bias + Observe/Exposure layer**.

Do not:
- reinterpret B3.3 bias as actual trading exposure;
- add stop/target/time exits;
- optimize sizing or partial exposure using PnL;
- tune range-grace thresholds;
- modify the C-2 classifier;
- introduce Volume / MTF / Divergence / HMM as rescue logic.

The next human-review goal is simple: preserve major trend identity with Core Bias while restoring genuine `0 = observe / flat` periods in executable Exposure.
