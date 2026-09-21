# Issue #78 — Breakout Quality Challenge Stage 1 Preregistration
## Immediate strength, follow-through, and acceptance after the first genuine post-entry breakout

## Purpose

The Compression Structure studies found that pre-breakout narrowness and overlap do not reliably define a healthy universal breakout setup.

The next question is therefore moved from **what the box looked like** to **what price does when it leaves the box**.

Primary question:

> **Given the same causal 5-bar pre-breakout box, does breakout strength and early acceptance separate healthy continuation from false breakout better than pre-breakout compression geometry?**

This stage does not yet test retest / second-entry rules or position sizing.

## Frozen sample and breakout event

Reuse the exact Stage 1B event construction:

- accepted Issue #76 nine-market daily discovery sample;
- 68,118 event rows;
- 1,624 completed known-start Markup / Markdown episodes;
- at least five completed post-entry bars must occur before a breakout is eligible;
- 5-bar causal pre-breakout box using bars t-5 ... t-1;
- Markup breakout: close[t] > box_high;
- Markdown breakout: close[t] < box_low;
- first qualifying directional breakout only;
- maximum one breakout event per episode.

Do not change the structure window or breakout admission rule in this study.

Expected event count from Stage 1B: 1,028.

## Causal information sets

Two information sets are frozen separately.

### B0 — Breakout-close information

Known at the close of breakout bar t.

B0 features may only be evaluated against outcomes beginning after t.

### B3 — Early post-breakout information

Known after the next three completed bars t+1 ... t+3.

B3 features may only be evaluated against outcomes beginning after t+3.

This prevents early follow-through / re-entry information from leaking into its own target.

## Frozen scale

Use the pre-breakout volatility scale known at t-1:

- PRICE_LOG: scale[t-1];
- YIELD_LEVEL: scale[t-1] * 100.

This remains fixed for the breakout event.

No new volatility normalizer is introduced.

# Part A — B0 immediate breakout quality

## A1 — Breakout close overshoot

Directional close distance beyond the frozen box boundary:

Markup:
`overshoot = close[t] - box_high`

Markdown:
`overshoot = box_low - close[t]`

Primary normalized feature:

`overshoot_atr = overshoot / prebreak_scale`

Higher = stronger close beyond the old structure.

Also report:

`overshoot_box = overshoot / box_height`

as a secondary engineering diagnostic only because box height was already shown to have its own behavior.

No overshoot threshold is introduced.

## A2 — Directional close location within breakout bar

Use reconstructed high / low / close of breakout bar.

Markup:

`close_location = (close - low) / (high - low)`

Markdown:

`close_location = (high - close) / (high - low)`

Clamp numerically to [0,1].

Higher = breakout bar closes nearer its favorable extreme.

This tests whether a breakout that closes strongly, rather than merely wicking out and fading, is healthier.

## A3 — Breakout bar range

`breakout_range_atr = (high[t] - low[t]) / prebreak_scale`

This is a diagnostic for expansion intensity.

It is not assumed that a larger bar is healthier.

## B0 primary future outcomes

Measured strictly after breakout bar t:

1. **Stay outside box for next 3 closes**
2. **Stay outside box for next 5 closes**
3. **Favorable extension within next 5 moves** beyond breakout-bar favorable extreme
4. **Favorable extension within next 10 moves**
5. **Remaining formal-regime life >=20 moves**
6. **Remaining formal-regime life**

These are the same broad health concepts used in Stage 1B.

# Part B — B3 early acceptance / follow-through

Only breakout events with three completed bars after t are eligible.

## B1 — Outside-close fraction

Across t+1 ... t+3:

`outside_close_fraction3 = number of closes still beyond the original box boundary / 3`

Values: 0, 1/3, 2/3, 1.

Higher = stronger acceptance outside the old box.

## B2 — Worst close acceptance margin

Directional signed distance of the **worst** close among t+1 ... t+3 from the original breakout boundary, normalized by prebreak scale.

Markup:

`min(close[t+1:t+3] - box_high) / scale`

Markdown:

`min(box_low - close[t+1:t+3]) / scale`

Positive means all three closes remain outside.
Negative means at least one close returned inside the old box.

This is the primary continuous false-breakout / acceptance feature.

## B3 — Three-bar follow-through

Directional close displacement from breakout close to t+3 close:

`followthrough3_atr = direction * (close[t+3] - close[t]) / scale`

Higher = stronger net continuation after breakout.

## B4 — Early favorable extension

Favorable extreme achieved during t+1 ... t+3 relative to breakout-bar favorable extreme, normalized by scale.

This is diagnostic because it is closely related to continuation itself.

It cannot be the sole promotion basis.

## B3 future outcomes

All begin strictly **after t+3**.

1. **Future re-expansion within next 5 moves**:
   make a new favorable extreme beyond the best extreme already observed through t+3.
2. **Future re-expansion within next 10 moves**.
3. **Positive future net move** from close[t+3] to formal regime end.
4. **Remaining formal-regime life >=20 moves after t+3**.
5. **Remaining formal-regime life after t+3**.

No outcome may reuse t+1 ... t+3 information.

# Primary analysis

## Test 1 — Immediate overshoot

For `overshoot_atr`:

- within-market AUC for each B0 binary outcome;
- equal-market mean / median AUC;
- markets with AUC >0.5;
- within-market quintile gradients Q5 minus Q1.

This is the primary B0 breakout-strength test.

## Test 2 — Close location incrementality

Control for overshoot strength using within-market overshoot quintiles.

Within each market × overshoot quintile:

- compare high vs low close_location using a within-cell median split;
- require at least 3 events on both sides.

Aggregate equal-market first.

Question:

> **At comparable breakout distance, does closing near the favorable extreme add information?**

## Test 3 — Breakout range incrementality

Symmetric diagnostic:

Within market × overshoot quintile, compare higher vs lower `breakout_range_atr`.

This asks whether expansion bar size adds information beyond where the close finished.

Do not promote range merely because large bars and overshoot are correlated.

## Test 4 — Early acceptance

For B3:

Primary feature = `worst_acceptance_margin3`.

Evaluate:

- within-market AUC;
- quintile gradients;
- equal-market aggregation;
- era and direction diagnostics.

Expected direction: higher margin = healthier continuation.

## Test 5 — Follow-through incrementality beyond acceptance

Within market × acceptance quintile:

- compare high vs low `followthrough3_atr` using within-cell median split;
- require >=3 each side.

Question:

> **Once we know whether price stayed accepted outside the box, does continued directional progress add further information?**

## Test 6 — Acceptance incrementality beyond immediate overshoot

Within market × overshoot quintile:

- compare stronger vs weaker `worst_acceptance_margin3`;
- equal-market aggregation.

Question:

> **Does post-breakout acceptance tell us something that breakout-bar strength alone did not?**

This is central to separating “strong breakout” from “breakout that looked strong but failed immediately.”

# Temporal robustness

Repeat primary AUC / endpoint gradients for:

- 2010–2014;
- 2015–2019;
- 2020–2026.

2015–2019 remains a required stress era.

Pre-2010 may be reported descriptively only.

# Direction robustness

Report Markup / Markdown separately.

No direction-specific thresholds or definitions.

# Promotion logic

## Immediate strong-breakout evidence is promoted

only if `overshoot_atr` and/or close-location evidence shows:

- useful health separation in a clear majority of markets;
- sensible quintile ordering;
- no material 2015–2019 inversion;
- effect not explained entirely by the other B0 feature.

## Acceptance evidence is promoted

only if `worst_acceptance_margin3`:

- strongly separates future re-expansion / future net / durability;
- works across a clear majority of markets;
- survives 2015–2019;
- adds information conditional on breakout overshoot.

## Follow-through is promoted

only if it adds useful information after acceptance is known.

## Failure interpretation

If immediate breakout strength is weak but acceptance is strong, the conclusion is:

> the market does not reveal breakout quality mainly on the breakout bar; it reveals it by whether the new price area is accepted over the next several bars.

If both fail, do not proceed to a second-entry rule from these definitions.

# Non-goals

This stage does not yet test:

- retest depth;
- retest-to-boundary geometry;
- FVG;
- Breakout → Retest → Resume entry;
- exposure sizing;
- stop placement;
- Sharpe / PnL optimization.

# Guardrails

- no changing the 5-bar box;
- no breakout-buffer search;
- no overshoot threshold search;
- no 1 / 2 / 4 / 5-bar acceptance-window search;
- no composite score built after results;
- no market-specific / direction-specific parameters;
- no use of t+1 ... t+3 information in B0 outcomes that overlap those bars beyond the preregistered health summaries;
- B3 outcomes begin only after t+3;
- one breakout event maximum per episode;
- discovery sample conclusions remain in-sample.

## Intended answer

> **Is a healthy breakout recognizable from how strongly it exits the box, how strongly it closes, and—most importantly—whether the market accepts prices outside the old range during the next three bars?**

Refs #78, #80, #76.
