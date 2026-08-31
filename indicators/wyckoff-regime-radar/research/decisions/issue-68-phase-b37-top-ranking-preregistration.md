# Issue #68 Phase B3.7 — TOP Formation / Ranking Audit Preregistration

Status: diagnostic only / frozen C-2 / frozen B3.3 / no performance use.

## Question

When a new directional trend appears visually established but TOP still does not belong to that trend family, is the delay caused primarily by:

1. the target trend family already losing at the **raw-score** layer; or
2. the target trend family winning raw but being demoted by the existing **gates/effective-score** layer?

B3.7 does not define an economic reversal date and does not tune to FR10Y/JGB10Y. Those charts are human-review counterexamples only.

## Symmetric target families

Bull audit:
- target trend family = Stage 2 / Stage 3;
- precursor range = Stage 1;
- opposite range = Stage 4;
- opposite trend family = Stage 5 / Stage 6.

Bear audit mirrors this exactly:
- target trend family = Stage 5 / Stage 6;
- precursor range = Stage 4;
- opposite range = Stage 1;
- opposite trend family = Stage 2 / Stage 3.

## Mechanical decomposition

Using the existing C-2 outputs only:

- six smoothed raw stage scores;
- six existing stage gates;
- six effective scores;
- six sharpened probability weights;
- existing TOP id.

For each direction independently:

- `target_raw = max(raw scores in target trend family)`;
- `other_raw = max(raw scores outside target trend family)`;
- `target_eff = max(effective scores in target trend family)`;
- `other_eff = max(effective scores outside target trend family)`.

On bars where final TOP is **not** in the target trend family:

- `RAW_LAYER_LOSS` if `target_raw <= other_raw`;
- `GATE_LAYER_FLIP` if `target_raw > other_raw` but `target_eff <= other_eff`.

These two categories must exhaust all target-family TOP losses on usable post-warmup bars.

Also record the effective-score winning competitor identity and grouped competitor family:

- precursor range;
- opposite range;
- opposite trend;
- other/neutral residual if any.

No threshold is changed.

## Engineering checks

On the already-burned FX fixtures and reciprocal quotations:

- effective-score argmax must reproduce C-2 TOP identity on usable bars;
- raw-loss vs gate-flip attribution must be exhaustive;
- bull-target results on P must mirror bear-target results on 1/P;
- no strategy-performance metric is permitted.

## TradingView human audit

Generate a direction-selectable Pine audit (default Bull for rates-yield reversals) with horizontal bands:

1. TARGET TOP — green when target trend family is TOP;
2. RAW ADV — green when target trend family wins before gates;
3. PRECURSOR BLOCK — red when precursor-range effective score beats target trend family;
4. OPP RANGE BLOCK — red when opposite-range effective score beats target trend family;
5. OPP TREND BLOCK — red when opposite trend-family effective score beats target trend family;
6. FORMAL — aligned / neutral / opposite;
7. CORE — aligned / neutral / opposite.

Priority human review:

- FR10Y 1D, especially 2021–2024;
- JGB10Y 1D as control.

Interpretation:

- RAW ADV red for long periods -> root cause is upstream raw-stage formulation/ranking;
- RAW ADV green but TARGET TOP red -> gates/effective-score layer demotes the target family;
- blocker bands identify the main competing stage family.

## Hard boundary

No PnL, returns, Sharpe, drawdown, hit rate, transaction costs, sizing, stops, targets, time exits, Strategy Tester optimization, Volume/MTF/Divergence/HMM rescue, or threshold shopping is allowed in B3.7.
