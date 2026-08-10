# Issue #57 — v0.6 Phase B stale-decay horizon sweep

Status: **engineering_sweep_complete_pending_phase_b_choice**

Burned Issue #55 history only; 1x/2x/3x confirm_bars engineering sensitivity; no PnL.

Existing `confirm_bars` = **3**. Candidate stale-decay horizons are exactly **3 / 6 / 9 bars**.

| Metric | Phase A | 1× | 2× | 3× |
|---|---:|---:|---:|---:|
| Formal carry share | 11.96% | 6.85% | 9.94% | 11.52% |
| Formal zero share | 44.25% | 50.73% | 47.10% | 45.31% |
| Carry-run P90 (bars) | 6.80 | 3.00 | 5.00 | 6.75 |
| Strong-candidate disagreement share | 14.14% | 15.16% | 14.70% | 14.14% |
| Formal dwell median (bars) | 15.00 | 13.00 | 14.50 | 15.50 |
| Neutral-run median (bars) | 531.00 | 8.00 | 6.25 | 7.50 |
| Neutral-run P90 (bars) | 947.80 | 18.20 | 17.90 | 585.55 |
| One-bar formal flips | 1 | 3 | 3 | 2 |
| Total formal switches | 230 | 344 | 293 | 247 |
| Into-neutral transitions | 5 | 84 | 47 | 17 |

## Cost of decay relative to Phase A

| Candidate | Carry reduction | Formal-zero increase | Added Formal switches | Added into-neutral transitions |
|---|---:|---:|---:|---:|
| 1× (3 bars) | 42.68% | 6.48 pp | 114 | 79 |
| 2× (6 bars) | 16.90% | 2.85 pp | 63 | 42 |
| 3× (9 bars) | 3.66% | 1.06 pp | 17 | 12 |

## Decision boundary

Choose among exact 1x/2x/3x multiples of the existing confirm_bars using only the engineering trade-off between stale carry reduction and added Neutral/switch churn. Do not use PnL.
