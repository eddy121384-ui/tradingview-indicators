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

## Exposure-matched attribution

The Reflation strategy's realized average weights are roughly 44.4% SPY / 35.6% TLT / 20.0% GLD, so its improvement versus 40/40/20 cannot automatically be called timing alpha.

A post-hoc, noncausal exposure-matched diagnostic holds approximately the same average equity/duration mix without using regime timing.

Versus that control:

- full history: +0.51% CAGR, +0.056 Sharpe;
- 2007–2019: +0.80% CAGR, +0.098 Sharpe, +0.091 Calmar;
- 2020–2026: only +0.08% CAGR, +0.010 Sharpe, and Calmar is slightly worse.

This means the primary +0.88% CAGR improvement versus 40/40/20 mixes two effects: higher average equity exposure and regime timing. Timing itself looks meaningful in the older development era, but very weak in the post-2019 reused sample.

## Episode concentration

To check whether the timing result is merely one lucky macro episode, active log return versus the era-frequency exposure-matched control was decomposed by contiguous Reflation episodes.

### Development, 2007–2019

- 49 Reflation episodes;
- 24 positive timing-contribution episodes;
- total active log return: +0.0942;
- largest winner: 2010-10-01 through 2011-05-03, contribution +0.0403;
- that episode is 27.1% of gross positive Reflation-episode contribution;
- after removing that largest winner, cumulative active log return remains +0.0539.

The old-era result is concentrated, but not dependent on one single episode.

### Post-2019 reused exploratory sample

- 31 Reflation episodes;
- 12 positive timing-contribution episodes;
- total active log return: only +0.0050;
- largest winner: 2020-11-23 through 2021-05-21, contribution +0.0506;
- that single episode is 61.2% of gross positive Reflation-episode contribution;
- after removing it, cumulative active log return falls to -0.0456.

Therefore the recent-history timing case is not robust. The small post-2019 net benefit is heavily dependent on the 2020–2021 reflation/reopening episode.

## Decision boundary

Phase B supports a narrower statement than "Macro Pressure Map is a validated production asset allocator":

> The frozen V6.6 Reflation state contains historically useful equity-versus-duration allocation information, especially in pre-2020 data, but the incremental timing value weakens materially after 2019 and is highly episode-concentrated in the recent sample.

Do not retune the Reflation weights or build nine separately optimized portfolio recipes from this result.

If Issue #64 continues, the next clean experiment should be a **separately preregistered Stagflation gold-over-equity override**, because that is a different Phase A hypothesis. It must be evaluated incrementally and must not be retroactively folded into the Reflation primary test to rescue it.

## Reproducibility

Latest verified workflow: `32702615312` on head `1b87cc3dac7ad0dd2cb80d6e8554ba5b030a6164`.

Phase B artifact: `9511106011`, digest `sha256:92d8bcd03663597419e861b6ff147c9d5b9191693a0598db3ddd9101b1e4e2b2`.

The workflow completed tests, Phase A evidence, Phase B primary evidence, exposure-matched attribution, episode concentration diagnostics, strict JSON validation and artifact upload successfully.
