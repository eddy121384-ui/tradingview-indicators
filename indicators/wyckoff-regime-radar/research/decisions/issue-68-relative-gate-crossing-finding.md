# Issue #68 — FR10Y vs DE10Y Relative-Gate Crossing Finding

Status: discovery-only finding. Production C-2 remains frozen.

Window: 2022-01-03 through 2023-12-29, daily.

## Observed TradingView results

The audit table had a display-format defect: several decimal strings used Pine patterns such as `#.1` / `#.3`, which can render misleading literal suffixes. Integer counts are authoritative; percentages below are recomputed from counts.

### FR10Y

- valid bars: 512
- `RAW S1 >= S2`: 512 / 512 = 100.0%
- `EFF S2 > S1`: 110 / 512 = 21.48%
- therefore `RAW S1 >= S2 -> EFF S2 > S1`: 110 / 512 = 21.48%
- ratio-valid bars: 473
- positive relative-gate surplus: 107 / 473 = 22.62%
- algebra mismatch count: 0
- flip runs: 20
- average flip-run length from counts: 110 / 20 = 5.50 bars
- maximum flip run: 27 bars
- dominant qualitative S1 bottleneck on flip bars: downside-exhaustion gate
- dominant qualitative S2 gate source: breakout path

### DE10Y

- valid bars: 512
- `RAW S1 >= S2`: 512 / 512 = 100.0%
- `EFF S2 > S1`: 185 / 512 = 36.13%
- therefore `RAW S1 >= S2 -> EFF S2 > S1`: 185 / 512 = 36.13%
- ratio-valid bars: 435
- positive relative-gate surplus: 182 / 435 = 41.84%
- algebra mismatch count: 0
- flip runs: 19
- average flip-run length from counts: 185 / 19 = 9.74 bars
- maximum flip run: 82 bars
- dominant qualitative S1 bottleneck on flip bars: downside-exhaustion gate
- dominant qualitative S2 gate source: breakout path

## Interpretation

The FR-vs-DE semantic split is created materially at the RAW x gate -> effective-score layer.

Both markets begin with S1 Accumulation above S2 Markup at RAW on all 512 bars, yet DE reverses that pairwise ordering after gates on 185 bars versus only 110 for FR. DE's reversals are also much more persistent, including an 82-bar maximum run versus 27 bars for FR.

The direct algebra check has zero mismatches, so the crossing measurement is internally consistent. The qualitative source rows point to the same architecture in both markets: S2 reversals are breakout-gate led, while the main S1 suppression bottleneck is the downside-exhaustion gate.

This localizes the next causal question to the downside-exhaustion score rather than to S2 RAW strength, S3 rescue, gamma, or common normalization.

## Next step

Decompose the frozen downside-exhaustion score into its five weighted source components:

- `noBreakLowScore` (30%)
- `negSlopeDullScore` (25%)
- `panicDullScore` (20%)
- `lowVolScore` (15%)
- `lowZoneStableScore` (10%)

Compare FR10Y and DE10Y on all bars, key flip bars, and non-flip bars. Attribute suppression using weighted deficit points `(100 - component) * weight` so the five deficits sum mechanically to `100 - downsideExhaustion` before the gate transform.

No tuning, no PnL, and no production change is authorized.