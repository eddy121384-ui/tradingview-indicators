# Issue #74 — Cash defensive overlay Phase A/B decision

## Verdict

Phase A:

`cash_substitution_has_historical_stagflation_loss_mitigation_value_with_better_recent_episode_robustness_but_pre2020_concentration`

Phase B:

`deep_cash_defense_is_recent_hiking_episode_specific_not_a_stable_all_stagflation_rule`

Overall:

`cash_is_a_credible_defensive_asset_role_but_60pct_cash_requires_stronger_conditioning_than_core_stagflation`

All results are reused/development historical evidence, not untouched OOS confirmation. Macro Pressure Map V6.6 production formulas, weights, lookbacks, thresholds and Pine are unchanged.

## Frozen data and execution

The SPY/TLT/SHV/GSG outcome panel was frozen before Issue #74 PnL in commit `5b407ebf1df7f88b4c3ab720234bf2b587a01027`.

- 4,935 common adjusted-price rows, 2007-01-11 through 2026-08-24
- CSV SHA256 `eba5c4d82c647536a23856e091b874f7a82940d7358bc5235ed066a20ae9566c`
- archive SHA256 `e2a76e4aa6c43f64c9574000723ebf96309f7f129d148b805e26123c11643398`
- portfolio evaluation 2007-01-12 through 2026-08-14, 4,928 rows
- one-bar signal lag
- month-start plus lagged-template-change rebalance
- primary cost 5 bp per 100% one-way turnover, with 0/10 bp sensitivity

## Phase A — Gold to Cash substitution

Stagflation changes from the neutral 40/40/20 SPY/TLT/SHV mix to **20/40/40**. Against the matching Reflation-only baseline, full reused-history Phase A adds about:

- +0.33 pp/year CAGR
- +0.057 Sharpe
- +2.58 pp maximum-drawdown improvement
- +0.053 Calmar

The incremental result is positive in both eras. At 10 bp, the full-history CAGR edge remains positive at about +0.26 pp/year.

Executed Stagflation allocation averages about 19.91% SPY / 39.86% TLT / 40.23% SHV. The overlay reduces historical Stagflation losses; it does not turn Stagflation into an absolute-return engine.

### Reviewed episode robustness

Codex review identified that the earlier concentration helper mixed non-Stagflation residual rows into the total while individual episodes were Stagflation-only. The reviewed episode diagnostic now uses **Stagflation-active rows only** for the total, winner, and leave-largest-winner-out calculation.

Phase A minus Reflation-only:

- full active log return: **+6.3655%**; removing the largest winner leaves **+3.5004%**
- pre-2020: **+1.8568%**; largest 2007-09-17 → 2008-01-17 winner +2.2338%; excluding it gives **-0.3770%**
- post-2019 reused: **+4.5087%**; largest 2021-12-29 → 2022-06-06 winner +2.8651%; excluding it still leaves **+1.6437%**

So the recent Phase A result is not solely a 2021-22 artifact, while the older era remains episode-concentrated.

## Phase B — Deep Cash defense

Phase B changes the Stagflation template from Phase A 20/40/40 to **20 SPY / 20 TLT / 60 SHV**, cutting both equity and duration exposure.

Full reused history versus Phase A:

- +0.06 pp/year CAGR
- +0.022 Sharpe
- +2.49 pp maximum-drawdown improvement
- +0.051 Calmar

But the era split is decisive:

- pre-2020: CAGR -0.25 pp/year, Sharpe -0.023
- post-2019: CAGR +0.66 pp/year, Sharpe +0.084, max-drawdown improvement +4.01 pp

Reviewed Stagflation-active episode totals show the recent edge remains highly concentrated:

- full Phase B minus Phase A active log return: **+1.7420%**; removing 2021-22 leaves **-3.3232%**
- pre-2020: already negative at **-2.5270%**
- post-2019: **+4.2690%**; the 2021-12-29 → 2022-06-06 winner contributes +5.0652%; excluding it leaves **-0.7962%**

At 10 bp, the full-history Phase B-minus-A CAGR edge also becomes slightly negative. The deep-cash rule therefore remains a 2021-22-style tightening-shock result, not a stable default for every core Stagflation regime.

## Same-window Gold vs Cash diagnostic

This remains a post-hoc diagnostic, not a new rule. Each already-frozen overlay is compared with its own matching Reflation-only baseline on identical 2007-01-12 through 2026-08-14 dates.

Full-history marginal effect:

- Gold: +0.24 pp CAGR, +0.020 Sharpe, +2.36 pp max-drawdown improvement
- Cash: +0.33 pp CAGR, +0.057 Sharpe, +2.58 pp max-drawdown improvement

Reviewed Stagflation-active leave-largest-winner-out results:

- Gold pre-2020: +1.4821% active, **-4.6765%** ex largest winner
- Gold post-2019: +3.0849% active, **-0.1856%** ex 2021-22
- Cash pre-2020: +1.8568% active, **-0.3770%** ex largest winner
- Cash post-2019: +4.5087% active, **+1.6437%** ex 2021-22

The corrected diagnostic still supports Cash as the cleaner historical core defensive role, especially post-2019. It does not establish universal superiority over Gold.

## Phase C status

Phase C is no longer blocked. The operator supplied an equivalently exact verified V6.6 raw-IPI reconstruction, the preregistered evidence gate passed, and the frozen rule was executed:

- activation: lagged Stagflation Pressure AND lagged raw IPI >= +60
- severe allocation: 20 SPY / 20 TLT / 40 SHV / 20 GSG
- 74 active outcome rows across 11 episodes

Phase C **failed** versus Phase B: full-history ΔCAGR -0.1362 pp/year, ΔSharpe -0.0228, and maximum drawdown worsened by 0.8831 pp. Zero-cost results remain negative, so the failure is not caused by execution costs.

Durable Phase C details are in `decisions/issue-74-phase-c.md` and `.json`. No threshold, weight, momentum, oil-only, or new-asset rescue is permitted inside Issue #74.

## Review hardening

The current evidence path now locks the Codex findings into code and CI:

- Phase A/B and legacy Gold/Cash episode totals are Stagflation-active only
- both preregistered severe-inflation evidence paths are executable and validated
- Phase C emits preregistered average allocation by regime, asset contribution and regime contribution
- Phase C separates gross allocation effect, transaction-cost residual and net effect
- pull-request CI checks out immutable `github.event.pull_request.head.sha`
- focused regression tests protect the episode scopes and legacy evidence fallback

## Reviewed provenance

Reviewed research code head `5765b2304bf128b74b8bcce902334ee483c8f46c`, pinned workflow run `34077133711` — success.

- Phase A/B artifact `10002497312`, digest `sha256:870bcbd38d4f7fa744e63bb6b42d42ef3d92c0b701118d1d84285ccac19524e1`
- Phase C artifact `10002497479`, digest `sha256:e25c47f42e48215af872662b58159ed387c03db3c17639d6e648d0836abfbf25`
- Gold/Cash artifact `10002497650`, digest `sha256:81b7270f6ee1f6742ed252cd8f4f5a249c54ce89c00791bef97037fac48973d9`

## Decision

- Cash / very-short Treasuries retain the cleaner core defensive role.
- Gold is not required for the historical Stagflation loss-mitigation effect.
- Do not automatically use 60% Cash in every Stagflation regime.
- The preregistered Phase C GSG satellite failed and should not be rescued by tuning.
- Macro Pressure Map V6.6 remains a risk-overlay candidate, not a validated production allocator.
