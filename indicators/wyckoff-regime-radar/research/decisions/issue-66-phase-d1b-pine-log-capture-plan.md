# Issue #66 Phase D-1B — Pine Log Capture Plan

## Why

The TradingView account used for runtime verification cannot export chart data. Phase D still needs runtime evidence from TradingView itself, so D-1B uses Pine Logs rather than chart-data export.

This is an implementation/parity transport change only. It does **not** change the accepted C-2 classifier, any threshold, any stage formula, or persistence.

## Parent

Accepted static D-1 harness generated from the frozen v0.5.2.1 Pine source with the accepted Issue #57 + Issue #66 C-2 lineage.

## Capture contract

Generate a second Pine harness that is byte-for-byte the D-1 generated classifier plus an appended log-only block.

The log block:

- captures the last 1200 confirmed bars by default;
- emits one `D1B|...` record per bar;
- includes `time`, OHLC, and all 36 D-1 parity fields;
- uses a fixed schema and high-precision decimal formatting;
- does not feed any captured value back into classifier calculations.

1200 daily bars leaves substantial post-warmup evaluation history beyond the 756-bar percentile-rank lookback.

## Runtime procedure

1. Use EURUSD 1D with default indicator parameters.
2. Add the generated D-1B Pine script to the chart.
3. Open Pine Logs for the script.
4. Copy/save the log text and provide it for parsing.
5. Parse only lines containing `D1B|` into the same column schema consumed by the existing D-1 comparator.

## Acceptance

The existing D-1 runtime parity gates remain unchanged:

- Formal-stage agreement >= 99.5%;
- Candidate-stage agreement >= 99.0%;
- preregistered continuous-field P99 absolute error <= 0.50;
- no formula/threshold changes may be selected from runtime parity results.

If runtime parity fails, repair translation/runtime semantics only. Do not modify C-2 classifier formulas to make parity pass.
