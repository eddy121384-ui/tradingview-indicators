# Equity risk classic baselines — prospective rule freeze (2026-10-15)

**Status:** preregistered before calculating, inspecting, or writing any new baseline P&L. Research only, `production_authorized=false`; not original-paper exact replication, not pristine out-of-sample.

## Motivation and paper anchors

Before attributing skill to GPI/IPI/FCPI, measure what established **price-only** strategies can do for US equities.

- Faber, *A Quantitative Approach to Tactical Asset Allocation* (2007): month-end 10-month simple moving average, total-return asset, cash when price below average. https://mebfaber.com/2017/12/13/episode-86-quantitative-approach-tactical-asset-allocation/
- Moskowitz, Ooi & Pedersen, *Time Series Momentum* (JFE 2012): own 12-month excess return, **long/short futures and volatility scaling in the paper**. https://doi.org/10.1016/j.jfineco.2011.11.003 — OUR equity-long/cash variation is **not** that original implementation.
- Moreira & Muir, *Volatility-Managed Portfolios* (JF 2017): lagged *daily* realized variance inverse; **DO NOT TEST** until genuine daily data and cost/risk scaling rules are available. https://doi.org/10.1111/jofi.12513

## Data and frozen comparators

Sources are pinned to parent `research/issue-189-deep-history-pit` SHA `1fabf0f9c94c391a7c2d302caff6bbdf56062d95`. Explicit existing CSV inputs:

- `generated/issue-166/equity-monthly-total-returns.csv` column `equity_tr` (1960-01..2026-08): **Fama-French/CRSP broad US equity market total returns, NOT S&P500 or SPX**; row-by-row as recorded. Using this common series avoids SPY inception cutoff.
- `generated/issue-174/nine-sleeve-monthly-returns.csv` column `cash` (1966-03..2026-08): a TB3MS/1200 historical T-bill *proxy*, NOT a live executed ETF/rolled bill. Already revised data, not proven real-time.
- No Deep-History states, GPI/IPI/FCPI, equity returns or historical crisis outcomes used to fit any parameters.

Build a synthetic wealth index of the market total returns, starting at 100 *before* 1960-01, chaining all valid monthly `equity_tr`. Rule evaluated using through month **t** only and applied **t+1**:

1. **BH:** 100% equity, 0% cash.
2. **Cash:** 0% equity, 100% cash.
3. **Fixed50 and Fixed60:** 50%/60% equity with the balance earning cash, constant-mix monthly.
4. **SMA10:** long equity at t+1 iff end-t synthetic total-return wealth index is strictly above its SMA of end-t values in the **10 months t-9..t**, else cash. Strict ties -> cash.
5. **MOM12_excess:** long equity at t+1 iff `product(1+equity_tr[t-11..t]) > product(1+cash[t-11..t])`, else cash. This is **restricted long/cash own-excess momentum**, NOT MOP's futures shorting or vol-scaled paper portfolio. Strict ties -> cash.
6. **Exposure-matched fixed controls:** separate 100% history-informed **descriptive** fixed equity weight equal to the given dynamic strategy's realized FULL-SAMPLE average equity exposure; NOT a deployable ex-ante benchmark. Explicitly mark this lookback use.

First common *trading* month: **1967-03**, after 12 cash observations beginning 1966-03. End month: 2026-08. No dropped months; report count before research results. Overlap with other papers does not establish exact-paper replication.

All backtests assume close-t signal -> return in month t+1, no intra-month trades, target equity weights in [0,1], no leverage or short, cash earns month t+1 proxy return. Monthly target-weight turnover is absolute difference of target equity weights (0->1 costs 2bp of portfolio, not 4bp counting both legs); the initial deployment incurs **no cost** for any strategy, consistently. Base cost **2bp** per 100% equity notional traded, sensitivity **10bp**; include base cost in main returns. Fixed constant-mix controls assume their rebalancing turnover within monthly model is not charged for intra-month drift (limitation).

## Frozen assessment (no parameter optimization)

Metrics: geometric CAGR; annualized sample volatility; Sharpe-like = sqrt(12) × mean(monthly portfolio return minus same-month cash proxy)/sd(monthly portfolio returns); MaxDD; worst 1m; switching count; annualized abs equity-weight turnover; mean equity exposure; percentage equity participation in positive and negative equity months; and gross summed monthly missed-upside vs avoided-loss in equity-up/down months (not a compounding attribution).

Report full-common window; precommitted subperiods: E1 1967-03–1979-12, E2 1980–1999, E3 2000–2019, E4 2020–2026-08. Crisis windows (descriptive, not a separate alpha test): 1973–74, 1987-08..12, 2000-03..2002-10, 2007-10..2009-03, 2020-02..04, 2022.

Precommitted comparison: dynamic vs BH, Fixed50/60, its exposure-matched constant; positive-return/upside tradeoff; cross-era performance; 2 vs 10bp cost stability; no declaration of success by an arbitrary threshold after looking. If strategy fails to dominate exposure-matched fixed over multiple eras, report that plainly.

## Data and execution integrity / limitations

- Verify all 800 equity months and 726 cash months on their **original source windows** are complete, finite, monthly-consecutive, returns > -100%; reconstruct 10-month index with past returns only.
- Code must independently assert signal at t never contains t+1 values; backtest outputs include applied target and signal timing; include tests for synthetic examples, ties, high costs, omitted months, shifted signals.
- This is **revised-vintage research**: French/CRSP revisions, TB3MS proxy timing/settlement and costs are approximate; no contemporaneous PIT certificate, capacity or tax assumption.
- Equity total returns known end-month. TB3MS monthly-average proxy may not be fully available exactly at end-t, so MOM12 cash benchmark at t is a potential *publication-lag concern*. Report it and do not call strict live PIT.
- The formal Moreira-Muir inverse-variance strategy and original MOP multiasset futures TSMOM are OUT OF SCOPE; require daily Fama-French source vintage and a separate, preregistered design. Do not backfill daily vol from monthly returns.
- No threshold search (SMA 9/11, MOM 6/9, lever caps etc.), no entry/exit patch, no macro overlay, no outcome-informed edits, no modification of parent's results.

**Stop condition:** If required source/rules cannot be reproduced accurately, deliver `blocked` with exact reason instead of replacing the series or parameters.
