# Issue #57 — v0.6 Phase B persistence audit

Status: **audit_complete_pending_persistence_redesign**

All Issue #55 frozen 2012-2022 FX bars are already-observed/burned and are used here only for persistence diagnosis. No PnL or independent OOS claim.

No persistence parameter is changed in this report, and no PnL is evaluated.

## Cross-pair summary

| Metric | v0.5.2.1 | v0.6 Phase A |
|---|---:|---:|
| Strong-candidate bars disagreeing with Formal | 13.76% | 14.14% |
| All bars with Candidate/Formal disagreement | 6.19% | 6.31% |
| Formal carried with no strong candidate | 11.58% | 11.96% |
| P90 disagreement-run length (bars) | 2.00 | 2.00 |
| P90 carry-run length (bars) | 6.60 | 6.80 |
| Median adopted switch delay (bars) | 2.00 | 2.00 |
| Candidate-run adoption rate | 50.05% | 51.08% |
| Median formal dwell duration (bars) | 15.00 | 15.00 |
| Total one-bar formal flips | 1 | 1 |
| Total formal switches | 227 | 230 |

## Per-pair v0.6 Phase-A state-machine baseline

| Pair | Disagree / candidate bars | Formal carry | Disagree P90 | Carry P90 | Adopt delay median | Adoption rate | Dwell median | 1-bar flips / switches |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| EURUSD | 11.44% | 12.83% | 2.00 | 6.00 | 2.00 | 52.63% | 24.00 | 0/45 |
| USDJPY | 16.50% | 13.42% | 2.00 | 8.60 | 2.00 | 49.52% | 13.50 | 1/63 |
| GBPUSD | 15.06% | 11.08% | 2.00 | 6.00 | 2.00 | 45.37% | 14.00 | 0/62 |
| AUDUSD | 13.21% | 10.58% | 2.00 | 7.60 | 2.00 | 55.81% | 16.00 | 0/60 |

## Definitions

- Candidate/Formal disagreement counts only **strong** internal candidates, not weak display-only candidates.
- Formal carry means a nonzero Formal state remains active while `candidate_id == 0`.
- Adoption delay is measured only when a new strong-candidate run begins in a state different from Formal.
- One-bar flip is the exact pattern `A -> B -> A`.

## Decision boundary

This audit does not choose new confirmBars, fast-switch thresholds, or any PnL-optimal rule. It only identifies where the current formal-state machine is stale, noisy, or appropriately persistent.
