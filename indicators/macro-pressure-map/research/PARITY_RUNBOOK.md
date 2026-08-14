# Macro Pressure Map V6.6 — Stage-2 Parity Runbook

Issue: #59  
Draft implementation: PR #60

## Goal

Determine whether the frozen Python V6.6 mirror reproduces the **actual frozen TradingView V6.6** when both engines receive the same TradingView source rows.

This is an engineering parity test, not an economic-performance test.

Do not run event studies or tune V6.6 parameters based on public history before this gate is sufficiently established or its limitations are explicitly bounded.

## Frozen target

Use:

- `indicators/macro-pressure-map/src/macro-pressure-map-v6.6.pine`
- default configuration:
  - Market Proxy Timeframe = `D`
  - Use Economic Data = `false`
  - Use Official Financial Conditions Data = `false`
  - Use 5Y Breakeven = `false`
  - Use Industrial Metals in IPI = `false`
  - Use KRE/SPY Stress Add-on = `false`
  - smoothing = on, length 5

Parity compares the three plotted EMA axes because they are directly exposed by the frozen indicator:

- `GPI - Growth Pressure`
- `IPI - Inflation Pressure`
- `FCPI - Financial Conditions Pressure`

The dashboard states still use raw unsmoothed GPI/IPI/FCPI; those are not redefined by this runbook.

## TradingView setup

1. Open an `AMEX:SPY` daily (`1D`) chart.
2. Add the frozen Macro Pressure Map V6.6 with the default settings above.
3. Create a **personal** Pine script from:
   - `research/macro-pressure-map-v6.6-parity-sources.pine`
4. Add the parity helper to the same chart.
5. Keep the helper `Market Proxy Timeframe` at `D`.

The helper requests the same 20 default source series as the V6.6 market-only path.

## Path A — CSV export, when available

The helper declares each TradingView source as a `PARITY SRC ...` plot using `display.data_window`, so those values remain available to chart-data export without drawing 20 visible lines.

Export chart data with both scripts active, then run:

```bash
python compare_tradingview_parity.py \
  --input <tradingview-export.csv> \
  --output parity-report.json
```

The comparator locates:

- the 20 `PARITY SRC ...` columns from the helper; and
- the frozen V6.6 GPI / IPI / FCPI plotted output columns.

Python then recomputes V6.6 from those same TradingView source rows.

### CSV engineering gate

Initial preregistered gate:

- at least 100 comparable rows per axis;
- each plotted axis p99 absolute error <= 0.10 points;
- each plotted axis maximum absolute error <= 0.50 points.

If this fails, investigate implementation semantics before changing any gate or V6.6 parameter.

## Path B — Pine Logs fallback, no chart-data export required

The helper can also consume the original V6.6 plotted outputs via `input.source()` and write complete daily parity rows to Pine Logs.

### Required helper input selection

In the parity helper settings, set:

- `Frozen V6.6 plot: GPI - Growth Pressure` -> the plot from **Macro Pressure Map V6.6** named `GPI - Growth Pressure`;
- `Frozen V6.6 plot: IPI - Inflation Pressure` -> `IPI - Inflation Pressure`;
- `Frozen V6.6 plot: FCPI - Financial Conditions Pressure` -> `FCPI - Financial Conditions Pressure`.

Do **not** leave these three inputs pointing to chart `close`.

### Log history

Default `Pine Logs start year` is 2007. The helper emits one `MPM_PARITY|...` line per confirmed daily bar from that year onward, containing:

- all 20 default TradingView source values; and
- the three original V6.6 plotted EMA axes.

The long history is necessary because V6.6 uses rolling 252-day Z-scores plus 20/63-day momentum. Sparse checkpoint values cannot reconstruct the rolling state.

If the full log history is inconvenient to copy, a later start year may be used, but allow enough warm-up history before interpreting parity rows. Do not compare only isolated checkpoints.

Copy the `MPM_PARITY` log lines to a UTF-8 text file and run:

```bash
python compare_tradingview_parity_logs.py \
  --input <pine-logs.txt> \
  --output parity-logs-report.json
```

### Pine Logs engineering gate

Initial preregistered gate:

- at least 100 comparable rows per axis after rolling warm-up;
- each plotted axis maximum absolute error <= 0.50 points.

The log path uses a simpler max-error gate because it may involve copied/formatted numeric text rather than native CSV precision.

## Failure diagnosis order

If parity fails, do not tune V6.6. Diagnose in this order:

1. Confirm SPY 1D chart and `D` timeframe in both scripts.
2. Confirm the original V6.6 optional paths are all off.
3. For Pine Logs, confirm all three `input.source()` fields point to the original V6.6 plots.
4. Confirm all 20 helper source series are non-`na` over the compared period.
5. Compare the earliest divergence date.
6. Audit rolling semantics:
   - `ta.roc`;
   - `ta.sma`;
   - `ta.stdev` biased/population behavior;
   - `na` handling;
   - EMA initialization.
7. Only after implementation semantics are ruled out should vendor/feed questions be investigated.

## After implementation parity

Once same-TradingView-input parity is acceptable, run the public Yahoo/FRED history builder and compare public-provider inputs against TradingView inputs separately.

That second comparison answers a different question: **feed sensitivity**, not implementation correctness.

Only after both are understood should Issue #59 proceed to historical axis diagnostics, regime transitions, three-axis convergence, and baseline comparison.
