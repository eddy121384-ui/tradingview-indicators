# Issue #78 — Python Classifier Parity: AAPL Runtime Finding

## Status

Engineering parity fixture only.

No R0 / Warning-First economic result was calculated or inspected.

Formal Cross-Sectional OOS2 remains behind the full three-stock parity gate.

PR #80 remains Draft / open / unmerged.

---

## Runtime capture

TradingView Pine build:

- `#78 PY PARITY LOG`
- marker: `I78P1|`
- native timeframe: `1D`
- captured TradingView runtime namespace: `BATS:AAPL`
- intended calibration identity: AAPL common stock

The runtime namespace differs from the preregistration's human-readable `NASDAQ:AAPL` label. This is recorded transparently as a feed-namespace observation, not an economic substitution: the parity test replays the exact OHLCV rows emitted by the same TradingView chart, and no policy economics are inspected on this fixture.

Capture:

- 2,500 daily bars
- first captured bar: 2016-10-17
- last captured bar: 2026-09-28
- Price-Log routing flag: 0 / false for Yield-Level, i.e. Price Log

---

## Comparable window

The Python mirror is initialized only from the 2,500 logged OHLCV rows, while the running Pine classifier had chart history before the first logged row.

Therefore early recursive / rank state is not a valid implementation-parity comparison.

The accepted comparison window begins at the first bar where all six Pine and Python stage-probability channels are finite on the replayed data:

- first comparable row index: **1053**
- first comparable date: **2020-12-22**
- last comparable date: **2026-09-28**
- comparable bars: **1,447**

This window rule is based only on classifier warm-up / finite-state availability, not on policy outcomes.

---

## Hard parity results

### State outputs

Across the 1,447-bar common window:

- `formalId`: **100.0000% exact agreement**
- `topId`: **100.0000% exact agreement**
- `candidateDisplayId`: **100.0000% exact agreement**
- `stalePressureBars`: **100.0000% exact agreement**
- `stalePressureReason`: **100.0000% exact agreement**

### Fresh Markup / Markdown transitions

- Pine fresh Markup / Markdown transitions: **30**
- Python fresh Markup / Markdown transitions: **30**
- transition timestamp mask agreement: **100% exact**
- episode-start timestamp agreement: **100% exact**

### symATR

On the common window:

- max absolute error: **5.03e-16**
- preregistered maximum: **1e-10**
- result: **PASS**

### Continuous diagnostics

The largest 99th-percentile absolute error among the logged continuous classifier diagnostics was:

- `topGap` P99 absolute error: **2.39e-05 points**

Preregistered diagnostic tolerance:

- P99 absolute error <= **0.50 points**

Result: **PASS by a very wide margin**.

There are a handful of isolated larger floating-point / warm-start residuals in continuous internal values, including a maximum `evidence` difference of about 0.160 points and a maximum `markupGate` difference of about 0.061 points, but they do not change any logged state ID, fresh Markup / Markdown transition, or episode start in the accepted common window.

---

## AAPL decision

> **AAPL parity fixture PASS.**

The scalable Python Issue #78 RC mirror reproduces the TradingView Pine classifier closely enough on the AAPL runtime fixture to proceed to the next preregistered engineering fixture.

This is not yet permission to run formal stock OOS2 economics.

Remaining parity fixtures:

1. JPM
2. XOM

Only after both also pass may the Python implementation SHA be frozen for formal Cross-Sectional OOS2.

Refs #78, #80.
