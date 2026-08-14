# Issue #57 — Bridge handoff-weight behavior map

Status: **burned-data behavior study only**. Existing v0.6 is unchanged.

## Question

When an early semantic bridge first appears (`1+2`, `1+3`, `4+5`, `4+6`), which part of the internal weight handoff distinguishes bridges that later become the same-direction actionable pair (`2+3` or `5+6`) from bridges that fail?

## Frozen decomposition

For every bridge onset:

- **context stage** = 1 for bullish bridges, 4 for bearish bridges;
- **carried target** = the same-side actionable stage already present in Top2;
- **companion target** = the other same-side actionable stage not yet in Top2.

Examples:

- `1+2`: context=1, carried=2, companion=3;
- `1+3`: context=1, carried=3, companion=2;
- `4+5`: context=4, carried=5, companion=6;
- `4+6`: context=4, carried=6, companion=5.

## Outcome

Reuse the existing non-overlapping 20-bar bridge watches.

Primary descriptive outcome: same-direction actionable conversion within **10 bars**.

Also report 5-bar and 20-bar conversion for context. No threshold is tuned from outcome.

## Onset measurements

At bridge onset record:

- context weight;
- carried-target weight;
- companion-target weight;
- carried minus context margin;
- companion minus context margin;
- target-family minus context margin;
- 3-bar change in context, carried target, companion target, and both margins.

## Mechanical structural flags

These are rank/sign relations, not fitted numeric thresholds:

1. `carried_already_leads_context`: carried-target weight > context weight.
2. `context_falling_carried_rising_3`: over the prior 3 bars, context weight fell and carried-target weight rose.
3. `context_falling_companion_rising_3`: over the prior 3 bars, context weight fell and companion-target weight rose.
4. `both_new_targets_rising_context_falling_3`: context fell while both carried and companion targets rose.

For each flag, report event count and success-within-10 rate by pair and in aggregate/median-pair form.

## Interpretation boundary

This work reuses already-observed FX fixtures to understand the current indicator. It may identify a useful handoff mechanism, but it cannot validate a production trading rule and must not be used to tune a numeric cutoff from these outcomes.
