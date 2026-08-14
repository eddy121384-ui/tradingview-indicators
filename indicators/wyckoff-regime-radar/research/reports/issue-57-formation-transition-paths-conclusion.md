# Issue #57 — Formation transition-path conclusion

Status: **PATH STRUCTURE IS DESCRIPTIVE, BUT ACTIONABLE-PAIR ONSET APPEARS TOO LATE FOR EARLY TRANSITION DETECTION**

Decision tag:

`formation_path_structure_found_actionable_onset_too_late_for_leading_signal`

This study uses only the seven already-burned FX fixtures to understand the existing v0.6 indicator. No production logic is changed.

## What was tested

Each first bar of a new actionable Top-2 episode (`2+3` bullish or `5+6` bearish) was classified only by the immediately preceding bar's Top-2 pair. Categories were fixed before outcomes were run:

- semantic context bridge: `1+2 / 1+3 -> 2+3` or `4+5 / 4+6 -> 5+6`;
- direct opposite actionable flip: `5+6 -> 2+3` or `2+3 -> 5+6`;
- other one-stage carry;
- both stages new.

## Main findings

### 1. Transition path does affect the indicator's regime shape

The semantic context bridge appeared 37 times across all seven FX pairs and had a median pair-level episode duration of about **4 bars**, versus about **2 bars** for the much more common other one-stage-carry path (219 events).

This suggests the stage path contains descriptive information about how the indicator transitions, rather than every `2+3` / `5+6` onset being equivalent.

### 2. But the semantic bridge is not a clean directional trading signal

The semantic bridge had a positive median-pair 5-bar aligned return of about **+0.42%**, but this did not persist: the 10-bar return was about **-0.69%** and the 20-bar return about **-0.22%**. Ten-bar MAE (~1.49%) also exceeded MFE (~1.07%).

So this path should not be promoted into a trading entry rule from burned-data results.

### 3. No direct one-bar bull-to-bear / bear-to-bull actionable flips occurred

Across all seven FX fixtures there were **zero** direct `2+3 <-> 5+6` flips.

That is a useful structural observation: the indicator normally passes through a mixed/context configuration before the opposite actionable family forms, rather than instantly switching between fully directional Top-2 pairs.

### 4. The important problem: actionable-pair onset is probably too late

At the moment the new `2+3` or `5+6` actionable pair first appeared, Formal was already aligned in most cases:

- semantic context bridge: median pair Formal-aligned-at-onset rate **100%**;
- other one-stage carry: about **92%**.

This means the event definition itself is often occurring after the regime transition has already been recognized by Formal. Therefore it cannot be the early warning that the original trading intuition is looking for.

## Decision

Do not tune actionable-pair strength, persistence, or precursor category into a new entry rule.

The next research should move **one step earlier in the transition path** and ask:

> When a context bridge first appears — `1+2 / 1+3` on the bullish side or `4+5 / 4+6` on the bearish side — how often does it subsequently become `2+3 / 5+6`, how quickly, and what is Formal doing at that earlier moment?

That earlier bridge-onset event is a better candidate for the user's intended "the market was messy and is now starting to organize" moment.

Suggested next behavior map:

- first appearance of bullish bridge `{1,2}` or `{1,3}` after not being in a bullish bridge;
- first appearance of bearish bridge `{4,5}` or `{4,6}` after not being in a bearish bridge;
- conversion to matching actionable pair within 1 / 3 / 5 / 10 bars;
- time to conversion;
- Formal state at bridge onset and at conversion;
- price path / MFE / MAE after bridge onset;
- distinguish bridges that later convert from bridges that fail and dissolve.

No production threshold or rule is changed. PR #58 remains Draft and Issue #57 remains open.
