# Issue #68 Phase B3.14 — Break Evidence Memory Audit preregistration

Status: diagnostic only / frozen C-2 / no performance use.

## Question

When Break is the final negative S2-vs-S5 component immediately before an exact fresh-trend raw handoff, is the negative Break edge mainly caused by **old-side evidence persisting**, **new-side evidence not yet appearing**, or both?

## Frozen scope

Use the same frozen four-FX fixtures, same reciprocal transforms, same 373 exact S2/S5 raw handoffs and same B3.10 handoff detector.

Production C-2 is unchanged.

No change to:
- `breakoutBars`;
- MA lengths;
- breakout/breakdown modes;
- range-break formulas;
- Break weight;
- any threshold;
- lifecycle / Core Bias / Exposure;
- Volume / MTF / Divergence / HMM;
- performance/PnL.

## Existing Break decomposition

Fresh Bull Break score is the existing `breakoutScore`; fresh Bear Break score is the existing `explicitBreakdownScore`. The S2-vs-S5 Break edge is their weighted difference and remains unchanged.

Each side's score is sourced from existing evidence only:

- range-break evidence;
- MA-cross / current-MA-side evidence;
- breakout/breakdown mode override.

No new proxy evidence may be invented.

## Anchored population

Primary attribution population:

- exact B3.10 S2/S5 raw handoffs;
- previous bar `t-1`;
- Break must be the B3.10 final blocker on that handoff.

This population was observed as 106/373 in B3.10 and must be mechanically reproduced, not hard-coded.

## Attribution labels

For each Break-final-blocker event at `t-1`, orient evidence to the new target direction.

Classify:

1. `OLD_MEMORY_ACTIVE`
   - an existing opposite-side recent range-break and/or recent MA-cross event is still active and contributes to the old-side Break score.

2. `OLD_MODE_ACTIVE`
   - the existing opposite breakout/breakdown mode override is active.

3. `NEW_RANGE_PRESENT`
   - target-side existing range-break evidence is present.

4. `NEW_MA_PRESENT`
   - target-side existing MA-cross/current-MA-side evidence is present.

5. `NEW_MODE_ACTIVE`
   - target-side existing mode override is active.

Multiple labels may be true. Do not force a single-cause story.

Also identify the winning source of each side's Break score using the exact existing max/override hierarchy. Ties must remain ties or be explicitly reported; do not resolve ties by arbitrary priority for the primary causal counts.

## Primary outputs

- mechanically reproduced Break-final-blocker event count;
- share with old-side recent-event memory active;
- share with old-side mode active;
- share with target-side range / MA / mode evidence already present;
- source-pair matrix: target winning source vs old winning source;
- share where current MA relation is already target-side but old-side Break evidence still wins;
- reciprocal agreement for boolean labels and source families;
- unexplained accounting = 0.

## Engineering gates

- Break-final-blocker event reproduction must be exact versus B3.10;
- reciprocal boolean attribution agreement >=99%;
- source-family reciprocal agreement >=99% on comparable non-tie events;
- unexplained accounting = 0;
- no performance keys in reports.

There is deliberately **no** gate requiring old memory to be common or requiring Break to explain the rates lag. A null result is acceptable.

## Decision rule

- If old-side recent-event memory dominates Break-final-blocker events and survives after current MA relation has already moved to the target side, B3.15 may inspect the existing `breakoutBars` memory semantics — still without tuning it.
- If target-side evidence is simply absent in most events, investigate target Break formation rather than memory decay.
- If neither dominates, demote Break as a single primary cause and move to Heat / multi-component interaction.

FR10Y/JGB10Y visual work is only unlocked after this mechanical attribution passes.
