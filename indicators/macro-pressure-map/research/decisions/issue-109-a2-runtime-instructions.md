# Issue #109 A2 — TradingView exact trajectory export instructions

Use this only with:

`indicators/macro-pressure-map/research/issue-109-v66-a2-trajectory-export.pine`

## 1. Chart

Open:

- symbol: **SPY**
- timeframe: **1D**

The export needs history back to at least **2007-01-04**.

If the CSV later starts after that date, the acceptance gate will fail and no A2 payoff model will run.

## 2. Add the frozen production V6.6

Add:

`Macro Pressure Map V6.6 [Tiered GPI/IPI/FCPI]`

Use the same frozen/default research configuration.

Critical settings:

- Market Proxy Timeframe = `D`
- Fast Momentum Length = `20`
- Mid Momentum Length = `63`
- Smooth Main Pressure Lines = **ON**
- Pressure Line Smoothing Length = **5**

Do not alter weights, symbols, optional component toggles, macro-data toggles, thresholds, or other V6.6 research settings for this export.

## 3. Add the A2 helper

Paste/add:

`issue-109-v66-a2-trajectory-export.pine`

The helper has two source inputs.

Set:

- **Frozen V6.6 plot: GPI - Growth Pressure**
  → choose the `GPI - Growth Pressure` plot from the production V6.6 indicator.

- **Frozen V6.6 plot: IPI - Inflation Pressure**
  → choose the `IPI - Inflation Pressure` plot from the production V6.6 indicator.

Do not leave either source pointed at SPY close.

The helper's top-right status table should show:

- GPI source: `OK`
- IPI source: `OK`
- Raw axes: `READY`
- Trajectory: `READY`

## 4. Export

Use TradingView:

**Export chart data**

Export the full available SPY 1D history as CSV.

Do not edit the CSV.

Upload the raw exported CSV to ChatGPT.

## 5. Acceptance before payoff research

The CSV will be hash-frozen first.

Then `issue_109_a2_export_validation.py` must pass:

- date uniqueness/order;
- raw-axis reconstruction;
- 20/63 trajectory recomputation;
- 51 frozen #64 GPI/IPI checkpoints;
- exact regime mapping against #64 transition history.

Only after that gate passes may A2 compare:

`M0 = state only`

versus:

`M1 = state + exact GPI/IPI trajectory`

on the already-frozen pairwise asset outcomes.

No production V6.7 Action Layer is authorized by merely exporting the data.
