# Issue #55 — Pre-final state-separation scorecard

Final OOS remains **SEALED / NOT COMPUTED**.

This deliberately ignores whether labels such as Markup/Markdown are semantically correct. The question is only whether the formal-state label separates future paths and whether that separation is stable from Development to Exploratory OOS.

Only states with at least **20** eligible bars enter eta-squared/rank comparisons.

| Pair | H | States n≥20 Dev→Exp | Return η² Dev→Exp | MFE η² Dev→Exp | MAE η² Dev→Exp | Vol η² Dev→Exp | Return-rank ρ | Sign stable |
|---|---:|---|---|---|---|---|---:|---:|
| EURUSD | 5 | 4→2 | 0.019→0.016 | 0.027→0.033 | 0.024→0.001 | 0.111→0.035 | — | 1/2 |
| EURUSD | 10 | 4→2 | 0.050→0.032 | 0.052→0.046 | 0.041→0.001 | 0.206→0.047 | — | 1/2 |
| EURUSD | 20 | 4→2 | 0.062→0.091 | 0.037→0.069 | 0.076→0.014 | 0.272→0.072 | — | 1/2 |
| EURUSD | 60 | 4→2 | 0.206→0.302 | 0.114→0.006 | 0.097→0.289 | 0.254→0.019 | — | 0/2 |
| USDJPY | 5 | 4→3 | 0.084→0.069 | 0.031→0.047 | 0.090→0.066 | 0.092→0.087 | 0.50 | 3/3 |
| USDJPY | 10 | 4→3 | 0.153→0.076 | 0.084→0.056 | 0.136→0.094 | 0.175→0.092 | 1.00 | 3/3 |
| USDJPY | 20 | 4→3 | 0.121→0.060 | 0.131→0.053 | 0.116→0.156 | 0.154→0.100 | 1.00 | 3/3 |
| USDJPY | 60 | 4→3 | 0.354→0.086 | 0.346→0.033 | 0.177→0.139 | 0.185→0.026 | 0.50 | 3/3 |
| GBPUSD | 5 | 4→4 | 0.032→0.062 | 0.033→0.019 | 0.025→0.082 | 0.025→0.023 | -0.80 | 1/4 |
| GBPUSD | 10 | 4→4 | 0.050→0.158 | 0.055→0.050 | 0.023→0.211 | 0.064→0.106 | -0.80 | 1/4 |
| GBPUSD | 20 | 4→4 | 0.029→0.204 | 0.048→0.045 | 0.021→0.530 | 0.136→0.419 | -0.80 | 1/4 |
| GBPUSD | 60 | 4→3 | 0.058→0.129 | 0.011→0.019 | 0.063→0.134 | 0.399→0.062 | 0.50 | 1/3 |
| AUDUSD | 5 | 3→2 | 0.002→0.005 | 0.001→0.015 | 0.006→0.007 | 0.003→0.033 | — | 0/1 |
| AUDUSD | 10 | 3→2 | 0.000→0.014 | 0.003→0.025 | 0.001→0.003 | 0.027→0.042 | — | 0/1 |
| AUDUSD | 20 | 3→2 | 0.006→0.031 | 0.001→0.027 | 0.005→0.000 | 0.154→0.049 | — | 0/1 |
| AUDUSD | 60 | 3→2 | 0.325→0.167 | 0.280→0.034 | 0.138→0.135 | 0.168→0.019 | — | 0/1 |

## Aggregate exploratory separation

| H | Return median η² | MFE median η² | MAE median η² | Vol median η² | Median return-rank ρ | Return-sign stability |
|---:|---:|---:|---:|---:|---:|---:|
| 5 | 0.039 | 0.026 | 0.037 | 0.034 | -0.15 | 5/10 (50.0%) |
| 10 | 0.054 | 0.048 | 0.048 | 0.069 | 0.10 | 5/10 (50.0%) |
| 20 | 0.076 | 0.049 | 0.085 | 0.086 | 0.10 | 5/10 (50.0%) |
| 60 | 0.148 | 0.026 | 0.137 | 0.023 | 0.50 | 4/9 (44.4%) |

Interpretation boundary: eta-squared is descriptive, not a significance test; high separation that fails Development→Exploratory stability is not treated as validated regime information.

Boundary: Development + Exploratory OOS only. Final OOS remains sealed.
