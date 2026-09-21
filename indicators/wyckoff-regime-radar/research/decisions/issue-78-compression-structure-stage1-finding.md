# Issue #78 — Compression Structure Challenge Stage 1 Finding
## Historical Cage baseline and first identification check

## Scope

This finding executes the frozen preregistration in
`issue-78-compression-structure-stage1-preregistration.md`.

The study asked whether the user’s prior Shiori Compression Cage semantics:

- 5-bar pre-breakout box;
- at least 3 of 5 bars each spanning >=80% of total box height;
- breakout close beyond the boundary by 20% of box height;

could serve as a universal pre-breakout structure baseline, and whether narrow total box width independently predicted healthier breakout continuation.

The Issue #76 logger was sufficient to reconstruct OHLC coordinates exactly from `move1/mfe1/mae1`; maximum reconstruction identity error was ~5.6e-14.

## Sample

Accepted base:

- 68,118 event rows;
- 1,624 completed known-start Markup / Markdown episodes.

To force a genuinely post-entry setup:

- at least 5 completed post-entry bars had to occur first;
- the first eligible directional breakout after that point was used;
- maximum one breakout event per episode.

Result:

- 898 accepted post-entry breakout events;
- 513 episodes had no qualifying breakout before formal trend end;
- 213 episodes ended before a breakout scan was possible.

## Finding 1 — Historical 3-of-5 / 80% Cage is too sparse

Only **3 of 898** accepted breakout events satisfy the historical binary Cage.

Coverage-count distribution:

- 0 of 5 bars meeting 80% span: 776 events;
- 1 of 5: 111;
- 2 of 5: 8;
- 3 of 5: 3;
- 4 or 5 of 5: 0.

The three Cage events occur in only three markets.

Therefore the historical binary rule is not statistically usable as a universal compression definition in this nine-market daily sample.

The few Cage events did show low immediate re-entry / good short-horizon extension, but the sample is far too sparse for inference.

This is an admission failure, not evidence that overlap itself is useless.

## Finding 2 — The frozen breakout buffer confounds the Width test

The historical breakout rule required:

`close beyond boundary by 0.20 * box_height`

This creates a mechanical asymmetry:

- narrow boxes require only a small absolute breakout displacement;
- wide boxes require a larger displacement before the event is admitted.

Stage 1 therefore found apparent results in which narrower boxes often had *worse* conditional breakout health, including AUCs below 0.5 for several outcomes.

Those results cannot be interpreted cleanly as evidence that width compression is harmful, because the event-admission rule itself becomes stricter as width rises.

In other words:

> **box width is both the feature under test and part of the breakout qualification threshold.**

That violates the intended isolation of structure from breakout strength.

No substantive “narrow vs wide” conclusion is accepted from this Stage 1 Width result.

## Finding 3 — Overlap and width are not identical concepts

Even under the sparse historical Cage:

- `coverage80_fraction` and `box_width_atr` are only modestly negatively associated across markets;
- the few historical Cage events are concentrated in the narrowest width quintile;
- literal common-overlap fraction is much higher in Cage than non-Cage events.

This supports keeping **overlap** and **width** conceptually separate.

But the historical binary rule is too sparse to operationalize that distinction.

## Research decision

### Do not promote the historical binary Cage

The 3-of-5 / 80% rule is retained as historical context only.

It is not promoted into breakout / retest / sizing research.

### Do not interpret the current Width result

Because the 20%-of-box breakout buffer mechanically depends on width, the Stage 1 Width result is treated as an identification failure.

### Open a clean Stage 1B

The next study should:

1. keep the causal 5-bar pre-breakout box;
2. define breakout as the first close strictly outside the box, with **no box-height-dependent buffer**;
3. use a parameter-free continuous overlap statistic rather than the sparse historical binary Cage;
4. keep `box_width_atr` as the separate width dimension;
5. re-run the same breakout-health outcomes and incrementality logic.

A suitable overlap statistic is mean pairwise interval IoU across the five bars:

`intersection(range_i, range_j) / union(range_i, range_j)`

averaged across all 10 bar pairs.

This directly measures how much the bars occupy the same price region and introduces no new threshold.

## What remains frozen

- 5-bar causal pre-breakout window;
- first genuine post-entry breakout only;
- at most one breakout event per episode;
- same nine-market discovery sample;
- same health outcomes;
- equal-market primary aggregation;
- no market / direction-specific parameters;
- no lookback search.

Refs #78, #80, #76.
