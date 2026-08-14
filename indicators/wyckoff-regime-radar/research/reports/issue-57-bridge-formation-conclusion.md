# Issue #57 — Early bridge formation simple conclusion

Status: **BRIDGE STATE ALONE IS TOO BROAD; INTERNAL HANDOFF STRUCTURE IS PROMISING**

Decision tag:

`bridge_state_low_conversion_internal_context_to_target_handoff_promising`

This is a burned-data behavior study of the existing v0.6 price-only indicator. No production rule or threshold is changed.

## 1. Bridge states are common but usually do not mature

A bridge was defined before outcomes as:

- bullish: Candidate + Secondary = `1+2` or `1+3`;
- bearish: Candidate + Secondary = `4+5` or `4+6`.

Across seven FX pairs there were 298 non-overlapping bridge watches.

Median pair conversion to the same-direction actionable pair was only:

- 5 bars: 5.00%;
- 10 bars: 9.52%;
- 20 bars: 14.29%.

Median pair opposite-actionable-first rate was 21.62%; timeout rate was 64.29%. Therefore merely seeing a bridge pair is not a strong transition signal.

## 2. Top2 total strength does not separate success from failure

Successful-within-10 and unsuccessful bridge states both had almost identical Top2 combined strength:

- success: 99.87;
- no success: 99.92.

So the useful information is not simply whether Candidate + Secondary are jointly very strong.

## 3. The internal handoff is the interesting structure

At bridge onset, successful-within-10 cases looked very different internally:

- context stage (`1` for bull / `4` for bear) median weight: 10.59 vs 77.19 in failures;
- target actionable-family (`2+3` bull / `5+6` bear) median weight: 87.71 vs 19.24;
- six-stage entropy: 0.066 vs 0.166.

In plain language, a successful bridge is usually not "Accumulation/Distribution is still dominant and one directional stage appears." It is closer to:

> **the old context stage has already yielded most of its weight to the new directional family, while one missing companion stage has not quite climbed into the Top2 yet.**

That suggests the next object to study is the **handoff / rank-crossing process** between the fading context stage and the missing companion stage, not a fixed Top2-strength threshold.

## 4. Price behavior is consistent with the structural split, but is not independent proof

Successful-within-10 bridges had better historical price paths on the same burned sample:

- 10-bar aligned return: +0.60% vs -0.19%;
- 10-bar MFE: 1.60% vs 0.89%;
- 10-bar MAE: 0.80% vs 1.14%.

Because success/failure is defined using future indicator evolution on already-observed data, these numbers are descriptive and cannot be treated as a validated entry rule.

## Simple conclusion

- `1+2 / 1+3 / 4+5 / 4+6` by itself is too noisy to be the early-transition alert.
- Top2 combined strength is also not the discriminator.
- The promising mechanism is **internal weight transfer**: context stage falls while the target actionable family takes over.
- Next research should measure the missing companion stage approaching/overtaking the context stage (gap, gap velocity, rank crossing) and determine whether that identifies the small subset of bridge states that genuinely mature.

PR #58 remains Draft. Issue #57 remains open. No production logic changed.
