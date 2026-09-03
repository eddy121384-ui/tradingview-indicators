# Issue #74 — Cash defensive overlay Phase A/B checkpoint

## Verdict

Phase A:

`cash_substitution_has_historical_stagflation_loss_mitigation_value_with_better_recent_episode_robustness_but_pre2020_concentration`

Phase B:

`deep_cash_defense_is_recent_hiking_episode_specific_not_a_stable_all_stagflation_rule`

Overall:

`cash_is_a_credible_defensive_asset_role_but_60pct_cash_requires_stronger_conditioning_than_core_stagflation`

All results are reused/development historical evidence. They are not untouched OOS confirmation and do not validate a production allocator.

## Frozen boundary

The Issue #74 hypothesis ladder was committed before Issue #74 portfolio PnL was viewed. V6.6 formulas, component weights, lookbacks, thresholds, 3x3 regime semantics, FCPI role, and production Pine remain unchanged. No optimizer, threshold search, allocation-weight sweep, commodity momentum filter, or rescue asset was used.

The outcome panel was frozen **before** portfolio evaluation by Actions into commit `5b407ebf1df7f88b4c3ab720234bf2b587a01027`:

- SPY / TLT / SHV / GSG;
- 4,935 common adjusted-price rows;
- 2007-01-11 through 2026-08-24;
- CSV SHA-256 `eba5c4d82c647536a23856e091b874f7a82940d7358bc5235ed066a20ae9566c`;
- gzip/archive SHA-256 `e2a76e4aa6c43f64c9574000723ebf96309f7f129d148b805e26123c11643398`.

The portfolio comparison window is 2007-01-12 through 2026-08-14, 4,928 rows. Primary cost is 5 bp per 100% one-way turnover with 0/10 bp sensitivity.

## Phase A — Gold -> Cash substitution

Preregistered SPY/TLT/SHV templates:

- Neutral: 40/40/20;
- Reflation: 60/20/20;
- Stagflation cash substitution: 20/40/40.

Against the same-universe Reflation-only baseline, the Phase A Stagflation cash overlay improves full reused-history results:

- CAGR: +0.33 percentage points per year;
- Sharpe: +0.057;
- maximum drawdown: +2.58 percentage points;
- Calmar: +0.053.

The incremental result is positive in both era slices:

- pre-2020: +0.14 pp CAGR, +0.031 Sharpe;
- post-2019 reused exploratory history: +0.70 pp CAGR, +0.087 Sharpe and +2.58 pp max-drawdown improvement.

At 10 bp costs, the full-history Phase A CAGR edge remains positive at about +0.26 pp/year.

### What Phase A is actually doing

Executed Stagflation rows realize approximately 19.91% SPY / 39.86% TLT / 40.23% SHV. Stagflation remains a negative absolute contributor after 2019; the overlay is a damage-reduction mechanism, not a Stagflation profit engine.

Across the full sample, Stagflation rows contribute about -0.71 pp/year under the Reflation-only strategy and about -0.40 pp/year under Phase A. Thus the cash substitution reduces the historical loss burden by roughly +0.31 pp/year.

### Episode robustness

Phase A still has an older-era concentration problem. In 2007-2019 its largest winning Stagflation episode is 2007-09-17 through 2008-01-17; removing that episode turns the active log return slightly negative.

The post-2019 result is materially more robust. The largest winning episode is 2021-12-29 through 2022-06-06, but removing that entire episode leaves active log return **positive** at about +0.01463. Therefore the recent cash-substitution result is not solely a 2021-22 artifact.

## Phase B — Deep cash defense

Preregistered Stagflation template changes from Phase A 20/40/40 to **20 SPY / 20 TLT / 60 SHV**, explicitly reducing both equity and duration risk.

Full reused history versus Phase A:

- CAGR: +0.06 pp/year;
- Sharpe: +0.022;
- maximum drawdown: +2.49 pp;
- Calmar: +0.051.

But the era split is the critical result:

### 2007-2019

Phase B is worse than Phase A on return and risk-adjusted return:

- CAGR: -0.25 pp/year;
- Sharpe: -0.023;
- Calmar: -0.006;
- only a small +0.31 pp max-drawdown improvement remains.

### Post-2019 reused history

Phase B is much better than Phase A:

- CAGR: +0.66 pp/year;
- Sharpe: +0.084;
- maximum drawdown: +4.01 pp;
- Calmar: +0.112.

That attractive recent result is **not robust across Stagflation episodes**. The 2021-12-29 through 2022-06-06 episode contributes about +0.05065 active log return; after removing it, Phase B minus Phase A turns negative at about -0.01024. Full-history Phase B minus Phase A also flips negative after removing this single winner.

This makes the mechanism economically intuitive but narrow: cutting long duration aggressively was highly valuable in a 2021-22-style inflation / tightening shock, but the data do not support making 60% cash the default response to every V6.6 core Stagflation state.

Cost sensitivity tells the same story. At 10 bp costs, Phase B minus Phase A full-history CAGR becomes slightly negative (about -0.01 pp/year), although Sharpe and drawdown remain better. Annualized turnover is about 4.43x for Phase B versus 3.09x for Phase A and 1.74x for the Reflation-only baseline.

## Same-window Gold vs Cash diagnostic

After the preregistered Phase A/B result was known, a **post-hoc diagnostic** compared the already-frozen Issue #64 Gold Stagflation overlay with the Issue #74 Cash Stagflation overlay on the exact same 2007-01-12 through 2026-08-14 dates. This comparison does not create a new rule and cannot establish universal asset superiority.

Each overlay is measured against its own matching Reflation-only baseline.

Full-history marginal Stagflation effect:

- Gold: +0.24 pp CAGR, +0.020 Sharpe, +2.36 pp max-drawdown improvement, +0.047 Calmar;
- Cash: +0.33 pp CAGR, +0.057 Sharpe, +2.58 pp max-drawdown improvement, +0.053 Calmar.

So Cash exceeds Gold by about +0.09 pp incremental CAGR and +0.036 Sharpe on the identical window.

The more important difference is recent episode robustness:

- Gold pre-2020: removing the largest winner flips the active result negative;
- Gold post-2019: removing 2021-22 also flips negative;
- Cash pre-2020: removing the largest winner flips negative;
- **Cash post-2019: removing 2021-22 still leaves +0.01463 active log return.**

This supports Cash as a credible core defensive role and rejects the assumption that Gold is required for the historical Stagflation loss-mitigation effect. It does **not** imply Gold has no useful satellite or portfolio role.

## Accounting audit

Portfolio asset contribution, regime contribution, transaction-cost residual and exact daily reconciliation were generated from the frozen price snapshot. Maximum reconciliation error is approximately `3.47e-18`.

## Phase C remains blocked, deliberately

The preregistered Phase C question is whether the existing V6.6 **severe inflation** state can justify a conditional 20% GSG commodity sleeve while retaining Cash as the defensive core.

The required condition is lagged Stagflation Pressure **and lagged raw IPI >= +60**, where +60 is the already-existing V6.6 `inflationExtremeThreshold`.

Issue #64 committed the full 3x3 core regime transition history but did not commit every historical raw IPI value required to reconstruct `IPI >= +60` exactly. Therefore Phase C currently fails closed. No Phase C portfolio PnL has been calculated.

The expected prior TradingView Pine parity log SHA-256 is `c0220d4974b2fd0154c4cf8f33b4b3effb27a58e21ee96a1b0109011ce638e3d`. Phase C should proceed only when that exact evidence is recovered or an equivalently exact verified reconstruction is established. Do not substitute mutable network reconstruction merely to obtain a result.

## Provenance

Primary evidence workflow: Actions run `33708354990`, source code head `be3a687fb80f28a0cb4d09e88c2fc027617b706d`, conclusion `success`.

Phase A/B artifact: `9876055030`, digest `sha256:ce44a90523cff50ec9586724dcae9814a94a09d86b82788648e317d5c762aa95`.

Same-window Gold/Cash diagnostic artifact: `9876055349`, digest `sha256:44189ade884cbba297b120435e10d07aa435de3f81b24b9134c9c0947cb75489`.

## Decision

- Do not call V6.6 a validated production allocator.
- Gold is **not required** to obtain the historical Stagflation defensive effect.
- Cash/very-short Treasury exposure is supported as a cleaner core defensive asset role.
- Do **not** automatically use 60% Cash in every Stagflation regime; that deeper duration cut is strongly tied to the 2021-22 hiking shock and is cost-sensitive.
- Keep Phase C preregistered: broad commodities remain a conditional inflation satellite candidate, not a default core holding.
- Do not tune V6.6 thresholds, portfolio weights or add a momentum filter to rescue Phase C.
