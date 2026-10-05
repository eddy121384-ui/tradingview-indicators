# DSH Handoff — Issue #154 TradingView-native V6.6 Reconstruction

You are the implementation Research Engineer for Issue #154.

Repository:
`eddy121384-ui/tradingview-indicators`

Working branch:
`research/issue-154-tv-native-v66`

Issue:
`#154 — [Research] TradingView-native V6.6 reconstruction and Issue #145 mismatch autopsy`

Frozen preregistration:
`indicators/macro-pressure-map/research/issue-154-tv-native-v66-prereg.md`

Preregistration commit:
`3e563f98b200cb36ecc0e314b27c39354acf78b8`

Production Pine source of truth:
`indicators/macro-pressure-map/src/macro-pressure-map-v6.6.pine`

## Mission

Implement the preregistered TradingView-native reconstruction of default V6.6 GPI/IPI.

Your job is execution and verification, not research redesign.

You must:

1. acquire the exact V6.6 default TradingView daily input series;
2. freeze the raw source snapshots and hashes;
3. reproduce Pine-compatible daily component scores and default GPI/IPI;
4. sample the reconstruction at monthly end;
5. compare it against the frozen Issue #133 exact monthly V6.6 snapshot;
6. apply the frozen parity gate exactly;
7. only if parity passes, perform the frozen Issue #145 mismatch autopsy;
8. write durable machine-readable and human-readable findings;
9. leave the PR Draft and unmerged.

## Critical prerequisite: TradingView access

You MUST have access to the **TradingView Official MCP / official TradingView data connector** in your execution environment.

Use the exact production symbols:

GPI:
- AMEX:SPY
- AMEX:IWM
- AMEX:RSP
- AMEX:XLY
- AMEX:XLP
- AMEX:XLI
- AMEX:XLU
- COMEX:HG1!
- COMEX:GC1!

IPI:
- FRED:T10YIE
- AMEX:DBC
- NYMEX:CL1!
- NYMEX:RB1!

Important:
`FRED:T10YIE` is routable directly through TradingView historical OHLCV even if fuzzy search does not list it.

If your environment does NOT expose TradingView Official MCP / official TradingView historical bars:
- STOP;
- report `BLOCKED_TRADINGVIEW_CONNECTOR_UNAVAILABLE`;
- do NOT use Yahoo, FRED HTTP, Stooq, Polygon, Alpha Vantage, Bloomberg, or another provider as a substitute.

Provider substitution invalidates Issue #154.

## Do not modify the preregistration

The preregistration is frozen before any parity result.

Do not change:
- symbols;
- daily alignment semantics;
- score lengths;
- z-score/std semantics;
- component weights;
- monthly sampling;
- parity metrics;
- parity gates;
- trigger logic;
- mismatch-autopsy scope.

If you think the prereg is wrong:
- do not silently fix it;
- implement exactly as written unless implementation is impossible;
- if impossible, stop and report the specific blocker.

## Hard outcome firewall

Do not read or load:
- SPY/TLT forward return tables;
- Equity-minus-Duration outcome data;
- Issue #136 payoff outputs;
- any 1990–2006 historical payoff data.

This issue is signal reconstruction and component attribution only.

Every result summary must contain:

`"outcome_data_loaded": false`

and:

`"production_authorized": false`.

## Phase A — exact TradingView source acquisition

Use TradingView official historical OHLCV.

For every symbol:
- interval: `1D`;
- count: up to the connector maximum, currently 5000;
- retrieve raw bars;
- retain UTC timestamp and close;
- normalize to one row per UTC calendar date;
- preserve exact symbol identity.

Retries:
- retry transient connector/transport errors up to 3 times;
- retry the same exact symbol;
- bounded backoff is allowed;
- do not switch provider or ticker.

A previous smoke test observed one transient websocket bad-handshake on `NYMEX:CL1!`. Treat that as a transport failure, not authorization to substitute.

Persist a deterministic source snapshot.

Suggested files:

`indicators/macro-pressure-map/research/generated/issue-154-source/issue-154-tradingview-daily.csv`

`indicators/macro-pressure-map/research/generated/issue-154-source/issue-154-source-manifest.json`

The manifest should include for every symbol:
- exact symbol;
- rows;
- first timestamp/date;
- last timestamp/date;
- first close;
- last close;
- normalized per-symbol SHA256.

Also include:
- combined normalized panel SHA256;
- connector/source identity;
- `exact_v66_signal_loaded=false` for Phase A;
- `outcome_data_loaded=false`.

### Calendar alignment

Use SPY as canonical daily calendar.

For every other series:
- normalize timestamps to UTC calendar date;
- collapse duplicates by final returned bar;
- reindex to SPY dates;
- forward-fill only previously observed values to reproduce Pine `gaps_off`;
- never backward-fill before first observation.

Document the exact implementation.

## Phase B — Python reconstruction

Before writing new score code, inspect existing research helpers such as:
- `v6_6_core.py`
- Issue #59 parity work
- Issue #133/#136 bridge utilities

Reuse proven Pine-compatible helpers when they already implement the frozen semantics.

Do not create a competing interpretation if a validated helper exists.

Reconstruct:

GPI levels:
- IWM / SPY
- RSP / SPY
- XLY / XLP
- XLI / XLU
- HG1! / GC1!

IPI:
- T10YIE
- DBC
- CL1!
- RB1!

Component score:
- zLen 252
- fast 20
- mid 63
- Pine biased stdev / ddof=0
- zero variance => NA
- exact 0.5 / 0.3 / 0.2 raw weights
- `100*tanh(raw/2)`

Aggregate exactly as Pine.

Use RAW GPI/IPI, not smoothed plot lines.

Persist daily reconstruction including component scores.

Suggested file:

`indicators/macro-pressure-map/research/generated/issue-154/issue-154-daily-reconstruction.csv`

Include at least:
- date
- all raw levels/ratios
- each GPI component score
- each IPI component score
- energy score
- raw GPI
- raw IPI
- regime id / R7 flag

## Phase C — frozen exact parity

Use frozen Issue #133 exact monthly V6.6 snapshot.

Expected normalized SHA:

`1d03923503e7fe82a69b033897484c48aa646279ecf70164d090ed62a5a70719`

Do not use a live or regenerated Pine export in place of this target.

Monthly sample:
- final SPY-calendar observation of each calendar month;
- raw GPI/IPI;
- no monthly averaging.

Calculate every metric and gate from the prereg exactly.

Formal verdict must be one of:

- `tv_native_reconstruction_passed`
- `tv_native_reconstruction_failed`
- `tv_native_reconstruction_inconclusive_sample`

Do not invent `suggestive`, `near pass`, or discretionary rescue language in the machine verdict.

### Required parity outputs

Write:

`indicators/macro-pressure-map/research/generated/issue-154/issue-154-parity-result.json`

`indicators/macro-pressure-map/research/generated/issue-154/issue-154-monthly-parity.csv`

Include:
- common first/last month;
- common month count;
- GPI/IPI correlations;
- GPI/IPI MAE;
- GPI/IPI max absolute error;
- regime agreement;
- R7 precision/recall;
- exact/reconstructed trigger dates;
- trigger matches;
- trigger precision/recall/F1/count ratio;
- all 10 gate booleans.

## Phase D — mismatch autopsy

Run this phase ONLY if:

`tv_native_reconstruction_passed`.

If parity fails, do not perform autopsy.

For the six preregistered Issue #136 trigger months:
- 2018-10
- 2019-05
- 2020-04
- 2022-08
- 2023-03
- 2025-04

compare exact TradingView-native component behavior against the frozen Issue #145 analogue.

Read the existing Issue #145 artifacts/findings rather than redesigning that analogue.

Produce a month-centered diagnostic window sufficient to establish:
- level;
- 1M change;
- 3M change;
- turn month;
- distance to -10;
- R7 membership;
- async-turn completion timing.

### Autopsy goal

Attribute the remaining Issue #145 mismatch to component families.

Examples of acceptable conclusions:
- inflation leg is responsible for N of the missed episodes;
- commodity leg contributes timing shift in specific episodes;
- energy leg causes a threshold crossing difference;
- mismatch is mixed / cannot be assigned cleanly.

Examples of forbidden actions:
- changing Cleveland to Michigan;
- fitting coefficients;
- shifting lags;
- changing +/-10;
- changing trigger tolerance;
- changing score lengths;
- trying candidate fixes until one passes.

Issue #154 diagnoses. It does not repair.

Required output if authorized:

`indicators/macro-pressure-map/research/generated/issue-154/issue-154-145-mismatch-autopsy.csv`

and a structured section in the result JSON.

## Tests

Add targeted tests for at least:

- UTC/date normalization;
- duplicate-date handling;
- SPY-calendar forward-fill with no backward-fill;
- Pine-compatible component score;
- monthly final-SPY-observation sampling;
- regime mapping;
- parity-gate deterministic verdict;
- hard stop preventing autopsy when parity fails;
- exact symbol list cannot be changed silently.

If existing tests cover semantics, reuse them and add only Issue #154-specific coverage.

## CI

Add a dedicated Issue #154 workflow.

It should:
1. validate prereg commit/content;
2. run static/unit tests;
3. acquire/freeze TradingView source if MCP is available in CI;
4. run reconstruction;
5. verify Issue #133 target SHA;
6. run parity;
7. conditionally run autopsy only on parity pass;
8. assert `outcome_data_loaded=false`;
9. upload evidence artifact.

### Important environment caveat

If GitHub Actions cannot access the TradingView MCP because the connector is session-bound:
- do NOT fake the source acquisition in CI;
- instead design a two-stage workflow:
  A. connector-enabled acquisition produces a frozen normalized source snapshot;
  B. repository/CI replay consumes the frozen snapshot deterministically.

If this split is needed, the acquisition snapshot must be committed or otherwise durably frozen with hashes before parity evaluation.

Do not silently use public web data to make CI green.

## Durable finding

Create:

`indicators/macro-pressure-map/research/decisions/issue-154-tv-native-v66-finding.md`

The finding must state:
- exact source provenance;
- reconstruction verdict;
- every parity gate;
- whether autopsy was authorized;
- autopsy result if authorized;
- research limitations;
- `outcome_data_loaded=false`;
- `production_authorized=false`.

Also persist a compact machine-readable summary.

## Git / PR discipline

Continue on the existing branch:

`research/issue-154-tv-native-v66`

Do NOT create another branch unless technically required and explicitly documented.

Open or update a Draft PR against `main`.

Do NOT merge.

Do NOT modify production V6.6/V6.7 Pine.

Do NOT rewrite prior Issue findings.

## Completion report

When done, report exactly:

- branch;
- final commit SHA;
- Draft PR number;
- source acquisition status;
- source snapshot SHA;
- parity verdict;
- common months;
- GPI corr / MAE;
- IPI corr / MAE;
- regime agreement;
- R7 precision / recall;
- trigger F1 / count ratio;
- whether autopsy ran;
- top autopsy finding if it ran;
- workflow run id;
- artifact id + digest;
- tests;
- explicit statement: no outcome data loaded, no production change, no merge.

If blocked before parity, report the blocker and stop.
