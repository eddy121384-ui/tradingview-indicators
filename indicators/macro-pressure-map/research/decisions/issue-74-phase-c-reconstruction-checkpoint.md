# Issue #74 Phase C — TradingView source reconstruction checkpoint

## Status

`SOURCE_RECONSTRUCTION_VALIDATED_AFTER_WARMUP_BUT_EARLY_HISTORY_INCOMPLETE`

This checkpoint was recorded before any Phase C commodity-satellite portfolio PnL was calculated.

## Operator-supplied reconstruction log

A newly generated TradingView Pine Log was supplied from `MPM V6.6 PARITY SRC`.

- local filename: `pine-logs-MPM V6.6 PARITY SRC(1).csv`
- SHA-256: `a2bd73adb369d25533d706f29dc77484f63abf97e016fe3a8b43b917b62eabea`
- raw rows: 4,952
- unique dates after identical-duplicate collapse: 4,948
- source coverage: 2007-01-03 through 2026-09-02
- conflicting duplicate source rows: 0

The three `tv_plot_gpi` / `tv_plot_ipi` / `tv_plot_fcpi` fields are unusable in this new capture because all three remained pointed at the same default chart source. They are therefore not used as Phase C evidence.

## Independent source-row reconstruction

The 20 underlying TradingView source fields are present. Using the already-frozen Python V6.6 mirror with the default market-only configuration, raw GPI/IPI/FCPI become finite from 2008-04-03 onward because the mirror requires 252-row rolling history plus momentum warm-up.

The reconstructed axes were compared against every committed Issue #64 deterministic axis-audit checkpoint on or after mirror warm-up (47 checkpoints, 2008-08-06 through 2026-08-14):

- GPI maximum absolute difference: `2.1564728669432043e-08`
- IPI maximum absolute difference: `2.0430576341823325e-08`
- FCPI maximum absolute difference: `2.320506484188023e-08`
- regime-id mismatches: `0`

All three maximum axis differences are below the previously frozen Issue #64 independent-reconstruction tolerance of `5e-8` and are consistent with decimal logging-rounding noise.

This materially validates that the newly captured underlying TradingView source rows reproduce the frozen V6.6 mirror after adequate warm-up.

## Why Phase C is still blocked

Issue #74 Phase C was preregistered to use the full existing evaluation history and the exact existing V6.6 condition `raw IPI >= +60.0` inside lagged Stagflation Pressure.

The new capture starts at 2007-01-03. That is not enough pre-history for the 252-row V6.6 rolling calculations to reconstruct raw IPI for 2007-01-04 through 2008-04-02. Shortening the Phase C sample after seeing Phase A/B results would unnecessarily change the preregistered comparison window.

Therefore no Phase C portfolio PnL is calculated from this partial reconstruction.

## Required final reconstruction capture

Generate the same `MPM V6.6 PARITY SRC` Pine Logs again with:

- chart: SPY 1D;
- helper market timeframe: `D`;
- `Pine Logs start year = 2005` (instead of 2007).

The three frozen-plot `input.source()` selectors are not required for this reconstruction path because only the 20 underlying TradingView source rows will be used. If they are configured correctly, they provide an additional direct parity check, but Phase C reconstruction does not depend on them.

The 2005-start capture must then pass two gates before Phase C is unlocked:

1. reconstructed raw GPI/IPI/FCPI match all 51 committed Issue #64 axis-audit checkpoints within the frozen `5e-8` tolerance (subject only to known decimal logging precision);
2. reconstructed 2007-01-04 through 2026-08-14 3x3 regime transition CSV matches the frozen Issue #64 transition artifact / semantics.

Only after these gates pass may the daily `IPI >= +60` state be frozen and the preregistered Cash + GSG Phase C portfolio be evaluated.

## Integrity boundary

- This is a new reconstruction, not the missing historical operator-local CSV.
- No V6.6 formula, threshold, weight, lookback, production Pine, or Issue #64 verdict is changed.
- No Phase C portfolio result has been calculated at this checkpoint.
- No shortened-window Phase C result will be substituted merely to obtain an answer sooner.
