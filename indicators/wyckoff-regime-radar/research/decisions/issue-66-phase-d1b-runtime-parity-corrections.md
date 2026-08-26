# Issue #66 Phase D-1B — Runtime parity corrections from first TradingView capture

## Evidence source

First real TradingView D-1B Pine Logs capture on EURUSD 1D, default indicator parameters, 1199 confirmed bars.

The raw user capture is **not committed** to the repository. Only aggregate engineering findings are recorded here.

## Finding 1 — Python `ta.percentrank()` mirror is off by one

The existing `pine_math.percentrank()` compares the current value against `length-1` prior observations inside a `length`-bar window and divides by `length-1`.

TradingView runtime evidence shows the actual semantics used by this indicator are:

- compare the current observation against the **previous `length` observations**;
- use strict `<` ranking;
- divide by `length`;
- therefore the rank step for `rankLen=756` is exactly `100/756`.

On the capture, changing only this helper makes all directly logged rank fields (`speed_rank`, `accel_rank`, `dist_rank`) match TradingView to floating-point noise on every comparable row.

This is a Pine-runtime semantic correction only. It does not change C-2 classifier formulas or thresholds.

## Finding 2 — D-1B log transport emits one extra delimiter

The first generator currently emits `D1B||time|...` because the marker string already ends in `|` and the join expression adds another delimiter.

The parser expected `D1B|time|...`.

Repair:

- new captures emit exactly one delimiter after `D1B`;
- parser remains backward-compatible with the already-captured `D1B||...` form.

This is transport-only.

## Finding 3 — acceptance must exclude non-comparable pre-warmup rows

A Pine runtime capture begins after TradingView has already accumulated earlier chart state, while the Python mirror starts from the first captured OHLC row. With a 756-bar percentile rank plus upstream maturity/MA dependencies, early captured rows are not legitimately comparable.

The existing D-1 comparator already builds `common_mask` and reports `first_all_fields_comparable_row_index`, but ID-field acceptance was accidentally calculated over every numerically-present ID row, including pre-warmup rows where Python cannot yet reproduce the Pine state.

Correction:

- retain per-field raw diagnostics;
- calculate Candidate/Formal acceptance agreement only on rows where all parity fields are simultaneously comparable (`common_mask`).

Thresholds remain unchanged:

- Formal >= 99.5%;
- Candidate >= 99.0%;
- core continuous P99 <= 0.50 points.

## First-capture result after semantic corrections

On the 146 fully comparable post-warmup bars in the first EURUSD 1D capture:

- Candidate-stage agreement: **100%**;
- Formal-stage agreement: **100%**;
- top-stage ID agreement: **100%**;
- stale-pressure bars/reason agreement: **100%**;
- worst preregistered core continuous P99 error: **~0.050 points** (`top_gap`), well inside the 0.50-point gate;
- probability-field P99 errors are all below ~0.025 points.

Therefore the first real TradingView runtime evidence supports a D-1 parity PASS after correcting the Python built-in mirror and comparator warmup semantics.

## Boundary

These corrections may change Python mirror outputs because they repair Pine built-in/runtime semantics. They do **not** authorize any C-2 formula, threshold, stage, conflict, or persistence tuning.
