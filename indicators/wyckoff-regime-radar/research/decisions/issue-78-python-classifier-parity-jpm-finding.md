# Issue #78 — Python Classifier Parity: JPM Runtime Finding

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
- captured TradingView runtime namespace: `BATS:JPM`
- intended calibration identity: JPM common stock

As with AAPL, the runtime namespace differs from the preregistration's human-readable `NYSE:JPM` label. This is recorded transparently as a feed-namespace observation, not an economic substitution: the parity test replays the exact OHLCV rows emitted by the same TradingView chart, and no policy economics are inspected on this fixture.

Capture:

- 2,500 daily bars
- first captured bar: 2016-10-17
- last captured bar: 2026-09-28
- Yield-Level flag: 0 throughout, therefore stock representation resolves to Price Log

---

## Comparable window

The Python mirror is initialized only from the 2,500 logged OHLCV rows, while the running Pine classifier had chart history before the first logged row.

The accepted comparison window uses the same frozen rule as the AAPL fixture: begin at the first row where all six Pine and Python stage-probability channels are finite.

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

- Pine fresh Markup / Markdown transitions: **28**
- Python fresh Markup / Markdown transitions: **28**
- transition timestamp mask agreement: **100% exact**
- episode-start timestamp agreement: **100% exact**

### symATR

On the common window:

- max absolute error: **4.996e-16**
- preregistered maximum: **1e-10**
- result: **PASS**

### Continuous diagnostics

The largest 99th-percentile absolute error among the logged continuous classifier diagnostics was:

- `topGap` P99 absolute error: **2.924e-10 points**

Preregistered diagnostic tolerance:

- P99 absolute error <= **0.50 points**

Result: **PASS by a very wide margin**.

The largest isolated absolute residual in the common window was also `topGap`, about **0.1673 points**. This is a small warm-start / floating-point residual and does not change any logged state ID, fresh Markup / Markdown transition, or episode start.

---

## JPM decision

> **JPM parity fixture PASS.**

The scalable Python Issue #78 RC mirror reproduces the TradingView Pine classifier on the JPM runtime fixture with exact state / transition agreement and negligible continuous-field error under the preregistered gate.

Completed fixtures:

1. AAPL — PASS
2. JPM — PASS

Remaining fixture:

3. XOM

Only after XOM also passes may the Python implementation SHA be frozen for formal Cross-Sectional OOS2.

Refs #78, #80.
