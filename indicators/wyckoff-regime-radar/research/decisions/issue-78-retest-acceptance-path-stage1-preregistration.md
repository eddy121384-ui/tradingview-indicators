# Issue #78 — Retest / Acceptance Path Challenge Stage 1 Preregistration
## No-touch expansion vs retest-hold vs reclaim vs failed acceptance

## Purpose

Breakout Quality Stage 1 established two robust facts:

1. immediate breakout overshoot mainly predicts whether price avoids an immediate false breakout;
2. the stronger continuation evidence appears over the next three completed bars through outside-range acceptance and directional follow-through.

The next question is therefore path-structural rather than scalar:

> **After a genuine breakout, does a causal boundary retest that holds / reclaims produce a continuation profile comparable to immediate expansion, and is it clearly superior to failed acceptance back inside the old range?**

This is the first direct test of the user's discretionary “second-entry” intuition.

It does **not** yet define or backtest an actual second-entry order.

## Frozen base sample and breakout event

Reuse exactly the accepted Breakout Quality Stage 1 event construction:

- Issue #76 nine-market daily discovery sample;
- 68,118 accepted event rows;
- 1,624 completed known-start Markup / Markdown episodes;
- at least five completed post-entry bars before breakout eligibility;
- causal five-bar pre-breakout box using t-5 ... t-1;
- Markup breakout: close[t] > box_high;
- Markdown breakout: close[t] < box_low;
- first qualifying directional breakout only;
- one breakout event maximum per episode.

Expected breakout events: 1,028.

No box or breakout definition changes are allowed.

## Frozen path-observation window

Reuse the already validated Breakout Quality B3 window:

`t+1 ... t+3`

No 1 / 2 / 5 / 10-bar path-window search.

Path state is known only after the close of t+3.

All primary future outcomes begin strictly after t+3.

## Causal boundary interaction

The original frozen box boundary remains fixed.

### Markup

Breakout boundary = `box_high`.

A **boundary touch / retest** occurs if any low during t+1 ... t+3 is <= box_high.

A **close re-entry** occurs if any close during t+1 ... t+3 is <= box_high.

Final B3 acceptance is outside if close[t+3] > box_high.

### Markdown

Breakout boundary = `box_low`.

A boundary touch occurs if any high during t+1 ... t+3 is >= box_low.

A close re-entry occurs if any close during t+1 ... t+3 is >= box_low.

Final B3 acceptance is outside if close[t+3] < box_low.

No ATR distance threshold is used to decide whether a retest happened.

## Frozen four path states

Every breakout event with three completed post-breakout bars is assigned to exactly one mutually exclusive path.

### P0 — No-touch / Immediate Expansion

- no adverse wick touches the breakout boundary during t+1 ... t+3.

Interpretation:

> price leaves the range and does not meaningfully revisit the old boundary during the early acceptance window.

This does not require a minimum follow-through magnitude.

### P1 — Wick Retest / Hold

- at least one adverse wick touches or penetrates the breakout boundary;
- **no close** returns inside the old box during t+1 ... t+3;
- close[t+3] remains outside.

Interpretation:

> old resistance/support is tested intrabar, but closes continue to accept the breakout side.

This is the cleanest causal “retest held” state.

### P2 — Close Re-entry / Reclaim

- at least one close returns inside the old box during t+1 ... t+3;
- close[t+3] is back outside on the breakout side.

Interpretation:

> the breakout temporarily loses acceptance but reclaims the boundary by the end of the frozen three-bar window.

This is a deeper retest / recovery state.

### P3 — Failed Acceptance

- close[t+3] is inside the old box.

Interpretation:

> by the end of the evidence window, the market has not reclaimed the breakout side.

No later outcome is used in assigning P0–P3.

## Descriptive path geometry

For every event report:

- first boundary-touch bar: 1 / 2 / 3 / none;
- first close-re-entry bar: 1 / 2 / 3 / none;
- number of outside closes among t+1 ... t+3;
- deepest directional penetration back through the boundary in ATR units;
- t+3 acceptance margin in ATR units;
- three-bar directional follow-through in ATR units;
- immediate breakout overshoot in ATR units.

These are diagnostics only in Stage 1.

## Primary future outcomes

All begin strictly after t+3.

### O1 — Re-expand within next 5 moves

Does price make a new favorable extreme beyond the best favorable extreme already observed through t+3?

### O2 — Re-expand within next 10 moves

Same definition over the next 10 completed moves.

### O3 — Positive future net move

Is direction-aligned movement from close[t+3] to formal regime end positive?

### O4 — Remaining formal-regime life >=20 moves after t+3

### O5 — Remaining formal-regime life after t+3

No path state uses these outcomes.

## Primary comparisons

### Test A — Path prevalence

Report equal-market and pooled prevalence of P0 / P1 / P2 / P3.

Also report:

- Markup / Markdown;
- 2010–2014 / 2015–2019 / 2020–2026.

The study must first establish whether each path has enough support for inference.

### Test B — Raw future continuation by path

For each market and path report O1–O5.

Primary contrasts:

1. **P1 vs P3** — does wick retest / hold clearly beat failed acceptance?
2. **P2 vs P3** — does reclaim after close re-entry restore useful continuation?
3. **P1 vs P0** — is a clean retest / hold comparable to immediate expansion, or materially inferior?
4. **P2 vs P1** — does deeper close re-entry carry a continuation penalty even if reclaimed by t+3?

Primary aggregation is equal-market.

Only markets with at least 3 observations in both compared states are eligible for a pairwise contrast.

## Test C — Retest-hold vs immediate expansion at comparable three-bar progress

A major confound is that P0 may simply have much stronger directional follow-through.

Therefore, within each market:

1. rank `followthrough3_atr` into quintiles;
2. inside each quintile compare P1 vs P0 where both have at least 3 observations;
3. aggregate balanced cell differences to equal-market contrasts.

Question:

> **At comparable early directional progress, does a clean boundary retest / hold carry a future continuation penalty, advantage, or roughly equivalent profile versus no-touch expansion?**

If P1 remains comparable after matching follow-through, that is evidence that a retest itself is not a sign of weakness.

## Test D — Reclaim value at comparable acceptance margin

P2 and P3 both experienced close re-entry.

Within market × quintiles of deepest boundary penetration / t+3 acceptance geometry, compare reclaimed P2 vs unreclaimed P3 where identifiable.

Question:

> **Does actually reclaiming the boundary by t+3 matter beyond how deep the retest was?**

Because acceptance margin mechanically separates P2/P3 at t+3, this is diagnostic and may suffer limited overlap. Sparse cells must be reported rather than imputed.

## Test E — Immediate breakout strength by path

Report `overshoot_atr` distribution across P0–P3.

This asks whether path state simply restates original breakout strength.

No path is promoted only because its breakout bar was stronger.

## Test F — Temporal and direction robustness

Repeat primary pairwise contrasts in:

- 2010–2014;
- 2015–2019;
- 2020–2026;
- Markup;
- Markdown.

No era / direction-specific path definition.

## Promotion logic

### Retest / Hold path is supported

if P1:

- materially outperforms P3 across primary future continuation outcomes;
- is positive in a clear majority of eligible markets;
- does not collapse in 2015–2019;
- and remains reasonably competitive with P0 after controlling for three-bar follow-through.

This would support the idea that a clean retest can be a valid continuation state rather than a warning.

### Reclaim path is supported

if P2 materially outperforms P3 across markets and eras.

A weaker P2 than P1 would support a graded interpretation:

> wick retest / hold > close re-entry / reclaim > failed acceptance.

### Immediate Expansion is separately supported

if P0 shows strong future continuation without requiring a retest.

This preserves two valid healthy paths rather than forcing all good breakouts through a retest.

## Important falsification

If P1 does not outperform P3, or if its apparent advantage disappears after matching follow-through, do **not** create a second-entry rule from “retest held.”

If P2 does not outperform P3, a mere reclaim by t+3 is not enough evidence.

## Non-goals

Stage 1 does not yet define:

- an executable second-entry trigger;
- a stop location;
- FVG support zone;
- retest depth threshold;
- re-expansion threshold;
- exposure percentage;
- PnL / Sharpe.

Those require a later preregistered economic policy study only if a path survives.

## Guardrails

- no changing the three-bar observation window;
- no alternate boundary-touch buffer;
- no ATR retest threshold;
- no “successful retest” label that uses later re-expansion;
- no market-specific / direction-specific definitions;
- no path-state threshold tuning;
- no excluding weak paths after outcomes are visible;
- no production claim from this discovery sample.

## Intended answer

> **Is the trader intuition “breakout → retest old support/resistance → hold/reclaim → continuation” visible as a causal, cross-market path pattern, and how does it compare with immediate expansion and failed breakout?**

Refs #78, #80, #76.
