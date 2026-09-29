# Issue #121 Phase 1 finding — ultra-long-history losers' bracket rematch

Status: **COMPLETE — ONE MAPPING REVIVED**

Formal Phase 1 outcome:

- 27 cell × spread combinations evaluated
- **1 revived_long_history_candidate**
- 1 long_history_era_dependent
- 3 long_history_structural_but_timing_unstable
- 5 remains_unconfirmed
- 17 inconclusive_long_history_sample

Commodity-Cash remains source-gated and no payoff was computed.

## Frozen evidence backbone

This study re-ran and validated the frozen Issue #91 HMRA-v0.1 pipeline before classifying any Issue #121 mapping.

Primary source hashes:

- Damodaran annual return table:
  `127c772f0fea8763391dbf2c1c7d3ecd3a07ca2b23f81ab47af58b529e2b5647`
- JST R6:
  `c1bb91fe56ea50d4f27af5c0fc897d481e89ae38ce41eaecab62134c9354981d`

Pairings:

- structural same-year rows: 98
- strict-causal t+2 rows: 96

Core spreads:

- Equity − Treasury, 1928–2025
- Treasury − Cash, 1928–2025
- Gold − Cash, investable-Gold window 1975–2025

Primary resurrection evidence is strict-causal `state_t -> return_{t+2}`.

## The one genuine resurrection

### Reflation / Inflation Rising → Equity > Treasury

Classification:

`revived_long_history_candidate`

Structural same-year:

- n = 22
- mean Equity − Treasury = **+11.72pp/year**
- 95% bootstrap CI = **+3.10pp to +20.16pp**
- positive fraction = 72.7%

Strict-causal t+2:

- n = 22
- mean Equity − Treasury = **+13.81pp/year**
- 95% bootstrap CI = **+6.12pp to +20.97pp**
- positive fraction = 81.8%

Era robustness:

- 4 eligible eras
- **4 / 4 have the same positive sign**
- no eligible large opposite-sign era
- all 7 evaluable leave-one-era-out reruns remain positive
- strongest-era contribution share = **31.77%**, below the frozen 50% concentration ceiling

Every resurrection gate passes.

Interpretation:

> The modern exact-V6.6 Reflation Equity > Duration signal was likely underpowered rather than disproven by the 2007–2026 sample.

This does not make the HMRA state identical to exact V6.6 Reflation, but it establishes a durable long-history analogue supporting the same relative asset direction.

## Near-miss — positive causal edge but era-concentrated

### Disinflationary Drift → Equity > Treasury

Classification:

`long_history_era_dependent`

Structural:

- n = 10
- mean = **+12.15pp**
- CI = **+1.43pp to +23.60pp**

Strict-causal:

- n = 9
- mean = **+9.20pp**
- CI = **+1.79pp to +17.20pp**

The causal CI is fully positive, and both eligible eras have the same sign.

But:

- strongest-era contribution share = **63.36%**
- frozen maximum = 50%

Therefore it does **not** revive under the preregistered robustness gate.

## Strong structural relationships that fail causal timing

### Goldilocks / Disinflationary Expansion → Equity > Treasury

Classification:

`long_history_structural_but_timing_unstable`

Structural:
- n = 20
- mean = **+15.31pp**
- CI = **+9.78pp to +21.05pp**

Strict-causal:
- n = 19
- mean = **+2.44pp**
- CI = **−6.14pp to +11.51pp**

The same-year relationship is strong, but it does not survive the timing-safe forward test.

### Disinflationary Drift → Treasury > Cash

Classification:

`long_history_structural_but_timing_unstable`

Structural:
- n = 10
- mean = **+6.33pp**
- CI = **+1.81pp to +11.11pp**

Strict-causal:
- n = 9
- mean = **+0.20pp**
- CI = **−3.70pp to +4.25pp**

This is the clearest example of a mapping that looked attractive in #91 structurally but does not survive the stricter trading-information test.

### Reflation / Inflation Rising → Gold > Cash

Classification:

`long_history_structural_but_timing_unstable`

Structural, 1975+:
- n = 12
- mean = **+10.84pp**
- CI = **+4.03pp to +17.41pp**

Strict-causal:
- n = 12
- mean = **+5.50pp**
- CI = **−3.48pp to +13.72pp**

The direction is positive and leave-one-era-out is stable, but the primary causal CI still crosses zero.

Gold therefore does not revive as an ultra-long-history causal rule.

## Duration vs Cash — no resurrection

No Treasury − Cash HMRA cell passes the revival gate.

Important cases:

### Slowdown / Disinflation

Structural:
- n = 15
- mean = **+6.04pp**
- CI = **+2.16pp to +10.21pp**

Strict-causal:
- n = 15
- mean = **+1.20pp**
- CI = **−2.70pp to +4.30pp**

Only one era has >=3 strict-causal observations, so this is classified:

`inconclusive_long_history_sample`

The historical same-year relationship is real, but the evidence is not sufficient to resurrect it as a forward allocation rule.

### Reflation

Strict-causal Treasury − Cash:
- n = 22
- mean = +1.99pp
- CI = −0.85pp to +4.70pp

Classification:
`remains_unconfirmed`

### Stagflation

Strict-causal Treasury − Cash:
- n = 19
- mean = +1.11pp
- CI = −2.76pp to +5.18pp

Classification:
`remains_unconfirmed`

This does not erase the known #91 absolute-inflation interaction. It says that the unconditional HMRA cell alone is not a resurrected causal Treasury-vs-Cash rule.

## Gold vs Cash — no resurrection

No Gold − Cash cell passes the revival gate.

Most Gold cells are sparse after applying:

- 1975+ investable window
- strict causal t+2 timing
- era-support requirements

Notable cases:

- Reflation: structural positive, causal CI crosses zero
- Stagflation: causal mean **−4.56pp**, CI crosses zero, remains unconfirmed
- all other cells are either remains-unconfirmed or insufficient under the frozen gate

This is directionally consistent with #117's warning not to elevate Gold > Cash into a generic long-history macro law.

## Equity vs Treasury — strongest long-history family

Of all three rematched spreads, Equity − Treasury contains the only revived mapping and the only additional causal-positive but era-concentrated mapping.

Summary:

- Reflation: **REVIVED**
- Disinflationary Drift: causal-positive but era-dependent
- Goldilocks: structural only, timing unstable
- Stagflation: remains unconfirmed
- remaining cells: insufficient under the strict long-history gate

## Commodity source gate

Broad Commodities − Cash was not evaluated.

Official S&P GSCI documentation supports a first value date in 1969 and total-return semantics, but this Phase 1 audit did not establish a stable, machine-retrievable, legally reusable >=50-year total-return transport that can be hash-frozen in GitHub Actions.

Status:

`blocked_pending_reproducible_total_return_transport`

This is not a negative commodity verdict.

## Full classification counts

Across 27 cell × spread combinations:

- revived_long_history_candidate: **1**
- long_history_era_dependent: **1**
- long_history_structural_but_timing_unstable: **3**
- remains_unconfirmed: **5**
- inconclusive_long_history_sample: **17**

## What actually changed versus the modern research

The main loser that genuinely comes back is:

> **Reflation → Equity > Duration**

The long-history evidence is materially stronger than the modern exact-V6.6 #109 sample.

By contrast:

- Duration > Cash does **not** revive as a simple unconditional state rule
- Gold > Cash does **not** revive as a generic ultra-long-history causal rule
- several strong same-year historical relationships disappear under the conservative t+2 information-timing test

## Phase 2 eligibility

Exactly one mapping is eligible for a separately preregistered portfolio-policy rematch:

> **Reflation / Inflation Rising → Equity > Treasury**

No other Phase 1 mapping may enter Phase 2 under the frozen rules.

Phase 1 authorizes no production position or weight.
