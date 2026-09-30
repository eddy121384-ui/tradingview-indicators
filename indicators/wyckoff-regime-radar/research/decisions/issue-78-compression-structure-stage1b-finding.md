# Issue #78 — Compression Structure Challenge Stage 1B Finding
## Parameter-free overlap × width under an uncoupled breakout rule

## Scope

This finding executes the frozen preregistration in
`issue-78-compression-structure-stage1b-preregistration.md`.

Stage 1B removed the main Stage 1 confound:

- breakout no longer requires an additional distance proportional to box height;
- a valid Markup breakout is simply a close above the causal prior 5-bar box;
- a valid Markdown breakout is simply a close below it.

The pre-breakout structure remains fully causal and fixed to the five completed bars immediately before the breakout.

Two primary dimensions were tested:

1. **mean pairwise high-low interval IoU** — a continuous, parameter-free overlap measure;
2. **box width / pre-breakout ATR** — width compression.

## Sample

Base sample remains:

- 68,118 accepted Issue #76 event rows;
- 1,624 completed known-start Markup / Markdown episodes.

Post-entry event rule:

- at least five completed post-entry bars first;
- first directional box breakout after that point;
- maximum one breakout per episode.

Stage 1B produced:

- 1,028 accepted post-entry breakout events;
- 383 episodes with no qualifying breakout before formal trend end;
- 213 episodes too short for a scan.

OHLC reconstruction identity error remains effectively zero (~5.6e-14).

Historical old Cage remains extremely sparse even with the uncoupled breakout rule:

- only 4 of 1,028 events satisfy the old 3-of-5 / 80% rule.

Therefore the old binary Cage remains diagnostic only.

## Result 1 — “Narrower” is not supported as the useful structure dimension

Using `-box_width_atr` so higher score means narrower:

Equal-market AUC:

| Outcome | AUC | Markets >0.5 |
|---|---:|---:|
| Stay outside box for 3 closes | 0.478 | 2/9 |
| Stay outside box for 5 closes | 0.480 | 3/9 |
| Favorable extension within 5 moves | 0.455 | 3/9 |
| Favorable extension within 10 moves | 0.463 | 3/9 |
| Remaining formal life >=20 moves | 0.437 | 2/9 |

Narrowest Q1 minus widest Q5 equal-market differences are also mostly negative:

- stay outside 3 closes: -6.8 pp;
- stay outside 5 closes: -6.7 pp;
- extension within 5: -7.1 pp;
- extension within 10: -4.9 pp;
- remaining life >=20: -13.5 pp;
- mean remaining life: -6.7 moves.

The preregistered expected “narrower is healthier” relation is therefore not supported.

This is not a small miss around 0.50; the direction is broadly opposite for continuation / durability metrics.

## Result 2 — High overlap is weakly related to extension, not to acceptance or durability

Mean pairwise IoU standalone AUC:

| Outcome | AUC | Markets >0.5 |
|---|---:|---:|
| Stay outside box for 3 closes | 0.475 | 2/9 |
| Stay outside box for 5 closes | 0.479 | 4/9 |
| Favorable extension within 5 moves | 0.519 | 7/9 |
| Favorable extension within 10 moves | 0.529 | 6/9 |
| Remaining formal life >=20 moves | 0.489 | 4/9 |

So overlap is not a general breakout-health variable.

It shows only a modest positive relationship with subsequent favorable extension.

Endpoint quintiles are not broadly ordered enough to promote overlap standalone.

## Result 3 — Overlap has a small incremental extension signal after controlling width

Within market × width quintile, split overlap high vs low and require at least 3 events per side.

Eligible:

- 9 markets;
- 45 cells.

High-overlap minus low-overlap equal-market conditional differences:

- stay outside 3 closes: **-0.3 pp**;
- stay outside 5 closes: **-1.5 pp**;
- extension within 5 moves: **+4.2 pp**, positive in **7/9 markets**;
- extension within 10 moves: **+2.9 pp**, positive in **6/9**;
- remaining life >=20: +0.9 pp, 5/9;
- mean remaining life: -1.3 moves, 3/9.

Interpretation:

> **At comparable width, heavier overlap may modestly raise the chance of another favorable extension, but it does not make the breakout more likely to stay accepted outside the old box or remain in the formal regime longer.**

That is too narrow an effect to promote overlap as the universal compression definition.

## Result 4 — Width remains negative after controlling overlap

Within market × overlap quintile, compare narrower vs wider halves.

Eligible:

- 9 markets;
- 35 cells.

Narrow minus wide:

- stay outside 3 closes: **-7.9 pp**, positive only 1/9 markets;
- stay outside 5 closes: **-7.1 pp**, 1/9;
- extension 5: **-6.7 pp**, 2/9;
- extension 10: **-6.1 pp**, 2/9;
- remaining life >=20: **-9.0 pp**, 2/9;
- mean remaining life: **-4.5 moves**, 2/9.

So the lack of a narrow-width advantage is not explained by overlap redundancy.

## Result 5 — Overlap and width are related, but not equivalent

Equal-market Spearman between overlap IoU and box width:

- **-0.338**.

Higher overlap tends to occur in somewhat narrower boxes, but the relationship is only moderate.

Therefore the two concepts are distinct enough that the negative Width result is meaningful.

## Result 6 — Temporal robustness fails for Overlap

The modest all-sample overlap-extension signal is not temporally stable.

### 2010–2014

Overlap AUC:

- extension 5: 0.438;
- extension 10: 0.457.

### 2015–2019

- extension 5: **0.385**;
- extension 10: **0.383**;
- remaining life >=20: 0.369.

### 2020–2026

- extension 5: **0.620**;
- extension 10: **0.681**.

Overlap therefore behaves much better in the most recent era and poorly in the earlier frozen stress periods.

That blocks universal promotion.

## Result 7 — Width also fails temporal robustness

Width-compression results remain weak / negative across most frozen eras, with especially poor 2015–2019 continuation AUCs:

- extension 5: 0.354;
- extension 10: 0.382;
- remaining life >=20: 0.353.

There is no temporal case for promoting narrow width.

## Result 8 — Direction diagnostics do not rescue either structure dimension

Overlap:

- Markdown: extension 5 AUC 0.520, extension 10 0.514;
- Markup: extension 5 0.500, extension 10 0.531.

Width:

- both directions remain generally below 0.5 on extension / durability outcomes.

No direction-specific definition is justified.

## 2D surface — descriptive only

The preregistered overlap × width tercile surface does not show a simple “high overlap + narrow width = best” pattern.

Some strong cells occur at medium / wide width, and the highest-overlap / widest cell has strong stay-outside and durability values.

This surface is descriptive only and is **not** used to select a rule.

The main point is that the hoped-for narrow-compression corner does not dominate.

## Research decision

### Width Compression

**Not promoted.**

A narrow 5-bar box relative to ATR does not identify healthier post-entry breakouts in this discovery sample.

Do not search a new width cutoff.

### Pairwise Overlap

**Not promoted as a universal structure gate.**

There is a modest conditional signal for future favorable extension, but:

- no improvement in box acceptance;
- no broad durability advantage;
- clear temporal instability;
- 2015–2019 materially inverts the recent-era behavior.

Do not create an overlap threshold or add-risk gate from this result.

### Historical Cage

**Retired as a universal research candidate.**

The old 3-of-5 / 80% binary definition is too sparse on daily cross-market data.

It may remain a visual indicator feature, but it has not earned a role in the universal exposure engine.

## What this means conceptually

The user’s earlier discretionary observation now becomes more important:

> a good setup may not be defined mainly by how narrow the pre-breakout range was.

The missing information may live in the **breakout path itself**:

- how forcefully price leaves the box;
- whether it immediately expands;
- whether it falls back into the box;
- whether a retest is accepted or rejected;
- whether it re-expands after the retest.

That is consistent with Stage 1B:

- pre-breakout narrowness is weak;
- pre-breakout overlap has only modest extension information;
- neither reliably explains acceptance / durability.

## Next research gate

The next non-redundant study should be **Breakout Quality**.

Primary question:

> **Given the same causal pre-breakout box, does the strength and acceptance of the breakout itself separate healthy continuation from false breakout better than pre-breakout compression geometry?**

Candidate evidence families should be preregistered before results:

1. immediate breakout overshoot relative to ATR and box height;
2. first 1–3 bar directional follow-through;
3. close acceptance outside the box;
4. rapid re-entry into the box as negative evidence.

Only after breakout-quality evidence is understood should the project move to:

> Breakout → Retest → Resume

and formal second-entry research.

Refs #78, #80, #76.
