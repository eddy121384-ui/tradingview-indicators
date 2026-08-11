# Issue #57 — Phase E ONE-SHOT cross-market holdout result

Final verdict: **`unstable_on_independent_fx_pairs`**

The USDCAD / USDCHF / EURCHF holdout is now consumed and may not be reused as an independent test after redesign.

## Gate scorecard

- Coverage: **PASS** — material pair counts by state: {'1': 3, '2': 3, '3': 3, '4': 3}.
- Directional sanity: **FAIL** — 3/12 (25.0%) Markup > Markdown.
- Temporal stability: **PASS** — median occupancy TV 0.163; return-sign stability 24/47.
- Regime Support/Margin persistence: **PASS**.
- Incremental trading utility: **PASS** — beats 3/3 baselines on both annualized return and Sharpe.

## Path separation

- forward_return: median eta-squared **0.014**
- mfe: median eta-squared **0.016**
- mae: median eta-squared **0.014**
- realized_vol: median eta-squared **0.051**

## Per-pair state occupancy

| Pair | Neutral | AccFam | Markup | DistFam | Markdown | Material states |
|---|---:|---:|---:|---:|---:|---:|
| USDCAD | 5.3% | 23.7% | 29.5% | 9.4% | 32.1% | 4/4 |
| USDCHF | 7.9% | 25.2% | 25.4% | 10.7% | 30.8% | 4/4 |
| EURCHF | 5.8% | 15.4% | 26.0% | 17.1% | 35.8% | 4/4 |

## Frozen-response trading utility — equal-weight three-pair aggregate

| Strategy | Net ann. return | Vol | Sharpe | Max DD | Exposure |
|---|---:|---:|---:|---:|---:|
| wyckoff_v06_frozen_response | -1.17% | 2.98% | -0.38 | -7.59% | 59.8% |
| sma200 | -1.57% | 3.68% | -0.41 | -9.14% | 100.0% |
| momentum60 | -3.44% | 3.72% | -0.92 | -17.55% | 100.0% |
| donchian55 | -2.32% | 3.79% | -0.60 | -15.32% | 100.0% |
| always_flat | 0.00% | 0.00% | — | 0.00% | 0.0% |

## Strength persistence

- `regime_support`: high bin persists more than low in **11/12** comparable pair×horizon cases (91.7%).
- `regime_margin`: high bin persists more than low in **11/12** comparable pair×horizon cases (91.7%).

Boundary: this is a one-shot independent cross-market result. Any further redesign requires a new untouched sample.
