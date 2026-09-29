# Issue #78 — Python Parity State-Synchronization Amendment

## Status

Technical engineering amendment recorded after the XOM parity fixture exposed a cold-start state-boundary artifact.

No R0 / Warning-First economics were calculated or inspected on AAPL, JPM, or XOM.

This amendment does not change the frozen Pine classifier, the Python classifier formulas, any thresholds, or any OOS2 universe rule.

---

## What XOM exposed

The initial runtime reports used:

> first row where all six Pine and Python stage-probability channels are finite

as the practical comparison boundary.

That worked without incident on AAPL and JPM.

On XOM, however, the first all-fields-finite row occurred while TradingView Pine was already carrying an existing Markup `formalId=2` from chart history before the 2,500-bar log capture.

The Python replay intentionally starts its recursive persistence state at neutral because bars before the log capture are unavailable to it.

Therefore the two implementations had:

- essentially identical continuous classifier calculations;
- exact `topId`;
- exact `candidateDisplayId`;
- exact stale-pressure state;

but Python required its normal three-bar confirmation path to establish its own Markup `formalId`.

### Raw pre-amendment XOM comparison

Using the old first-finite boundary:

- comparison bars: 1,447;
- `formalId` agreement: **99.8618%**;
- mismatching bars: **2**;
- Pine fresh Markup / Markdown transitions: **32**;
- Python fresh transitions: **33**;
- transition-mask criterion: FAIL.

The two mismatches were the first two bars of the comparison window:

- 2020-12-21;
- 2020-12-22.

Python confirmed the same Markup state on 2020-12-23 and remained synchronized thereafter.

This is a truncated-history persistence initialization artifact, not a difference in classifier scores or policy economics.

---

## Corrected parity boundary

The parity state-comparison window is now defined as:

> **the first replay-owned nonzero Python formal confirmation at or after all required parity channels are finite.**

Why this boundary is appropriate:

1. Pine may carry recursive state from before the captured log window.
2. Python intentionally cannot know that pre-capture state.
3. Once Python establishes a nonzero formal state from the replayed bars themselves, subsequent persistence transitions are generated from the same observable state machine.
4. The synchronization anchor is determined from the Python replay only.
5. It does not inspect Pine's expected `formalId`, return, PnL, R0, Warning-First, or any formal OOS2 economic output.

The acceptance thresholds themselves are unchanged.

---

## Effect on the three frozen fixtures

Using this single state-synchronization rule:

| Fixture | First all-fields finite | Replay sync anchor | Compared bars | Formal ID | Fresh trend transitions |
|---|---|---|---:|---:|---:|
| AAPL | 2020-12-22 | 2020-12-22 | 1,447 | 100% | 30 vs 30 exact |
| JPM | 2020-12-22 | 2020-12-22 | 1,447 | 100% | 28 vs 28 exact |
| XOM | 2020-12-21 | 2020-12-23 | 1,445 | 100% | 32 vs 32 exact |

The AAPL and JPM conclusions are unchanged.

---

## Research firewall

This amendment is allowed by the preregistered mismatch policy because it addresses parity-harness initialization semantics only.

It does not authorize:

- classifier retuning;
- threshold changes;
- policy changes;
- stock-universe changes;
- economic-result filtering.

Formal Cross-Sectional OOS2 has still not begun.

Refs #78, #80.
