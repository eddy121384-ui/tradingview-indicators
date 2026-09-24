# Issue #78 — Heterogeneous OOS Challenge 1 Finding

## Status

This is the formal six-market Heterogeneous OOS1 finding under the frozen preregistration plus the two pre-outcome technical amendments:

1. XAUUSD logger memory safety: `calc_bars_count=10000` and removal of MTF Observe-Only lower-timeframe arrays.
2. NDX TradingView runtime namespace correction: `NASDAQ:NDX` -> `NASDAQ_DLY:NDX`.

Neither amendment changes the underlying instrument, classifier stage logic, Price-Log representation, breakout / acceptance rules, R0 policy, or Warning-First policy.

The six-market cohort is now complete:

- TVC:SPX
- NASDAQ_DLY:NDX
- OANDA:XAUUSD
- OANDA:XAGUSD
- BITSTAMP:BTCUSD
- BITSTAMP:ETHUSD

This is historical heterogeneous-market OOS, not prospective validation and not production approval.

## Integrity

Accepted forward-log rows: **45,182**

Completed formal Markup / Markdown episodes: **1,039**

Usable first B3 events: **624**

P1 + P2 states: **202**

Path counts:

- P0 No-touch: 200
- P1 Wick Hold: 132
- P2 Reclaim: 70
- P3 Failed Acceptance: 222

Maximum OHLC reconstruction error is approximately **2.22e-16**.

Per-market counts:

| Market | Rows | Episodes | B3 | P0 | P1 | P2 | P3 |
|---|---:|---:|---:|---:|---:|---:|---:|
| SPX | 9,999 | 192 | 133 | 45 | 30 | 17 | 41 |
| NDX | 8,876 | 187 | 115 | 38 | 20 | 14 | 43 |
| XAUUSD | 8,772 | 218 | 119 | 39 | 25 | 13 | 42 |
| XAGUSD | 9,999 | 269 | 156 | 52 | 29 | 14 | 61 |
| BTCUSD | 4,413 | 99 | 56 | 13 | 13 | 7 | 23 |
| ETHUSD | 3,123 | 74 | 45 | 13 | 15 | 5 | 12 |

## 1. R0 is positive across all three new asset classes

Mean normalized episode return by market:

| Market | R0 No De-risk | R0 + Warning-First |
|---|---:|---:|
| BTCUSD | +2.079 ATR | +1.733 ATR |
| ETHUSD | +0.355 | +0.337 |
| NDX | +0.281 | +0.221 |
| SPX | +0.597 | +0.438 |
| XAUUSD | +0.179 | +0.146 |
| XAGUSD | -0.002 | -0.038 |

R0 is positive in **5/6 markets**. XAGUSD is approximately flat.

Equal-market / equal-class mean episode return are the same because the design has exactly two markets per class:

- R0 No De-risk: **+0.582 ATR**
- R0 + Warning-First: **+0.473 ATR**

Asset-class means for R0:

- Crypto: **+1.217 ATR**
- Equity indices: **+0.439 ATR**
- Precious metals: **+0.088 ATR**

All **3/3 asset classes** are positive on an equal-class basis.

This is meaningful portability evidence.

## 2. The formal Strong-Portability gate is not fully met

The preregistered strong gate also required that no single market supply the majority of the aggregate positive result.

Among the five positive market means, BTCUSD contributes approximately **59.5%** of their summed positive mean return.

Therefore the formal classification is:

> **Mixed portability — positive and cross-asset, but still materially concentrated in BTCUSD / crypto.**

This is not a portability failure: all three asset classes are positive and 5/6 markets are positive.

But it is not strong enough to call the economic edge broadly distributed.

## 3. Tail dependence is present but not a one-episode artifact

Equal-market R0 mean episode return:

- all episodes: **+0.582 ATR**
- after removing each market's single best episode: **+0.406 ATR**

Per-market R0 mean after removing the single best episode remains positive for:

- BTCUSD: +1.592
- ETHUSD: +0.197
- NDX: +0.182
- XAUUSD: +0.126
- SPX: +0.461

XAGUSD becomes -0.123.

So the positive result is not created by one giant episode in the positive markets, although the aggregate still depends materially on crypto strength.

## 4. Warning-First defensive semantics transport extremely cleanly

Relative to R0 No De-risk, Warning-First improves:

- daily-bar volatility in **6/6 markets**;
- maximum drawdown in **6/6**;
- 5% expected shortfall in **6/6**;
- MFE <4 failed / small-trend harvest in **6/6**.

Examples:

- BTC DD: 17.09 -> 11.35
- NDX DD: 29.99 -> 21.54
- SPX DD: 35.36 -> 31.39
- XAU DD: 24.91 -> 20.11
- XAG DD: 102.20 -> 98.83
- ETH DD: 18.19 -> 13.53

This is a stronger portability result for the **risk-management mechanism** than for the raw R0 return edge.

## 5. The large-trend tax also transports

Equal-class MFE >=8 ATR harvest:

- R0: **+5.906 ATR**
- Warning-First: **+5.104 ATR**

Warning-First large-trend retention:

- Crypto: **86.9%**
- Equity indices: **83.8%**
- Precious metals: **87.6%**

It trails R0 on MFE >=8 in **6/6 markets**.

The same structural tradeoff therefore appears outside FX / sovereign rates:

> Warning-First protects deterioration and failed trends, but gives up part of genuine large-trend harvest.

That mechanism is highly portable.

## 6. Failed / small-trend protection is also cross-class

MFE <4 ATR equal-class mean:

- R0: **-0.727 ATR**
- Warning-First: **-0.674 ATR**

By class, Warning-First improves failed / small-trend harvest in:

- Crypto
- Equity indices
- Precious metals

and in every individual market.

This supports retaining Warning-First as a defensive / risk-budget challenger.

## 7. Temporal diagnostics are supportive, not perfect

R0 equal-class mean episode return:

- 2010–2014: **+1.425 ATR**, 2/3 classes positive
- 2015–2019: **+0.562 ATR**, 2/3 classes positive
- 2020–2026: **+0.424 ATR**, 3/3 classes positive

The old 2015–2019 discovery-era weakness does **not** reproduce as a broad heterogeneous-market collapse.

Warning-First in 2015–2019 is slightly better:

- R0: +0.562 ATR
- Warning-First: +0.576 ATR

with all 3 classes positive under Warning-First.

This is encouraging, but history coverage differs across markets and the exercise remains historical.

## 8. Direction remains an important unresolved asymmetry

R0 equal-class mean:

- Markup: **+1.220 ATR**, positive in 3/3 classes and 6/6 markets
- Markdown: **-0.115 ATR**, positive in only 1/3 classes and 2/6 markets

Warning-First:

- Markup: +1.067 ATR
- Markdown: -0.187 ATR

The OOS result is therefore strongly concentrated in Markup behavior.

Per the preregistration:

> do not create separate Markup / Markdown thresholds or policies from this result.

But this asymmetry prevents a claim that the economic edge is equally portable in both directions.

## 9. Evidence-state architecture remains populated

B3 coverage is not pathologically sparse across the new cohort.

Equal-market path prevalence among usable B3 events:

- P0: 30.8%
- P1: 22.7%
- P2: 11.4%
- P3: 35.1%

The evidence chain therefore continues to generate all four causal states on equity indices, precious metals, and crypto.

## Decision

### R0 No De-risk

The first heterogeneous OOS challenge is **not a failure**.

Evidence supports:

> the frozen R0 architecture has meaningful cross-asset portability beyond the original FX / sovereign-yield discovery universe.

However the preregistered **Strong portability** gate is not fully satisfied because:

- BTCUSD supplies about 59.5% of summed positive market-mean return;
- the aggregate is much stronger in Markup than Markdown;
- XAGUSD is approximately flat.

Formal classification:

> **Mixed portability, positive / encouraging.**

Do not tune the current six-market cohort to improve that classification.

### R0 + Warning-First

Warning-First earns a stronger statement:

> **The frozen defensive mechanism is portable across all three new asset classes.**

It improves failed-trend damage, volatility, max drawdown and ES broadly in 6/6 markets, while retaining roughly 84–88% of large-trend harvest by asset class.

Retain it as the frozen optional defensive / risk-budget challenger, not as a universal return-maximizing default.

## Next gate

Per the OOS stop rules:

- no asset-specific tuning;
- no Markup / Markdown-specific thresholds;
- no BTC down-weight rule;
- no metals rescue rule;
- no Warning-First v2;
- no Resume reintroduction.

The next legitimate gate is **prospective / forward validation** of the frozen survivors:

1. R0 No De-risk
2. R0 + Warning-First

A separately preregistered second historical OOS cohort is acceptable only if prospective collection is impractical, but the current six-market cohort must remain untouched.

PR #80 remains Draft / open / unmerged.

Refs #78, #80, #76.
