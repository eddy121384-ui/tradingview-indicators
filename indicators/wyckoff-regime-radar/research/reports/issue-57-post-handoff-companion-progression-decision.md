# Issue #57 — Post-handoff companion progression decision

Status: burned-data behavior conclusion; no production change.

## Plain conclusion

After the new carried stage has already overtaken the old context stage, the companion stage is **not** a strong early confirmation signal.

Across the fixed +1 / +3 / +5 checkpoints, the most stable descriptive structure is that the carried stage continues to lead the old context stage. When the old context retakes the lead, later completion of the same-direction actionable pair is much less common in the aggregate behavior map.

The companion stage shows only later, weaker confirmation behavior:

- +1: companion rising is only marginally different; companion Top-3 / rank improvement do not help.
- +3: companion rising looks somewhat better, but other companion flags are sparse and unstable.
- +5: companion rising, Top-3, and rank improvement show better future conversion rates than their complements, but samples are small and the pattern was not present consistently at earlier checkpoints.

The continuous successful-vs-unsuccessful comparison tells the same story: successful still-unresolved transitions are primarily characterized by a very dominant carried stage and a much weaker old context stage. Median companion weight/change is tiny and does not show a clean early ramp before completion.

## Working interpretation

The current v0.6 transition path looks more like:

`old context -> carried target seizes control -> carried target keeps control while old context fails to reclaim -> companion may appear later -> full 2+3 / 5+6 completion`

rather than:

`old context -> both new target stages gradually rise together -> full completion`.

Therefore the next useful behavior question is not to fit a companion threshold. It is to study **handoff persistence / context-reclaim failure**: after the carried stage seizes the lead, how does retaining versus losing that lead over subsequent bars relate to transition survival and eventual completion?

## Boundary

This conclusion reuses burned FX fixtures to understand current indicator behavior. It is not independent validation, not a trading entry rule, and does not justify selecting a numeric cutoff.
