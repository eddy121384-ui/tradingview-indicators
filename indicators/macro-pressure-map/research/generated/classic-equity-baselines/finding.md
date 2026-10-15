# Classic equity de-risking baseline — first historical calculation (2026-10-15)

- Frozen *before first output*: [prereg](../classic_equity_baselines_prereg.md), commit `3445dc4`.
- Parent dataset ref `1fabf0f`; equity `issue-166/equity-monthly-total-returns.csv` (Git blob `2d850320`) and cash `issue-174/nine-sleeve-monthly-returns.csv` (Git blob `e2fb13ab`).
- Standalone reproducible Node implementation: [classic_equity_baselines.mjs](../classic_equity_baselines.mjs); initial results: [initial-results.json](initial-results.json).
- Study is **in-sample and revised-vintage**, not pristine out-of-sample, not a replication of MOP futures strategy, no GPI/IPI/FCPI consulted. `production_authorized=false`.

## Main full-common monthly comparison

**1967-03–2026-08; 714 months; signal uses t-month data, payoff in t+1; per-switch 2bp; total-return broad US market (French/CRSP, NOT S&P500).** No parameter optimization.

| policy | CAGR | annualized vol | MaxDD | Sharpe-like | avg equity exposure | switches |
|---|---:|---:|---:|---:|---:|---:|
| 100% Buy & Hold | 10.91% | 15.69% | **−50.31%** | 0.456 | 100% | 0 |
| 50% stocks / 50% cash | 8.04% | 7.86% | −27.93% | 0.456 | 50% | 0 |
| 60% stocks / 40% cash | 8.66% | 9.42% | −32.97% | 0.456 | 60% | 0 |
| **10-month SMA** | **10.28%** | 11.63% | **−24.24%** | **0.518** | 74.93% | 88 |
| **12-month excess momentum (long/cash)** | 10.16% | 11.90% | −28.31% | 0.500 | 72.41% | 49 |
| constant **74.93% stocks** (SMA matched) | 9.55% | 11.76% | −39.95% | 0.456 | 74.93% | 0 |
| constant **72.41% stocks** (MOM matched) | 9.40% | 11.36% | −38.81% | 0.456 | 72.41% | 0 |

The matched constants use **whole-sample hindsight to set only their static exposure**; they demonstrate the trade-off versus *simply holding less equity*, not a fully out-of-sample tradable benchmark. For SMA, historical MaxDD improvement over matched static is about **15.71 percentage points**; for MOM, about **10.51pp**. Their payoff is not merely a constant exposure reduction *in this sample*.

## Cross-era CAGR (predeclared, no selection)

| period | Buy & Hold | SMA10 | MOM12 |
|---|---:|---:|---:|
| 1967-03..1979-12 | 6.13% | 7.89% | 8.55% |
| 1980..1999 | **17.43%** | 13.95% | 14.20% |
| 2000..2019 | 6.38% | **7.84%** | 6.89% |
| 2020..2026-08 | **15.30%** | 11.48% | 11.36% |

This is **NOT an across-era CAGR domination**: both trend policies lag in the long 1980–99 bull era and since 2020. Dynamic strategies also sometimes de-risk too slowly for shock declines and re-enter too late.

## Predeclared stress windows: compounded within selected calendar windows

| calendar window | Buy & Hold | SMA10 | MOM12 |
|---|---:|---:|---:|
| 1973–1974 | −41.75% | −7.87% | +6.56% |
| Aug–Dec 1987 | −21.79% | −20.45% | −20.45% |
| Mar 2000–Oct 2002 | −37.16% | −6.68% | −6.56% |
| Oct 2007–Mar 2009 | −44.68% | −1.44% | −7.70% |
| Feb–Apr 2020 | −9.37% | −7.91% | **−20.21%** |
| 2022 | −19.92% | −10.70% | −13.02% |

These are **arbitrary *predeclared* calendar episodes**, not each strategy's full MaxDD, and are not signal-precision or OOS tests. The shock windows show **1987 was barely protected**, and the 2020 MOM12 model fared worse than Buy & Hold over the selected plunge-and-rebound window.

## Cost sensitivity and limits

With 10bp rather than 2bp per 100% equity-turnover, CAGR falls to **10.15% SMA** and **10.09% MOM** (SMA turnover ≈148%/year; MOM ≈82%/year). Cost proxy ignores spreads, market impact, taxes and trade at next-month opens. Constant-mix benchmarks do not pay intra-month drift rebalancing costs.

**What this supports:** well-known simple trend signals are nontrivial risk-control baselines. **What it does not support:** that trend dominates in every era or crash, or that GPI/IPI/FCPI adds value. Proper next comparison is **macro vs trend vs macro+trend at matched equity exposure and frozen rules**, *only after* addressing revised-vintage/PIT limitations.

## Volatility-managed strategy status

Moreira/Muir original requires **prior-month daily realized variance**, not a 12-month rolling monthly-vol substitute. The French daily factors source exists (see https://mba.tuck.dartmouth.edu/pages/faculty/Ken.French/data_library.html; official daily CSV ZIP https://mba.tuck.dartmouth.edu/pages/faculty/Ken.French/ftp/F-F_Research_Data_Factors_daily_CSV.zip); current research execution could not retrieve ZIP bytes from this environment. Daily data **not yet downloaded or validated**, so **no volatility-target result is claimed**. Once downloaded, verify daily compound-to-monthly alignment and vintage against #166 before a separate prereg.
