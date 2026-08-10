# Issue #57 — v0.6 Phase C state-cardinality audit

Status: **cardinality_audit_complete_pending_phase_c_decision**

Already-observed/burned Issue #55 history using frozen v0.6 Phase-B 2x stale decay. 6/4/3 semantic mappings were declared before this analysis. No PnL and no independent validation claim.

Mappings were declared before this analysis:

- **6-state:** original six stages.
- **4-state:** Accumulation + Re-accumulation / Markup / Distribution + Re-distribution / Markdown.
- **3-state:** Balance/Transition (1/3/4/6) / Uptrend (2) / Downtrend (5).

## State coverage

### development

| Representation | Target states | Median populated >=1% | Median populated >=5% | Effective states | All target states >=1% pair rate |
|---|---:|---:|---:|---:|---:|
| 6-state | 6 | 4.5 | 4.0 | 3.601 | 0.0% |
| 4-state | 4 | 4.0 | 4.0 | 3.480 | 100.0% |
| 3-state | 3 | 3.0 | 3.0 | 2.816 | 100.0% |

### exploratory_oos

| Representation | Target states | Median populated >=1% | Median populated >=5% | Effective states | All target states >=1% pair rate |
|---|---:|---:|---:|---:|---:|
| 6-state | 6 | 4.0 | 2.5 | 2.842 | 0.0% |
| 4-state | 4 | 4.0 | 2.5 | 2.842 | 75.0% |
| 3-state | 3 | 3.0 | 2.5 | 2.521 | 100.0% |

### final_oos

| Representation | Target states | Median populated >=1% | Median populated >=5% | Effective states | All target states >=1% pair rate |
|---|---:|---:|---:|---:|---:|
| 6-state | 6 | 4.0 | 4.0 | 3.394 | 0.0% |
| 4-state | 4 | 4.0 | 4.0 | 3.394 | 100.0% |
| 3-state | 3 | 3.0 | 3.0 | 2.876 | 100.0% |

## Forward-return separation (median eta-squared across pairs)

| Segment | Representation | 5 | 10 | 20 | 60 |
|---|---|---:|---:|---:|---:|
| development | 6-state | 0.015 | 0.032 | 0.029 | 0.285 |
| development | 4-state | 0.008 | 0.024 | 0.029 | 0.285 |
| development | 3-state | 0.012 | 0.018 | 0.013 | 0.260 |
| exploratory_oos | 6-state | 0.029 | 0.040 | 0.062 | 0.163 |
| exploratory_oos | 4-state | 0.029 | 0.040 | 0.062 | 0.163 |
| exploratory_oos | 3-state | 0.017 | 0.020 | 0.042 | 0.164 |
| final_oos | 6-state | 0.026 | 0.021 | 0.032 | 0.086 |
| final_oos | 4-state | 0.026 | 0.021 | 0.032 | 0.086 |
| final_oos | 3-state | 0.011 | 0.008 | 0.018 | 0.050 |

## Temporal stability

### development_to_exploratory_oos

| Representation | Occupancy L1 shift | Return-rank rho 5/10/20/60 | Return-sign stability 5/10/20/60 |
|---|---:|---|---|
| 6-state | 0.982 | 0.30 / 0.10 / 0.30 / 0.50 | 60.0% / 30.0% / 50.0% / 55.6% |
| 4-state | 0.945 | 0.30 / 0.10 / 0.50 / 0.50 | 60.0% / 30.0% / 50.0% / 55.6% |
| 3-state | 0.676 | 0.75 / 1.00 / 0.75 / 0.75 | 60.0% / 40.0% / 50.0% / 50.0% |

### exploratory_oos_to_final_oos

| Representation | Occupancy L1 shift | Return-rank rho 5/10/20/60 | Return-sign stability 5/10/20/60 |
|---|---:|---|---|
| 6-state | 0.739 | 0.05 / -0.45 / -0.45 / -0.75 | 63.6% / 54.5% / 45.5% / 60.0% |
| 4-state | 0.739 | 0.05 / -0.45 / -0.45 / -0.75 | 63.6% / 54.5% / 45.5% / 60.0% |
| 3-state | 0.607 | 0.75 / 0.25 / 0.00 / -0.75 | 80.0% / 50.0% / 40.0% / 40.0% |

## Decision boundary

Prefer the smallest predeclared representation that materially improves state coverage and temporal stability while retaining nontrivial future-path separation. Do not choose from trading PnL. The Issue #55 final-OOS period is burned development evidence here, not an independent validation sample.
