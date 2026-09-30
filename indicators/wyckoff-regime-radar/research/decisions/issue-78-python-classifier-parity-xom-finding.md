# Issue #78 — Python Classifier Parity: XOM Runtime Finding

## Status

Engineering parity fixture only.

No R0 / Warning-First economic result was calculated or inspected.

Formal Cross-Sectional OOS2 has not started.

PR #80 remains Draft / open / unmerged.

---

## Runtime capture

TradingView Pine build:

- `#78 PY PARITY LOG`
- marker: `I78P1|`
- native timeframe: `1D`
- captured TradingView runtime namespace: `BATS:XOM`
- intended calibration identity: XOM common stock

The preregistration used the human-readable `NYSE:XOM` label. As with AAPL and JPM, TradingView emitted a `BATS:` runtime namespace. This is recorded as a feed-namespace observation only.

Capture:

- 2,500 daily bars
- first captured bar: **2016-10-14**
- last captured bar: **2026-09-28**
- Yield-Level flag: 0 throughout, therefore representation = **Price Log**

---

## State-synchronization note

XOM exposed a truncated-history persistence initialization issue in the initial parity-window implementation.

The first all-fields-finite row was:

- row index 1053
- **2020-12-21**

At that point Pine already carried Markup `formalId=2` from chart history before the capture, while Python cold-started persistence from neutral.

Under the old first-finite boundary:

- `formalId` agreement = **99.8618%**
- 2 mismatching bars
- fresh transitions = Pine 32 vs Python 33

The mismatch was confined to 2020-12-21 and 2020-12-22.

All other logged discrete classifier channels were already exact.

The technical state-synchronization amendment is documented separately and does not alter classifier semantics or acceptance thresholds.

The replay-owned synchronization anchor is:

- row index 1055
- **2020-12-23**

Accepted post-sync comparison bars:

- **1,445**

---

## Hard parity results after the frozen synchronization rule

### State outputs

Across the 1,445-bar post-sync window:

- `formalId`: **100.0000% exact agreement**
- `topId`: **100.0000% exact agreement**
- `candidateDisplayId`: **100.0000% exact agreement**
- `stalePressureBars`: **100.0000% exact agreement**
- `stalePressureReason`: **100.0000% exact agreement**

### Fresh Markup / Markdown transitions

- Pine: **32**
- Python: **32**
- timestamp-mask agreement: **100% exact**
- episode-start agreement: **100% exact**

### symATR

- max absolute error: **5.03e-16**
- preregistered maximum: **1e-10**
- result: **PASS**

### Continuous diagnostics

Largest 99th-percentile absolute error:

- `topGap`: **1.524e-10 points**

Preregistered tolerance:

- P99 <= **0.50 points**

Result: **PASS by a very wide margin**.

Largest isolated residuals were also small and did not alter any accepted state or transition:

- `evidence` max abs error ≈ **0.0538 points**
- `topGap` max abs error ≈ **0.00579 points**

---

## XOM decision

> **XOM parity fixture PASS under the corrected state-synchronization boundary.**

The raw pre-amendment two-bar mismatch is retained in the record rather than hidden.

Completed frozen fixtures:

1. AAPL — PASS
2. JPM — PASS
3. XOM — PASS

This closes the three-stock runtime parity fixture set.

Refs #78, #80.
