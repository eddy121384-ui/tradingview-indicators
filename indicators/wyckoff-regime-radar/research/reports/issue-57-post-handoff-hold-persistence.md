# Issue #57 — Post-handoff hold persistence map

**Reused-data structural study only. Existing v0.6 is unchanged.**

- Seizure events: **125** across **7** FX pairs.

## Does holding the lead improve eventual completion?

| Checkpoint | Eligible unresolved | Held continuously | Lost lead | Success <=20 if held | Success <=20 if lost | Pair wins |
|---|---:|---:|---:|---:|---:|---:|
| +1 | 116 | 85 | 31 | 20.00% | 0.00% | 6/7 |
| +3 | 114 | 63 | 51 | 25.00% | 0.00% | 7/7 |
| +5 | 112 | 49 | 63 | 20.00% | 9.09% | 5/7 |
| +10 | 97 | 30 | 67 | 12.50% | 0.00% | 4/7 |

## What happens when the old context retakes the lead?

- Retake / no-retake events: **89 / 36**.
- Median-pair retake rate: **71.43%**.
- Median-pair median first-retake lag: **3.00 bars**.
- Same-direction completion <=20 after a retake: **10.00%**.
- Same-direction completion <=20 with no retake: **42.86%**.
- No-retake beats retake on **7/7** comparable FX pairs.

## Per pair retake comparison

| Pair | Seizures | Retake rate | Success after retake | Success no retake |
|---|---:|---:|---:|---:|
| EURUSD | 15 | 73.33% | 18.18% | 75.00% |
| USDJPY | 18 | 83.33% | 13.33% | 33.33% |
| GBPUSD | 19 | 68.42% | 7.69% | 83.33% |
| AUDUSD | 20 | 65.00% | 7.69% | 42.86% |
| EURCHF | 14 | 71.43% | 10.00% | 25.00% |
| USDCAD | 21 | 80.95% | 0.00% | 25.00% |
| USDCHF | 18 | 55.56% | 10.00% | 62.50% |

## Boundary

Descriptive reuse of already-used fixtures; no checkpoint or production rule is selected.
