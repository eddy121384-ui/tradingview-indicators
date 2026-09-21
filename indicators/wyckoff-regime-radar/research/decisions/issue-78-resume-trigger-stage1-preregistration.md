# Issue #78 — Resume Trigger Challenge Stage 1 Preregistration
## Frozen retest anchors, trigger coverage, confirmation tax, and post-trigger health

## Purpose

Retest / Acceptance Path Stage 1 established that:

- P0 Immediate Expansion is a healthy path;
- P1 Wick Retest / Hold is a valid continuation state;
- P2 Close Re-entry / Reclaim is a meaningful recovery state;
- P3 Failed Acceptance is negative evidence.

The next question is narrower:

> **Once P1 or P2 is known at t+3, what causal event should count as “the trend has resumed” for a possible second add-risk step?**

This stage compares multiple resume definitions without yet assigning position size or PnL.

A key design problem is recursive waiting: if every new pullback resets the level to beat, a rule can chase the market forever.

Therefore all resume anchors are **frozen once at t+3**. They never reset. Each breakout / retest episode gets at most one resume trigger per definition.

## Frozen base population

Reuse the exact Retest / Acceptance Path Stage 1 construction.

Eligible states:

- P1 Wick Retest / Hold;
- P2 Close Re-entry / Reclaim.

The path state is known at the close of t+3.

Expected pooled population:

- P1 = 110;
- P2 = 126;
- total = 236.

P0 is not a second-entry candidate because no retest occurred.
P3 is negative evidence and is not eligible for a resume trigger.

## Frozen scale

Use the same pre-breakout volatility scale known at t-1:

- PRICE_LOG: scale[t-1];
- YIELD_LEVEL: scale[t-1] * 100.

Keep it fixed through the episode.

## One-shot / non-recursive rule

At t+3:

1. identify the path state P1 or P2;
2. freeze all reference levels described below;
3. begin scanning from t+4;
4. the first trigger event for each definition is recorded;
5. once recorded, that definition stops;
6. no later pullback may reset or replace the reference level.

If a trigger never occurs before formal-regime end, record **no trigger**.

This explicitly prevents the “breakout → pullback → new breakout → new pullback → reset forever” loop.

# Resume candidates

## R1 — Frozen Favorable Close Extreme

Freeze the best favorable **close** observed from breakout bar t through t+3.

Markup:

`close_anchor = max(close[t:t+3])`

Trigger:

`first close after t+3 > close_anchor`

Markdown:

`close_anchor = min(close[t:t+3])`

Trigger:

`first close after t+3 < close_anchor`

Interpretation:

> the market must prove a new favorable closing extreme beyond everything already known through the retest window.

This is the cleanest close-based confirmation baseline.

## R2 — Frozen Favorable Price Extreme

Freeze the best favorable **intrabar price extreme** observed from t through t+3.

Markup:

`price_anchor = max(high[t:t+3])`

Trigger:

`first later bar with high > price_anchor`

Markdown:

`price_anchor = min(low[t:t+3])`

Trigger:

`first later bar with low < price_anchor`

The trigger bar is treated as known by bar close for all outcome alignment.

Interpretation:

> earliest structural re-expansion beyond the full known favorable extreme.

This should generally trigger earlier than R1 but may admit more wick-only false resumes.

## R3 — Frozen Retest-Segment Structure Break

Let `r` be the first boundary-touch bar inside t+1 ... t+3.

Freeze only the retest segment `r ... t+3`.

Markup:

`retest_structure_anchor = max(high[r:t+3])`

Trigger:

`first close after t+3 > retest_structure_anchor`

Markdown:

`retest_structure_anchor = min(low[r:t+3])`

Trigger:

`first close after t+3 < retest_structure_anchor`

Interpretation:

> break the local structure created by the retest itself.

This is intentionally easier than requiring a break of the entire pre-retest favorable extreme when the original breakout ran far before pulling back.

The anchor is frozen at t+3 and never updated.

## R4 — Frozen +0.5 ATR Progress Resume

Reuse the smallest already-established Confirmation Tax landmark.

From close[t+3]:

Markup trigger:

`first close >= close[t+3] + 0.5 * scale`

Markdown trigger:

`first close <= close[t+3] - 0.5 * scale`

No 0.25 / 0.75 / 1.0 ATR search is allowed in this stage.

Interpretation:

> momentum/progress benchmark rather than structural confirmation.

## R0 — No-extra-confirmation benchmark

This is not a trigger rule.

It represents acting immediately at the close of t+3 once P1/P2 state is known.

R0 is used only to measure confirmation tax paid by R1–R4.

# Primary trigger metrics

For each rule and path state:

## T1 — Trigger coverage

Share of P1/P2 episodes that trigger before formal regime end.

Also report no-trigger rate.

## T2 — Confirmation delay

For triggered episodes:

- bars from t+3 to trigger;
- median;
- equal-market mean;
- fraction triggered within 3 / 5 / 10 bars.

These windows are descriptive reporting landmarks, not alternate trigger definitions.

## T3 — Progress paid before confirmation

Directional close progress from close[t+3] to trigger close, normalized by fixed scale.

For R2, which can trigger by wick, also report:

- trigger-bar close progress;
- favorable intrabar progress at trigger.

## T4 — Remaining regime life at trigger

For triggered episodes:

- remaining formal-regime bars;
- share with >=10 bars remaining;
- share with >=20 bars remaining.

This measures whether a trigger arrives while useful trend runway remains.

# Primary post-trigger health outcomes

Measured strictly after the trigger bar.

## H1 — Re-expand within next 5 moves

Make a new favorable extreme beyond the best favorable extreme known through the trigger bar.

## H2 — Re-expand within next 10 moves

Same over 10 completed moves.

## H3 — Old-box failure within next 3 closes

Adverse outcome:

- Markup: any next-3 close <= original box_high;
- Markdown: any next-3 close >= original box_low.

This tests whether the resume was quickly rejected back into the old range.

## H4 — Remaining formal-regime life >=10 moves

## H5 — Remaining formal-regime life >=20 moves

## H6 — Remaining formal-regime life

No PnL is computed.

# Confirmation-tax diagnostics

Relative to R0 at t+3, for triggered episodes report:

## C1 — Delay bars

As above.

## C2 — Favorable close-path move consumed before trigger

Directional close progress from t+3 to trigger / scale.

## C3 — Fraction of eventual favorable close-path excursion already consumed

Let:

- `best_future_close` = best favorable close from t+3 through formal regime end;
- `available_close_excursion` = favorable distance from close[t+3] to best_future_close;
- `consumed_close_excursion` = favorable distance from close[t+3] to trigger close.

When available excursion > 0:

`confirmation_tax_fraction = consumed / available`

Clamp only for descriptive reporting if numerical noise produces tiny violations; do not use this as a trigger feature.

# Primary comparisons

## Test A — Coverage vs quality frontier

For R1–R4 report:

- trigger coverage;
- median delay;
- H1–H6.

The key tradeoff is:

> **How much false-resume protection / future health is bought by how much missed opportunity and how many never-triggered episodes?**

Do not select a winner from raw future health alone.

## Test B — R3 Retest-Structure Break vs R1 Full Close Extreme

This is the main test of the user's recursive-wait concern.

Question:

> **Does freezing and breaking only the retest segment produce materially earlier / broader entry while preserving post-trigger health relative to waiting for a full new favorable close extreme?**

Primary diagnostics:

- coverage difference;
- delay difference;
- confirmation-tax difference;
- H1/H2/H3;
- remaining life.

## Test C — R2 Price Extreme vs R1 Close Extreme

Measures confirmation tax of close confirmation.

Question:

> **How much earlier is wick/price re-expansion, and how much false-resume risk does that buy?**

## Test D — R4 Progress Resume vs structural triggers

Asks whether a simple fixed progress proof performs similarly to more interpretable structure triggers.

If R4 is just as robust, the extra structural complexity may not be justified.

# Path-specific analysis

Report P1 and P2 separately.

No path-specific trigger definition is allowed.

Important question:

> **Does P2 deep reclaim need materially stronger confirmation than P1 clean hold, or do the same frozen triggers work across both?**

No separate rule may be created from this discovery result.

# Temporal robustness

Repeat the primary coverage / delay / H1–H5 summaries for:

- 2010–2014;
- 2015–2019;
- 2020–2026.

Pre-2010 may be reported descriptively only.

2015–2019 remains the required stress era.

# Direction robustness

Report Markup and Markdown separately.

No direction-specific resume rule.

# Promotion logic

A resume definition may advance only if it has:

1. meaningful trigger coverage;
2. acceptable confirmation delay / tax;
3. strong post-trigger re-expansion and low old-box failure;
4. useful remaining trend runway;
5. broad market consistency;
6. no material 2015–2019 collapse;
7. no dependence on path-specific tuning.

A stricter trigger is **not** automatically better if it achieves better conditional outcomes mainly by refusing to trigger.

## Specific R3 admission question

R3 is especially interesting if it:

- triggers materially earlier / more often than R1;
- has comparable H1/H2;
- does not materially worsen H3;
- preserves more remaining regime life.

That would directly address the concern that “wait for a full new extreme” can arrive too late or never arrive.

# Non-goals

This stage does not yet:

- assign a second-entry position size;
- optimize stop placement;
- add FVG;
- search retest-depth thresholds;
- search progress thresholds;
- maximize Sharpe / PnL.

Economic policy testing waits until the resume trigger is selected or a frontier is retained.

# Guardrails

- all anchors frozen at t+3;
- no anchor reset after later pullbacks;
- one trigger maximum per definition per episode;
- no trigger horizon chosen after results;
- no alternate swing lookback;
- no market / direction-specific rules;
- no post-hoc trigger threshold search;
- no future outcome used to define resume;
- discovery-sample results remain in-sample.

## Intended answer

> **After a valid retest / reclaim, which one-shot resume definition confirms renewed directional control early enough to be useful without turning into either a recursive waiting loop or a weak false-resume trigger?**

Refs #78, #80, #76.
