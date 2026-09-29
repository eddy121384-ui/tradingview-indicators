# Issue #78 — Pine -> Python Classifier Parity Final Finding

## Decision

> **PASS — the scalable Python Issue #78 RC mirror is accepted as a faithful execution-scale implementation of the frozen Pine classifier for Cross-Sectional OOS2.**

This finding is strictly about implementation parity.

It is not evidence that the trading policy is profitable.

No AAPL / JPM / XOM R0 or Warning-First economics were inspected.

---

## Frozen implementation

Python classifier implementation frozen for OOS2:

- generated file:
  `research/generated/wyckoff-issue78-rc-python.py`
- generating commit containing the frozen mirror:
  `d5d166876dc998fce0cb792177b807f0e1aab333`
- Git blob:
  `1eec08e791403453853b589373bb2270c508c3bb`

Pine source of truth remains:

- Issue #68 RC
- frozen source blob:
  `e5c3fd2622841a6d3f97bdda4b9d0a6378ebda55`

Any future Python change used for formal OOS2 must preserve the parity suite and be documented before rerunning economic outcomes.

---

## Runtime fixtures

All fixtures used native 1D TradingView bars, frozen defaults and the log-only parity harness.

| Fixture | TV runtime namespace | Post-sync bars | formalId | Other discrete state | Fresh Markup/Markdown | symATR max abs |
|---|---|---:|---:|---:|---:|---:|
| AAPL | BATS:AAPL | 1,447 | 100% | 100% | 30 vs 30 exact | 5.03e-16 |
| JPM | BATS:JPM | 1,447 | 100% | 100% | 28 vs 28 exact | 4.996e-16 |
| XOM | BATS:XOM | 1,445 | 100% | 100% | 32 vs 32 exact | 5.03e-16 |

All three resolve to Price Log.

"Other discrete state" includes:

- topId
- candidateDisplayId
- stalePressureBars
- stalePressureReason

All were 100% exact on every accepted fixture window.

---

## Continuous-field parity

Worst recorded P99 absolute errors remained far below the preregistered 0.50-point diagnostic gate.

- AAPL worst P99: approximately **2.39e-05 points**
- JPM worst P99: approximately **2.924e-10 points**
- XOM worst P99: approximately **1.524e-10 points**

The remaining isolated residuals are numerically tiny relative to classifier scales and did not alter any accepted formal state, fresh trend transition, or episode start.

---

## XOM state-sync amendment

XOM revealed that "all numeric channels finite" alone is insufficient to compare recursive `formalId` state when:

- Pine carries a formal regime from history before the captured log window;
- Python intentionally cold-starts persistence at neutral.

The corrected engineering boundary begins at the first replay-owned nonzero Python formal confirmation after all required channels are finite.

This anchor:

- is determined from Python replay only;
- does not inspect Pine expected state;
- does not use policy economics;
- does not change any classifier formula or threshold.

The raw XOM pre-amendment discrepancy is retained in:

`issue-78-python-parity-state-sync-amendment.md`.

---

## OOS2 firewall status

The parity gate is now closed.

However, formal Cross-Sectional OOS2 **must not start yet** until the already-preregistered data-source addendum freezes:

- historical price provider;
- point-in-time security master;
- delisting coverage;
- corporate-action fields;
- sector / market-cap metadata;
- identifier mapping;
- raw snapshot / checksum procedure where feasible.

AAPL, JPM and XOM remain permanently excluded from formal OOS2 economics.

---

## Next action

> **Freeze the OOS2 historical data source / security master, then run the frozen Python classifier on the untouched individual-equity universe.**

PR #80 remains Draft / open / unmerged.

Refs #78, #80.
