# Issue #78 — Compression Structure Challenge Stage 1 Preregistration
## Overlap vs Width before the first genuine post-entry breakout

## Purpose

Define what a useful pre-breakout consolidation / compression structure actually is before studying retests, second entries, FVG acceptance, or sizing.

The user’s prior Shiori Confluence Suite contained a Compression Cage with this frozen concept:

- lookback = 5 bars;
- at least 3 of 5 bars must each span at least 80% of the total 5-bar high-low box;
- breakout boundary = prior 5-bar high / low;
- valid breakout close must exceed the boundary by 20% of box height.

This study treats that logic as a historical baseline, not as a validated optimum.

Primary question:

> **Before a genuine post-entry directional breakout, is breakout health better explained by high bar-overlap, by a narrow total box relative to volatility, or by both?**

The goal is not to tune the old Cage. It is to decide what “compression structure” should mean in the next research stage.

## Data source and OHLC reconstruction

Reuse the accepted Issue #76 nine-market daily logger:

- 68,118 accepted event rows;
- 1,624 completed known-start Markup / Markdown episodes;
- same nine daily markets;
- no classifier change.

The logger does not export direct OHLC columns, but it does export for every event bar:

- `move1`: next close vs event close;
- `mfe1`: next high vs event close;
- `mae1`: next low vs event close.

These are sufficient to reconstruct each subsequent bar’s close / high / low in the same additive raw-move coordinate:

- PRICE_LOG: log-price distance;
- YIELD_LEVEL: basis-point distance.

The reconstruction must be verified mechanically by checking that reconstructed one-bar close/high/low differences reproduce the logged `move1/mfe1/mae1` fields.

No outside price source is introduced.

## Episode / event unit

Use completed known-start formal trend episodes only:

- Markup stage 2;
- Markdown stage 5.

To avoid repeating the entry-structure problem from the prior 20-close breakout study, the breakout candidate must be **genuinely post-entry**.

For each episode:

1. wait until at least 5 completed post-entry bars exist;
2. starting with the next bar, scan forward;
3. accept the **first** directional breakout of a causal 5-bar pre-breakout box;
4. keep at most one breakout event per episode.

This creates a clean episode-level event and avoids counting many overlapping rolling breakouts from the same trend.

Episodes with no qualifying post-entry breakout are reported as non-events but are not forced into breakout-health outcomes.

## Frozen pre-breakout box

For breakout bar `t`, define the structure window using bars:

`t-5 ... t-1`

The breakout bar `t` itself may not affect the box definition.

### Box boundaries

- `box_high = max(high[t-5:t-1])`
- `box_low = min(low[t-5:t-1])`
- `box_height = box_high - box_low`

The box must have finite positive height.

## Frozen breakout definition

Use the historical Shiori Cage buffer without tuning.

### Markup

`close[t] > box_high + 0.20 * box_height`

### Markdown

`close[t] < box_low - 0.20 * box_height`

No alternative 0%, 10%, 15%, 25%, 30% buffers are searched in this stage.

## Structure family A — Historical Overlap Cage

For each of the 5 pre-breakout bars:

`bar_range_i = high_i - low_i`

Count:

`coverage80_count = number of bars with bar_range_i >= 0.80 * box_height`

Historical binary Cage:

`old_cage = coverage80_count >= 3`

Also report the frozen continuous/discrete diagnostic:

`coverage80_fraction = coverage80_count / 5`

This preserves the user’s prior indicator semantics.

## Structure family B — Width Compression

Measure the total 5-bar box width relative to the volatility scale known at `t-1`.

Use the existing frozen cross-market risk unit:

- PRICE_LOG: `scale[t-1]`;
- YIELD_LEVEL: `scale[t-1] * 100`.

Define:

`box_width_atr = box_height / prebreak_scale`

Lower values mean narrower compression.

Do **not** introduce a numeric “narrow enough” cutoff in Stage 1.

Primary width tests use:

- continuous rank / AUC where appropriate;
- within-market quintiles.

This avoids optimizing a new threshold.

## Secondary overlap diagnostic — literal common overlap

Because the historical Cage criterion is an indirect overlap measure, report one parameter-free diagnostic:

`common_overlap = max(0, min(high_i) - max(low_i))`

`common_overlap_fraction = common_overlap / box_height`

This is descriptive only and cannot replace the frozen historical Cage based on Stage 1 results.

## Primary breakout-health outcomes

All outcomes are measured **after breakout bar t**.

### H1 — Box re-entry by 3 closes

Binary adverse outcome:

> Does any of the next 3 completed closes return inside the original frozen box?

For Markup: close <= box_high.
For Markdown: close >= box_low.

### H2 — Box re-entry by 5 closes

Same definition over the next 5 completed closes.

### H3 — Favorable extension by 5 moves

Binary:

> Within the next 5 completed moves, does price make a new favorable high/low beyond the breakout bar’s favorable extreme?

Use reconstructed highs for Markup and lows for Markdown.

### H4 — Favorable extension by 10 moves

Same over 10 completed moves.

### H5 — Remaining formal-regime life >=20 moves

Does the formal Markup / Markdown episode remain active for at least 20 completed moves after breakout?

### H6 — Remaining formal-regime life

Continuous number of completed moves after breakout.

No single composite “healthy breakout” score is created in Stage 1.

## Primary tests

### Test A — Historical Cage standalone value

Compare old_cage vs non-cage breakout events within each market on H1–H6.

Primary aggregation:

- equal-market mean difference;
- median market difference;
- markets with expected-sign difference.

Expected direction:

- lower H1/H2 re-entry;
- higher H3/H4 extension;
- higher H5/H6 durability.

### Test B — Width gradient

Within each market, rank `box_width_atr` into quintiles.

Compare narrowest Q1 vs widest Q5.

Expected direction:

- narrower boxes should have lower re-entry and stronger continuation/durability if true width compression matters.

Also report within-market AUC of `-box_width_atr` for binary outcomes.

### Test C — Incrementality of overlap conditional on width

Within market × width quintile, compare old_cage vs non-cage when both groups have at least 3 events.

Aggregate:

- equal-cell diagnostic;
- equal-market primary diagnostic using overlap-balanced cell weights.

Question:

> **At comparable box width, does the historical overlap Cage add breakout-health information?**

### Test D — Incrementality of width conditional on overlap

Within old_cage = 0 and old_cage = 1 separately, report width quintile gradients where endpoint cells are adequately populated.

Question:

> **Does narrower width still matter after overlap state is known?**

### Test E — relationship between overlap and width

Report:

- Spearman correlation between coverage80_fraction and box_width_atr;
- old_cage prevalence by width quintile;
- common_overlap_fraction by old_cage state.

This establishes whether “overlap” and “narrow” are actually distinct dimensions.

## Temporal robustness

Repeat the primary standalone and width tests for:

- 2010–2014;
- 2015–2019;
- 2020–2026.

2015–2019 remains a required stress era.

No era-specific definition is allowed.

## Direction robustness

Report Markup and Markdown separately.

No direction-specific compression definition is allowed.

## Promotion logic

### Overlap is promoted

only if old_cage shows expected-sign breakout-health improvement in a clear majority of markets and retains useful effect conditional on width.

### Width is promoted

only if narrower boxes show a reasonably ordered health gradient across markets and retain useful effect within overlap states.

### Both are promoted

if each retains incremental information after conditioning on the other.

### Neither is promoted

if the apparent effects are weak, unstable, or entirely redundant.

No tuning follows from a failed result.

## Important non-goals

This stage does **not** yet test:

- strong-breakout vs weak-breakout bar strength;
- retest acceptance;
- second-entry / re-expansion;
- FVG;
- position sizing;
- stop / invalidation;
- Sharpe optimization.

Those belong only after the pre-breakout structure definition is understood.

## Guardrails

- no 3 / 8 / 10 / 20-bar lookback search;
- no 60 / 70 / 90% overlap search;
- no 2-of-5 / 4-of-5 search;
- no breakout-buffer search;
- no new width cutoff;
- no market-specific thresholds;
- no Markup / Markdown-specific thresholds;
- no post-outcome event filtering;
- no use of breakout bar in the pre-breakout box;
- one accepted breakout event maximum per episode;
- no production claim from this discovery sample.

## Intended answer

> **When a trend pauses and then breaks out again, is the quality of that breakout better explained by bars overlapping heavily, by the box being genuinely narrow relative to volatility, or by both?**

Refs #78, #80, #76.
