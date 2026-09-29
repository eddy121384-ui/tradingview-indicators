# Issue #117 post-payoff reproducibility amendment — HMRA state-semantic hash

Date: 2026-09-29

Status: **TRANSPORT / REPRODUCIBILITY ONLY — NO MODEL OR PAYOFF CHANGE**

## Trigger

After the preregistered Issue #117 payoff had already run, later GitHub runners occasionally produced a different raw-byte CSV hash for the derived monthly HMRA table even though all frozen upstream source hashes were unchanged.

The same class of floating serialization / last-digit calculation drift had already appeared in Issue #91.

## Verified invariants

Across retained source-freeze artifacts:

- shape remained 1291 × 13;
- date sequence was identical;
- growth_state was identical for every month;
- inflation_state was identical for every month;
- regime was identical for every month;
- defensive_gold_state was identical for every month;
- Gold and Cash derived CSV byte hashes remained exact;
- all five upstream source payload hashes remained exact.

The runner-level drift was confined to irrelevant floating numeric tails in the derived HMRA calculation/serialization and did not alter the state sequence used to select payoff observations.

## Durable gate

For upstream inputs, Gold, and Cash, keep byte-exact SHA-256 gates.

For the **derived monthly HMRA table**, bind the exact ordered state semantics:

- date
- growth_state
- inflation_state
- regime
- defensive_gold_state

These fields are serialized as deterministic JSON records in original row order with sorted object keys and compact separators.

Frozen state-semantic SHA-256:

`28de6da00f86148033a46ee6be80eaf3b2676a7b04d5439bdc9c972df88c0a20`

The earlier raw CSV byte hash remains recorded as a diagnostic:

`6b200a949c4a52f128639baa2c7ce2b924ce3e2818f9bc1eeb5922bd5ce0986c`

## Why this is the correct research gate

Issue #117 payoff selection depends on the HMRA **state assignment**, not on the last floating digits of displayed scores.

The state-semantic gate therefore fails closed if any month changes:

- Growth bucket;
- Inflation bucket;
- Regime;
- pooled defensive-state membership;
- date alignment.

At the same time it does not falsely fail because two runners serialize numerically equivalent scores differently.

## What does not change

This amendment does **not** change:

- any upstream observation;
- 12M transformations;
- 60M normalization;
- 70/30 weights;
- ±10 thresholds;
- t-2 lag;
- any state assignment;
- Gold/Cash outcome timing;
- 3M primary horizon;
- non-overlap selection;
- eras;
- episode rules;
- leave-one-substate rules;
- any verdict gate;
- the payoff result already observed before this amendment.

No outcome-driven model change is authorized by this amendment.
