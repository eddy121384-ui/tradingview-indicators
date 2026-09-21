# Issue #78 — Breakout Quality Challenge Stage 1 Finding
## Immediate breakout strength vs three-bar acceptance / follow-through

## Scope

This finding executes the frozen preregistration in
`issue-78-breakout-quality-stage1-preregistration.md`.

The event definition is unchanged from Compression Stage 1B:

- same accepted Issue #76 nine-market daily sample;
- same causal five-bar pre-breakout box;
- first genuine post-entry close outside the box;
- at most one breakout event per formal Markup / Markdown episode;
- no breakout-distance buffer;
- 1,028 accepted breakout events.

Two causal information sets were kept separate:

- **B0**: breakout-close information only;
- **B3**: information available only after the next three completed bars, with future outcomes starting after those three bars.

## Result 1 — Immediate overshoot predicts whether the breakout stays out, not whether it keeps trending far

Primary B0 feature:

`overshoot_atr = directional close distance beyond the old box boundary / pre-breakout ATR`

Equal-market AUC:

| B0 outcome | AUC | Markets > 0.5 |
|---|---:|---:|
| Stay outside old box for next 3 closes | **0.6756** | **9/9** |
| Stay outside old box for next 5 closes | **0.6666** | **9/9** |
| Favorable extension within next 5 moves | 0.5292 | 5/9 |
| Favorable extension within next 10 moves | 0.5031 | 4/9 |
| Remaining formal life >=20 moves | **0.5784** | **9/9** |

Q5 minus Q1 overshoot differences:

- stay outside 3 closes: **+41.3 pp**, 9/9 markets;
- stay outside 5 closes: **+39.4 pp**, 9/9;
- extension within 5: +5.0 pp, 6/9;
- extension within 10: ~0 pp;
- remaining life >=20: **+17.1 pp**, 9/9.

Interpretation:

> **A breakout that closes farther beyond the old range is much less likely to fail immediately, but a very large breakout close is not by itself a strong predictor of continued large extension.**

This directly separates “breakout strength” from “trend continuation.”

## Result 2 — Immediate overshoot is temporally robust for false-breakout resistance

Stay-outside AUC by era:

### 2010–2014
- next 3 closes: **0.647**
- next 5 closes: **0.649**

### 2015–2019
- next 3 closes: **0.585**
- next 5 closes: **0.592**

### 2020–2026
- next 3 closes: **0.655**
- next 5 closes: **0.690**

The effect weakens in 2015–2019 but does not invert.

Overshoot’s favorable-extension signal is not temporally stable, reinforcing the narrower interpretation:

> overshoot is primarily evidence that the breakout will **hold outside the box**, not proof of a long continuation by itself.

## Result 3 — Breakout-bar close location has some information but is not a universal candidate

Among observations with a non-zero reconstructed breakout-bar high-low range:

- close-location AUC for extension-5: 0.624;
- extension-10: 0.610;
- stay-outside-3 / 5: ~0.586 / 0.579.

However only **536 / 1,028** breakout events have a usable non-zero reconstructed breakout-bar range.

The missingness is concentrated in several TVC rate series under the current logger feed.

After controlling for overshoot, close location adds only:

- +6.0 pp extension-5, positive in 5/9 markets;
- +5.1 pp extension-10, 5/9;
- essentially no incremental stay-outside effect.

Decision:

> Do not promote close-location as a universal live input from the current dataset.

## Result 4 — Breakout-bar range helps immediate acceptance a little, not continuation

Within the same valid 536-event subset, larger breakout range conditional on overshoot adds approximately:

- **+6.9 pp** stay-outside-3, 7/9 markets;
- **+7.5 pp** stay-outside-5, 6/9;
- negative / mixed incremental extension.

This is useful descriptive evidence that an expansion bar may help the breakout hold, but it does not justify a separate universal gate.

## Result 5 — Three-bar acceptance is materially stronger continuation evidence

B3 population:

- 997 breakout events remain in the same formal episode through the next three completed bars.

Primary B3 feature:

`worst_acceptance_margin3`

= the worst directional close margin from the old box boundary over t+1 ... t+3, normalized by pre-breakout ATR.

Positive means every close remained outside the old box.
Negative means at least one close re-entered the old range.

Equal-market AUC for future outcomes **after t+3**:

| Future outcome | AUC | Markets >0.5 |
|---|---:|---:|
| Re-expand within next 5 moves | **0.6422** | **9/9** |
| Re-expand within next 10 moves | **0.6515** | **9/9** |
| Positive net move to formal regime end | 0.5290 | 6/9 |
| Remaining formal life >=20 moves | **0.6495** | **9/9** |

Q5 minus Q1:

- future re-expansion 5: **+36.2 pp**, 9/9;
- future re-expansion 10: **+36.4 pp**, 9/9;
- positive future net: +8.7 pp, 7/9;
- remaining life >=20: **+34.0 pp**, 9/9;
- mean remaining life: **+9.6 moves**, 9/9.

This is substantially stronger and broader than the pre-breakout compression variables.

## Result 6 — Acceptance is temporally robust

Future re-expansion AUC from `worst_acceptance_margin3`:

### 2010–2014
- next 5: **0.612**
- next 10: **0.622**

### 2015–2019
- next 5: **0.621**
- next 10: **0.702**

### 2020–2026
- next 5: **0.683**
- next 10: **0.678**

Unlike the prior overlap-compression result, the signal does **not** collapse in 2015–2019.

Both Markup and Markdown also show re-expansion AUC around 0.64–0.66 with 9/9 market direction on the main re-expansion outcomes.

## Result 7 — Acceptance adds large information beyond breakout overshoot

This is the central incrementality test.

Within market × overshoot quintile, compare stronger vs weaker three-bar acceptance.

Equal-market conditional differences:

- future re-expansion 5: **+22.1 pp**, **9/9 markets**;
- future re-expansion 10: **+20.7 pp**, **9/9**;
- positive future net: +7.3 pp, 7/9;
- remaining life >=20: **+21.2 pp**, **9/9**;
- mean remaining life: **+8.1 moves**, **9/9**.

Therefore:

> **Three-bar acceptance is not merely a delayed restatement of “the breakout bar was strong.”**

It is a distinct second layer of evidence.

## Result 8 — Three-bar directional follow-through is even stronger

Feature:

`followthrough3_atr`

= directional close displacement from breakout close to the close three bars later, normalized by the same pre-breakout scale.

Equal-market AUC:

- future re-expansion 5: **0.7170**, 9/9 markets;
- future re-expansion 10: **0.7064**, 9/9;
- positive future net: 0.5293, 7/9;
- remaining life >=20: **0.6589**, 9/9.

Q5 minus Q1:

- re-expansion 5: **+53.0 pp**, 9/9;
- re-expansion 10: **+45.6 pp**, 9/9;
- remaining life >=20: **+37.7 pp**, 9/9;
- mean remaining life: **+13.6 moves**, 9/9.

Temporal re-expansion AUC is also stable:

- 2010–2014: ~0.674 / 0.665;
- 2015–2019: ~0.688 / 0.738;
- 2020–2026: ~0.733 / 0.744.

## Result 9 — Follow-through adds information even after acceptance is known

Within market × acceptance quintile:

High vs low follow-through produces:

- future re-expansion 5: **+25.4 pp**, **9/9 markets**;
- future re-expansion 10: **+18.0 pp**, **9/9**;
- positive future net: +1.8 pp, 5/9;
- remaining life >=20: **+8.7 pp**, 8/9;
- mean remaining life: +4.4 moves, 7/9.

Acceptance and follow-through are correlated, but not redundant.

Equal-market Spearman:

- acceptance vs follow-through: ~0.77;
- acceptance vs outside-close fraction: ~0.88.

The continuous acceptance margin and follow-through therefore represent closely related but still incrementally distinct aspects of post-breakout behavior.

## Result 10 — Immediate overshoot and later follow-through are almost orthogonal

Equal-market Spearman:

- overshoot vs worst three-bar acceptance: ~**0.387**;
- overshoot vs outside-close fraction: ~0.323;
- overshoot vs three-bar follow-through: ~**0.028**.

This is an important structural result.

A breakout that is dramatic on day t is **not** necessarily the same breakout that continues progressing over the next three bars.

That supports treating:

1. **Immediate Expansion**
2. **Post-Breakout Acceptance / Follow-through**

as different evidence paths.

## Research decision

### Promote: Immediate overshoot, but only with narrow semantics

`overshoot_atr` is promoted as a **false-breakout resistance / immediate acceptance** variable.

It is not promoted as a standalone long-continuation proof.

### Promote: Three-bar acceptance

`worst_acceptance_margin3` passes the Stage 1 admission gate as a primary post-breakout evidence family.

Reasons:

- strong future re-expansion and durability separation;
- 9/9 market consistency on primary outcomes;
- no 2015–2019 collapse;
- both directions behave consistently;
- large incremental effect after controlling immediate overshoot.

### Promote: Three-bar follow-through

`followthrough3_atr` also passes.

It is the strongest continuation variable in this stage and retains material incremental information after acceptance is known.

### Do not promote: Breakout-bar close location / range as universal inputs

Current cross-market data coverage is incomplete and their incremental value is narrower.

## Updated market-behavior interpretation

The current evidence supports the user’s discretionary intuition in a more precise form:

> **A strong breakout bar mainly tells us the move is less likely to fail immediately. The stronger continuation evidence arrives from what the market does after the breakout: whether it can remain accepted outside the old range and continue making directional progress over the next several bars.**

This creates two valid proof paths rather than one:

### Path A — Immediate Expansion
A large directional overshoot reduces immediate false-breakout risk.

### Path B — Acceptance / Follow-through
Even after controlling the original breakout strength, staying accepted outside the old box and continuing directionally over the next three bars materially improves future re-expansion and trend durability.

## What this does NOT yet prove

This study does not yet distinguish:

- healthy shallow retest of the boundary;
- deeper retest that temporarily re-enters the box but then recovers;
- failed breakout that is accepted back inside the old box;
- Breakout → Retest → Resume second-entry timing.

Those require an explicit retest state model.

## Next research gate

The next study should therefore be:

> **Retest / Acceptance Path Challenge — after a breakout, when price revisits the old boundary, which paths represent healthy testing and which represent true failed acceptance?**

The preregistered next-stage candidates should distinguish at least:

1. **Immediate Expansion** — no meaningful retest before further extension;
2. **Boundary Retest / Hold / Resume** — price revisits the old boundary, holds / recovers, then re-expands;
3. **Failed Breakout** — price is accepted back inside the old box and does not promptly reclaim the breakout direction.

Only after these paths are causally defined should a “second entry” sizing rule be tested.

Refs #78, #80, #76.
