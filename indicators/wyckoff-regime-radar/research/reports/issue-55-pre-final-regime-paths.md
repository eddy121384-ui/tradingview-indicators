# Issue #55 — Pre-final-OOS regime path report

Final OOS remains **SEALED / NOT COMPUTED**.

This first pass asks only whether formal Markup (2) and Markdown (5) states point to different future close-return directions. It is not yet a trading backtest.

| Pair | Split | Horizon | Markup mean | n | Markdown mean | n | Mk − Md |
|---|---|---:|---:|---:|---:|---:|---:|
| EURUSD | development | 5 | 0.264% | 179 | 0.109% | 62 | 0.155% |
| EURUSD | development | 10 | 0.568% | 179 | 0.333% | 57 | 0.235% |
| EURUSD | development | 20 | 0.825% | 179 | 0.294% | 47 | 0.531% |
| EURUSD | development | 60 | 0.711% | 175 | 3.582% | 30 | -2.870% |
| EURUSD | exploratory_oos | 5 | -2.476% | 10 | 0.068% | 282 | -2.544% |
| EURUSD | exploratory_oos | 10 | -2.587% | 10 | 0.060% | 277 | -2.647% |
| EURUSD | exploratory_oos | 20 | -2.667% | 10 | 0.066% | 267 | -2.733% |
| EURUSD | exploratory_oos | 60 | — | 0 | -0.260% | 237 | — |
| USDJPY | development | 5 | -0.535% | 91 | 0.136% | 139 | -0.671% |
| USDJPY | development | 10 | -0.996% | 91 | 0.400% | 139 | -1.396% |
| USDJPY | development | 20 | -1.258% | 91 | 0.534% | 139 | -1.791% |
| USDJPY | development | 60 | -2.158% | 85 | 1.217% | 128 | -3.375% |
| USDJPY | exploratory_oos | 5 | -0.480% | 133 | 0.222% | 138 | -0.702% |
| USDJPY | exploratory_oos | 10 | -0.636% | 133 | 0.344% | 133 | -0.979% |
| USDJPY | exploratory_oos | 20 | -0.704% | 125 | 0.258% | 133 | -0.962% |
| USDJPY | exploratory_oos | 60 | -1.271% | 104 | 0.401% | 120 | -1.672% |
| GBPUSD | development | 5 | 0.066% | 211 | 0.195% | 66 | -0.129% |
| GBPUSD | development | 10 | 0.057% | 211 | 0.370% | 61 | -0.313% |
| GBPUSD | development | 20 | 0.153% | 211 | 0.892% | 51 | -0.739% |
| GBPUSD | development | 60 | 1.280% | 194 | 2.668% | 35 | -1.388% |
| GBPUSD | exploratory_oos | 5 | -0.232% | 109 | 0.052% | 222 | -0.284% |
| GBPUSD | exploratory_oos | 10 | -0.331% | 109 | 0.079% | 222 | -0.409% |
| GBPUSD | exploratory_oos | 20 | -0.043% | 109 | -0.056% | 217 | 0.013% |
| GBPUSD | exploratory_oos | 60 | -2.727% | 109 | 0.535% | 203 | -3.261% |
| AUDUSD | development | 5 | 0.086% | 172 | 0.150% | 134 | -0.064% |
| AUDUSD | development | 10 | 0.154% | 172 | 0.161% | 134 | -0.007% |
| AUDUSD | development | 20 | 0.066% | 172 | 0.402% | 126 | -0.336% |
| AUDUSD | development | 60 | -1.800% | 172 | 3.145% | 86 | -4.945% |
| AUDUSD | exploratory_oos | 5 | -0.238% | 3 | -0.085% | 322 | -0.153% |
| AUDUSD | exploratory_oos | 10 | -0.790% | 3 | -0.126% | 322 | -0.664% |
| AUDUSD | exploratory_oos | 20 | -3.061% | 3 | -0.323% | 316 | -2.738% |
| AUDUSD | exploratory_oos | 60 | -11.022% | 3 | -1.018% | 276 | -10.004% |

Directional sign check: Markup minus Markdown is positive in **4 / 31** pair/split/horizon comparisons.
Median Markup-minus-Markdown spread: **-0.739%**

Full JSON alongside this report contains all six stages plus MFE, MAE, realized volatility, medians and positive-return rates.

Boundary: descriptive development + exploratory OOS only; no final OOS and no trading utility claim.
