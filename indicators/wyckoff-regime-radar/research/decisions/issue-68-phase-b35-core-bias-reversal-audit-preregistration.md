# Issue #68 Phase B3.5 — Core Bias Reversal Audit Preregistration

Status: **preregistered forensic / no PnL / no model change**

## Motivation

B3.3 Core Bias Memory solved the prior washout problem by preserving directional memory through Formal 0/1/4. Cross-market TradingView review then exposed the opposite failure mode: on some large yield reversals (most visibly JGB 10Y and France 10Y), Core Bias appeared to remain on the old side for too long.

This phase does **not** assume that B3.3 memory itself causes the delay. By construction, B3.3 flips on the same bar that an opposite Formal trend family appears. The first task is therefore to localize latency across the existing C-2 evidence stack.

## Frozen architecture

Do not modify in B3.5:
- Issue #66 C-2 classifier formulas or thresholds;
- C-2 persistence rules;
- B3.3 Core Bias state machine;
- B3.4 Exposure A/B/C policies;
- Volume / MTF / Divergence / HMM witnesses.

Do not compute:
- return / PnL;
- Sharpe / drawdown / hit rate;
- transaction cost / sizing;
- Strategy Tester metrics.

## Reversal stack to audit

For directional analysis, map stages to three directional states:
- bullish trend family: Stage 2 / 3 => +1;
- bearish trend family: Stage 5 / 6 => -1;
- Stage 0 / 1 / 4 => 0 for the audit lane only.

Audit four layers:

1. **TOP** — current `top_id` mapped to trend-family direction, regardless of candidate quality.
2. **STRONG** — same mapping, but only when `strong_candidate == true`; otherwise 0.
3. **FORMAL** — `formal_id` mapped to trend-family direction; otherwise 0.
4. **CORE** — frozen B3.3 Core Bias Memory.

TOP is an early descriptive precursor, not an entry signal. STRONG is credible current classifier evidence, not executable exposure. FORMAL is the persisted classifier state. CORE is directional memory, not exposure.

## Mechanical forensic metrics

On frozen development fixtures, for each B3.3 Core flip:

- verify the triggering Formal stage is in the opposite trend family;
- verify **Formal opposite-family -> Core flip lag = 0 bars**;
- identify the contiguous opposite `strong_candidate` run ending at / leading into the Formal flip;
- report the length of that direct strong run;
- report the number of prior opposite-strong runs since the previous Core flip (precursor resets / failed attempts);
- report the total bars between the start of the direct strong run and the Core flip;
- report reciprocal mirror consistency for TOP-direction, STRONG-direction, FORMAL-direction, and CORE.

No arbitrary human-labeled reversal date is used in these metrics.

## TradingView human forensic

Generate a no-strategy audit indicator with four horizontal bands:

- TOP
- STRONG
- FORMAL
- CORE

Colors:
- green = bullish trend-family direction;
- red = bearish trend-family direction;
- gray = neutral / no directional trend-family state.

Default presentation must be human-readable: no performance plots, no strategy orders, no stage background, no label spam. A compact table may show current states.

Primary visual questions on the already-reviewed markets (EURUSD, USDJPY, US10Y, JGB10Y, FR10Y, DE10Y, GB10Y):

1. Does TOP turn to the new direction materially before STRONG?
2. Does STRONG turn materially before FORMAL?
3. Once FORMAL turns, does CORE flip immediately as designed?
4. On suspected stale-bias episodes, is the delay primarily **classifier evidence latency** (TOP/STRONG late) or **persistence latency** (STRONG early but FORMAL late)?

The rates screenshots are forensic examples, not tuning targets.

## Decision rules

B3.5 itself is diagnostic only.

- If Formal -> Core lag is non-zero, fix B3.3 implementation parity before any further research.
- If STRONG -> Formal is the material bottleneck, inspect persistence semantics in a successor subphase without threshold shopping.
- If TOP/STRONG themselves remain old-direction or neutral until late, the issue is upstream classifier semantics; do not try to rescue it in Exposure or Core Bias.
- If the apparent delay is isolated to unusual instruments and not reproducible across other markets, preserve B3.3 and record the limitation rather than forcing a global change.

A vs C exposure selection remains paused until this localization is complete.
