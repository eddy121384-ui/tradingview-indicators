# Issue #57 — v0.6 Phase B stale-decay candidate

Status: **candidate_engineering_comparison_complete**

Burned Issue #55 FX history only; state-machine engineering comparison; no PnL/OOS claim.

Candidate rule: Keep strong-candidate confirmation unchanged. Clear an existing Formal to neutral after confirm_bars of continuous chaos, weak opposing challenger, or coexistence pressure. Never promote weak candidates.

| Metric | Phase A state machine | Phase B candidate |
|---|---:|---:|
| Formal zero share | 44.25% | 47.10% |
| Formal carry without strong candidate | 11.96% | 9.94% |
| Disagreement / strong-candidate bars | 14.14% | 14.70% |
| Disagreement-run P90 | 2.00 | 2.00 |
| Carry-run P90 | 6.80 | 5.00 |
| Adopted switch delay median | 2.00 | 2.00 |
| Candidate adoption rate | 51.08% | 52.45% |
| Formal dwell median | 15.00 | 14.50 |
| Neutral-run median | 531.00 | 6.25 |
| Neutral-run P90 | 947.80 | 17.90 |
| One-bar formal flips | 1 | 3 |
| Formal switches | 230 | 293 |
| Direct nonzero→nonzero switches | 216 | 195 |
| Into-neutral transitions | 5 | 47 |

## Phase B clear-to-neutral reasons

- chaos: **3**
- persistent weak challenger: **41**
- coexistence pressure: **3**
- other: **0**

## Decision boundary

Judge this candidate only on stale-state reduction versus added neutral churn / switching noise. Do not use trading PnL to accept or reject it.
