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

The required Issue #64 allocation/contribution diagnostics are generated from the exact daily portfolio evidence using the committed frozen outcome-price snapshot. Asset return contribution is `invested_weight × asset_return`; transaction cost and the cost/return interaction are retained as a separate residual. Regime attribution uses the prior-bar V6.6 regime available to the portfolio on that return row, not the future-known same-day state.

For the full reused history, the V6.6 Reflation strategy's annualized arithmetic contribution is:

- SPY: +5.55 percentage points;
- TLT: +1.54 percentage points;
- GLD: +2.15 percentage points;
- transaction-cost residual: -0.09 percentage points;
- total annualized arithmetic net return: +9.15%.

Within executed Reflation / Inflation Rising rows, realized average allocation is approximately 60.34% SPY / 19.70% TLT / 19.96% GLD. That regime contributes about +2.58 percentage points per year to the strategy's full-history arithmetic net return, versus about +1.71 percentage points for fixed 40/40/20 on the same regime rows. The largest positive regime contribution overall is Slowdown / Disinflation at about +4.04 percentage points per year.

The contribution accounting reconciles to floating-point precision. These diagnostics increase attribution transparency but do not change the Phase B verdict.

## Realized-exposure-matched attribution

The Reflation strategy's realized average invested weights are about 44.38% SPY / 35.57% TLT / 20.05% GLD over the full sample. Its improvement versus 40/40/20 therefore cannot automatically be called timing alpha.

The post-hoc attribution control is deliberately noncausal. For the full sample and for each temporal segment separately, a static monthly-rebalanced target is solved on the realized return path so that the control's **actual average invested weights after drift and rebalance** match the V6.6 strategy's actual average invested weights.

Versus this stricter control, the durable interpretation remains approximately:

- full history: +0.51% CAGR and +0.056 Sharpe;
- 2007–2019: +0.81% CAGR and +0.097 Sharpe;
- post-2019 reused history: only +0.10% CAGR and +0.011 Sharpe, with slightly worse Calmar.

The primary +0.88% CAGR improvement versus 40/40/20 therefore mixes higher average equity exposure with regime timing. After stripping out realized average exposure, timing looks materially stronger in the older development era than in the post-2019 reused sample.

## Episode concentration — exposure-neutral whole-path counterfactual

The episode diagnostic treats a Reflation episode as a complete trading intervention rather than only the dates on which lagged Reflation status is `True`.

Two attribution issues were corrected in sequence:

1. the earlier diagnostic omitted the first following non-Reflation row even though the portfolio performs an event-driven exit rebalance there;
2. the first whole-path counterfactual correctly reran the strategy after disabling the episode, but still compared that lower-equity-exposure leaveout path with the exposure-matched control fitted to the original strategy. That mixed the exposure change caused by disabling the episode with the timing residual.

The final procedure therefore:

1. screens contiguous Reflation episodes using active log contribution **including the first following exit row when present**;
2. selects the largest positive episode within each era;
3. disables that entire Reflation override episode, replacing it with the neutral 40/40/20 target;
4. reruns the portfolio from inception so entry/exit event rebalances, transaction costs, and all subsequent drift are recomputed;
5. for that leaveout path and that evaluation segment, solves a **fresh static monthly-rebalanced control whose realized average invested weights match the leaveout path**;
6. reports leaveout active log return and metric deltas against this freshly re-matched control.

A replay guard first reconstructs the unmodified Phase B strategy and requires its daily net-return path to match the official Phase B daily evidence within `1e-12`. Each leaveout control must also match the counterfactual path's realized average invested weights within `1e-9`.

### Development, 2007–2019

- 49 Reflation episodes;
- 22 positive exit-inclusive timing-contribution episodes;
- normal active log return: +0.0943;
- largest winner: **2010-10-01 through 2011-05-03**;
- exit-inclusive contribution of that episode: +0.04084;
- that episode is 27.6% of gross positive Reflation-episode contribution;
- after fully disabling that episode, rerunning the portfolio, and re-matching the leaveout exposure, cumulative active log return remains **+0.04363**;
- exposure-neutral leaveout result remains positive: **ΔCAGR +0.372%/yr, ΔSharpe +0.0446**;
- leaveout-control maximum realized-weight mismatch: `2.17e-13`.

So the older-era timing evidence is concentrated, but it does **not** depend on one single winner.

### Post-2019 reused exploratory sample

- 31 Reflation episodes;
- 12 positive exit-inclusive timing-contribution episodes;
- normal active log return: only +0.00583;
- largest winner: **2020-11-23 through 2021-05-21**;
- exit-inclusive contribution: +0.05060;
- that episode accounts for **63.8%** of gross positive Reflation-episode contribution;
- after fully disabling it, rerunning the portfolio, and re-matching the lower realized equity exposure, cumulative active log return remains **negative at -0.03793**;
- exposure-neutral leaveout result is **ΔCAGR -0.622%/yr, ΔSharpe -0.0484**;
- leaveout-control maximum realized-weight mismatch: `2.78e-17`.

The exposure re-match reduces the apparent severity versus the prior non-rematched whole-path estimate (`-0.05691` active log, `-0.934%/yr` CAGR delta), confirming that the earlier number mixed in an exposure shift. But the qualitative robustness conclusion survives: the small post-2019 timing benefit is still highly dependent on the 2020–2021 reflation/reopening episode and turns negative once that winner is removed on an exposure-neutral basis.

## Drawdown accounting correction

Portfolio drawdown is explicitly seeded with each evaluated segment's pre-return starting wealth of `1.0`. This prevents a negative first return in a segment from being omitted from the running peak. A focused regression test locks this behavior.

## Decision boundary

Phase B supports a narrower statement than "Macro Pressure Map is a validated production asset allocator":

> The frozen V6.6 Reflation state contains historically useful equity-versus-duration allocation information, especially in pre-2020 data, but its incremental timing value weakens materially after 2019 and is highly episode-concentrated in the recent sample.

Do not retune the Reflation weights or build nine separately optimized portfolio recipes from this result.

Phase C was therefore tested as a separately preregistered Stagflation gold-over-equity override rather than being retroactively folded into Phase B.

## Reproducibility

The exposure-rematched whole-path Phase B evidence was first generated in Actions run `34556394055` from head `dae23540bf32978333184fc3b11b554671e648a9`. The Phase B evidence-generation step itself succeeded; the following durable-contract gate failed because the committed decision still contained the pre-rematch leaveout semantics and values, which is the expected synchronization failure this memo corrects.

The frozen outcome source remains CSV SHA-256 `3a7f590c146f9eda5920b6968fe86c9c3cc1887db35597f2d639a1c76b6e5a57`.

No preregistered Phase B allocation rule, V6.6 formula/threshold, or primary Phase B return result changed. Only the post-hoc robustness attribution was corrected to keep leaveout comparisons exposure-neutral.