# U.S. Rates K=6 visual-reference profile

- Profile: `us-rates-k6-visual-v0.1`
- Model kind: `descriptive_full_sample_reference`
- Frozen input SHA-256: `f85a37d574f58ed927c1b490f14d0057a2f1c295c7061cf2a5d08b433995c104`
- Feature rows: 4868
- Feature period: 2007-02-01 through 2026-07-30
- Representative seed: 43

This is a full-sample descriptive profile for chart inspection. Historical state colors are retrospective and are not out-of-sample evidence.

| State | Occupancy | Mean duration | Self-transition | Ordering score |
|---|---:|---:|---:|---:|
| R1 | 11.24% | 109.40 | 0.9925 | -0.6519 |
| R2 | 16.50% | 200.75 | 0.9962 | -0.4003 |
| R3 | 13.43% | 163.50 | 0.9953 | -0.2809 |
| R4 | 26.15% | 212.17 | 0.9961 | -0.1332 |
| R5 | 14.73% | 239.00 | 0.9958 | 0.6063 |
| R6 | 17.95% | 218.50 | 0.9965 | 0.6943 |

## Instability diagnostics

- Feature drift warning: max absolute feature z-score >= 3.0.
- State concentration warning: max 126-bar dominant-state share >= 90%.
- Both thresholds are prototype diagnostics, not universal statistical laws.
