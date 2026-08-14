# Issue #57 — Early bridge formation behavior map

**Burned-data structural study only. Existing v0.6 is unchanged.**

## Conversion

- Non-overlapping bridge watches: **298** across **7** FX pairs.
- Bull / bear events: **193 / 105**.
- Median pair conversion to same-direction actionable within 5 bars: **5.00%**.
- Within 10 bars: **9.52%**.
- Within 20 bars: **14.29%**.
- Median pair median lag when conversion occurs by 20: **7.0 bars**.
- Opposite-actionable first: **21.62%**; timeout: **64.29%**.

## What differs at bridge onset? (success within 10 vs not)

| Metric | Success <=10 | No success <=10 |
|---|---:|---:|
| Events | 29 | 269 |
| Top2 strength | 99.87 | 99.92 |
| Six-stage entropy | 0.066 | 0.166 |
| Context-stage weight | 10.59 | 77.19 |
| Target-family weight | 87.71 | 19.24 |
| Same-side pressure | 99.98 | 99.99 |
| Opposite pressure | 0.02 | 0.01 |
| 3-bar same-side pressure change | 0.51 | 0.06 |
| Formal already aligned | 50.00% | 34.29% |
| Formal neutral/transition | 40.00% | 48.57% |
| 10-bar aligned return | 0.60% | -0.19% |
| 10-bar MFE | 1.60% | 0.89% |
| 10-bar MAE | 0.80% | 1.14% |

## Per pair

| Pair | Events | Success <=5 | <=10 | <=20 | Median success lag |
|---|---:|---:|---:|---:|---:|
| EURUSD | 42 | 4.76% | 9.52% | 16.67% | 9.0 |
| USDJPY | 42 | 7.14% | 11.90% | 14.29% | 5.5 |
| GBPUSD | 41 | 9.76% | 14.63% | 17.07% | 1.0 |
| AUDUSD | 40 | 5.00% | 7.50% | 12.50% | 9.0 |
| EURCHF | 37 | 0.00% | 5.41% | 8.11% | 10.0 |
| USDCAD | 44 | 0.00% | 2.27% | 2.27% | 7.0 |
| USDCHF | 52 | 9.62% | 15.38% | 19.23% | 6.0 |

## Boundary

This map describes already-observed data. Differences between successful and failed bridges are hypotheses about indicator behavior, not validated entry rules.
