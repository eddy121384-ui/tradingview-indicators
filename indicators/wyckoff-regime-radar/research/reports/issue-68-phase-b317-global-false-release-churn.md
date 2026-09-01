# Issue #68 Phase B3.17 — Global False-Release / Churn Audit

Status: **diagnostic shadow only / frozen C-2 / no performance use**

Primary engineering gate: **PASS**
- eligible stale-overlap bars: **1523**
- raw-advance bars / episodes: **69 / 51**
- followed-handoff episodes: **25**
- false-release episodes: **26 (51.0%)**
- one-bar false releases: **20 (76.9% of false releases)**

## Episode timing

- raw-advance episode duration: median **1.0**, p75 **1.5**, max **4**
- lead to later observed handoff: median **1.0**, p75 **2.0**, max **7**

## Churn / transition safety

- observed raw transitions: **746**
- shadow raw transitions: **793**
- transition-count ratio: **1.063x**
- MA-side runs with 0 / 1 / >1 advance episodes: **539 / 40 / 5**
- raw-advance bars with target NEW RANGE already present: **20 / 69 (29.0%)**

## Engineering / reciprocal checks

- max Break / observed / shadow reconstruction error: **0.000e+00 / 2.842e-14 / 2.842e-14**
- minimum reciprocal eligibility agreement: **100.000%**
- minimum reciprocal raw-advance agreement: **99.958%**
- minimum reciprocal episode-outcome agreement on common advance bars: **100.000%**
- minimum reciprocal transition-count agreement (diagnostic only): **97.619%**
- unexplained episode accounting: **0**

## Per-pair summary

| Pair | Eligible bars | Advance eps | Followed | False | Obs trans | Shadow trans | MA runs >1 eps |
|---|---:|---:|---:|---:|---:|---:|---:|
| EURUSD | 347 | 7 | 4 | 3 | 216 | 220 | 0 |
| USDJPY | 393 | 19 | 6 | 13 | 196 | 215 | 2 |
| GBPUSD | 405 | 16 | 10 | 6 | 164 | 182 | 2 |
| AUDUSD | 378 | 9 | 5 | 4 | 170 | 176 | 1 |

## Boundary

Global safety audit of the frozen B3.16 one-source shadow only; production C-2 and all parameters remain unchanged.
