# Issue #57 — Post-handoff companion progression map

Status: preregistered burned-data behavior study. Existing v0.6 remains unchanged.

## Question

After a semantic bridge has formed and the carried new-direction stage already leads the old context stage, what happens next in the still-unresolved cases? In particular, does companion-stage development mechanically distinguish bridges that later complete the same-direction actionable pair?

## Frozen population

- Use the existing seven burned FX daily fixtures and the current Issue #57 v0.6 price-only core.
- Start from non-overlapping semantic bridge watches: bull `1+2` / `1+3`, bear `4+5` / `4+6`.
- Keep only bridge onsets where the carried target weight is already greater than the old context weight.
- Checkpoints are fixed at +1, +3, and +5 bars after onset.
- At a checkpoint, include only watches not already resolved by a same-direction or opposite actionable pair before or at that checkpoint.

## Frozen checkpoint features

For the original context / carried / companion stage identities:

1. companion weight change from onset;
2. old-context weight change from onset;
3. carried weight change from onset;
4. companion-minus-context margin and its change from onset;
5. whether companion weight is rising;
6. whether companion is positive and tie-aware Top-3 at the checkpoint;
7. whether companion overtakes the old context stage;
8. whether old context is falling while companion is rising;
9. whether the companion's tie-aware rank improves from onset;
10. whether the carried stage still leads the old context stage.

No numeric weight cutoff is selected or fitted.

## Frozen outcomes

From each checkpoint, scan forward and resolve on the first actionable pair encountered:

- success = same-direction actionable pair appears first;
- failure = opposite actionable pair appears first;
- otherwise unresolved through the horizon.

Report success within the next 5 and 10 bars. Compare each mechanical feature `yes` vs `no`, with total counts and median per-pair rates. Also compare successful vs non-successful checkpoint rows using the continuous weight/margin changes.

## Interpretation boundary

This is repeated exploration of already-burned data to understand current indicator behavior. It may generate hypotheses about a transition-alert mechanism, but it cannot validate a production entry rule and must not be used to fit a numeric threshold.
