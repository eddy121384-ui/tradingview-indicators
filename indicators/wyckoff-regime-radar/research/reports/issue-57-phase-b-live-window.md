# Issue #57 — v0.6 Phase B live-window persistence decision

Status: **live_window_engineering_sweep_complete_pending_phase_b_choice**

Burned Issue #55 FX history only, trimmed to first top_value > 0 per pair. Engineering persistence comparison only; no PnL or independent OOS claim.

The earlier raw-history Neutral statistics are superseded for the Phase-B choice because they included the long indicator warm-up.

## Live windows

| Pair | First live index | First live date | Live bars |
|---|---:|---|---:|
| EURUSD | 1052 | 2016-12-23 | 1348 |
| USDJPY | 1052 | 2016-12-23 | 1348 |
| GBPUSD | 1052 | 2016-12-23 | 1348 |
| AUDUSD | 1052 | 2016-12-23 | 1348 |

## Phase-A Formal carry after warm-up

Formal carry share: **21.33%** of live bars.

| Carry category | Share of live carry | Share of all live bars |
|---|---:|---:|
| Chaos pending clear | 2.00% | 0.43% |
| Weak opposing challenger | 56.70% | 12.09% |
| Weak support for current Formal | 26.26% | 5.60% |
| Coexistence / no display | 15.04% | 3.21% |
| Neutral no candidate | 0.00% | 0.00% |

Weak-challenger follow-through after warm-up:

| Window | Eligible runs | Formal adopts | Strong candidate emerges |
|---|---:|---:|---:|
| 5 bars | 205 | 26.34% | 54.63% |
| 10 bars | 205 | 36.59% | 65.85% |

## Warm-up-excluded stale-decay sweep

Existing `confirm_bars` = **3**; candidate horizons = **3 / 6 / 9 bars**.

| Metric | Phase A | 1× | 2× | 3× |
|---|---:|---:|---:|---:|
| Formal carry share | 21.29% | 12.20% | 17.69% | 20.51% |
| Formal zero share | 0.74% | 12.28% | 5.82% | 2.63% |
| Carry-run P90 | 6.80 | 3.00 | 5.00 | 6.75 |
| Disagreement / strong-candidate bars | 14.14% | 15.16% | 14.70% | 14.14% |
| Formal dwell median | 15.00 | 13.00 | 14.50 | 15.50 |
| Neutral-run median | 11.00 | 7.75 | 5.50 | 7.25 |
| Neutral-run P90 | 11.00 | 15.35 | 15.30 | 11.95 |
| One-bar Formal flips | 1 | 3 | 3 | 2 |
| Total Formal switches | 226 | 340 | 289 | 243 |
| Into-Neutral transitions | 5 | 84 | 47 | 17 |

## Engineering cost relative to Phase A

| Candidate | Carry reduction | Formal-zero increase | Added switches | Added into-Neutral |
|---|---:|---:|---:|---:|
| 1× (3 bars) | 42.68% | 11.54 pp | 114 | 79 |
| 2× (6 bars) | 16.90% | 5.08 pp | 63 | 42 |
| 3× (9 bars) | 3.66% | 1.89 pp | 17 | 12 |

## Decision boundary

Use this warm-up-excluded report, not the superseded raw-history neutral statistics, to choose the Phase-B stale-decay horizon. Choice must be based on stale carry versus Neutral/switch churn, not PnL.
