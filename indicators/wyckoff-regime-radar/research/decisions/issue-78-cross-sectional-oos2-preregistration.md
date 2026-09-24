# Issue #78 — Cross-Sectional OOS2 Preregistration
## Frozen R0 / Warning-First × large U.S. individual-equity universe

## Status

This document is frozen **before any Cross-Sectional OOS2 economic outcome is inspected**.

OOS2 is a historical out-of-sample challenge, not prospective validation and not production approval.

The purpose is to test whether the already-frozen Issue #78 architecture transports broadly across previously unused individual equities, rather than being carried by a small number of favorable macro markets.

No rule in this document may be changed after OOS2 outcomes are inspected merely to improve the result.

PR #80 remains Draft / open / unmerged.

---

## 1. Frozen policies

Only two policies are eligible.

### R0 No De-risk

- fresh formal Markup / Markdown entry begins at 25% Probe;
- first usable post-entry five-bar-box breakout defines B3;
- t+1 ... t+3 define P0 / P1 / P2 / P3;
- P0 / P1 / P2 promote to 100% Full at t+3;
- P3 and episodes without usable B3 remain at Probe;
- no deterioration overlay.

### R0 + Warning-First

Same earned-exposure path as R0, plus the already-frozen damage latch:

- giveback <2 entry ATR: no cut;
- 2–4 ATR: reduce earned exposure by 25 percentage points;
- 4+ ATR: reduce by 50 percentage points;
- minimum positive exposure remains 25%;
- reductions latch;
- a new favorable close-path extreme clears the latch.

No Warning-First v2 is permitted.

---

## 2. Frozen classifier / representation

Classifier source of truth:

- Issue #68 RC Pine source;
- frozen Git blob: `e5c3fd2622841a6d3f97bdda4b9d0a6378ebda55`.

For individual equities:

- native daily bars only;
- Price Log representation;
- same formal stage IDs;
- same fresh-transition semantics;
- same `symATR` episode scale;
- same five-bar B3 box and causal t+3 path construction;
- no future information.

The Python implementation may be used for scale only after passing the separate classifier-parity gate.

---

## 3. Formal OOS2 universe

Target population:

> U.S.-listed common equities on NYSE, Nasdaq and NYSE American that satisfy the frozen point-in-time eligibility rule.

Include:

- ordinary common shares;
- REIT common shares if classified as ordinary listed common equity by the data source;
- multiple listed share classes as separate securities.

Exclude:

- ETFs / ETNs;
- closed-end funds;
- preferred shares;
- ADRs / depositary receipts;
- warrants / rights;
- units;
- options;
- OTC securities.

No security may be added or removed because of its observed OOS2 performance.

### Point-in-time requirement

Formal OOS2 requires a dataset that can include securities that later delisted.

A present-day survivor list may be used only for engineering / diagnostic work and **cannot** support the formal OOS2 finding.

The exact data provider and identifier mapping must be frozen in a short data-source addendum **before any formal OOS2 outcome run**.

---

## 4. Historical window

Frozen formal event window:

- **2000-01-03 through 2026-08-31**, inclusive.

Bars before 2000-01-03 may be used only as causal warm-up history.

No event after 2026-08-31 belongs to historical OOS2; later data is prospective.

---

## 5. Point-in-time eligibility at episode entry

A stock episode is eligible only if, at the fresh formal entry bar:

1. at least 252 prior valid daily bars exist;
2. split-adjusted close is at least **USD 5.00**;
3. trailing 60-session median dollar volume is at least **USD 5 million**;
4. the security is classified as an included common-equity type on that date.

Dollar volume must use only information available up to the entry bar.

Once an episode is admitted, later price / liquidity deterioration does not retroactively remove it.

No market-cap or sector filter determines admission.

---

## 6. Corporate actions and delistings

Required price treatment:

- OHLC must be adjusted consistently for stock splits / reverse splits;
- cash dividends must not be back-adjusted into historical price moves;
- volume must be split-consistent with the price series.

Formal OOS2 must include delisted securities.

Any episode right-censored by delisting / terminal data loss must be flagged explicitly.

If the provider supplies a terminal delisting return / cash-out value, it must be incorporated causally into the terminal path.

If terminal delisting economics are unavailable, such episodes must be reported as a separate censoring diagnostic; they may not be silently dropped.

If more than 1% of admitted episodes are terminally censored without usable terminal economics, the formal finding must disclose that limitation prominently and may not claim Strong portability.

---

## 7. Primary weighting

Primary cross-sectional unit:

> **one stock, one vote.**

For each stock, compute its mean completed-episode return under each frozen policy.

Primary equal-stock tables include stocks with at least **5 completed eligible episodes**.

Stocks with fewer than 5 completed eligible episodes remain in coverage / censoring diagnostics and are not silently discarded.

Secondary diagnostics:

- pooled equal-episode;
- equal-sector;
- equal-size-bucket if point-in-time market-cap metadata is available;
- calendar-time aggregate only as a diagnostic because simultaneous stock episodes are not independent.

The formal interpretation must not be driven by pooled episode count.

---

## 8. Primary R0 portability metrics

Report at minimum:

- number of securities;
- number of eligible episodes;
- equal-stock mean expectancy;
- median stock expectancy;
- fraction of stocks with positive expectancy;
- 25th / 75th percentile stock expectancy;
- mean win rate;
- mean winner;
- mean loser;
- payoff ratio;
- profit factor;
- MFE <4 / 4–8 / >=8 ATR harvest;
- Markup / Markdown split;
- temporal blocks;
- sector breadth;
- concentration of positive expectancy.

### Positive-result concentration

Compute:

- share of summed positive stock expectancy contributed by top 1% of positive stocks;
- top 5%;
- best single stock;
- equal-stock mean after removing the best 1% of positive stocks.

Do not redefine the concentration metric after outcomes.

---

## 9. Temporal diagnostics

Frozen blocks:

- 2000–2004
- 2005–2009
- 2010–2014
- 2015–2019
- 2020–2026

A stock contributes to a block only through episodes whose entry occurs in that block.

Report equal-stock means and positive-stock breadth for every block with adequate coverage.

The 2015–2019 block remains a required stress diagnostic and may not be dropped.

---

## 10. Sector / size diagnostics

Use the provider's point-in-time sector classification where available.

Primary sector diagnostic:

- equal-stock mean expectancy within each sector;
- positive-stock breadth within each sector;
- leave-one-sector-out equal-stock expectancy.

If point-in-time market-cap data is available, freeze quartile boundaries by each episode entry date and report equal-stock results by size quartile.

If point-in-time market-cap metadata is unavailable, do **not** substitute a post-hoc size proxy after seeing outcomes.

---

## 11. Frozen interpretation gates

### Strong cross-sectional portability

All of the following must hold for R0:

1. equal-stock mean expectancy > 0;
2. median stock expectancy > 0;
3. at least **55%** of included stocks have positive expectancy;
4. top 1% of positive stocks contribute less than **25%** of summed positive stock expectancy;
5. equal-stock mean remains >0 after removing the best 1% of positive stocks;
6. at least **4 of 5** temporal blocks have positive equal-stock expectancy;
7. at least **8 of 11** standard equity sectors are positive where all 11 are represented with adequate sample;
8. no single sector is required to make the full equal-stock mean positive.

### Mixed portability

R0 equal-stock mean is positive, but one or more Strong gates fail.

### Weak / failed portability

Either:

- equal-stock mean <=0 **and** median stock expectancy <=0; or
- fewer than **45%** of stocks have positive expectancy.

Any result between the Mixed and Weak boundaries is reported as **Ambiguous**, not forced into a pass / fail label.

These labels are descriptive research gates, not production recommendations.

---

## 12. Warning-First risk-shaping gate

Warning-First is not required to beat R0 raw return.

Its portability question is different.

Report the fraction of stocks where Warning-First improves:

- realized bar volatility;
- max drawdown;
- 5% expected shortfall;
- MFE <4 ATR harvest.

Also report:

- MFE >=8 ATR harvest retention;
- turnover change;
- raw expectancy change.

### Strong defensive portability

All four defensive metrics above improve in at least **60%** of eligible stocks, and aggregate equal-stock MFE >=8 retention remains at least **70%** of R0.

Otherwise classify the defensive portability as Mixed / Weak from the full evidence; do not retune the 2 / 4 ATR latch.

---

## 13. Tail / dependence diagnostics

Because individual stocks are cross-sectionally correlated:

- do not interpret episode count as independent sample size;
- report results by stock and by sector;
- report calendar clustering of episodes;
- report concentration by stock and sector;
- report leave-one-sector-out results;
- where practical, use block bootstrap by calendar month / quarter as a diagnostic rather than naive IID episode bootstrap.

No significance threshold alone may promote a policy.

---

## 14. Calibration symbols excluded from OOS2

The Python classifier parity study may use the following stock symbols strictly for engineering calibration:

- NASDAQ:AAPL
- NYSE:JPM
- NYSE:XOM

These symbols are **excluded from the formal OOS2 economic cohort** regardless of their later results.

Already-inspected non-stock OOS1 instruments may also be used for parity.

No policy economics are to be inspected on the three calibration stocks during parity work.

---

## 15. Stop rules

After the first formal OOS2 outcome is inspected:

- no stock-specific thresholds;
- no sector-specific thresholds;
- no separate Markup / Markdown policy;
- no minimum-price / liquidity retuning;
- no changing the 5-episode inclusion rule;
- no dropping weak sectors;
- no deleting delisted losers;
- no BTC-style concentration repair;
- no new Resume trigger;
- no Warning-First v2;
- no adding a third policy because R0 / Warning-First disappoint.

A new hypothesis requires a new preregistered cohort.

---

## 16. Data-source lock still required

This preregistration freezes the research design.

Before formal OOS2 execution, add a short amendment that freezes:

- data provider;
- exact security-master source;
- delisting coverage;
- corporate-action fields;
- sector / market-cap metadata;
- identifier mapping;
- raw-data snapshot / checksum where feasible.

Until that amendment exists, no OOS2 economic output may be treated as formal.

---

## Decision authority

This OOS2 study tests **breadth and concentration**, not whether a few famous stocks look good.

The central question is:

> **Does the frozen trend-harvest architecture have positive expectancy across the cross-section, or is its apparent edge concentrated in a narrow minority of exceptional instruments?**

Refs #78, #80, #76.
