# Issue #117 post-payoff reproducibility amendment — HMRA semantic hash

Date: 2026-09-29

Status: **TRANSPORT / REPRODUCIBILITY ONLY — NO MODEL OR PAYOFF CHANGE**

## Trigger

After the preregistered Issue #117 payoff had already run, the modern-overlap bridge re-ran the frozen source builder and hit the durable byte-hash guard for the generated monthly HMRA CSV.

All five upstream frozen source hashes were unchanged:

- Fed Industrial Production raw payload
- BLS CPI canonical observations
- pinned World Bank Gold mirror payload
- pinned Gold mirror README
- Kenneth French factors ZIP

A direct comparison of the original source-freeze artifact and a subsequent source-freeze rerun showed:

- identical 1291 × 13 HMRA shape;
- identical date sequence;
- identical growth state;
- identical inflation state;
- identical regime;
- identical defensive-state flag;
- no material numeric difference;
- the subsequent rerun also reproduced the original byte hash.

The failed bridge run therefore reflects intermittent floating CSV serialization drift rather than a source, formula, state, or payoff change.

Issue #91 encountered the same class of reproducibility problem and already established the precedent of a semantic CSV hash for derived floating evidence.

## Amendment

Keep byte-exact hashes as the durable gate for:

- all upstream source payloads;
- Gold monthly CSV;
- Cash RF monthly CSV.

For the **derived monthly HMRA CSV only**, add a semantic hash:

1. parse CSV fields as text;
2. preserve row order and column names;
3. preserve exact strings for:
   - date
   - growth_state
   - inflation_state
   - regime
4. normalize defensive_gold_state to boolean;
5. normalize empty numeric fields to null;
6. quantize all other numeric fields to 10 decimal places using ROUND_HALF_EVEN;
7. serialize records as deterministic JSON with sorted object keys and compact separators;
8. SHA-256 the UTF-8 JSON bytes.

Frozen semantic HMRA SHA-256:

`953a21566736e36dca6716b3788cbc374aed8842c860f8114a81f62beea16c2c`

This semantic hash matched both the original pre-payoff source artifact and the post-payoff rerun compared during diagnosis.

## What does not change

This amendment does **not** change:

- source identities;
- source values;
- 12M growth/inflation transformation;
- 12M acceleration;
- 60M prior normalization;
- 70/30 score weights;
- ±10 thresholds;
- t-2 lag;
- state assignments;
- defensive-state mapping;
- Gold or Cash outcomes;
- 3M primary horizon;
- non-overlap selector;
- era boundaries;
- episode rules;
- any success gate;
- the already observed Issue #117 payoff result.

The original HMRA raw CSV byte hash remains recorded as a diagnostic:

`6b200a949c4a52f128639baa2c7ce2b924ce3e2818f9bc1eeb5922bd5ce0986c`

but semantic equality is the durable reproducibility gate for this derived floating CSV.
