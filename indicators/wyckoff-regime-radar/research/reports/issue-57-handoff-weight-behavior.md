# Issue #57 — Bridge handoff-weight behavior map

**Burned-data structural study only. Existing v0.6 is unchanged.**

- Bridge events: **298** across **7** FX pairs.
- Median-pair conversion <=5 / <=10 / <=20: **5.00% / 9.52% / 14.29%**.

## Successful vs unsuccessful bridge at onset

| Metric | Success <=10 | No success <=10 |
|---|---:|---:|
| Old context weight | 10.59 | 77.19 |
| New carried target weight | 86.99 | 19.24 |
| New companion weight | 0.02 | 0.00 |
| Carried - context margin | 76.40 | -59.24 |
| Companion - context margin | -9.87 | -77.19 |
| New family - context margin | 77.12 | -59.24 |
| 3-bar old context change | 0.00 | 1.49 |
| 3-bar carried change | 4.85 | 2.17 |
| 3-bar companion change | 0.00 | 0.00 |
| 3-bar carried-context margin change | 1.87 | -0.41 |
| 3-bar companion-context margin change | -0.00 | -1.47 |

## Mechanical handoff flags

| Flag | Events yes | Success <=10 when yes | Success <=10 when no |
|---|---:|---:|---:|
| carried_already_leads_context | 125 | 15.00% | 4.35% |
| context_falling_carried_rising_3 | 100 | 16.67% | 7.41% |
| context_falling_companion_rising_3 | 31 | 0.00% | 10.53% |
| both_new_targets_rising_context_falling_3 | 30 | 0.00% | 10.26% |

## Per pair

| Pair | Events | <=10 success | Carried-leads success | Carried-not-leads success |
|---|---:|---:|---:|---:|
| EURUSD | 42 | 9.52% | 20.00% | 3.70% |
| USDJPY | 42 | 11.90% | 11.11% | 12.50% |
| GBPUSD | 41 | 14.63% | 26.32% | 4.55% |
| AUDUSD | 40 | 7.50% | 15.00% | 0.00% |
| EURCHF | 37 | 5.41% | 7.14% | 4.35% |
| USDCAD | 44 | 2.27% | 4.76% | 0.00% |
| USDCHF | 52 | 15.38% | 27.78% | 8.82% |

## Boundary

Descriptive behavior map on burned fixtures. No numeric cutoff or production rule is selected.
