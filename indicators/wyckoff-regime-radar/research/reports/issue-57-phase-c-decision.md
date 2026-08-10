# Issue #57 — Phase C decision

Decision: **phase_c_select_four_state_canonical_regime**

Phase C selects the predeclared four-state representation as the canonical v0.6 regime layer.

The six Wyckoff stage scores are **not deleted**. They remain available as substructure diagnostics and can still explain whether an Accumulation-family regime is Accumulation vs Re-accumulation, or whether a Distribution-family regime is Distribution vs Re-distribution.

## Canonical v0.6 mapping

1. **Accumulation family** = Stage 1 Accumulation + Stage 3 Re-accumulation
2. **Markup** = Stage 2 Markup
3. **Distribution family** = Stage 4 Distribution + Stage 6 Re-distribution
4. **Markdown** = Stage 5 Markdown

Neutral remains `0`.

## Why not keep six as the canonical output?

Across the three already-observed Issue #55 time segments, the six-state representation never populated all six states above a 1% share in any pair (`0%` full-coverage pair rate). Median populated states were only `4.5 / 4.0 / 4.0` out of six.

The four-state mapping repaired that under-population without materially sacrificing future-return separation:

- Development: all four states >=1% in `100%` of pairs; median populated `4/4`.
- Exploratory OOS: median populated `4/4`; full-coverage pair rate `75%`.
- Burned Final OOS: all four states >=1% in `100%` of pairs; median populated `4/4`.

For Exploratory OOS and the burned Final-OOS segment, the four-state and six-state median forward-return eta-squared values are identical at all 5/10/20/60-bar horizons. Development loses only a small amount of 5/10-bar separation while retaining the same 20/60-bar separation.

The 4-state mapping also slightly reduces Development -> Exploratory occupancy shift (`0.982 -> 0.945`).

## Why not collapse to three?

The three-state representation has the cleanest coverage and lower occupancy shift (`0.676` and `0.607` across the two time transitions), and its short-horizon rank stability is often better.

However, this stability comes from a materially coarser representation. It loses forward-return separation in multiple segments/horizons, especially in the burned Final-OOS period:

- 5 bars: `0.026 -> 0.011`
- 10 bars: `0.021 -> 0.008`
- 20 bars: `0.032 -> 0.018`
- 60 bars: `0.086 -> 0.050`

Because the Phase-C decision rule is to prefer the smallest representation that preserves materially useful separation, three states is judged too coarse for the canonical layer.

## Implementation boundary

`v06_state_mapping.py` freezes the selected four-state mapping and aggregates the six stage weights into four canonical regime weights while retaining all original six-stage fields.

No PnL was used to select this mapping. The Issue #55 Final OOS remains burned and cannot independently validate this choice.

## Next gate

Proceed to **Phase D: confidence redesign** using the four canonical regime weights. Recalculate the margin/strength concepts at the four-state level and test whether any quantity deserves to be called confidence. If calibration is not demonstrated, keep it as descriptive strength/margin rather than probability/confidence.
