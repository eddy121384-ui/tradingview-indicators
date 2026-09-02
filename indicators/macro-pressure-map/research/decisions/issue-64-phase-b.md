# Issue #64 Phase B — Reflation allocation override

## Interim verdict

**`reflation_override_adds_historical_portfolio_value_but_recent_timing_is_weak_and_episode_concentrated`**

The preregistered Phase B rule was frozen before portfolio results were viewed:

- default: SPY / TLT / GLD = 40 / 40 / 20;
- Reflation / Inflation Rising: 60 / 20 / 20;
- one-trading-row execution lag;
- monthly rebalance plus event-driven rebalance when the lagged template changes;
- primary transaction cost: 5 bp per one-way turnover;
- no weight sweep, no per-regime optimizer, no Stagflation rule in the primary test.

All evidence remains reused/development historical evidence. It is not untouched OOS confirmation.

## Primary result versus the same neutral allocation

On the common 2007-04-05 through 2026-08-14 window:

- V6.6 Reflation override: CAGR 9.06%, Sharpe 0.942, max drawdown -25.43%, Calmar 0.356;
- fixed 40/40/20: CAGR 8.18%, Sharpe 0.875, max drawdown -25.43%, Calmar 0.322.

Incremental result:

- CAGR: +0.88% per year;
- Sharpe: +0.067;
- Calmar: +0.035;
- drawdown: essentially unchanged.

The advantage survives the preregistered 10 bp cost sensitivity. However, the strategy trades much more: annualized turnover is about 1.78 versus 0.16 for fixed neutral.

A causal 63-day inverse-volatility benchmark is stronger on risk-adjusted metrics: CAGR 9.06%, Sharpe 0.985, max drawdown -22.46%, Calmar 0.403. Phase B therefore does not establish V6.6 as the best allocator among simple alternatives.

## Portfolio contribution audit

The required Issue #64 allocation/contribution diagnostics are now generated from the exact daily portfolio evidence using the committed frozen outcome-price snapshot. Asset return contribution is `invested_weight × asset_return`; transaction cost and the cost/return interaction are retained as a separate residual. Regime attribution uses the prior-bar V6.6 regime available to the portfolio on that return row, not the future-known same-day state.

For the full reused history, the V6.6 Reflation strategy's annualized arithmetic contribution is:

- SPY: +5.55 percentage points;
- TLT: +1.54 percentage points;
- GLD: +2.15 percentage points;
- transaction-cost residual: -0.09 percentage points;
- total annualized arithmetic net return: +9.15%.

Within executed Reflation / Inflation Rising rows, realized average allocation is approximately 60.34% SPY / 19.70% TLT / 19.96% GLD. That regime contributes about +2.58 percentage points per year to the strategy's full-history arithmetic net return, versus about +1.71 percentage points for fixed 40/40/20 on the same regime rows. The largest positive regime contribution overall is Slowdown / Disinflation at about +4.04 percentage points per year.

The contribution accounting reconciles exactly up to floating-point precision: maximum absolute asset-plus-cost reconciliation error and regime reconciliation error are both `2.78e-17` across the full/pre-2020/post-2019 segments and all Phase B comparison strategies.

These diagnostics increase attribution transparency but do not change the Phase B verdict. They show that the historical Reflation advantage is genuinely concentrated in the intended Reflation rows, while the separate exposure-matched and episode tests still limit how strongly that historical advantage can be generalized.

## Realized-exposure-matched attribution

The Reflation strategy's realized average invested weights are about 44.38% SPY / 35.57% TLT / 20.05% GLD over the full sample. Its improvement versus 40/40/20 therefore cannot automatically be called timing alpha.

The post-hoc attribution control is deliberately noncausal. For the full sample and for each temporal segment separately, a static monthly-rebalanced target is solved on the realized return path so that the control's **actual average invested weights after drift and rebalance** match the V6.6 strategy's actual average invested weights. This addresses the review concern that matching only average target templates could leave residual exposure bias.

The realized-weight mismatch is effectively zero:

- full history max absolute mismatch: `2.50e-16`;
- 2007–2019: `2.54e-13`;
- post-2019: `8.33e-17`.

Versus this stricter control:

- full history: +0.51% CAGR, +0.056 Sharpe, +0.012 Calmar;
- 2007–2019: +0.81% CAGR, +0.097 Sharpe, +0.090 Calmar;
- post-2019 reused history: only +0.10% CAGR, +0.011 Sharpe, while Calmar is -0.003 lower.

This means the primary +0.88% CAGR improvement versus 40/40/20 mixes two effects: higher average equity exposure and regime timing. After stripping out realized average exposure, timing still looks material in the older development era but is economically very small in the post-2019 reused sample.

## Episode concentration

To check whether the residual timing result is merely one lucky macro episode, active log return versus the era-piecewise realized-exposure-matched control was decomposed by contiguous Reflation episodes.

### Development, 2007–2019

- 49 Reflation episodes;
- 24 positive timing-contribution episodes;
- total active log return: +0.0943;
- largest winner: 2010-10-01 through 2011-05-03, contribution +0.0405;
- that episode is 27.1% of gross positive Reflation-episode contribution;
- after removing that largest winner, cumulative active log return remains +0.0538.

The old-era result is concentrated, but not dependent on one single episode.

### Post-2019 reused exploratory sample

- 31 Reflation episodes;
- 12 positive timing-contribution episodes;
- total active log return: only +0.0058;
- largest winner: 2020-11-23 through 2021-05-21, contribution +0.0509;
- that single episode is 61.2% of gross positive Reflation-episode contribution;
- after removing it, cumulative active log return falls to -0.0450.

Therefore the recent-history timing case is not robust. The small post-2019 net benefit is heavily dependent on the 2020–2021 reflation/reopening episode.

## Drawdown accounting correction

Portfolio drawdown is now explicitly seeded with each evaluated segment's pre-return starting wealth of `1.0`. This prevents a negative first return in a segment from being omitted from the running peak. A focused regression test locks this behavior. The correction does not change CAGR, Sharpe, regime timing, exposure matching, or episode attribution, and it does not change the full-history primary max-drawdown / Calmar conclusion.

## Decision boundary

Phase B supports a narrower statement than "Macro Pressure Map is a validated production asset allocator":

> The frozen V6.6 Reflation state contains historically useful equity-versus-duration allocation information, especially in pre-2020 data, but its incremental timing value weakens materially after 2019 and is highly episode-concentrated in the recent sample.

Do not retune the Reflation weights or build nine separately optimized portfolio recipes from this result.

Phase C was therefore tested as a separately preregistered Stagflation gold-over-equity override rather than being retroactively folded into Phase B.

## Reproducibility

Contribution-audit source workflow: `33492086706` on code head `51a9998ac0b370bdda8e2ccb5dc6e0e5e79e8b0e`, conclusion `success`.

Phase B artifact: `9794325559`, digest `sha256:cd381e633323c620f1c5c51bebe823711199212f7f166eea2bcfe6610f839712`.

The artifact contains `phase-b-asset-contribution.csv`, `phase-b-regime-allocation-contribution.csv`, `phase-b-contribution-reconciliation.csv`, and `phase-b-contribution-manifest.json` in addition to the existing Phase B evidence. The contribution manifest confirms `committed_frozen_snapshot`, frozen CSV SHA-256 `3a7f590c146f9eda5920b6968fe86c9c3cc1887db35597f2d639a1c76b6e5a57`, and maximum reconciliation error `2.78e-17`.
