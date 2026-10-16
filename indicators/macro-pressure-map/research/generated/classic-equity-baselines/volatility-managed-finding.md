# Volatility-managed equity — results (2026-10-16)

- Prereg (frozen before any vol P&L): `volatility_managed_prereg.md`, commit `a4c729f`.
- Engine: `volatility_managed_backtest.mjs`; mechanics tests: `test_volatility_managed.mjs` (6 checks PASS).
- Parent dataset ref `1fabf0f`; no macro data consulted; `production_authorized=false`.

## Official daily data validation (task 1–3)

- Source: `F-F_Research_Data_Factors_daily_CSV.zip`, SHA256
  `2f29e22546069914890a712680a6f81f3680ebc3543b52864484d209ca13a7db`
  (fetched 2026-10-16, committed as `daily-market-total-returns.csv` +
  `daily-provenance.json`).
- 26,317 rows, 19260701..20260831. Compounded to monthly vs repo #166 totals:
  **800 overlap months, MAE 0.047pp/mo, max |diff| 0.181pp (1989-05)**,
  68/800 months >10bp scattered across eras and signs, era means ≈ 0.
- 2025+ CIZ window: all diffs ±0.1bp — **no FIZ/CIZ methodology break visible**
  in monthly chaining. Residual consistent with file-decimal precision plus
  component aggregation/rounding. Not forced closer; fit as variance-signal
  input (monthly level diffs immaterial to daily variances). **Not BLOCKED.**

## Leg 1 — paper-faithful replication (excess space, ex-post c, unconstrained)

1967-03..2026-08, 714 payoffs. `c=4.204e-05` (full-sample vol match, ex-post).

| | unmanaged factor | managed |
|---|---|---|
| excess CAGR | 6.18% | 5.01% |
| vol | 15.69% | 15.69% (by construction) |
| Sharpe (excess) | 0.463 | 0.392 |
| MaxDD | −55.37% | −66.93% |
| worst month | −23.09% | −27.28% |

Regression managed on unmanaged: **alpha +0.091pp/mo, beta 0.70**.
Weight distribution: median 0.84, mean 1.06, p75 1.38, p90 2.11, p99 4.56,
max 7.59; 41% months >1.0, 21% >1.5 — same shape family as paper Table 5
(≈1/1.6/2.6/6.4), slightly less extreme. Independently recomputed in Python
from the daily file: all headline digits match.

Reading: positive alpha with lower Sharpe and deeper drawdowns on this
1967–2026 window — **the paper's Sharpe improvement does not reproduce here**.
Not an exact replication (paper sample ends 2015, pre-CIZ data, their monthly
file vs our daily chaining), and direction differs, both stated plainly.
No leverage-constrained variant was run (would be a new prereg).

## Leg 2 — deployable fair comparison (total-return space, [0,1], expanding calibration)

`w=min(1, expanding-mean-RV/RVprev)`, same cash/costs/panel as baselines:

| policy | CAGR | vol | Sharpe-like | MaxDD | turnover/yr | avg equity |
|---|---|---:|---:|---:|---:|---:|
| Vol-managed fair | 10.44% | 13.38% | 0.477 | −41.20% | 101% | 90.69% |
| Buy & Hold | 10.91% | 15.69% | 0.456 | −50.31% | 0% | 100% |
| SMA10 | 10.28% | 11.63% | 0.518 | −24.24% | 148% | 74.93% |
| MOM12 | 10.16% | 11.90% | 0.500 | −28.31% | 82% | 72.41% |
| matched 90.69% fixed | 10.43% | — | — | — | — | 90.69% |

Eras (fair CAGR): E1 6.40%, E2 15.81%, E3 7.26%, E4 12.27%.
Crises compounded: 1973–74 −39.02%, 1987 −18.33%, 2000–02 −26.50%,
2007–09 −21.47%, 2020 −14.16%, 2022 −12.72%.
First weight 1.000 (1967-03); capped below 1 in 22.5% of months.

Reading: slightly below BH on CAGR, slightly above on Sharpe-like, shallower
MaxDD; behind SMA10/MOM12 on risk-adjusted and drawdown. The exposure-matched
fixed control (10.43%) shows nearly all of Leg 2's return is exposure, same
pattern as the monthly baselines. No dominance claim; no macro test (separate
prereg required before any GPI/IPI/FCPI three-way comparison).
