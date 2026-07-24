# Issue #35 — Expanded-restart cutoff gate

## Decision

`cutoff_sensitive_after_expansion`

The five-feature SPY 1D K=8 candidate passed 4 of 5 adjacent cutoffs when evaluated with nine deterministic restart attempts per frozen seed group. The shared restart schedule must not be promoted from `[0,1,2]` to `[0,1,2,3,4,5,6,7,8]` on this evidence.

Issue #24 remains paused. The 2% rare-state guardrail is unchanged.

## Frozen input

The promotion decision used the exact SPY OHLC captured by GitHub Actions Run #58:

- source run: `30077475634`
- source artifact: `hidden-regime-SPY` (`8590548073`)
- input file: `ohlc.csv`
- input SHA-256: `016448a0492769c527a8dc8e24d60fbda4c4e0e4bbdbcf27506caf30b76dddc4`
- frozen validation run: `30079063637`
- frozen result artifact: `hidden-regime-frozen-run58-cutoff-gate` (`8591114375`)
- retained restart-attempt records: 135

## Results

| Cutoff | Guardrails | Minimum OOS occupancy | Selected restart seeds |
|---|---|---:|---|
| 2026-07-17 | pass | 4.0640% | 42→46, 84→86, 126→126 |
| 2026-07-20 | pass | 4.0590% | 42→46, 84→86, 126→126 |
| 2026-07-21 | `no_rare_oos_states` | 1.9680% | 42→47, 84→90, 126→126 |
| 2026-07-22 | pass | 4.7970% | 42→44, 84→90, 126→127 |
| 2026-07-23 | pass | 3.3210% | 42→42, 84→87, 126→129 |

## Live-source drift observation

A later live Yahoo download in Run #60 used the same 4,163 dates but differed from the Run #58 OHLC on 3,135 rows by roughly `1e-4`. That small adjusted-price revision changed the selected local optimum and produced a 5/5 result. Because the input was not identical, the Run #60 live result is not accepted as the promotion gate.

This finding reinforces the requirement that model-selection and stability decisions use frozen, hash-verified inputs rather than repeated live downloads.
