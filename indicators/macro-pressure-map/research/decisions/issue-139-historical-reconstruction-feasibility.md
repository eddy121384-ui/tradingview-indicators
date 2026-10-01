# Issue #139 — MPM V6.6 Monthly Historical Reconstruction Feasibility

Status: **source audit only — no Equity-vs-Duration outcomes inspected**

Issue: #139  
Branch: `research/issue-139-history-feasibility`

## Executive conclusion

A materially longer **composition-stable exact V6.6** history is not available.

The blocker is not the macro-confirmation layer. V6.6 defaults to `useMacroData=false`, so the exact regime engine is driven by market-only GPI/IPI. The historical limitation comes from the market proxies themselves and from the V6.6 component-score warmup.

The practical feasibility tiers are:

1. **Exact-full-composition V6.6:** effectively a post-2006 / approximately 2007+ construct.
2. **Exact-Pine partial-composition:** can mechanically extend earlier because `f_avg*` / `f_wavg*` renormalize around missing components, but the economic composition changes through time. This is not acceptable as independent long-history validation.
3. **Near-exact underlying-index reconstruction:** can recover some pre-ETF history, but the exact daily 10Y breakeven component still begins in 2003 and the Select Sector benchmarks begin in 1998. It adds only a limited amount of clean history.
4. **Monthly structural analogue:** feasible for a materially longer history. A conservative all-component analogue can plausibly begin around **1989**, but it must be validated against exact V6.6 signal behavior before any asset outcome is joined.

The recommended next step is therefore **not** to pretend that pre-2007 data are exact V6.6. It is to build and preregister a monthly structural analogue, validate its signal fidelity on a modern overlap window with no payoff data, freeze it, and only then test the untouched 1989–2006 period.

---

## 1. V6.6 code facts

Source of truth:

- `indicators/macro-pressure-map/src/macro-pressure-map-v6.6.pine`
- `indicators/macro-pressure-map/specs/macro-pressure-map-v6.6-spec.md`

Default settings relevant to historical regime reconstruction:

```text
marketTf = D
zLenDaily = 252
fastLen = 20
midLen = 63
useMacroData = false
useT5YIE = false
useIndustrialMetalsInIPI = false
```

Default market-only GPI:

```text
IWM/SPY
RSP/SPY
XLY/XLP
XLI/XLU
Copper/Gold
```

combined with `f_avg5`, which averages only non-missing component scores.

Default market-only IPI:

```text
10Y breakeven T10YIE                 0.35
DBC broad commodity basket           0.40
Oil/Gasoline energy pressure         0.25
```

combined with `f_wavg3`, which renormalizes weights over non-missing inputs.

### Score warmup implication

`f_componentScore` requires:

- a 252-observation level z-score;
- 20- and 63-observation rate-of-change momentum;
- a 252-observation z-score of that momentum;
- 20/63 moving-average direction with 252-observation volatility.

The momentum-z-score leg is the longest dependency: the 63-period ROC must first become valid, after which 252 valid momentum observations are needed.

Therefore a new daily component generally needs roughly **315 valid daily observations** before its full score can be valid.

This means a raw instrument inception date is not the same as its usable V6.6 component date.

---

## 2. Exact-source inventory

### GPI

| V6.6 component | Exact symbol | Authoritative live/history fact | Historical reconstruction assessment |
|---|---|---|---|
| Small-cap relative strength | IWM / SPY | SPY inception 1993-01-22; IWM inception 2000-05-22 | Exact ETF ratio cannot predate 2000. Russell 2000 benchmark history goes back to 1978, so an underlying-index substitute is feasible but not exact ETF history. |
| Equal-weight breadth | RSP / SPY | RSP inception 2003-04-24; benchmark is S&P 500 Equal Weight Index | Exact ETF ratio cannot predate 2003. The underlying index is the proper near-exact substitute if a frozen historical series can be licensed/snapshotted. Pre-launch values must be treated as back-tested where applicable. |
| Cyclical / defensive | XLY / XLP | both Select Sector SPDR funds launched 1998-12-16 | Exact ratio cannot predate late 1998. The corresponding Select Sector benchmarks also have a 1998 launch date; pre-1998 extension requires a different historical sector construction and is structural, not exact. |
| Industrials / utilities | XLI / XLU | both funds launched 1998-12-16 | Same limitation as XLY/XLP. |
| Copper / gold | HG1! / GC1! | long-lived commodity futures markets | Long history is feasible, but a reproducible continuous-contract roll convention must be frozen. TradingView continuous-contract history itself should not be assumed identical to an external reconstruction without overlap validation. |

### IPI

| V6.6 component | Exact symbol | Authoritative live/history fact | Historical reconstruction assessment |
|---|---|---|---|
| 10Y breakeven | FRED:T10YIE | FRED daily range begins 2003-01-02 | **Primary hard wall.** There is no exact T10YIE before 2003. Any earlier inflation-expectations series is a structural analogue. |
| Broad commodity basket | DBC | ETF inception 2006-02-03 | Exact ETF history begins 2006. The DBIQ Optimum Yield Diversified Commodity Index has a historical inception of 1988-12-02, so a near-exact underlying-index extension is possible, subject to methodology/version and licensing controls. |
| WTI oil | CL1! | WTI futures began trading in 1983 | Long exact-contract-family history is feasible with a frozen roll convention. |
| Gasoline | RB1! | RBOB futures introduced 2005-10-03 for Jan-2006 onward contracts | Exact RB history is modern. Extending the energy leg earlier requires splicing the predecessor unleaded-gasoline contract or using a historical energy index; that is near-exact/structural rather than exact RB. |

Optional default-off components are not required for this feasibility gate:

- T5YIE;
- DBB industrial metals;
- macro-confirmation data;
- official FCI data.

---

## 3. Why "exact Pine" can appear to start earlier without being composition-stable

V6.6 is deliberately NA-tolerant.

If only one GPI component is available, `f_avg5` can return that one component.

If one or two IPI legs are missing, `f_wavg3` renormalizes the surviving weights.

Therefore a historical Pine plot can produce GPI/IPI before the date when all default components exist.

That is mechanically faithful to the code but economically different.

Examples:

- before IWM/RSP/sector ETFs exist, GPI may be dominated by Copper/Gold or whichever market components have valid scores;
- before T10YIE and DBC exist, IPI can be dominated by the energy leg;
- as new instruments appear and finish their score warmups, the composite definition changes endogenously.

For Issue #139, this is classified as:

`Exact-Pine partial-composition != composition-stable exact V6.6`.

It must not be used as the untouched long-history validation sample for Issue #136.

---

## 4. Exact-full-composition boundary

The latest default raw instrument is DBC, with fund inception on 2006-02-03.

Because its V6.6 component score needs roughly 315 valid daily observations, a full-composition default IPI cannot become valid immediately at DBC inception.

Therefore full-composition exact V6.6 cannot begin earlier than roughly **2007 Q2**, subject to the actual aligned exchange/FRED calendar and TradingView history.

This is consistent with treating the existing 2007+ modern window as the exact-composition research era.

A precise first-full-composition date should only be declared after a component-level reconstruction is run and every required score is verified non-null; Issue #139 does not fabricate a calendar date from business-day approximations.

---

## 5. Near-exact underlying-index feasibility

Several ETF limitations can be partially removed by replacing the fund with its documented benchmark:

### Recoverable or partly recoverable

- SPY -> S&P 500 Index; S&P reports a first value date of 1928-01-03.
- IWM -> Russell 2000 Index; FTSE Russell reports historical data back to 1978-12-31.
- RSP -> S&P 500 Equal Weight Index; correct economic benchmark, but the historical file/version and pre-launch treatment must be verified and frozen.
- DBC -> DBIQ Optimum Yield Diversified Commodity Index; DBIQ reports historical inception 1988-12-02.
- XLY/XLP/XLI/XLU -> corresponding Select Sector benchmark indices from their 1998 launch period onward.

### Still not recoverable as exact

- T10YIE remains unavailable before 2003.
- exact RB gasoline remains unavailable before the 2005 contract launch.
- pre-1998 Select Sector history requires a different sector proxy/construction.

### Feasibility judgment

A near-exact index-backed reconstruction can add some pre-2007 history, especially 2003–2006, but it does **not** deliver the multi-cycle 1970s–1990s extension needed to materially increase independent early-recovery episodes.

Therefore it is useful as a **bridge / fidelity layer**, not as the main long-history solution.

---

## 6. Structural monthly analogue feasibility

The earliest major missing semantic object is market inflation expectations.

A credible historical substitute exists:

- Cleveland Fed / FRED `EXPINF10YR` — 10-Year Expected Inflation;
- monthly history begins 1982-01;
- model-based, not a traded TIPS breakeven;
- uses Treasury yields, inflation data, inflation swaps, and survey expectations;
- therefore it has model/revision/vintage risk and cannot be labeled T10YIE.

For the broad commodity basket:

- the DBIQ Optimum Yield Diversified Commodity Index reports historical inception 1988-12-02;
- this is a much closer semantic substitute for DBC than an unrelated commodity series;
- pre-live values are historical/back-tested index values and must be version-frozen.

For long-history equity-style growth proxies:

- Russell 2000 benchmark history reaches 1978;
- Kenneth French Data Library industry and size portfolios provide daily/monthly histories back to 1926;
- these can supply fixed historical cyclicals/defensives and industrials/utilities analogues without relying on ETFs that did not exist.

### Conservative earliest window

If the structural analogue requires:

- Cleveland 10Y expected inflation;
- DBIQ diversified commodity index;
- long-history size/breadth/industry equity proxies;
- commodity/futures growth proxies;

the conservative common start is approximately **1989** because the DBIQ diversified commodity index historical inception is December 1988.

An earlier 1982 start is possible only by replacing the DBC semantic role with another commodity benchmark. That introduces another proxy choice and should be a separate candidate, not silently substituted.

---

## 7. Recommended research architecture

### Do not do

Do not:

- extend the exact V6.6 label backward using changing available-component counts;
- call Cleveland Fed expected inflation a breakeven;
- splice ETF and index history without documenting the boundary;
- optimize historical proxies based on Equity-vs-Duration payoff;
- inspect 1989–2006 asset outcomes before the bridge signal is frozen.

### Do

Create a new **signal-only bridge study**.

Recommended design:

#### Development overlap

Use a fixed modern development interval to implement the structural analogue against exact V6.6.

Suggested development period:

`2007-01 through 2016-12`

No asset payoffs.

#### Untouched signal-fidelity holdout

Freeze the analogue mapping and bridge thresholds, then evaluate:

`2017-01 through latest common completed month`

Still no asset payoffs.

The holdout should test whether the analogue reproduces the *signal object*, not returns.

#### Candidate bridge gates to preregister

At minimum:

1. GPI monthly correlation >= 0.70;
2. IPI monthly correlation >= 0.70;
3. GPI monthly slope-sign agreement >= 70%;
4. IPI monthly slope-sign agreement >= 70%;
5. exact 3x3 regime agreement >= 60%;
6. Regime-7 precision >= 60%;
7. Regime-7 recall >= 60%;
8. asynchronous-turn trigger matching within +/-1 month >= 60%;
9. trigger-count ratio between 0.5 and 2.0;
10. no inherited temporal segment shows regime agreement below 45%.

These numeric gates are **recommendations only in Issue #139**. They are not frozen until the next preregistration issue is opened before the analogue is evaluated.

If the bridge fails, do not inspect asset outcomes.

If the bridge passes, freeze the analogue and generate untouched historical signals for approximately 1989–2006.

Only then may a separate issue join historical Equity-vs-Duration outcomes.

---

## 8. Candidate source map for the next bridge issue

This is a feasibility shortlist, not yet a frozen model.

### GPI structural roles

| V6.6 role | Preferred long-history candidate | Earliest useful history | Classification |
|---|---|---:|---|
| Small-cap relative strength | Russell 2000 / S&P 500 | 1978+ | near-exact economic role |
| Equal-weight breadth | S&P 500 Equal Weight / S&P 500 if frozen history is obtainable; otherwise a predetermined breadth/equal-weight portfolio proxy | source-dependent | near-exact if S&P series; structural otherwise |
| Cyclical / defensive | fixed Fama-French industry portfolio grouping | 1926+ | structural analogue |
| Industrials / utilities | fixed Fama-French industry portfolio grouping | 1926+ | structural analogue |
| Copper / gold | frozen continuous futures or benchmark series | 1980s or earlier | near-exact, roll-dependent |

### IPI structural roles

| V6.6 role | Preferred long-history candidate | Earliest useful history | Classification |
|---|---|---:|---|
| 10Y inflation expectations | Cleveland Fed EXPINF10YR | 1982+ | structural analogue |
| Broad commodity basket | DBIQ Optimum Yield Diversified Commodity Index | 1988-12+ | near-exact benchmark analogue |
| Energy pressure | WTI + documented gasoline predecessor / fixed energy benchmark | 1980s+ | near-exact/structural depending splice |

The candidate mapping must be fully frozen before any signal-fidelity result is viewed.

---

## 9. Source / version risks that must be controlled

### S&P / Russell index history

- index histories may include back-tested values before live launch;
- vendor licensing may constrain redistribution;
- the exact index variant (price / total return / net return) must be frozen;
- V6.6 uses market **price** inputs, so price-return index variants are generally conceptually closer than total-return variants.

### DBIQ

- the diversified commodity index has a historical inception date well before its live date;
- methodology has changed over time, including a 2025 update;
- a future bridge study must snapshot the actual historical file and hash it rather than rely on an always-current web series.

### Cleveland expected inflation

- it is model-based, not directly traded;
- historical estimates can be affected by model/data revisions;
- vintage handling must be explicit;
- using the latest revised history is acceptable only if the study labels it as a revised historical structural analogue, not as real-time information.

### Fama-French portfolios

- highly reproducible and long-history;
- industry assignments are based on historical SIC data and are not the same taxonomy as modern GICS sectors;
- any mapping from FF industries to XLY/XLP/XLI/XLU economic roles must be fixed before bridge evaluation.

### Futures

- continuous-contract construction is not unique;
- roll rules can materially affect level/momentum signals;
- contract-family continuity and predecessor splices must be explicit and hashed.

---

## 10. Feasibility verdict

### Exact extension to the 1980s

**Not feasible without changing the signal construct.**

### Exact-full-composition extension before 2007

At most marginal. DBC plus score warmup places the fully populated exact construct around 2007, and exact T10YIE does not exist before 2003.

### Near-exact extension

**Feasible but short.** It may recover a few years in the early 2000s, useful for bridge validation but unlikely to solve the sample-size problem by itself.

### Monthly structural analogue

**Feasible and worth pursuing.**

The preferred conservative target is approximately **1989–2006 untouched historical signal history**, using a frozen 1989+ analogue that is first required to pass modern signal-fidelity validation.

This gives roughly eighteen additional years at monthly frequency while keeping the crucial research firewall:

`define proxy -> validate signal fidelity -> freeze -> reconstruct old signals -> only then join outcomes`.

---

## 11. Product / research boundary

Issue #139 changes no V6.6 or V6.7 production behavior.

It does not modify Issue #136's signal, gates, or verdict.

It authorizes no Action Layer rule.

It does not authorize historical asset-outcome inspection yet.
