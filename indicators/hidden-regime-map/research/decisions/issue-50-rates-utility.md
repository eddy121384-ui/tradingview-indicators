# Issue #50 rates regime-utility result

Outcome: `inconclusive_instability`

Frozen input SHA-256: `f85a37d574f58ed927c1b490f14d0057a2f1c295c7061cf2a5d08b433995c104`

## Final OOS metrics

| variant | ann. return | Sharpe | max drawdown | Calmar | ann. turnover |
|---|---:|---:|---:|---:|---:|
| tlt_buy_hold | -0.0395 | -0.494 | -0.2403 | -0.164 | 0.000 |
| equal_duration | 0.0036 | -0.501 | -0.1135 | 0.031 | 0.000 |
| inverse_vol_63 | 0.0215 | -0.617 | -0.0459 | 0.469 | 0.547 |
| trend_duration_200 | -0.0865 | -1.566 | -0.3009 | -0.288 | 23.262 |
| vol_target_tlt_20 | -0.0112 | -0.628 | -0.1066 | -0.105 | 5.101 |
| hmm_k3_duration_blend | 0.0124 | -0.416 | -0.1016 | 0.122 | 0.004 |
| hmm_k4_duration_blend | 0.0109 | -0.442 | -0.1016 | 0.107 | 2.500 |

## Mechanical decision

Trading winners: {}

Risk winners: {}

This result is bounded to the preregistered U.S. rates experiment. A passing outcome remains provisional until adjacent-window or walk-forward sensitivity succeeds.
