# Issue #59 — Out-of-component validation runbook

Purpose: test whether frozen Macro Pressure Map V6.6 adds information beyond simple baselines using outcomes that are **not** direct default-path V6.6 inputs.

## What this helper logs

`macro-pressure-map-v6.6-ooc-outcomes.pine` logs:

- `TVC:US10Y` — 10Y nominal Treasury yield market feed
- `TVC:US02Y` — 2Y nominal Treasury yield market feed
- `FRED:DGS10` — official 10Y constant-maturity Treasury yield sensitivity check
- `FRED:DGS2` — official 2Y constant-maturity Treasury yield sensitivity check
- `FX_IDC:USDJPY`
- `FX_IDC:EURUSD`
- `CBOT:ZN1!` — 10Y Treasury futures continuous contract
- `NASDAQ:TLT` — long-duration Treasury ETF

These are research outcomes only. None is added to production V6.6.

## TradingView steps

1. Open **SPY / 1D**.
2. Add the frozen production script:
   `indicators/macro-pressure-map/src/macro-pressure-map-v6.6.pine`
3. Add the helper:
   `indicators/macro-pressure-map/research/macro-pressure-map-v6.6-ooc-outcomes.pine`
4. Open the helper settings / Inputs.
5. Set the three source fields to the frozen V6.6 plots:
   - `Frozen V6.6 plot: GPI - Growth Pressure` -> `MPM V6.6: GPI - Growth Pressure`
   - `Frozen V6.6 plot: IPI - Inflation Pressure` -> `MPM V6.6: IPI - Inflation Pressure`
   - `Frozen V6.6 plot: FCPI - Financial Conditions Pressure` -> `MPM V6.6: FCPI - Financial Conditions Pressure`
6. Leave `Outcome timeframe = D` and `Pine Logs start year = 2007`.
7. Open **Pine Logs** for `MPM V6.6 OOC`.
8. Export the Pine Logs CSV and supply it together with the already captured `MPM_PARITY` log.

The helper panel itself can appear visually blank. Its job is to emit `MPM_OOC|...` rows, not to draw a chart.

## Expected log shape

Each confirmed daily bar should contain a row beginning with:

`MPM_OOC|date=...`

and fields including:

`us10y_tvc`, `us02y_tvc`, `dgs10_fred`, `dgs2_fred`, `usdjpy`, `eurusd`, `zn1`, `tlt`.

If one optional TradingView symbol is unavailable to the account, `ignore_invalid_symbol=true` keeps the helper running; that field can remain `na`. The study can still proceed with the available out-of-component outcomes.

## Mechanical research command

From `indicators/macro-pressure-map/research`:

```bash
python incremental_validation.py \
  --parity-log /path/to/pine-logs-MPM-V6.6-PARITY-SRC.csv \
  --ooc-log /path/to/pine-logs-MPM-V6.6-OOC.csv \
  --output-json decisions/issue-59-ooc-incremental.json \
  --output-md decisions/issue-59-ooc-incremental.md
```

## Frozen comparisons

Axis signal: trailing 20-trading-day change.

Simple baselines:

- GPI vs Copper/Gold 20-day momentum
- IPI vs 10Y breakeven 20-day change
- FCPI vs HY OAS 20-day change
- FCPI sensitivity baseline: VIX 20-day change

Outcomes are evaluated over 5, 20, and 60 trading days.

The primary 20-day study reports both:

1. all qualifying daily rows; and
2. **entry events only** — the first day entering the top/bottom 20% bucket — to reduce duplicated evidence from persistent multi-day regimes.

The 20/80% research buckets are descriptive only. They are not proposed V6.7 thresholds and may not be tuned during Issue #59.

## Decision rule

A composite earns incremental-value credit only when its separation is repeatedly stronger than the simple baseline on out-of-component outcomes and remains reasonably directionally coherent across 2008–2012, 2013–2019, and 2020–2026.

Failure to beat the baseline does not automatically mean an axis is useless; it means the composite has not justified its extra complexity for that use case.
