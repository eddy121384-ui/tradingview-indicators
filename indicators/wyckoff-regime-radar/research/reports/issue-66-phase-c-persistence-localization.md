# Issue #66 Phase C — Candidate→Formal Persistence Localization (v3)

Status: **reused frozen data / no PnL / no formula change**

Persistence contract: **actual inherited Issue #57 Phase-B stale-pressure state machine**

Exact replay of all five stored state series: **PASS**

| State series | Exact replay |
|---|---:|
| Formal id | YES |
| Candidate id | YES |
| Candidate bars | YES |
| Stale-pressure bars | YES |
| Stale-pressure reason | YES |

## Current-bar mirror inputs

| Input | Mirror agreement |
|---|---:|
| Top stage | 81.73% |
| Evidence threshold pass | 99.98% |
| Candidate conflict | 74.77% |
| Strong-stage id | 86.84% |
| Candidate display id | 99.65% |
| Chaos | 100.00% |
| Coexist | 99.56% |
| Fast switch | 99.88% |
| Active confirm bars | 99.88% |
| Stale-pressure reason | 92.95% |
| Stale-pressure bars | 92.08% |

## Candidate residual attribution

| Rank | Cause | Strong-stage mismatch overlap | Share |
|---:|---|---:|---:|
| 1 | Candidate conflict | 857 | 98.96% |
| 2 | Top-gap threshold | 11 | 1.27% |
| 3 | Top-stage mismatch | 6 | 0.69% |
| 4 | Probability-valid mismatch | 0 | 0.00% |
| 5 | Dominant threshold | 0 | 0.00% |
| 6 | Evidence threshold | 0 | 0.00% |

Unexplained strong-stage mismatch bars: **0**.

## Persistence amplification

Candidate-display mismatch bars: **23**  
Strong-stage mismatch bars: **866**  
Formal mismatch bars: **505**  
Formal / strong-stage mismatch amplification: **0.58×**  
Formal mismatch bars where all current persistence inputs are already mirrored: **251** (49.70%)

Current persistence-input mismatch bars: `strong_stage=866, candidate_display=23, chaos=0, coexist=29, active_confirm_bars=8`

## Counterfactual replay localization (diagnostic only)

| Replay | Formal mirror | Gain vs original |
|---|---:|---:|
| Original stale-pressure persistence | 92.33% | 0.00% |
| Chaos-only stale pressure | 93.01% | 0.68% |
| Disable weak-challenger pressure | 93.01% | 0.68% |
| Disable coexist pressure | 92.71% | 0.38% |
| Fixed confirm / no fast shortening | 91.82% | -0.50% |
| Immediate strong confirmation | 91.06% | -1.26% |
| Immediate stale clear | 88.94% | -3.39% |
| Stateless strong-stage | 86.84% | -5.49% |

## Decision boundary

No counterfactual is a proposed production change. If the full stale-pressure loop is structurally symmetric under exact mirrored inputs, repair the dominant residual input family before considering any persistence redesign.
