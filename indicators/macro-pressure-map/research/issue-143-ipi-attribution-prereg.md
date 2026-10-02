# Issue #143 Preregistration — Historical IPI Bridge Attribution

Status: **FROZEN BEFORE ANY ISSUE #143 EXACT-IPI ATTRIBUTION METRIC**

Issue: #143  
Draft PR: #144  
Branch: `research/issue-143-ipi-attribution`

This study follows Issue #141's frozen `signal_bridge_failed` result.

It is an attribution study, not a rescue retune.

## Hard firewall

No asset-return outcome may be loaded.

Forbidden:

- SPY/TLT forward returns;
- S&P 500 / Treasury outcomes;
- Equity-minus-Duration spreads;
- Issue #136 payoff tables;
- 1984–2006 historical asset returns.

Permitted targets:

- exact V6.6 GPI/IPI/regime from the frozen Issue #133 monthly snapshot;
- public / structural IPI input series;
- regime and Issue #136 asynchronous-turn timing implied by those signals.

`outcome_data_loaded=false` is a hard result-contract requirement.

## Phase-A source freeze

Source-only workflow run:

`36954294127`

Source code head:

`0c16847c07321648422cbc718a480cc32a1f2236`

No exact V6.6 signal or asset outcome was loaded in that run.

### Frozen normalized public exact-input daily panel

Coverage:

- 5,197 SPY trading-calendar rows;
- 2006-01-03 through 2026-08-31.

Columns:

- SPY anchor;
- T10YIE;
- DBC;
- CL=F;
- RB=F.

Normalized CSV SHA256:

`2ecb4d6693031020cc550bc7ed4de071282dc8ed503ddb131f170ecdaaaa2eba`

DBC begins 2006-02-06; all other frozen panel columns are present from 2006-01-03.

### Frozen structural monthly panel

Coverage:

- 248 monthly rows;
- 2006-01 through 2026-08.

Normalized CSV SHA256:

`d5d2a60e6a343fad7ba0a7a126ce3f7911715c8792ca186a0f3bc65602ac9ead`

This panel contains the frozen Issue #141 World Bank commodity inputs and Cleveland Fed 10Y expected inflation.

### T10YIE provenance bridge

Direct FRED downloads repeatedly timed out in GitHub Actions before any attribution metric was observed.

Therefore T10YIE is sourced from two commit-pinned public mirrors of the FRED CSV:

Old mirror:

- repo: `luizamfsantos/CPI-BER-Time-Series-Analysis`
- commit: `675d17f2e8e5a3ab8ea38e04a75638c41262e250`
- raw SHA256:
  `129fca14e4396e6b638136f94e3ccb0f09d44d9f787a1397e416b42b5476d2d7`
- coverage: 2003-01-02 through 2019-11-04.

New mirror:

- repo: `HermanDp45/AlphaTransfer`
- commit: `bb715c67233881f7697d16f23e6e87a6db4ae021`
- raw SHA256:
  `a35f627e810aa12f579d1d3fc2b872e4cd8b2d0ae6ea3ce98cb758ef357a7429`
- coverage: 2019-01-02 through 2026-09-03.

The two mirrors have 212 overlapping finite observations.

Frozen overlap check:

`max_abs_diff = 0.0`.

Splice rule:

use old mirror before 2019-01-02 and new mirror from 2019-01-02 onward.

This is a public-feed provenance bridge, not a claim of TradingView-feed identity.

## Exact target

Reuse the Issue #133 frozen monthly exact V6.6 snapshot.

Exact normalized CSV SHA256:

`1d03923503e7fe82a69b033897484c48aa646279ecf70164d090ed62a5a70719`

Only:

- date;
- exact GPI;
- exact IPI;
- exact regime id

may be read from that snapshot.

## Frozen score definitions

### Original daily V6.6 score

For D0 use the frozen `v6_6_core.py` semantics:

- zLen = 252;
- fastLen = 20;
- midLen = 63;
- Pine-compatible non-NA rolling windows;
- biased standard deviation `ddof=0`;
- component raw weights 0.5 level / 0.3 momentum / 0.2 direction;
- final `100*tanh(raw/2)`.

IPI weights:

- T10YIE score: 0.35;
- DBC score: 0.40;
- energy score: 0.25;
- energy score = mean(WTI score, RBOB gasoline score).

D0 must be sampled at the final SPY trading observation of each calendar month.

### Frozen monthly score

For all M* variants use Issue #141's frozen translation:

- zLen = 12;
- fastLen = 1;
- midLen = 3;
- rolling standard deviation `ddof=1`;
- component raw weights 0.5 level / 0.3 momentum / 0.2 direction;
- final `100*tanh(raw/2)`.

Monthly exact-public inputs are the final SPY-calendar observation in each completed month.

No affine scaling, lagging, sign flipping, or calibration to exact IPI is permitted.

## Frozen variants

### D0 — public exact-input daily replica

Inputs:

- T10YIE mirror splice;
- DBC Yahoo Close;
- CL=F Yahoo Close;
- RB=F Yahoo Close.

Original daily V6.6 scoring.

Purpose:

bound public-feed / provider mismatch relative to the exact TradingView IPI target.

### M0 — exact-input monthly-score baseline

Same four public exact-input series as D0, sampled to completed month end.

Frozen 12/1/3 monthly score.

Purpose:

D0 -> M0 isolates frequency / score-translation degradation plus month-end compression.

### M-BE — expected-inflation swap only

M0 except:

T10YIE -> Cleveland Fed 10Y expected inflation.

All other inputs unchanged.

### M-COM — broad-commodity swap only

M0 except:

DBC -> Issue #141 frozen World Bank eight-series equal-weight geometric commodity basket:

- WTI;
- US natural gas;
- aluminum;
- copper;
- wheat US HRW;
- maize;
- arabica coffee;
- world sugar.

All other inputs unchanged.

### M-OIL — oil-provider swap only

M0 except:

Yahoo CL=F WTI -> World Bank monthly WTI.

T10YIE, DBC, and RBOB remain unchanged.

### M-GAS — gasoline semantic swap only

M0 except:

RBOB gasoline -> World Bank US natural gas.

T10YIE, DBC, and Yahoo CL=F WTI remain unchanged.

### M-ALL — full Issue #141 IPI source family

Use:

- Cleveland Fed 10Y expected inflation;
- World Bank eight-series commodity basket;
- World Bank WTI;
- World Bank US natural gas.

Frozen 12/1/3 monthly score.

This is the IPI-side reconstruction corresponding to Issue #141.

## Frozen evaluation periods

Development diagnostic:

`2007-01 through 2016-12`.

Primary attribution holdout:

`2017-01 through 2026-08`.

No result from development may alter any source, score, period, or metric.

## Metric implementation

All comparisons are calendar-month aligned.

A month is eligible for a variant only when exact GPI/IPI/regime and that variant's IPI are finite.

### IPI level fidelity

Pearson correlation between variant IPI and exact IPI.

Evaluable with >=12 paired months.

### IPI slope fidelity

One-month exact mathematical sign of IPI change:

- negative = -1;
- exactly zero = 0;
- positive = +1.

Agreement fraction is computed over consecutive calendar months with valid current/prior values on both sides.

Evaluable with >=12 paired slope observations.

### IPI three-state fidelity

Use frozen exact V6.6 thresholds:

- Cooling: IPI < -10;
- Stable: -10 <= IPI <= +10;
- Rising: IPI > +10.

Report exact state agreement fraction.

### Regime fidelity

Pair each variant IPI with **exact GPI** from the Issue #133 snapshot.

This intentionally isolates IPI attribution.

Use the exact 3x3 +/-10 regime grid.

Report:

- exact regime-id agreement;
- R7 precision;
- R7 recall.

Zero precision/recall denominator = unevaluable.

### Trigger fidelity

Pair variant IPI with exact GPI and apply the frozen Issue #136 turning rule to both axes:

- axis turn: dX_t > 0 and dX_(t-1) <= 0;
- both GPI/IPI turns occurred in {t,t-1,t-2};
- current regime = R7;
- first completion only per contiguous R7 episode.

Exact target triggers are recomputed from exact GPI/IPI using the same rule.

One-to-one matching within +/-1 calendar month:

1. sort candidate pairs by absolute month distance;
2. exact month;
3. variant month;
4. greedily take unmatched pairs.

Report precision / recall / F1 / count ratio.

## Attribution validity gate

Before interpreting source-vs-frequency degradation, D0 must establish an adequate public exact-input anchor on the holdout.

D0 anchor is valid only if all are true:

1. >=100 common eligible holdout months;
2. IPI level correlation >=0.90;
3. IPI slope-sign agreement >=0.80;
4. IPI three-state agreement >=0.75;
5. exact 3x3 regime agreement >=0.70;
6. R7 precision >=0.65;
7. R7 recall >=0.65;
8. trigger F1 within +/-1 month >=0.60.

If D0 fails any gate:

formal verdict =
`ipi_attribution_anchor_failed`.

In that case all M* comparisons are descriptive only and no dominant historical proxy cause may be declared.

If D0 passes:

formal verdict =
`ipi_attribution_valid`.

## Frozen degradation accounting

For each fidelity metric where higher is better, define degradation from parent P to child C:

`damage_metric = metric_P - metric_C`.

Negative damage means the child improved that metric and is retained as negative in raw tables, but **attribution damage score clips improvements at zero**.

For each comparison, attribution damage score is the unweighted mean of available:

- max(0, correlation damage);
- max(0, slope-agreement damage);
- max(0, IPI-state-agreement damage);
- max(0, regime-agreement damage);
- max(0, R7-precision damage);
- max(0, R7-recall damage);
- max(0, trigger-F1 damage).

Comparisons:

- frequency_score = D0 -> M0;
- breakeven_score = M0 -> M-BE;
- commodity_score = M0 -> M-COM;
- oil_provider_score = M0 -> M-OIL;
- gasoline_proxy_score = M0 -> M-GAS;
- total_full_proxy_score = M0 -> M-ALL.

These scores are diagnostic bookkeeping, not statistical significance tests.

## Primary-cause labeling

Only when D0 anchor passes:

Let the five atomic damage scores be:

- frequency;
- breakeven;
- commodity;
- oil provider;
- gasoline proxy.

If the largest score is <0.03:

`no_single_material_driver`.

If largest - second_largest <0.03:

`mixed_drivers`.

Otherwise the largest receives one of:

- `frequency_translation_primary`
- `breakeven_proxy_primary`
- `commodity_proxy_primary`
- `oil_provider_primary`
- `gasoline_proxy_primary`.

### Interaction residual

For each raw fidelity metric:

`interaction = total(M0 -> M-ALL) - sum(one-at-a-time source-swap damages excluding frequency)`.

Report this descriptively.

Do not use interaction residual to change the primary-cause label.

## Explicit anti-tuning rules

After the first attribution metrics are observed, do not:

- change source panels;
- change T10YIE splice;
- change D0 daily lengths;
- change monthly 12/1/3 lengths;
- alter IPI weights;
- rescale Cleveland expected inflation;
- change the World Bank commodity basket;
- replace natural gas with another gasoline proxy;
- change WTI provider choice;
- change +/-10 thresholds;
- change holdout;
- change matching tolerance;
- change D0 validity gates;
- change damage-score weights or labeling thresholds.

Any replacement proxy or redesign requires a new issue.

## Historical outcome boundary

Issue #143 may not authorize 1984–2006 asset-outcome testing.

Even if attribution is valid, any redesigned IPI must undergo a new preregistered signal bridge and pass that bridge before historical outcomes may be joined.

`production_authorized=false`.
