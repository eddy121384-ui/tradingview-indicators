# Issue #78 — Compression Structure Challenge Stage 1B Preregistration
## Parameter-free overlap × width with an uncoupled breakout definition

## Purpose

Repair the identification problem discovered in Compression Structure Stage 1 without tuning toward a favorable result.

Stage 1 established two facts:

1. the historical 3-of-5 / 80% Cage is too sparse for universal inference;
2. the historical `20% * box_height` breakout buffer mechanically couples box width to event admission.

Stage 1B therefore asks the same conceptual question with a cleaner design:

> **Before the first genuine post-entry breakout, does bar overlap, narrow box width, or both predict healthier continuation?**

## Frozen sample and event unit

Reuse the exact accepted Issue #76 nine-market daily discovery sample:

- 68,118 accepted event rows;
- 1,624 completed known-start Markup / Markdown episodes.

OHLC coordinates are reconstructed from `move1 / mfe1 / mae1` exactly as in Stage 1.

For each episode:

1. at least 5 completed post-entry bars must occur first;
2. the first directional breakout after that point is the event;
3. at most one breakout event per episode.

## Frozen 5-bar pre-breakout structure

For breakout bar `t`:

`window = t-5 ... t-1`

`box_high = max(high)`

`box_low = min(low)`

`box_height = box_high - box_low`

The breakout bar may not enter the structure calculation.

No alternate lookback is allowed.

## Stage 1B breakout definition — uncoupled from width

### Markup

`close[t] > box_high`

### Markdown

`close[t] < box_low`

No additional breakout buffer is used.

This is intentional: Stage 1B studies the pre-breakout structure, not breakout-bar strength.

Breakout strength / overshoot belongs to a later study.

## Primary structure dimension A — Mean Pairwise Overlap IoU

For each of the five bars, treat the high-low interval as a price interval.

For every unordered pair of bars `i,j`:

`intersection_ij = max(0, min(high_i, high_j) - max(low_i, low_j))`

`union_ij = max(high_i, high_j) - min(low_i, low_j)`

`iou_ij = intersection_ij / union_ij`

Define:

`mean_pairwise_iou = mean(iou_ij)`

across the 10 pairs.

Properties:

- continuous;
- parameter-free;
- directly measures how much the bars trade in the same price region;
- does not require a 60/70/80/90% cutoff.

Higher values mean greater overlap / balance.

## Historical Cage — diagnostic only

Continue to report:

- `coverage80_count`;
- `old_cage = coverage80_count >= 3`.

But this binary rule cannot be promoted in Stage 1B even if a few events look favorable.

It is retained only to bridge the user’s prior indicator.

## Primary structure dimension B — Width Compression

Use the same pre-breakout volatility scale known at `t-1`:

- PRICE_LOG: `scale[t-1]`;
- YIELD_LEVEL: `scale[t-1] * 100`.

Define:

`box_width_atr = box_height / prebreak_scale`

Lower means narrower relative to the market’s current risk unit.

No width cutoff is introduced.

## Primary breakout-health outcomes

Same conceptual outcomes as Stage 1:

1. **Stay outside original box through next 3 closes** — healthy orientation.
2. **Stay outside original box through next 5 closes**.
3. **Favorable extension within next 5 moves** beyond the breakout bar’s favorable extreme.
4. **Favorable extension within next 10 moves**.
5. **Remaining formal-regime life >=20 moves**.
6. **Remaining formal-regime life**.

“Stay outside” is the complement of any close re-entry into the original box.

No composite health score.

## Test A — Overlap standalone information

For each binary health outcome:

- calculate within-market AUC using `mean_pairwise_iou`;
- report equal-market mean / median AUC;
- report markets with AUC >0.5.

Also rank overlap into within-market quintiles and compare Q5 (highest overlap) vs Q1 (lowest overlap).

Expected direction if overlap compression matters:

- higher stay-outside rate;
- higher extension probability;
- greater remaining life.

## Test B — Width standalone information

For each binary health outcome:

- calculate within-market AUC using `-box_width_atr`;
- report equal-market mean / median AUC;
- report markets with AUC >0.5.

Rank width into within-market quintiles and compare Q1 (narrowest) vs Q5 (widest).

## Test C — Incrementality of overlap conditional on width

Within each market × width quintile:

- compare high-overlap vs low-overlap using a **within-cell median split of mean_pairwise_iou**;
- require at least 3 events on each side.

This median split is not a production threshold. It is an identification device for conditional incrementality.

Aggregate:

- equal-cell diagnostic;
- equal-market primary diagnostic using balanced cell weights.

## Test D — Incrementality of width conditional on overlap

Symmetrically:

Within each market × overlap quintile:

- compare narrow vs wide using a within-cell median split of `box_width_atr`;
- require at least 3 events on each side.

Again, the split is diagnostic only.

## Test E — Joint 2D surface

Create a coarse within-market 3×3 rank surface:

- overlap tercile: low / middle / high;
- width tercile: narrow / middle / wide.

Report equal-market health outcomes for populated cells.

Do not select a “best cell” as a rule.

Purpose:

> visualize whether high overlap and narrow width are complementary, redundant, or interact nonlinearly.

## Test F — relationship between dimensions

Report within-market:

- Spearman correlation between overlap IoU and width;
- equal-market mean correlation.

Strong correlation would imply redundancy.

Weak/moderate correlation leaves room for complementarity.

## Temporal robustness

Repeat standalone AUC / endpoint gradients for:

- 2010–2014;
- 2015–2019;
- 2020–2026.

Pre-2010 may be reported descriptively but cannot substitute for the frozen stress slices.

## Direction robustness

Report Markup / Markdown separately.

No direction-specific definition.

## Promotion logic

### Overlap promoted

if it shows:

- AUC / quintile health gradient in the expected direction;
- positive direction in a clear majority of markets;
- no material 2015–2019 inversion;
- useful conditional effect after controlling width.

### Width promoted

under the symmetric criteria.

### Both promoted

only if both retain incremental information.

### Neither promoted

if effects are weak / unstable.

No new threshold tuning follows.

## Non-goals

Stage 1B still does not test:

- breakout-bar strength;
- overshoot size;
- retest depth;
- retest acceptance;
- second-entry / re-expansion;
- FVG;
- sizing;
- stop / invalidation;
- Sharpe optimization.

Those follow only after the pre-breakout structure dimensions are understood.

## Guardrails

- no alternative lookback;
- no alternate overlap metric search after outcomes;
- no width threshold search;
- no breakout-buffer search;
- no market-specific rules;
- no direction-specific rules;
- no future information in the five-bar box;
- first post-entry breakout only;
- one breakout maximum per episode;
- discovery sample conclusions remain in-sample.

## Intended answer

> **With breakout strength removed from the admission rule, do overlapping bars and genuinely narrow width independently identify healthier post-entry breakout structures?**

Refs #78, #80, #76.
