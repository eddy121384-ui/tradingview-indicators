# Issue #57 — Formation-path behavior map (burned data)

Status: **PREDECLARED DESCRIPTIVE CATEGORIES — NOT A PRODUCTION RULE**

Purpose: understand whether the *path* Candidate + Secondary take into a new actionable Top-2 pair carries more information than static consensus strength or generic concentration speed.

The same seven already-burned FX fixtures may be reused because this is behavior mapping of the existing v0.6 indicator, not independent validation or parameter optimization.

## Event

An event is the first bar of a consecutive actionable Top-2 episode:

- bullish actionable pair = stages `2 + 3` in either rank order;
- bearish actionable pair = stages `5 + 6` in either rank order.

Each episode contributes one onset only.

## Precursor

Use **only the immediately preceding bar's Top-2 stage IDs**. Do not search a fitted historical window for a prettier path.

The prior pair is assigned to exactly one category, in this precedence order:

### 1. `semantic_context_bridge`

A Wyckoff-semantic bridge into the actionable family:

- new bull `2+3`: prior Top-2 is `1+2` or `1+3`;
- new bear `5+6`: prior Top-2 is `4+5` or `4+6`.

Interpretation: accumulation/distribution context hands off directly into the corresponding directional/re-directional pair while carrying one eventual stage forward.

### 2. `opposite_actionable_flip`

A direct flip from the opposite actionable family:

- new bull `2+3`: prior Top-2 is `5+6`;
- new bear `5+6`: prior Top-2 is `2+3`.

### 3. `one_stage_carry_other`

The prior Top-2 shares exactly one stage with the new actionable pair, but is not one of the semantic context bridges above.

### 4. `both_stages_new`

The prior Top-2 shares no stage with the new actionable pair and is not the direct opposite-actionable pair above.

The same actionable pair on the prior bar cannot be an onset by construction.

## Outcomes

For each category, report descriptively:

- event count;
- episode duration;
- survival at 5 / 10 / 20 bars;
- direction-aligned return at 5 / 10 / 20 bars from onset close;
- direction-aligned MFE and MAE over 10 bars;
- Formal direction at onset: aligned / neutral-transition / opposite;
- if Formal is not aligned at onset, adoption within 5 / 10 / 20 bars and median lag when adopted within 20.

Also report pair-level results and pair-median aggregates so one FX pair cannot silently dominate the conclusion.

## Interpretation boundary

This study may identify a structural pattern worth understanding. It may **not** promote a category into a trading rule merely because its burned-data return is highest.

No thresholds, lookbacks, weights, Pine logic, or production output may be changed from this behavior map alone.
