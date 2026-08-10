# Issue #57 — v0.6 Phase B Formal-carry decomposition

Status: **carry_decomposition_complete_pending_phase_b_decision**

Already-observed Issue #55 FX history only; internal state-machine diagnosis; no PnL.

Across all four pairs, Formal is carried with no strong candidate on **11.98%** of bars.

## What those carry bars actually are

| Carry category | Bars | Share of carry | Share of all bars |
|---|---:|---:|---:|
| Chaos while old Formal has not yet cleared | 23 | 2.00% | 0.24% |
| Weak challenger differs from Formal | 652 | 56.70% | 6.79% |
| Weak candidate supports existing Formal | 302 | 26.26% | 3.15% |
| Coexistence / no displayed candidate | 173 | 15.04% | 1.80% |
| Non-chaos, no displayed candidate | 0 | 0.00% | 0.00% |

## Weak-challenger follow-through

A weak challenger is a displayed candidate that differs from Formal but did not qualify as a strong internal candidate.

| Look-ahead after weak-challenger run | Eligible runs | Formal adopts challenger | Strong challenger emerges | Runs length >=2: Formal adopts |
|---|---:|---:|---:|---:|
| 5 bars | 205 | 26.34% | 54.63% | 26.50% |
| 10 bars | 205 | 36.59% | 65.85% | 36.75% |

## Per-pair carry tails

| Pair | Carry share | Weak challenger share of carry | Weak challenger run median / P90 / max | Neutral-no-candidate P90 / max |
|---|---:|---:|---:|---:|
| EURUSD | 12.83% | 48.70% | 2.50 / 6.90 / 13 | — / — |
| USDJPY | 13.42% | 64.91% | 2.00 / 8.00 / 14 | — / — |
| GBPUSD | 11.08% | 55.64% | 2.00 / 5.00 / 9 | — / — |
| AUDUSD | 10.58% | 57.09% | 2.00 / 8.10 / 23 | — / — |

## Decision boundary

Use this decomposition to decide whether Phase B should change confirmation delay, weak-challenger handling, or stale-state decay. Do not select a rule from trading PnL.
