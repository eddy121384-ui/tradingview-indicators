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

## Public-data research layer

`public_data.py` makes the public-feed approximation explicit instead of hiding symbol substitutions inside analysis code.

The default V6.6 market-only path currently maps:

- ETFs directly through Yahoo (`SPY`, `IWM`, `RSP`, `XLY`, `XLP`, `XLI`, `XLU`, `DBC`, `HYG`, `IEF`);
- TradingView continuous futures to Yahoo research proxies (`HG1! -> HG=F`, `GC1! -> GC=F`, `CL1! -> CL=F`, `RB1! -> RB=F`);
- `TVC:DXY -> DX-Y.NYB`, `CBOE:VIX -> ^VIX`, `TVC:MOVE -> ^MOVE`;
- FRED symbols such as `T10YIE`, `BAMLH0A0HYM2`, and `DFII10` through FRED CSV.

Optional T5YIE, DBB, KRE, official FCI, and macro-confirmation mappings are also declared but remain off under the default parity target.

Every mapping is written into a generated manifest with provider, public symbol, TradingView/Pine symbol, coverage, and feed-risk notes. Public providers are **not** assumed to be TradingView-equivalent.

### Calendar semantics

The first public-data build uses the SPY trading calendar as the daily research anchor. Other series are reindexed to those dates and forward-filled only after their first observation. Values are never backfilled into earlier history.

This is intended to be a closer approximation to a TradingView daily chart than a union calendar, but it remains a Stage-2 parity hypothesis.

### Build a public history bundle

Install research dependencies, then from this folder run for example:

```bash
python build_public_history.py --start 2007-01-01 --output-dir data/public-v6.6
```

The builder emits:

- `v6.6-public-sources.csv` — aligned public input series;
- `v6.6-public-history.csv` — source series plus GPI / IPI / FCPI, plot lines, states, regime, and main FCPI subcomponents;
- `v6.6-public-manifest.json` — mappings, coverage, V6.6 config, calendar rules, and parity warnings.

These outputs are research inputs only. Do not treat them as TradingView parity evidence.

## Important V6.6 semantic detail

The dashboard states and Core Regime use **raw unsmoothed** `GPI`, `IPI`, and `FCPI`. The default EMA(5) is only used for the displayed plot lines. Do not classify regimes from `plot_GPI`, `plot_IPI`, or `plot_FCPI`.

## Tests

From this directory:

```bash
python -m pytest -q test_v6_6_core.py test_public_data.py
```

Current tests cover:

- exact threshold boundary semantics;
- all nine Core Regime cells;
- weighted reallocation when a component is missing;
- bounded end-to-end axis outputs on synthetic data;
- no-lookahead behavior when future rows are appended;
- default versus optional public source selection;
- SPY-anchor calendar alignment;
- forward-fill without pre-history backfill;
- source-manifest mapping and coverage metadata.

## Next step

Stage 1 now has an executable mirror plus a reproducible public-data mapping/build path. The next gate is Stage 2: Pine ↔ Python parity.

The preferred parity design should remove feed mismatch where possible by exporting TradingView source/diagnostic values and feeding the same rows into Python. Public-provider comparisons can then be analyzed separately as a feed-sensitivity question.

Do not interpret historical performance until parity is sufficiently established or its limitations are explicitly bounded.
