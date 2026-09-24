# Issue #78 — Proof-Basis Challenge Stage 1 Preregistration
## Progress × Entry-Frozen Structure Incrementality

## Purpose

Test whether **price-structure confirmation adds information beyond directional progress** when deciding whether a live Markup / Markdown episode has earned more risk.

This is not a contest in which only one proof family may survive.

The core question is:

> **At a comparable amount of directional progress, does an episode that has also broken a pre-entry structural boundary have better subsequent continuation than one that has not?**

If yes, Progress and Structure may be complementary inputs to a later exposure state machine.

If no, structure may be visually intuitive but redundant with progress and should not be added to the live rule.

## Frozen sample

Reuse the accepted Issue #76 nine-market daily discovery sample:

- 68,118 accepted event rows;
- 1,624 completed known-start Markup / Markdown episodes;
- same frozen formal regime semantics;
- no classifier changes;
- equal-market aggregation primary;
- causal information only.

## Structure definition — one frozen family only

Do not search multiple swing / Donchian / MA / pattern definitions in this pass.

Use an **entry-frozen 20-completed-close range**.

The 20-bar lookback is frozen before outcomes are viewed and is consistent with the already-used pre-entry 20-move window in the Normalizer Challenge.

### Reconstructing closes from the accepted logger

The Issue #76 logger contains one-bar forward close moves (`move1`) rather than a direct close column.

Set the fresh trend-entry close to relative price `0`.

Using only consecutive pre-entry `move1` observations, reconstruct the prior 20 completed closes relative to the entry close.

No external OHLC data are introduced.

### Markup boundary

- resistance = highest reconstructed close among the 20 completed closes immediately preceding the fresh Markup entry;
- structural proof is true once the entry close or any subsequent completed close is strictly above that frozen resistance.

### Markdown boundary

- support = lowest reconstructed close among the 20 completed closes immediately preceding the fresh Markdown entry;
- structural proof is true once the entry close or any subsequent completed close is strictly below that frozen support.

The boundary never moves during the episode.

This is deliberately an **entry-frozen structural level**, not a rolling breakout rule.

## Structure states

Report separately:

- `structure_at_entry`: boundary already broken by the fresh regime-entry close;
- `structure_by_5`: boundary has been broken by entry or within the first 5 completed post-entry moves;
- `structure_by_10`: boundary has been broken by entry or within the first 10 completed post-entry moves;
- `post_entry_structure_by_k`: breakout occurs after entry but by checkpoint `k`, for episodes not already structurally confirmed at entry.

Primary checkpoint tests use the information state actually known by that checkpoint: `structure_by_5` and `structure_by_10`.

## Progress baseline

Keep the Normalizer Challenge decision unchanged:

- entry ATR remains the frozen practical normalizer;
- directional progress is cumulative direction-aligned movement from entry divided by fixed episode-entry ATR.

At checkpoints:

- first 5 completed post-entry moves;
- first 10 completed post-entry moves.

No new ATR threshold is introduced in Stage 1.

Progress is treated continuously and through within-market quintiles.

## Primary outcomes — scale-free

Do not use the ATR-defined Large / Failed label as the primary target.

At each checkpoint, using only future path after the checkpoint:

1. **Future favorable extension** — does the same formal episode later make a new favorable cumulative close-path extreme above the checkpoint-known running extreme?
2. **Positive future net** — is direction-aligned net movement from checkpoint close to formal regime end positive?
3. **Remaining life >=20 moves**.
4. **Remaining life** in completed moves.

The old MFE <4 / >=8 ATR labels may be reported only as a legacy bridge.

## Stage 1A — Standalone structure information

For each market × checkpoint:

- compare scale-free outcomes for structure-confirmed vs not-confirmed episodes;
- report equal-market probability / mean differences;
- report direction and era diagnostics;
- report structure-confirmation prevalence.

This answers whether structure has information at all.

## Stage 1B — Incrementality conditional on progress

This is the primary test.

Within each market and checkpoint:

1. rank directional progress into quintiles;
2. inside each progress quintile, compare structure-confirmed vs not-confirmed episodes;
3. a market × quintile cell is eligible only if both groups contain at least 3 episodes;
4. calculate:
   - future-extension probability delta;
   - positive-future-net probability delta;
   - remaining20 probability delta;
   - mean remaining-life delta.

Aggregate in two ways:

### Equal-cell diagnostic

Equal weight across eligible market × quintile cells.

### Equal-market diagnostic

Within each market, weight eligible quintile-cell deltas by the smaller of the two group counts in that cell, then give each market equal weight.

The equal-market diagnostic is primary.

Report:

- mean conditional delta;
- median market conditional delta;
- markets with positive conditional delta;
- number of eligible markets and cells.

No empty / ineligible cells may be silently imputed.

## Stage 1C — Progress-gradient preservation within structure state

For structure-confirmed and non-confirmed groups separately:

- report Q5 minus Q1 progress gradient for all primary outcomes where endpoint cells are sufficiently populated.

This asks whether progress remains useful even after structure state is known.

The desired complementarity pattern would be:

- structure adds information conditional on progress;
- progress still orders outcomes inside both structure states.

## Stage 1D — Timing / redundancy diagnostics

Report:

- directional-progress distribution when structure first confirms;
- entry-ATR progress at first structural breakout;
- bars from entry to first structural breakout;
- share structurally confirmed at entry;
- share first confirmed by move 5;
- share first confirmed by move 10;
- Spearman association between progress and structure timing where defined.

These are descriptive only in Stage 1.

Do not create a live policy from these timing statistics yet.

## Temporal robustness

Repeat conditional structure deltas in:

- 2010–2014;
- 2015–2019;
- 2020–2026.

2015–2019 remains a required stress era.

No era-specific rule is allowed.

## Direction robustness

Report Markup / Markdown separately.

No direction-specific structural definition is allowed.

## Promotion criteria

Structure is promoted into Stage 2 only if the evidence broadly supports:

1. structure-confirmed episodes show better future continuation at the checkpoint;
2. positive conditional-on-progress effect in a clear majority of eligible markets;
3. the effect is not driven only by one progress quintile;
4. direction behavior is broadly consistent;
5. 2015–2019 does not invert the result materially;
6. sample overlap is sufficient to identify an incremental effect.

A visually intuitive breakout is not enough.

## Stage 2 if promoted

Only after Stage 1 is frozen may a policy comparison be preregistered.

Candidate architecture family:

1. Formal Hold baseline;
2. Progress-only baseline;
3. Structure-only;
4. **Two-Key Proof**:
   - 25% fresh trend exposure;
   - 50% when either Progress or Structure earns its first key;
   - 100% when both keys have been earned;
5. existing Progressive progress-only ladder as an engineering benchmark.

Progress thresholds for Stage 2 must remain frozen / mechanically matched to prior confirmation-cost work.

Structure-only and Two-Key rules may not be tuned after Stage 1 results.

Stage 2 must measure confirmation tax, normalized return, volatility, Sharpe / Sortino, drawdown, left tail, turnover, and equal-vol return.

## Guardrails

- no swing-pivot parameter search;
- no alternative 10 / 30 / 50 / 55-bar breakout search;
- no rolling boundary in this pass;
- no high/low data imported after seeing results;
- no MA / ADX / MACD / RSI additions;
- no market-specific structure definition;
- no long / short-specific structure definition;
- no ATR threshold search;
- no policy PnL / Sharpe optimization in Stage 1;
- no future information in structure state;
- no treating Stage 1 correlation as production validation.

## Intended answer

> **Does breaking an entry-frozen market structure boundary tell us something about future trend continuation that directional progress alone does not?**

Refs #78, #80, #76.
