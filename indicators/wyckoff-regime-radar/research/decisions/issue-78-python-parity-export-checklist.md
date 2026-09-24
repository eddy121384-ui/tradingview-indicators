# Issue #78 — Python Classifier Parity Export Checklist

## Purpose

This checklist produces TradingView runtime evidence for the scalable Issue #78 Python mirror.

This is an **engineering parity capture only**.

Do not inspect or calculate R0 / Warning-First economics on the calibration stocks.

Formal OOS2 remains behind the parity gate.

---

## Build

Branch:

`research/issue-78-trend-capture-frontier`

Pine file:

`indicators/wyckoff-regime-radar/research/generated/wyckoff-issue78-python-parity-export.pine`

Indicator short title:

`#78 PY PARITY`

Python mirror:

`indicators/wyckoff-regime-radar/research/generated/wyckoff-issue78-rc-python.py`

Comparator:

`indicators/wyckoff-regime-radar/research/compare_issue78_python_parity.py`

---

## Calibration order

Run one symbol at a time.

1. `NASDAQ:AAPL`
2. `NYSE:JPM`
3. `NYSE:XOM`

All three are engineering fixtures and are permanently excluded from formal OOS2 economics.

Start with AAPL. Do not proceed to policy economics after AAPL; the first CSV is used only to diagnose implementation parity.

---

## TradingView settings

For each symbol:

- timeframe: **1D**
- use the `#78 PY PARITY` indicator;
- leave all classifier inputs at their frozen defaults;
- Representation Mode: **Auto** (for stocks this must resolve to Price Log);
- Volume Mode: **Auto**;
- MTF Mode: **Observe Only**;
- Divergence Mode: **Observe Only**;
- Witness Stage Bias Mode: **Balanced**;
- do not alter thresholds;
- use the same chart feed for OHLCV and Pine reference channels.

The parity build is capped at 10,000 bars for memory safety.

---

## Export

Use TradingView **Export chart data** after the indicator has fully loaded.

The CSV must contain the chart OHLCV plus the parity channels.

Required chart fields:

- Time / Date
- Open
- High
- Low
- Close
- Volume

Required parity fields include:

- PARITY formalId
- PARITY symATR
- PARITY volumeQuality
- PARITY volumeWeight
- PARITY volumeAbsorption
- PARITY volumeDistribution
- PARITY volumeBreakout
- PARITY volumeBreakdown
- PARITY accGate
- PARITY markupGate
- PARITY reaccGate
- PARITY distGate
- PARITY markdownGate
- PARITY redistGate
- PARITY probAcc
- PARITY probMarkup
- PARITY probReacc
- PARITY probDist
- PARITY probMarkdown
- PARITY probRedist
- PARITY topId
- PARITY topGap
- PARITY evidence
- PARITY candidateDisplayId
- PARITY stalePressureBars
- PARITY stalePressureReason

Do not rename or manually edit the CSV.

---

## First runtime gate

Upload the AAPL CSV unchanged.

The comparator replays the **exact TradingView OHLCV rows** through Python, avoiding cross-vendor feed differences.

Hard gate:

- formalId agreement >= 99.99% on the common post-warmup window;
- fresh Markup / Markdown transitions = 100% exact;
- episode-start timestamps = 100% exact;
- symATR within the frozen numeric tolerance;
- continuous diagnostic P99 error <= 0.50 points.

A failure authorizes only implementation-semantic fixes.

It does not authorize classifier tuning.

---

## After AAPL

If AAPL passes:

- repeat unchanged on JPM;
- repeat unchanged on XOM.

Only after all three calibration stocks pass may the Python commit SHA be frozen for formal Cross-Sectional OOS2.

Refs #78, #80.
