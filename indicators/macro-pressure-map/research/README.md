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

The initial parity target is the Pine default configuration: market proxy only, official FCI off, T5YIE off, industrial metals off, and KRE add-on off.

## Input contract

`compute_v66()` expects a date-indexed pandas DataFrame whose columns use these canonical names:

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

Missing optional columns are treated as `NaN`. Supplied series are forward-filled on the aligned research calendar to approximate Pine `request.security(..., gaps=barmerge.gaps_off)` behavior. This is a parity hypothesis, not yet a proven fact; if TradingView evidence disagrees, document and fix the semantic mismatch before historical utility analysis.

## Important V6.6 semantic detail

The dashboard states and Core Regime use **raw unsmoothed** `GPI`, `IPI`, and `FCPI`. The default EMA(5) is only used for the displayed plot lines. Do not classify regimes from `plot_GPI`, `plot_IPI`, or `plot_FCPI`.

## Tests

From this directory:

```bash
python -m pytest -q test_v6_6_core.py
```

Initial tests cover:

- exact threshold boundary semantics;
- all nine Core Regime cells;
- weighted reallocation when a component is missing;
- bounded end-to-end axis outputs on synthetic data;
- no-lookahead behavior when future rows are appended.

## Next step

Stage 1 is not complete until a reproducible public-data loader / symbol mapping is added. Stage 2 then requires Pine ↔ Python parity evidence before event studies or regime-performance claims are allowed.

Do not interpret historical performance until parity is sufficiently established or its limitations are explicitly bounded.
