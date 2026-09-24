# Issue #78 — Python Classifier Parity Pine Logs Checklist

## Purpose

TradingView chart-data export is not required.

This checklist uses **Pine Logs** to provide the exact TradingView OHLCV and frozen classifier outputs needed for Pine ↔ Python parity.

This is engineering parity only. Do not inspect R0 / Warning-First economics on calibration stocks.

Formal OOS2 remains behind this gate.

---

## Build

Branch:

`research/issue-78-trend-capture-frontier`

Use this Pine file:

`indicators/wyckoff-regime-radar/research/generated/wyckoff-issue78-python-parity-log.pine`

Indicator short title remains:

`#78 PY PARITY`

The logger emits records beginning with:

`I78P1|`

Default capture window:

`2500` daily bars.

This is deliberately longer than the classifier warm-up so Python can rebuild the rolling state from the exact same OHLCV rows and still leave a large post-warm-up comparison window.

---

## Calibration order

1. `NASDAQ:AAPL`
2. `NYSE:JPM`
3. `NYSE:XOM`

These three symbols are engineering fixtures only and are excluded from formal OOS2 economics.

Start with AAPL.

---

## TradingView settings

- symbol: `NASDAQ:AAPL`
- timeframe: **1D**
- use the generated parity-log Pine above;
- leave classifier inputs at frozen defaults;
- Representation Mode: **Auto**;
- Volume Mode: **Auto**;
- MTF Mode: **Observe Only**;
- Divergence Mode: **Observe Only**;
- Witness Stage Bias Mode: **Balanced**;
- `Enable parity Pine Logs`: ON;
- `Parity log capture bars`: leave at **2500**.

The build keeps `calc_bars_count=10000` and removes the lower-timeframe arrays that are inert under the frozen Observe-Only MTF mode.

---

## What to send back

Open Pine Logs after the script finishes and save / download / copy the log output in whatever form TradingView allows.

The usable rows start with:

`I78P1|`

You do **not** need to clean the file.

A TradingView Pine-Logs CSV containing timestamp + message is fine.

Upload it unchanged.

The parser tolerates surrounding TradingView log text and extracts only `I78P1|` records.

---

## Logged payload

Each record contains the exact chart:

- ticker / timeframe / timestamp;
- open / high / low / close / volume;

plus:

- Price-Log routing flag;
- formalId;
- symATR;
- volume quality / weight;
- volume absorption / distribution / breakout / breakdown;
- six stage gates;
- six stage probabilities / weights;
- topId / topGap;
- evidence;
- candidateDisplayId;
- stale-pressure bars / reason.

No policy PnL is logged.

---

## Runtime acceptance

The uploaded Pine Logs are parsed and the exact TradingView OHLCV rows are replayed through Python.

Hard gate:

- formalId agreement >= **99.99%** on the common post-warm-up window;
- fresh Markup / Markdown transitions = **100% exact**;
- episode-start timestamps = **100% exact**;
- symATR within the frozen numerical tolerance;
- continuous diagnostic P99 error <= **0.50 points**;
- stock representation must resolve to Price Log.

A failure authorizes implementation-semantic fixes only, never classifier tuning.

---

## After AAPL

If AAPL passes, repeat unchanged on JPM and XOM.

Only after all three calibration stocks pass may the Python implementation SHA be frozen for formal Cross-Sectional OOS2.

Refs #78, #80.
