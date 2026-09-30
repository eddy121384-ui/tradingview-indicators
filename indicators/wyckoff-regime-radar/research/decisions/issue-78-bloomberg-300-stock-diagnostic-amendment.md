# Issue #78 — Bloomberg 300-Stock Diagnostic OOS2 Amendment

## Status

Frozen **before any 300-stock R0 / Warning-First economic result is inspected**.

This amendment does not replace the formal point-in-time / delisted-security OOS2 preregistration.

It defines the already-approved **survivorship-limited Bloomberg diagnostic cohort** created by Issue #119.

PR #80 remains Draft / open / unmerged.

---

## 1. Cohort

Frozen universe:

- 300 current U.S. equities;
- 100 from SPX Index;
- 100 from MID Index;
- 100 from SML Index;
- deterministic equal-sector sampling inside each sleeve;
- 11 sectors represented;
- AAPL / JPM / XOM excluded before sampling.

Universe SHA-256:

`e6f07371c9306f2598115cb886cc1cd5d4970d9fdc5e87dd1882bbac304c5712`

This cohort is **not survivorship-bias-free**.

Any result from this study must be labeled diagnostic and cannot replace the later point-in-time / delisted-security confirmation.

---

## 2. Raw data

Provider:

> Bloomberg Desktop API

Frozen historical end:

> 2026-08-31

Classifier OHLCV normalization and raw-file provenance are frozen by Issue #119.

Final snapshot:

- 300 / 300 securities complete;
- 0 failed securities;
- 1,525,618 raw rows;
- 326 audited OHLC range repairs across 35 securities;
- no failed security replaced.

---

## 3. Frozen classifier and policies

Classifier:

- exact frozen Issue #78 Python mirror;
- Git blob:
  `1eec08e791403453853b589373bb2270c508c3bb`.

Policies:

- `R0_NoDerisk`;
- `R0_WarningFirst`.

No third policy is permitted in this diagnostic.

No classifier threshold, R0 rule, Warning-First rule, B3 rule or t+3 path rule may be changed after outcomes are inspected.

---

## 4. Event construction

Use native daily Bloomberg rows.

For Price Log:

- close coordinate = `log(close)`;
- high coordinate = `log(high)`;
- low coordinate = `log(low)`;
- episode scale = frozen classifier `symATR`;
- one-bar move = next log close minus current log close;
- one-bar favorable / adverse extreme is measured from current close to next high / low.

A fresh trend entry is:

- formal stage becomes 2 (Markup) or 5 (Markdown);
- previous effective formal stage is different.

A row with incomplete or nonpositive OHLC is not economically executable and acts as an episode boundary.

A completed episode must:

- begin at a fresh Markup / Markdown transition;
- end because the effective formal stage changes before the frozen historical end;
- have finite one-bar move / high / low coordinates through the episode.

An episode still open at the frozen historical end or cut by unusable OHLC is reported as censored and is not silently treated as completed.

---

## 5. Entry eligibility

At the fresh entry bar, require all of the following:

1. entry date in 2000-01-03 through 2026-08-31;
2. at least 252 prior valid OHLC daily rows;
3. split-adjusted close >= USD 5.00;
4. the last 60 sessions ending at the entry bar all have finite close and volume;
5. trailing 60-session median `close * volume` >= USD 5,000,000.

The 60-session liquidity window includes the entry bar and uses no future data.

A stock with no structurally initialized classifier history naturally contributes zero eligible episodes.

No name is replaced because it has short history, missing history, or weak performance.

---

## 6. Primary stock inclusion

Primary cross-sectional unit:

> one stock, one vote.

A stock enters the primary equal-stock table only if it has at least:

> **5 completed eligible episodes**

This is unchanged from the original preregistration.

Stocks with fewer than 5 episodes stay in coverage diagnostics.

---

## 7. Temporal adequacy rule

Frozen blocks:

- 2000-2004
- 2005-2009
- 2010-2014
- 2015-2019
- 2020-2026

For each block:

- a stock contributes if it has at least one completed eligible episode whose entry is in that block;
- the block is considered adequately represented for the Strong-gate count only if at least **20 stocks** contribute.

The equal-stock mean gives one vote to each contributing stock regardless of its episode count.

This adequacy threshold is frozen before outcomes.

---

## 8. Sector adequacy rule

Use the frozen Bloomberg cohort sector metadata from Issue #119.

This is current cohort metadata, not point-in-time historical sector metadata, and must be labeled diagnostic.

A sector is considered adequately represented for the Strong-gate sector count if at least:

> **5 primary-table stocks**

are present in that sector.

Sector mean expectancy gives one vote per qualifying stock.

Leave-one-sector-out expectancy uses the same primary-table stock set.

---

## 9. Size-sleeve diagnostic

Use only the already-frozen cohort sleeve:

- large;
- mid;
- small.

Do not derive a new historical market-cap quartile after outcomes are visible.

Size-sleeve results are diagnostic and do not alter the preregistered Strong gate.

---

## 10. Primary R0 metrics

For primary-table stocks report:

- mean completed-episode expectancy;
- median stock expectancy;
- positive-stock fraction;
- 25th / 75th percentile stock expectancy;
- equal-stock mean win rate;
- equal-stock mean winner;
- equal-stock mean loser;
- equal-stock payoff ratio;
- equal-stock profit factor;
- MFE <4 / 4-8 / >=8 ATR harvest;
- Markup / Markdown split;
- temporal blocks;
- sector breadth;
- current size-sleeve breadth;
- positive-expectancy concentration.

Positive concentration:

- top 1% of positive stocks;
- top 5% of positive stocks;
- best single positive stock;
- equal-stock mean after removing the top 1% of positive stocks.

For top-x% counts use `ceil(x% * number of positive stocks)`, with minimum one when at least one positive stock exists.

---

## 11. Warning-First defensive metrics

At the stock level compare `R0_WarningFirst` against `R0_NoDerisk`.

Defensive improvement means:

- bar volatility: lower;
- max drawdown: lower;
- ES5: higher / less negative;
- MFE <4 ATR mean harvest: higher.

Report the fraction of eligible stocks improving each metric.

For a metric, the denominator is stocks for which both policies have a finite value for that metric.

Also report:

- equal-stock MFE >=8 ATR harvest retention;
- turnover change;
- raw expectancy change.

MFE >=8 retention is:

> equal-stock Warning-First mean harvest in the >=8 slice divided by equal-stock R0 mean harvest in the >=8 slice

when the R0 denominator is positive and finite.

---

## 12. Interpretation

Apply the already-frozen R0 Strong / Mixed / Weak / Ambiguous gates exactly as preregistered, subject to the frozen temporal and sector adequacy definitions above.

Because this cohort is survivorship-limited, the label must be prefixed:

> **Diagnostic**

Examples:

- Diagnostic Strong;
- Diagnostic Mixed;
- Diagnostic Weak / Failed;
- Diagnostic Ambiguous.

A Diagnostic Strong result is not production approval and does not replace the later survivorship-aware confirmation.

---

## 13. Execution firewall

The analyzer code, aggregation rules, output schema, and tests must be committed before the first economic run.

After the first economic output is inspected:

- no stock replacement;
- no new eligibility threshold;
- no change to the 5-episode rule;
- no temporal adequacy change;
- no sector adequacy change;
- no direction-specific policy;
- no Warning-First v2;
- no third policy;
- no threshold optimization.

---

## Next gate

> Freeze and CI-test the analyzer, then run it once on the untouched 300-stock Bloomberg snapshot.

Refs #78, #119, #120, #80.
