# Issue #55 — Exploratory-OOS trading utility under frozen rules

Final OOS remains **SEALED / NOT COMPUTED**.

Rules were committed before this report: formal-state response map, one-bar lag, 1-pip-per-unit-turnover primary cost, SMA200 / Momentum60 / Donchian55 baselines.

## Equal-weight four-pair aggregate

| Strategy | Net ann. return | Net vol | Sharpe | Max DD | Avg abs exposure | Turnover | Cost drag |
|---|---:|---:|---:|---:|---:|---:|---:|
| wyckoff_frozen_response | -3.19% | 4.46% | -0.71 | -8.59% | 64.1% | 20.0 | 0.18% |
| sma200 | -0.90% | 5.37% | -0.14 | -7.20% | 100.0% | 25.0 | 0.23% |
| momentum60 | -1.53% | 5.02% | -0.28 | -6.46% | 100.0% | 60.5 | 0.59% |
| donchian55 | -2.92% | 4.81% | -0.59 | -8.93% | 100.0% | 9.5 | 0.09% |
| always_flat | 0.00% | 0.00% | — | 0.00% | 0.0% | 0.0 | 0.00% |

## Per pair — Wyckoff frozen response

| Pair | Net ann. return | Sharpe | Max DD | Exposure | Turnover |
|---|---:|---:|---:|---:|---:|
| EURUSD | -4.94% | -0.88 | -13.32% | 61.8% | 14.0 |
| USDJPY | -8.93% | -1.35 | -17.82% | 57.4% | 29.0 |
| GBPUSD | -2.89% | -0.34 | -11.84% | 69.1% | 21.0 |
| AUDUSD | 3.80% | 0.49 | -9.95% | 68.3% | 16.0 |

## Wyckoff minus baseline (equal-weight aggregate)

| Baseline | Ann. return difference | Sharpe difference |
|---|---:|---:|
| sma200 | -2.30% | -0.56 |
| momentum60 | -1.67% | -0.42 |
| donchian55 | -0.27% | -0.11 |

Boundary: Exploratory OOS only. These results cannot be used to alter the frozen Final-OOS response map or baselines.
