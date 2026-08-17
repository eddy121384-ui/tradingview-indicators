# Issue #57 — Post-retake reseizure behavior map

Status: preregistered reused-data structural diagnostic only. Existing v0.6 is unchanged.

## Question

After a carried/new stage has seized the lead over the old context stage, and the old context later retakes that lead before the bridge resolves, can the new stage regain the lead? If so, does that distinguish a temporary pullback from a failed transition?

## Frozen event definitions

Start from the same non-overlapping bridge watches used by the Issue #57 bridge/handoff diagnostics.

A seizure event is eligible only when, at bridge onset, `carried_weight > context_weight`.

For each eligible seizure:

1. **First retake** = the first pre-resolution bar after onset where `context_weight >= carried_weight`.
2. Only seizure events with a first retake are included in this diagnostic.
3. **First reseizure** = the first later **pre-resolution** bar where `carried_weight > context_weight` again.
4. The original bridge-watch resolution remains unchanged:
   - same-direction actionable pair = success;
   - opposite-direction actionable pair = failure;
   - otherwise 20-bar timeout.
5. The resolution bar itself is not allowed to create a reseizure. This prevents the final answer from being used as its own predictor.

## Frozen checkpoints

After the first retake, inspect whether a reseizure occurs within **1 / 3 / 5 bars**. A checkpoint is eligible only if the original bridge remains unresolved strictly beyond that checkpoint.

No numeric weight threshold is fitted. All comparisons use only strict stage ordering (`carried > context` vs `context >= carried`).

## Outputs

For each FX pair and in pair-median aggregate:

- total retake events;
- fraction with any pre-resolution reseizure;
- median lag from retake to reseizure;
- eventual same-direction completion rate with reseizure vs without reseizure;
- opposite-actionable and timeout rates with reseizure vs without reseizure;
- at +1 / +3 / +5 after retake, future completion rate when reseizure has already occurred vs not yet occurred;
- cross-pair consistency counts.

## Interpretation boundary

This is descriptive reuse of already-used FX fixtures. It may identify a structural transition-health pattern, but it does not establish a trading rule, entry signal, or independent OOS edge. No checkpoint or production threshold will be selected from these data.
