# Issue #78 — Pine -> Python Classifier Parity Plan
## Required engineering gate before Cross-Sectional OOS2

## Purpose

TradingView Pine is the frozen classifier source of truth, but single-chart execution is not practical for hundreds or thousands of stocks.

Cross-Sectional OOS2 therefore requires a Python implementation of the frozen Issue #68 RC classifier.

The Python port is an **execution-scale implementation**, not a new model.

It may not change classifier semantics.

---

## 1. Source of truth

Frozen Pine source:

- file: `chase-risk-market-regime-radar-issue68-rc.pine`
- Git blob: `e5c3fd2622841a6d3f97bdda4b9d0a6378ebda55`

Existing Issue #76 / #78 loggers remain the accepted reference for:

- `formalId`;
- fresh transitions;
- `symATR`;
- Price Log vs Yield Level representation;
- causal event timing.

For stock OOS2 the representation is always Price Log.

---

## 2. Porting rule

Port the classifier literally before refactoring.

Implementation order:

1. input / metadata normalization;
2. rolling primitives with Pine-compatible NA semantics;
3. ATR / volatility / range primitives;
4. frozen context / evidence components;
5. stage scores / gates;
6. confirmed stage;
7. `formalId`;
8. `symATR`;
9. fresh-transition flag.

Do not optimize or vectorize away semantics until parity passes.

Any later optimization must preserve the parity suite.

---

## 3. Pine semantics that require explicit tests

At minimum test Pine-compatible behavior for:

- `ta.sma`;
- `ta.ema`;
- `ta.rma`;
- `ta.highest` / `ta.lowest`;
- `ta.stdev` if used by the RC;
- `ta.percentrank` / rank semantics if used;
- crossover / crossunder;
- historical indexing;
- initialization / warm-up NA behavior;
- boolean NA handling;
- ternary evaluation where it affects NA propagation;
- rolling windows after missing bars;
- logarithmic price moves;
- split-adjusted stock price input.

No Python-library default is assumed equivalent without a unit test.

---

## 4. MTF handling

The frozen Issue #68 default MTF mode is `Observe Only`.

Under that default, lower-timeframe MTF witness weight is zero and does not change the formal stage.

The OOS1 memory-safe logger already removed the eight lower-timeframe arrays for this reason.

The Python OOS2 implementation may omit those lower-timeframe arrays **only while the frozen default remains Observe Only**.

A contract test must fail if the frozen MTF default changes.

---

## 5. Parity fixture set

### Already-inspected non-stock references

Use at least:

- TVC:SPX
- NASDAQ_DLY:NDX
- OANDA:XAUUSD
- BITSTAMP:BTCUSD

These have already been used in OOS1 and do not contaminate stock OOS2.

### Stock engineering calibration set

Freeze:

- NASDAQ:AAPL
- NYSE:JPM
- NYSE:XOM

These are engineering fixtures only and are excluded from formal OOS2 economics.

Do not inspect R0 / Warning-First performance on these stocks during parity work.

---

## 6. Required parity export

For every calibration symbol, the same raw daily input bars must be fed to Pine reference and Python port.

Required per-bar fields:

- timestamp;
- open;
- high;
- low;
- close;
- volume;
- `formalId`;
- `symATR`;
- confirmed-stage / any intermediate stage ID needed to localize mismatches.

Preferred method:

> export raw OHLCV and hidden Pine reference channels from the same TradingView chart dataset, then replay those exact OHLCV rows through Python.

Do not compare Python on one vendor's bars with Pine on another vendor's bars and call data differences an implementation mismatch.

---

## 7. Warm-up

Parity statistics begin only after the maximum classifier warm-up requirement is satisfied.

The warm-up length must be derived from the frozen source, documented in code, and covered by a test.

Do not choose a shorter warm-up because it improves parity.

---

## 8. Hard acceptance criteria

The Python classifier may be used for formal OOS2 only if all criteria pass.

### Stage parity

- `formalId` exact agreement >= **99.99%** of post-warm-up bars on every fixture;
- **100% exact agreement on every fresh formal Markup / Markdown transition**;
- **100% agreement on episode start timestamps**.

Any mismatch that changes a fresh Markup / Markdown episode is a hard FAIL.

### ATR parity

For finite post-warm-up `symATR` values:

- maximum relative error <= **1e-8**;
- maximum absolute error <= **1e-10** where scale makes that criterion meaningful.

If deterministic Pine / Python semantics permit exact or tighter parity, retain the tighter result rather than relaxing it.

### Representation parity

For stock fixtures:

- Price Log must match 100%.

---

## 9. Mismatch policy

Permitted response to a mismatch:

- identify an implementation difference;
- fix the Python port;
- rerun the frozen fixture suite.

Not permitted:

- change the Pine classifier;
- retune thresholds;
- drop a difficult fixture;
- loosen acceptance criteria after seeing OOS2 economics;
- alter stock-universe rules.

If a mismatch is caused by data-source differences, first restore identical raw OHLCV inputs.

---

## 10. Parity artifacts

Commit:

- Python classifier module;
- Pine parity-export helper if needed;
- fixture manifests / hashes;
- unit tests for Pine-compatible rolling primitives;
- per-symbol parity summary CSV;
- mismatch report if any;
- final parity finding.

Suggested paths:

- `research/issue78_rc_python.py`
- `research/test_issue78_rc_python.py`
- `research/generated/wyckoff-issue78-python-parity-export.pine`
- `research/decisions/issue-78-python-classifier-parity-finding.md`

Raw large fixture files do not need to live in Git if licensing / size prevents it; their provenance and hashes must still be recorded.

---

## 11. OOS2 firewall

Until parity is accepted:

> **Do not run formal stock OOS2 policy economics.**

Engineering tests may inspect classifier stage outputs only.

AAPL / JPM / XOM are excluded from formal OOS2 by preregistration.

Once parity passes, freeze the Python commit SHA used for OOS2 and do not change it during the cohort run except for bug fixes that are demonstrated to restore Pine parity and are documented before rerunning outcomes.

---

## 12. Definition of success

The parity project succeeds when the Python implementation can be treated as a faithful scalable executor of the frozen Pine classifier.

It does **not** succeed because Python produces attractive backtest results.

The only question at this gate is:

> **Does Python reproduce Pine closely enough that scaling from 6 charts to thousands of stocks does not change the model being tested?**

Refs #78, #80, #76.
