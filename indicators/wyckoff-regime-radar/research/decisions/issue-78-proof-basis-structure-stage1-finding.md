# Issue #78 — Proof-Basis Challenge Stage 1 Finding
## Progress × Entry-Frozen Structure Incrementality

## Scope

This finding executes the frozen preregistration in
`issue-78-proof-basis-structure-stage1-preregistration.md`.

Question:

> **At a comparable amount of directional progress, does breaking a frozen pre-entry 20-close structural boundary add information about future trend continuation?**

The structure definition was frozen before outcomes were inspected:

- Markup: break above the highest reconstructed close from the 20 completed closes preceding entry;
- Markdown: break below the lowest reconstructed close from the same window;
- boundary fixed at entry;
- no swing / pivot / rolling-breakout search.

Primary outcomes are scale-free.

## Sample

Accepted base:

- 68,118 event rows;
- 1,624 completed known-start trend episodes.

Structure reconstruction requires 20 consecutive pre-entry moves:

- 1,341 episodes have valid entry-frozen structure;
- 1,233 survive to the 5-move checkpoint;
- 1,024 survive to the 10-move checkpoint;
- 283 early-history episodes lack the required 20-move pre-entry window.

## Result 1 — Structure looks strongly informative before controlling for progress

Equal-market structure-confirmed minus not-confirmed differences:

### 5 completed moves

- later favorable extension: **+18.7 percentage points**, positive in **8/9 markets**;
- positive future net: **+6.4 pp**, positive in 7/9;
- remaining life >=20 moves: **+29.0 pp**, positive in **9/9**;
- mean remaining regime life: **+15.1 moves**, positive in **9/9**.

### 10 completed moves

- later favorable extension: **+19.6 pp**, positive in 7/9;
- positive future net: **+10.2 pp**, positive in 7/9;
- remaining life >=20: **+30.0 pp**, positive in 8/9;
- mean remaining life: **+15.7 moves**, positive in 8/9.

So structure is not a meaningless visual label.

However, standalone separation is not sufficient because structure confirmation is correlated with directional progress.

## Result 2 — Structure retains some incremental information after controlling for progress

Primary conditional test:

- rank progress into within-market quintiles;
- compare structure-confirmed vs not-confirmed only inside the same progress quintile;
- require at least 3 episodes in each group;
- equal-market aggregation is primary.

### 5 completed moves

Eligible: **9 markets / 34 market-quintile cells**.

Structure-confirmed minus not-confirmed:

- favorable extension: **+5.7 pp**, positive in **8/9 markets**;
- positive future net: **+5.9 pp**, positive in 7/9;
- remaining life >=20: **+15.2 pp**, positive in **8/9**;
- mean remaining life: **+9.3 moves**, positive in **8/9**.

This is real evidence of incrementality.

The 5-move extension effect is not confined to one progress bucket:

- Q1: +1.1 pp;
- Q2: +10.0 pp;
- Q3: +7.2 pp;
- Q4: +9.8 pp;
- Q5: +15.8 pp, but only 2 markets remain identifiable in Q5.

### 10 completed moves

Eligible: 9 markets / 23 cells.

- favorable extension: **+6.3 pp**, positive in 6/9;
- positive future net: **+12.6 pp**, positive in 6/9;
- remaining life >=20: **+17.5 pp**, positive in 7/9;
- mean remaining life: **+10.8 moves**, positive in **8/9**.

The durability signal remains, but identification is already deteriorating because nearly all high-progress episodes have structurally confirmed.

## Result 3 — The main problem is overlap / saturation

Structure is extremely common in the current formal-regime sample.

At the 5-move checkpoint:

- equal-market structure-confirmation rate is about **75.6%**;
- approximately **51.7%** of eligible episodes were already structurally confirmed at the fresh regime-entry close.

By progress quintile, structure-confirmation rate is approximately:

- Q1: 62.3%
- Q2: 63.0%
- Q3: 70.3%
- Q4: 87.0%
- Q5: 95.2%

At the 10-move checkpoint the saturation becomes stronger:

- overall checkpoint structure rate about **88%**;
- Q1: 77.2%
- Q2: 80.5%
- Q3: 89.7%
- Q4: 93.2%
- Q5: **99.5%**.

Therefore the frozen 20-close breakout is increasingly close to a companion description of strong progress rather than an independent late proof state.

At 10 moves there is effectively no high-progress non-breakout comparison left.

## Result 4 — Entry structure and post-entry structure behave differently

This distinction is important.

### Structure already present at entry

Conditional on progress quintile, `structure_at_entry` still shows modest positive durability information.

At 5 moves:

- favorable extension: about **+4.6 pp**, positive in 8/9 markets;
- positive future net: +5.2 pp, positive in 7/9;
- remaining life >=20: **+14.8 pp**, positive in 8/9;
- remaining life: **+7.7 moves**, positive in 7/9.

At 10 moves, the extension effect is weaker, but remaining-life signals stay broadly positive.

This suggests the 20-close relationship may contain **entry-state / regime-initiation quality** information.

### Breakout occurring only after entry

Among episodes **not** already structurally confirmed at entry, a post-entry breakout looks very strong standalone.

But after controlling for progress, the picture is much less stable.

At 5 moves, eligible 8 markets / 18 cells:

- favorable extension: +7.4 pp, but positive in only **4/8 markets**;
- positive future net: +4.4 pp, 4/8;
- remaining life >=20: +16.4 pp, **7/8**;
- remaining life: +10.4 moves, 6/8.

At 10 moves:

- favorable extension: +7.6 pp, only 4/8 positive;
- positive future net: +14.0 pp, 5/8;
- remaining life >=20: +28.9 pp, 5/8;
- remaining life: +14.0 moves, 7/8.

Thus post-entry structural breakout appears more consistently related to **durability / remaining life** than to a clean independent favorable-extension probability.

It does not yet behave like a robust second add-risk key.

## Result 5 — Temporal admission fails because overlap becomes too sparse

The preregistered temporal conditional test is not clean enough to promote this structure definition.

At 5 moves:

- 2010–2014: only 4 eligible markets / 4 cells; favorable-extension and remaining-life conditional effects are mixed;
- 2015–2019: 5 markets / 6 cells; durability is positive, but extension is not broad;
- 2020–2026: 5 markets / 6 cells; mixed across outcomes.

At 10 moves the overlap problem is severe:

- the 2015–2019 conditional comparison has only **1 eligible market / 1 cell**;
- other preregistered eras do not have enough same-progress structure/no-structure overlap for a meaningful universal conclusion.

This is an identification failure, not proof that the true incremental effect is zero.

But under the frozen admission rules it is enough to block policy promotion.

## Result 6 — Direction behavior is broadly compatible but not decisive

At 5 moves, conditional favorable-extension effect is positive in both directions:

- Markdown: about +6.1 pp;
- Markup: about +11.5 pp.

Remaining-life effects are also positive in both directions.

At 10 moves the sample becomes thinner, especially for same-progress non-breakout episodes.

No direction-specific structure rule is justified.

## Research decision

### Supported

1. **Price structure contains information.**
2. The frozen 20-close breakout retains some information after controlling for directional progress, especially about **regime durability / remaining life**.
3. Structure present at entry may encode a distinct regime-initiation quality state.
4. Directional progress is not made redundant by structure.

### Not supported

The frozen entry-20-close breakout does **not** pass the preregistered admission gate as a clean independent **post-entry second add-risk key**.

Reasons:

- more than half the eligible episodes are already structurally confirmed at entry;
- confirmation rises to ~76% by move 5 and ~88% by move 10;
- high-progress non-breakout episodes nearly disappear;
- post-entry breakout conditional effects are mixed for favorable extension;
- temporal conditional overlap is too sparse to establish robust incrementality.

Therefore do **not** run the proposed Two-Key economic policy test from this structure definition yet.

## Interpretation

The result is more nuanced than "structure does not matter."

A better statement is:

> **The current 20-close breakout appears to describe a mixture of entry-state quality and progress-associated trend durability. It is informative, but it is too entangled with the formal regime entry and subsequent progress to serve as a clean second post-entry confirmation key.**

That is exactly the distinction this Stage 1 study was designed to identify.

## Next research question

Do not tune the lookback from 20 to 10 / 30 / 50 on the same sample.

The next useful structure research should target a concept that is structurally different and less mechanically saturated, for example:

- a genuinely **post-entry consolidation / pullback structure** followed by renewed breakout;
- or new logger evidence containing OHLC so swing / range structure can be defined independently of the current close-only regime transition.

A separate, explicitly preregistered study could also test whether **structure-at-entry should alter initial probe size**, because this study found modest conditional durability information there. That is an entry-risk-context question, not the same as post-entry proof.

Refs #78, #80, #76.
