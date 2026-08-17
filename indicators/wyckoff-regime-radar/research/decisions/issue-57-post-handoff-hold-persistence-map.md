# Issue #57 — Post-handoff hold-persistence behavior map

Status: **exploratory / reused-data structural study only**.

This study does not change the v0.6 indicator and does not select a production threshold.

## Question

After a bridge event where the new carried stage has already overtaken the old context stage, does the ability to **keep that lead** make eventual same-direction regime completion more likely?

A second question is whether an old-context **retake** (old context weight becomes >= carried weight before resolution) usually means the attempted transition is failing.

## Frozen definitions before reading results

- Universe: the same seven already-used FX D1 fixtures used by the current Issue #57 behavior-map research.
- Seizure onset: a semantic bridge (`1+2`, `1+3`, `4+5`, `4+6`) where the carried new-direction stage already has strictly greater weight than the old context stage at onset.
- Resolution: reuse the existing non-overlapping 20-bar bridge watch: same-direction actionable pair = success; opposite actionable pair = failure; otherwise timeout.
- Hold checkpoints: **+1 / +3 / +5 / +10 bars** after seizure onset.
- A checkpoint is evaluated only if the bridge is still unresolved at that checkpoint.
- `lead_held_through_checkpoint`: carried weight remains strictly greater than context weight on **every bar** from onset through that checkpoint. Endpoint-only recovery does not count.
- `old_context_retake`: first bar before resolution where context weight becomes greater than or equal to carried weight.
- Primary outcome: eventual same-direction actionable completion inside the original 20-bar watch.

## Interpretation boundary

This is a behavior map on reused historical fixtures. It may generate a candidate state-transition feature, but it cannot independently validate a trading rule. No 1/3/5/10 checkpoint will be chosen as a production rule from these data alone.
