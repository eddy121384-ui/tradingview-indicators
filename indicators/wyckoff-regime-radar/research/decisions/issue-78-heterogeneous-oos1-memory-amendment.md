# Issue #78 — Heterogeneous OOS1 Technical Amendment: Pine Memory Safety

## Reason

The preregistered OANDA:XAUUSD feed raises TradingView runtime error `Memory limits exceeded` when the full frozen Issue #68 RC source is evaluated across all available 1D history.

The first memory-safety change removed the eight lower-timeframe `request.security_lower_tf()` arrays from the OOS export build. Those arrays belong to the frozen default `MTF Mode = Observe Only` layer and have zero stage-bias weight, so their removal does not alter `formalId`.

XAUUSD still exceeds TradingView's memory limit after those requests are removed.

TradingView documents `calc_bars_count` on `indicator()` as a supported way to reduce resource usage by restricting how many recent historical bars a script executes across.

## Frozen amendment

Before any usable XAUUSD OOS outcome is inspected, the OOS1 export logger is amended to:

`calc_bars_count = 10000`

The native timeframe remains 1D.

No classifier threshold, weight, representation rule, breakout rule, t+3 rule, R0 rule, Warning-First rule, or outcome definition changes.

## Interpretation

This is an execution-scope amendment, not a model amendment.

For formal OOS1 completion, any feed exported with v3 is interpreted over the most recent history available within the 10,000-bar execution cap. Markets with shorter histories remain naturally shorter.

The already-recorded four-market partial diagnostic remains a separate partial result and is not retroactively rewritten.

If the full six-market OOS1 finding mixes earlier uncapped exports with v3 exports, the finding must explicitly disclose that provenance. If exact execution-scope parity is required for a later confirmatory pass, all six markets should be re-exported with v3 before that pass.

## Stop rule

Do not reduce `calc_bars_count` again after inspecting XAUUSD outcomes merely to force the feed to run. If 10,000 bars still exceed memory, pause and redesign the export implementation without inspecting OOS results.

PR #80 remains Draft / open / unmerged.

Refs #78, #80, #76.
