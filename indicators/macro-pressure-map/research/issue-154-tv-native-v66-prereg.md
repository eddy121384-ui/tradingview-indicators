# Issue #154 Preregistration — TradingView-native V6.6 Reconstruction

Status: **FROZEN BEFORE ANY ISSUE #154 RECONSTRUCTION PARITY METRIC**

Issue: #154  
Branch: `research/issue-154-tv-native-v66`

## Objective

Reconstruct default Macro Pressure Map V6.6 GPI/IPI directly from the exact TradingView symbols used by the production Pine indicator, then compare the reconstructed monthly signal to the frozen Issue #133 exact V6.6 Pine snapshot.

Only if reconstruction parity passes may Issue #154 proceed to the Issue #145 mismatch autopsy.

## Hard firewall

Signal reconstruction / attribution only.

Forbidden:
- SPY/TLT forward returns;
- Equity-minus-Duration payoff tables;
- Issue #136 payoff outcomes;
- any historical asset-return join;
- any production-code change.

Permitted:
- TradingView raw daily bars for exact production symbols;
- frozen Issue #133 exact monthly GPI/IPI/regime snapshot;
- Issue #145 long-history analogue component/signal artifacts;
- component scores, regime membership, and turning chronology.

`outcome_data_loaded=false` is a hard result-contract requirement.

## Frozen production source of truth

Pine:
`indicators/macro-pressure-map/src/macro-pressure-map-v6.6.pine`

Relevant default settings:

- market timeframe = D
- zLenDaily = 252
- fastLen = 20
- midLen = 63
- useMacroData = false
- useT5YIE = false
- useIndustrialMetalsInIPI = false
- growthThreshold = 10
- inflationThreshold = 10
- useSmoothing affects display only and must NOT enter regime reconstruction.

## Frozen exact symbols

### GPI
- `AMEX:SPY`
- `AMEX:IWM`
- `AMEX:RSP`
- `AMEX:XLY`
- `AMEX:XLP`
- `AMEX:XLI`
- `AMEX:XLU`
- `COMEX:HG1!`
- `COMEX:GC1!`

### IPI
- `FRED:T10YIE`
- `AMEX:DBC`
- `NYMEX:CL1!`
- `NYMEX:RB1!`

No symbol substitution is allowed.

A pre-issue smoke test established that `FRED:T10YIE` is directly routable through TradingView OHLCV even though fuzzy search returns no match.

## Phase A — TradingView raw-source freeze

Use TradingView Official MCP / official TradingView data path only.

For every frozen symbol:
- interval = `1D`;
- request up to the maximum supported 5000 bars;
- retain UTC timestamp and close;
- persist normalized raw series;
- record row count, first/last timestamp, first/last close, and SHA256.

Transient transport errors:
- retry the exact same symbol up to 3 times;
- exponential or fixed bounded backoff is allowed;
- no alternate symbol/provider fallback;
- fail closed after retries.

### Daily alignment semantics

Use `AMEX:SPY` as the canonical daily market calendar.

For each non-SPY daily series:
1. normalize timestamps to calendar date in UTC;
2. collapse accidental duplicate dates deterministically by retaining the final returned bar;
3. reindex to the SPY date calendar;
4. reproduce Pine `request.security(... gaps=barmerge.gaps_off, lookahead_off)` by carrying the most recent already-observed value forward across missing SPY dates;
5. never backward-fill before a series' first observation.

A source is not eligible before its first true observation.

The reconstructed full-composition period starts only when every default GPI/IPI component score is finite.

## Frozen Pine-compatible component score

For positive level series X:

- `lvl = zscore(X,252)`
- `rocFast = ROC(X,20)`
- `rocMid = ROC(X,63)`
- `momRaw = 0.6*rocFast + 0.4*rocMid`
- `mom = zscore(momRaw,252)`
- `dirRaw = (SMA20(X)-SMA63(X))/stdev252(X)`
- `dir = tanh(dirRaw)`
- `raw = 0.5*lvl + 0.3*mom + 0.2*dir`
- `score = 100*tanh(raw/2)`

Frozen implementation semantics:
- Pine-compatible rolling non-NA windows;
- Pine default biased standard deviation, equivalent to `ddof=0`;
- ROC = percentage rate of change, matching `ta.roc`;
- zero standard deviation => NA;
- no clipping/rescaling/calibration.

## Frozen GPI reconstruction

Levels:
- IWM/SPY
- RSP/SPY
- XLY/XLP
- XLI/XLU
- HG1!/GC1!

Score each level with the frozen daily component score.

`GPI = f_avg5(...)` with Pine available-component semantics.

For the primary exact-composition parity window, require all five GPI component scores finite.

## Frozen IPI reconstruction

- breakeven score = score(`FRED:T10YIE`)
- commodity score = score(`AMEX:DBC`)
- oil score = score(`NYMEX:CL1!`)
- gasoline score = score(`NYMEX:RB1!`)
- energy score = available-component mean of oil/gasoline, matching Pine `f_avg2`

Default IPI:

`IPI = f_wavg3(breakeven,0.35,commodity,0.40,energy,0.25)`

For the primary exact-composition parity window, require breakeven, commodity, oil, and gasoline scores all finite.

## Frozen monthly sampling

The frozen Issue #133 exact target is monthly.

For the daily reconstruction:
- group by calendar month;
- select the final SPY-calendar daily observation in each month;
- compare raw unsmoothed GPI/IPI;
- derive regime using +/-10 thresholds from those raw values.

Do not average daily GPI/IPI within the month.

## Frozen exact target

Reuse Issue #133 exact normalized monthly V6.6 snapshot.

Expected SHA256:

`1d03923503e7fe82a69b033897484c48aa646279ecf70164d090ed62a5a70719`

Only:
- date
- exact GPI
- exact IPI
- exact regime

may be read.

## Parity period

Primary parity uses the intersection of:
- frozen exact Issue #133 monthly snapshot;
- reconstructed full-composition monthly signal.

No hand-picked start date may be chosen after viewing metrics.

Report the resulting first/last common month and common count.

## Frozen parity metrics

Report:
- common eligible months;
- GPI Pearson correlation;
- IPI Pearson correlation;
- GPI mean absolute error;
- IPI mean absolute error;
- GPI max absolute error;
- IPI max absolute error;
- exact 3x3 regime agreement;
- R7 precision;
- R7 recall;
- exact-vs-reconstructed async-turn precision / recall / F1 within +/-1 month;
- trigger count ratio.

Use Issue #136's frozen asynchronous-turn rule and deterministic +/-1 month matching.

## Formal parity gate

Verdict `tv_native_reconstruction_passed` only if ALL are true:

1. common eligible months >= 180;
2. GPI correlation >= 0.995;
3. IPI correlation >= 0.995;
4. GPI MAE <= 1.50 index points;
5. IPI MAE <= 1.50 index points;
6. regime agreement >= 0.95;
7. R7 precision >= 0.90;
8. R7 recall >= 0.90;
9. async-turn trigger F1 >= 0.80;
10. trigger-count ratio between 0.80 and 1.25 inclusive.

If common months <180:
`tv_native_reconstruction_inconclusive_sample`.

Otherwise any failed fidelity gate:
`tv_native_reconstruction_failed`.

There is no suggestive rescue verdict.

## Mismatch-autopsy authorization

Issue #145 mismatch autopsy is authorized inside Issue #154 only when:

`reconstruction_verdict == "tv_native_reconstruction_passed"`.

If parity fails:
- stop after recording the failure;
- do not interpret Issue #145 component mismatches using the failed reconstruction;
- do not alter parity thresholds or source semantics.

## Frozen Issue #145 autopsy scope

If authorized, inspect only these exact Issue #136 modern trigger months:

- 2018-10
- 2019-05
- 2020-04
- 2022-08
- 2023-03
- 2025-04

For each trigger episode report:
- exact reconstructed GPI/IPI;
- Issue #145 analogue GPI/IPI;
- exact IPI distance to -10;
- analogue IPI distance to -10;
- exact daily component scores sampled at month end:
  - T10YIE
  - DBC
  - WTI
  - gasoline
  - energy
- Issue #145 analogue IPI component scores:
  - Cleveland expected inflation
  - DBIQ
  - World Bank WTI
  - MGASNYH gasoline
  - energy
- component 1M and 3M changes;
- component turn-event month;
- exact vs analogue R7 episode membership;
- exact vs analogue async-turn completion month.

The autopsy is attribution only.

No source replacement, lag, coefficient, score-length, threshold, or trigger-rule change is permitted inside Issue #154.

## Production boundary

`production_authorized=false`.

No production Pine change.
No historical asset-outcome test.
No automatic merge.
