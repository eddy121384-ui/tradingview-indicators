# Macro Pressure Map V6.6 Research

This folder implements Issue #59: validation of the frozen Macro Pressure Map V6.6 before any V6.7 redesign.

## Research rule

`macro-pressure-map-v6.6.pine` is the behavioral source of truth. During Issue #59, do not change component definitions, weights, thresholds, lookbacks, or regime rules in response to observed historical results.

The Python code here is a research mirror, not a replacement for the TradingView indicator.

## Current scope

`v6_6_core.py` mirrors:

- `f_componentScore()` level / momentum / direction construction;
- population-standard-deviation Z-scores (`ta.stdev` default biased behavior);
- GPI market and optional macro-confirmation paths;
- IPI market and optional macro-confirmation paths;
- FCPI market and optional official-FCI paths;
- optional T5YIE, industrial-metals, and KRE switches;
- V6.6 default weights and thresholds;
- GPI / IPI / FCPI five-state classification;
- 3x3 Core Regime classification;
- Risk Note and Risk Posture logic;
- display-only EMA lines separately from raw regime axes.

The parity target is the Pine default configuration: market proxy only, official FCI off, T5YIE off, industrial metals off, and KRE add-on off.

## Input contract

`compute_v66()` expects a date-indexed pandas DataFrame whose columns use these canonical names.

### GPI market

`spy`, `iwm`, `rsp`, `xly`, `xlp`, `xli`, `xlu`, `copper`, `gold`

### IPI market

`breakeven_10y`, `breakeven_5y`, `oil`, `gasoline`, `commodity_basket`, `industrial_metals`

### FCPI market

`dxy`, `vix`, `move`, `hyg`, `ief`, `kre`, `hy_oas`, `real_yield`

### Optional official FCI

`nfci`, `stlfsi`

### Optional macro confirmation

`pmi`, `cfnai`, `building_permits`, `initial_claims`, `unemployment`, `cpi`, `core_cpi`, `pce`, `core_pce`, `ppi`, `wage`

Missing optional columns are treated as `NaN`. Supplied series are forward-filled on the aligned research calendar to approximate Pine `request.security(..., gaps=barmerge.gaps_off)` behavior.

## Public-data research layer

`public_data.py` makes the public-feed approximation explicit instead of hiding symbol substitutions inside analysis code.

The default V6.6 market-only path maps:

- ETFs directly through Yahoo (`SPY`, `IWM`, `RSP`, `XLY`, `XLP`, `XLI`, `XLU`, `DBC`, `HYG`, `IEF`);
- TradingView continuous futures to Yahoo research proxies (`HG1! -> HG=F`, `GC1! -> GC=F`, `CL1! -> CL=F`, `RB1! -> RB=F`);
- `TVC:DXY -> DX-Y.NYB`, `CBOE:VIX -> ^VIX`, `TVC:MOVE -> ^MOVE`;
- FRED symbols such as `T10YIE`, `BAMLH0A0HYM2`, and `DFII10` through FRED CSV.

Optional T5YIE, DBB, KRE, official FCI, and macro-confirmation mappings are declared but remain off under the default parity target.

Every mapping is written into a generated manifest with provider, public symbol, TradingView/Pine symbol, coverage, and feed-risk notes. Public providers are **not** assumed to be TradingView-equivalent.

### Calendar semantics

The public-data build uses the SPY trading calendar as the daily research anchor. Source observations dated on weekends / anchor holidays are preserved on a union calendar before forward-filling, then projected onto SPY trading dates. Values are never backfilled before their first observation.

### Build a public history bundle

Install research dependencies, then from this folder run for example:

```bash
python build_public_history.py --start 2007-01-01 --output-dir data/public-v6.6
```

The builder emits source history, calculated V6.6 history, and a manifest. These outputs are research inputs only and are not TradingView parity evidence.

## Important V6.6 semantic detail

The dashboard states and Core Regime use **raw unsmoothed** `GPI`, `IPI`, and `FCPI`. The default EMA(5) is only used for displayed plot lines. Do not classify regimes from `plot_GPI`, `plot_IPI`, or `plot_FCPI`.

## Validation tooling

The research folder now includes:

- Pine ↔ Python parity helpers / comparators;
- first historical axis / regime diagnostics;
- out-of-component baseline comparisons;
- non-overlapping joint-event analysis;
- `matched_incremental_validation.py`, which tests second-axis confirmation inside one fixed anchor-event universe rather than comparing unrelated event samples.

## Tests

From this directory:

```bash
python -m pytest -q \
  test_v6_6_core.py \
  test_public_data.py \
  test_incremental_validation.py \
  test_joint_holdout_validation.py \
  test_matched_incremental_validation.py
```

Coverage includes:

- threshold / Core Regime semantics;
- Pine-compatible rolling / missing-value behavior;
- public-data calendar causality;
- horizon-length event embargoes;
- training-tail purge before forward-outcome evaluation;
- matched nested confirmation-lift calculation.

## Final Issue #59 result

Final verdict:

**`descriptive_but_little_incremental_information`**

The research established engineering-valid V6.6 parity and coherent macro-state compression, but after circularity controls, non-overlapping events, leakage repair, holdout-status audit, and a matched conditional test, it did **not** establish robust standalone or joint incremental predictive value.

Durable evidence:

- `decisions/issue-59-final-verdict.md`
- `decisions/issue-59-tradingview-parity.md`
- `decisions/issue-59-ooc-incremental.md`
- `decisions/issue-59-joint-holdout.md` (historical filename; interpretation downgraded to exploratory)
- `decisions/issue-59-matched-incremental.md`

## Next step

Do not optimize V6.6 on the already-inspected Issue #59 sample.

If predictive value is still a goal, freeze the GPI+IPI confirmation hypothesis now and evaluate it prospectively only on genuinely unseen future observations after the current evidence cutoff.

A separate V6.7 may improve UI / interpretation — for example clearer transition velocity and risk context — but such a redesign should not be described as predictive improvement without fresh OOS evidence.
