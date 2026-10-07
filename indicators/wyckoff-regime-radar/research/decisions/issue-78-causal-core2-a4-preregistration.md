# Issue #78 — A4 causal Core-2 translation preregistration

Date: 2026-10-07 (frozen BEFORE any A4 forward-return outcome is computed)

Scope: convert the surviving Core-2 architecture (A3) from retrospective
full-history within-stock ranks into a strictly causal, live-usable state
definition, on the already-recovered OOS3 snapshot ONLY. OOS4 remains
untouched (`oos4_touched=false`). Discovery, not validation. No policy,
sizing, entry/exit, production, or Pine work.

## Frozen raw axes (reused exactly, never redefined)

- `dir_structure` = frozen A1 definition (`ma_bull − ma_bear`)
- `dir_velocity` = frozen A1 definition (`2·speed_rank − 100`)
- `extension` = `abs(dir_velocity)`

No Supply-Demand. No new factors. No new weights.

## Primary causal percentile (frozen)

For each stock and bar `t`, using ONLY prior ready observations of that
same stock (bars strictly before `t`; the current bar never participates in
its own reference set; no future observation may affect any rank at `t`):

- Reference distribution: EXPANDING prior-ready history.
- Minimum reference history: 252 prior ready observations. With fewer,
  causal Core-2 state at `t` is UNAVAILABLE (no state, no evaluation).
- A bar is evaluable only if it is itself ready AND has ≥252 prior ready bars.
- Empirical percentile with tie averaging (frozen formula, 0–1 scale):

  `pct(t) = (count_strictly_less + 0.5 · count_equal) / N_prior`

  where counts run over the N_prior prior-ready values of that score.
  Rationale: the reference set is prior-only, so the current bar is scored
  against history with ties split evenly; self never enters the set.

No alternative percentile formula will be compared or selected afterward.

## Primary hard cells (causal prior-only ranks, 0–1 scale)

- bull_low: structure ≥ 0.80 AND extension ≤ 0.20 (aligned +1)
- bull_high: structure ≥ 0.80 AND extension ≥ 0.80 (aligned +1)
- bear_low: structure ≤ 0.20 AND extension ≤ 0.20 (aligned −1)
- bear_high: structure ≤ 0.20 AND extension ≥ 0.80 (aligned −1)

## Relaxed robustness (predeclared)

70/30 version of all four cells. Robustness only; never replaces 80/20.

## Horizons, blocks, aggregation (frozen)

- Forward horizons 1/5/10/20 bars, same ATR-normalized forward move; primary
  horizon h10.
- Fixed blocks: 2000–2004 / 2005–2009 / 2010–2014 / 2015–2019 / 2020–2026 /
  ALL. One-stock-one-vote. Min 5 bars per stock-cell, min 30 stocks per
  aggregate (descriptive otherwise). Tail stats p5/p10/ES5/neg/pos-share,
  sleeve/sector where adequate.

## Fidelity diagnostics (descriptive, no gates)

Causal vs retrospective (A3) bins: evaluable-bar coverage after warmup,
per-bar percentile Spearman and MAE, cell counts, per-cell Jaccard,
migration/confusion across {bull_low, bull_high, bear_low, bear_high,
non-core}, one-stock-one-vote, blocks, sleeves. Retrospective bins are NOT
truth; no tuning to maximize agreement.

## A4 decision gates (frozen; no near-pass rescue)

`CORE2_CAUSAL_TRANSLATION_READY_FOR_OOS4` ONLY IF ALL hold:

1. strict prior-only construction passes no-lookahead tests;
2. ≥200 OOS3 stocks have adequate hard-cell h10 evaluation after warmup;
3. h10 ALL mean of the two bull-cell equal-stock means > mean of the two
   bear-cell equal-stock means;
4. bear_high is worst or tied-worst h10 ALL cell (economically or
   statistically: within noise of the minimum);
5. bull-vs-bear qualitative ordering holds in ≥4/5 adequate fixed blocks;
6. relaxed 70/30 does not reverse the primary interpretation;
7. result is not driven only by a tiny stock subset / one sleeve / one
   sector / tails;
8. OOS4 remains untouched.

Otherwise: `CORE2_CAUSAL_TRANSLATION_NOT_READY` (valid implementation, failed
ordering) or `CORE2_CAUSAL_TRANSLATION_INCONCLUSIVE` (insufficient
sample/coverage).

## bull_low vs bull_high classification (frozen rule)

On the preregistered paired low-minus-high h10 evidence only:

- SUPPORTED: ALL mean delta > 0 with positive-stock fraction ≥ 55% AND
  positive in ≥3/5 adequate blocks;
- CONTRADICTED: ALL mean delta < 0 with positive-stock fraction < 45%;
- else NEUTRAL.

Not a trading signal; not required for Core-2 readiness.

Refs #78 #168 #162 #159 #156 #153 #148 #147 #138 #80.
