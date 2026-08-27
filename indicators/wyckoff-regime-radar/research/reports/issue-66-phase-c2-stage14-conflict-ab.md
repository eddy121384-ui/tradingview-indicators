# Issue #66 Phase C-2 — Stage 1/4 Candidate-Conflict Symmetry Repair A/B

Status: **reused frozen data / no PnL**

Primary Stage 1/4 conflict gate: **PASS**

Only the Stage-1 candidate-conflict clause differs from accepted B-7; Stage 4 is the frozen canonical mirror source.

## Primary conflict layer

| Metric | B-7 | C-2 |
|---|---:|---:|
| Candidate-conflict mirror agreement | 74.77% | 89.30% |
| Total conflict mismatch bars | 1660 | 704 |
| Stage 1↔4 attributable mismatch bars | 933 | 28 |
| Stage 2↔5 attributable mismatch bars | 0 | 0 |
| Stage 3↔6 attributable mismatch bars | 0 | 0 |

## Frozen invariants

B-7 registered numeric classifier metrics preserved: **YES**  
Stage 2/5 and 3/6 conflict mismatch remain zero: **YES**  
Actual Issue #57 persistence replay still exact under C-2: **YES**

## Downstream observations (not tuning targets)

| Metric | B-7 | C-2 | Gain |
|---|---:|---:|---:|
| Candidate conflict mirror | 74.77% | 89.30% | 14.53% |
| Strong-stage mirror | 86.84% | 99.33% | 12.49% |
| Candidate-display mirror | 99.65% | 99.65% | 0.00% |
| Formal mirror | 92.33% | 99.73% | 7.40% |
| Formal transition mirror | 90.90% | 99.59% | 8.69% |
| Stale-pressure reason mirror | 92.95% | 99.56% | 6.61% |
| Stale-pressure bars mirror | 92.08% | 99.47% | 7.39% |

Formal mismatch bars: 505 → 18  
Strong-stage mismatch bars: 866 → 44  
Formal state-carry share: 49.70% → 61.11%

Downstream results may not be used to retune C-2.
