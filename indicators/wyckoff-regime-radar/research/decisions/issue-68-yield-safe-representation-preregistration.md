# Issue #68 — Yield-Safe Representation Repair Preregistration

## Trigger

TradingView runtime review of the full HARD production candidate on `TVC:FR10Y` exposed a pre-existing C-2 representation-domain failure: Issue #66 B-1 uses `log(price)` and log-space ATR to enforce reciprocal symmetry for positive price assets, but government-bond yield datasets can cross zero and become negative. On such bars, direct `log(yield)` is undefined and contaminates the representation layer with `na`.

This is an upstream C-2 blocker discovered during runtime regression. It is not caused by the Issue #68 HARD current-context cap and must not be disguised as a HARD threshold/gate change.

## Frozen semantic split

Issue #66 B-1 remains the correct default representation for positive price assets and retains its reciprocal invariant:

`classifier(P) ≈ mirror(classifier(1/P))`.

Yield-like level series are a different mathematical domain: zero and negative observations are valid, and price-reciprocal semantics do not apply to a yield level. Therefore the production candidate may use a separate level-space representation only for yield-like datasets.

## Auto classification

Add one non-tuning representation input:

- `Auto` (default)
- `Price Log`
- `Yield Level`

`Auto` resolves to `Yield Level` only when TradingView static symbol metadata identifies both:

- `syminfo.type == "bond"`
- `syminfo.currency == "NONE"`

Otherwise Auto remains exact Issue #66 `Price Log`.

The metadata decision is static for the loaded symbol. It must not inspect historical values, must not switch mode when price/yield crosses zero, and must introduce no lookahead or path dependence.

## Yield Level representation

When `Yield Level` is active, only the Issue #66 B-1 representation family changes:

1. slope source: raw level `close` instead of `log(close)`;
2. return/volatility source: first difference `close-close[1]` instead of log return;
3. moving averages: arithmetic SMA in level space instead of geometric/log-space MA;
4. symmetric ATR: Wilder true range in raw level units;
5. distance-to-MA and maturity distance: signed level difference / level ATR;
6. low-vol rank input: level ATR (its percentile rank is unit-scale invariant within the symbol);
7. range width: `(rangeHigh-rangeLow)/levelATR` instead of log range width/log ATR;
8. MA spread continuation: `(ma-maturityMa)/levelATR`;
9. MA cross and MA-side breakout evidence use the selected representation source and selected representation MA.

All downstream thresholds, weights, stage formulas, witness logic, HARD S1/S4 cap, lifecycle, plots, dashboard, and alerts remain frozen.

## Price-asset parity requirement

For Auto symbols that do not resolve to Yield Level, the selected model series must alias the existing C-2 log variables so positive-price behavior remains exact C-2/HARD parity. No generic replacement of Issue #66 log-space symmetry is authorized.

## Hard boundaries

- no HARD 35/75 tuning;
- no stage weight or threshold change;
- no new lookback;
- no symbol-name whitelist such as `FR10Y`/`DE10Y`;
- no historical `close <= 0` auto-detection;
- no Stateful/grace revival;
- no PnL/Strategy Tester;
- no changes to Volume/MTF/Divergence semantics;
- no production-source overwrite yet.

## Static acceptance gates

The generated yield-safe HARD candidate must:

1. be mechanically downstream of the already-passed full HARD production candidate;
2. preserve all HARD current-context lines exactly;
3. preserve every stage RAW/gate formula outside the B-1 representation family;
4. preserve the production witness, visual, dashboard, and alert layers;
5. preserve plot-generating call count;
6. contain no `strategy.*` logic;
7. use only static `syminfo.type` / `syminfo.currency` metadata for Auto routing;
8. retain explicit `Price Log` override for reciprocal-price testing and explicit `Yield Level` override for metadata fallback.

## Runtime acceptance gates

After static generation passes, load the exact generated candidate in TradingView.

Primary runtime repair check: `FR10Y` 1D must no longer lose the core representation simply because yield is `<= 0`; the 2019–2021 negative/near-zero period must render finite model/risk behavior after normal warmup rather than a long log-domain hole.

Controls:

- `DE10Y` 1D: negative-yield history must remain finite after warmup;
- `JP10Y` 1D: near-zero history must remain finite;
- `US10Y` 1D: positive-yield control must run through the same Auto Yield Level path;
- one positive price/FX control under Auto must remain Price Log and preserve Issue #66 reciprocal semantics.

Only after this representation blocker passes may the frozen six-market HARD regression resume.