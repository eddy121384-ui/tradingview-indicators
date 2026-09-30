# Issue #78 — Heterogeneous OOS1 Partial 4-Market Diagnostic

## Status

This is an explicitly **incomplete diagnostic**, not the preregistered OOS1 pass/fail result.

The frozen six-market OOS1 cohort is:

- TVC:SPX
- NASDAQ:NDX
- OANDA:XAUUSD
- OANDA:XAGUSD
- BITSTAMP:BTCUSD
- BITSTAMP:ETHUSD

At this point only four valid raw logs are available:

- TVC:SPX
- OANDA:XAGUSD
- BITSTAMP:BTCUSD
- BITSTAMP:ETHUSD

NDX and XAUUSD are missing.

Therefore:

- the original six-market preregistration remains unchanged;
- no formal equal-asset-class pass/fail conclusion is allowed;
- EquityIndex and PreciousMetals each have only one market;
- this file records only whether the frozen architecture obviously collapses on the available cohort.

## Data integrity

Accepted rows:

- SPX: 9,999
- XAGUSD: 9,999
- BTCUSD: 4,413
- ETHUSD: 3,123
- total: **27,534**

All four feeds are:

- native 1D;
- PRICE_LOG;
- accepted by the frozen whitelist;
- reconstructed with maximum OHLC error about **2.22e-16**.

Completed Markup / Markdown episodes:

- SPX: 192
- XAGUSD: 269
- BTCUSD: 99
- ETHUSD: 74
- total: **634**

First usable B3 events:

- SPX: 133
- XAGUSD: 156
- BTCUSD: 56
- ETHUSD: 45
- total: **390**

Frozen path counts across the available cohort:

- P0 No-touch: 123
- P1 Wick Hold: 87
- P2 Reclaim: 43
- P3 Failed Acceptance: 137

## 1. R0 does not obviously collapse on the partial OOS cohort

Mean normalized episode return by market:

| Market | R0 No De-risk | R0 + Warning-First |
|---|---:|---:|
| BTCUSD | +2.079 ATR | +1.733 ATR |
| ETHUSD | +0.356 | +0.337 |
| SPX | +0.597 | +0.438 |
| XAGUSD | -0.002 | -0.038 |

R0 No De-risk is positive in **3/4** available markets.

Equal-available-market mean episode return:

- R0 No De-risk: **+0.757 ATR**
- R0 + Warning-First: **+0.617 ATR**

This is encouraging but cannot be treated as the preregistered six-market OOS result.

## 2. Available asset-class picture

Because the cohort is incomplete, this is descriptive only.

### Crypto

Average of BTCUSD and ETHUSD:

- R0 No De-risk mean episode return: **+1.217 ATR**
- R0 + Warning-First: **+1.035 ATR**

### Equity index

SPX only:

- R0: **+0.597 ATR**
- Warning-First: **+0.438 ATR**

### Precious metals

XAGUSD only:

- R0: **-0.002 ATR**
- Warning-First: **-0.038 ATR**

So the available data do not show a universal collapse, but metals remain unresolved because XAUUSD is missing and XAG alone is approximately flat.

## 3. Warning-First preserves the expected defensive shape

Whole-path diagnostics show the same qualitative behavior in every available market.

### BTCUSD

- max DD: 17.09 -> **11.35**
- 5% ES: -1.760 -> **-1.360**
- bar volatility: 0.735 -> **0.589**

### ETHUSD

- max DD: 18.19 -> **13.53**
- 5% ES: -1.240 -> **-1.026**
- bar volatility: 0.473 -> **0.400**

### SPX

- max DD: 35.36 -> **31.39**
- 5% ES: -1.635 -> **-1.344**
- bar volatility: 0.638 -> **0.525**

### XAGUSD

- max DD: 102.20 -> **98.83**
- 5% ES: -1.718 -> **-1.358**
- bar volatility: 0.743 -> **0.618**

Therefore Warning-First improves:

- max drawdown in **4/4** available markets;
- 5% expected shortfall in **4/4**;
- daily-bar volatility in **4/4**.

It also lowers average exposure and raises turnover, consistent with the discovery-sample mechanism.

## 4. Failed-trend protection transports cleanly

For MFE <4 ATR episodes, equal-available-market mean harvest is:

- R0 No De-risk: **-0.674 ATR**
- R0 + Warning-First: **-0.625 ATR**

Warning-First improves failed / small-trend damage in **4/4 markets**:

- BTCUSD: +0.010 ATR
- ETHUSD: +0.017
- XAGUSD: +0.044
- SPX: +0.125

This is a clean portability result for the management semantics.

## 5. Large-trend tax also transports cleanly

For MFE >=8 ATR:

- R0 No De-risk: **+6.768 ATR**
- R0 + Warning-First: **+5.818 ATR**

Warning-First trails R0 in **4/4 markets**:

- BTCUSD: -1.984 ATR
- ETHUSD: -0.027
- XAGUSD: -0.693
- SPX: -1.096

So the exact same structural tradeoff reappears:

> Warning-First protects deteriorating / failed trends but gives up some genuine large-trend harvest.

That is more informative than simply observing a lower aggregate volatility number.

## 6. Evidence-state prevalence remains populated

B3 coverage of completed trend episodes:

- BTCUSD: 56.6%
- ETHUSD: 60.8%
- XAGUSD: 58.0%
- SPX: 69.3%

P3 Failed Acceptance share among B3 states:

- BTCUSD: 41.1%
- ETHUSD: 26.7%
- XAGUSD: 39.1%
- SPX: 30.8%

The breakout / acceptance architecture is not becoming pathologically sparse on the available new asset classes.

## 7. Tail dependence

After removing each market's single best episode, R0 mean episode return remains positive for:

- BTCUSD: +1.593 ATR
- ETHUSD: +0.197
- SPX: +0.461

XAGUSD becomes negative:

- XAGUSD: -0.123

Therefore the positive partial-OOS result is not solely one giant episode in the three positive markets, but the metal result remains fragile.

## Partial decision

Allowed conclusion:

> **The frozen R0 / Warning-First architecture does not obviously fail on the four available heterogeneous markets. R0 remains economically positive in SPX and both crypto markets, while XAG is approximately flat. Warning-First reproduces its discovery-sample risk-shaping semantics very consistently: lower failed-trend damage and lower DD / ES / volatility, paid for by lower large-trend harvest.**

Not allowed:

- heterogeneous OOS passed;
- all three new asset classes validated;
- precious-metals portability established;
- production-ready.

The full preregistered OOS1 decision still requires NDX and XAUUSD.

## Next step

Do not change the six-market preregistration.

Operationally:

1. keep this four-market diagnostic frozen;
2. continue diagnosing the NDX and XAUUSD logger-feed issue;
3. when both missing logs are available, rerun the untouched six-market primary analyzer;
4. only then issue the formal OOS1 finding.

PR #80 remains Draft / open / unmerged.

Refs #78, #80, #76.
