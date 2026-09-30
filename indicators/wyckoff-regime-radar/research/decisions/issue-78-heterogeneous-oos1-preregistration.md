# Issue #78 — Heterogeneous OOS Challenge 1 Preregistration
## Frozen R0 / R0 + Warning-First on entirely new asset classes

## Purpose

Issue #78 daily discovery used only the frozen nine-market FX / sovereign-yield universe.

The current frozen system frontier is:

1. **R0 No De-risk**
   - 25% Probe from fresh formal Markup / Markdown;
   - first qualifying post-entry breakout after the frozen initial waiting period;
   - fixed three-bar acceptance / follow-through window;
   - P0 / P1 / P2 earn 100% Full at t+3;
   - P3 and episodes without a usable B3 breakout remain at Probe;
   - no Resume gate before add-risk.

2. **R0 + Warning-First**
   - identical R0 earned participation;
   - frozen 2 / 4 entry-ATR giveback damage latch;
   - 2–4 ATR giveback reduces earned exposure by 25pp;
   - 4+ ATR reduces by 50pp;
   - minimum positive exposure remains 25%;
   - a new favorable close-path extreme clears the latch.

The same-sample composition study did **not** justify further parameter work.

The next legitimate question is genuine portability:

> **Do the frozen R0 and R0 + Warning-First architectures retain useful directional / risk-management behavior on asset classes that were completely absent from the Issue #78 discovery universe?**

No result from the new cohort may be inspected before this preregistration.

## OOS status

This is the first **heterogeneous-market OOS challenge** for the current frozen architecture.

The six markets below were not part of the nine-market discovery sample used to create or select:

- the Markup / Markdown regime interpretation;
- the breakout / t+3 acceptance construction;
- P0 / P1 / P2 / P3;
- R0 Immediate;
- Warning-First 2 / 4 ATR deterioration logic.

The underlying Issue #68 classifier itself predates this challenge and remains frozen.

This is still historical backtesting, not prospective forward validation. Passing this challenge would support portability, not production readiness.

## Frozen OOS universe

Use exactly six daily TradingView feeds, chosen before outcome inspection and balanced across three new asset classes.

### Equity indices

- `TVC:SPX` — S&P 500 Index
- `NASDAQ:NDX` — Nasdaq-100 Index

### Precious metals

- `OANDA:XAUUSD` — spot gold / USD
- `OANDA:XAGUSD` — spot silver / USD

### Crypto

- `BITSTAMP:BTCUSD` — Bitcoin / USD
- `BITSTAMP:ETHUSD` — Ether / USD

No market may be dropped because its result is unfavorable.

No substitute ticker may be introduced after results are viewed. If a feed cannot be exported, record it as unavailable and stop before interpreting the reduced cohort unless a replacement is separately preregistered.

## Why these markets

The construction deliberately changes the economic source of trends:

- corporate / equity-index risk;
- monetary / commodity metals;
- 24/7 crypto assets.

It also avoids adding more FX pairs or sovereign yields, which would be too close to the discovery universe.

Continuous futures are excluded from this first OOS cohort to avoid introducing roll-gap handling as an additional research degree of freedom.

## Frozen classifier / representation

Use the exact frozen Issue #68 RC classifier source with all existing parameters unchanged.

No weekly cap, no weekly Trendability, and no new MTF rule are added.

Representation remains the frozen Auto logic:

- yield feeds would use Yield Level;
- all six preregistered OOS feeds should resolve to Price Log.

If any feed unexpectedly resolves to Yield Level, stop and diagnose the feed rather than silently overriding representation after viewing results.

## Native timeframe

Run every feed on **1D native bars**.

Do not resample intraday data.

Do not reuse the old nine-market daily CSVs in the OOS result.

## Forward-logger contract

Reuse the accepted Issue #76 forward-behavior schema mechanically:

- event bar = current bar - 20;
- event-time formal stage and ATR scale are frozen at the event bar;
- 1 / 5 / 10 / 20-bar future movement is already observed when a log row is emitted;
- raw high / low excursions are exported so relative OHLC can be causally reconstructed;
- only confirmed bars may log.

The OOS logger may change only:

- indicator / export labels;
- the allowed-feed whitelist;
- a cohort provenance field.

Classifier semantics must not change.

## Episode construction

Reuse Issue #78 episode construction exactly:

- completed known-start Markup / Markdown spells only;
- right-censored terminal episodes excluded;
- episode entry ATR frozen as the normalizer;
- same direction alignment.

Do **not** require the new cohort to reproduce the old 68,118-row / 1,624-episode counts.

Those counts belong only to the discovery cohort.

## Breakout / acceptance construction

Reuse without modification:

- wait through the first five completed post-entry bars;
- define the causal five-bar pre-breakout box;
- use the first genuine close beyond the box;
- require a complete t+1 ... t+3 acceptance window;
- classify at t+3 into:
  - P0 No-touch / Immediate Expansion;
  - P1 Wick Retest / Hold;
  - P2 Close Re-entry / Reclaim;
  - P3 Failed Acceptance.

No new breakout buffer.

No compression gate.

No Resume requirement.

No market-specific lookback.

## Frozen policies

### Policy A — R0 No De-risk

- 25% Probe from fresh formal trend entry;
- remain Probe before a usable t+3 state;
- P0 / P1 / P2 -> earned Full at t+3 for the next move;
- P3 -> stay Probe;
- no usable B3 event -> stay Probe;
- once Full is earned, remain Full until formal-regime loss.

### Policy B — R0 + Warning-First

Identical earned participation.

Apply frozen Warning-First from formal episode entry:

- giveback <2 entry ATR -> no reduction;
- 2–4 -> minus 25pp;
- 4+ -> minus 50pp;
- minimum positive exposure 25%;
- reductions latch;
- new favorable close-path extreme resets the latch for the following move;
- R0 promotion does not itself clear an existing latch.

## Accounting baselines

Also report:

- Probe Only;
- Formal Hold.

They are diagnostics only and cannot replace the two frozen candidates.

## Primary aggregation

Two primary views are required.

### Equal-market

Each of the six markets receives equal weight.

### Equal-asset-class

First average the two markets inside each preregistered asset class, then average:

- Equity indices;
- Precious metals;
- Crypto.

This prevents the result from being dominated by whichever class has more episodes or bars.

Do not pooled-row weight the main conclusion.

## Heterogeneous-calendar accounting

Because crypto trades seven days per week while the traditional feeds do not, raw `sqrt(252)` annualization is not a universal primary metric.

Primary path metrics therefore include:

- cumulative normalized return;
- mean normalized return per observed daily bar;
- daily normalized volatility;
- daily return / volatility ratio;
- max drawdown in normalized return units;
- 5% expected shortfall;
- 1% daily quantile;
- average exposure;
- turnover per completed episode;
- cumulative turnover per calendar year.

Secondary calendarized return is:

> cumulative normalized return / elapsed calendar years in the accepted path.

No fixed 252-vs-365 market-specific trading parameter is introduced.

## Episode-level metrics

For each policy:

- mean / median normalized episode harvest;
- win rate;
- profit factor;
- average exposure;
- turnover;
- MFE;
- large-trend capture;
- failed-trend damage.

Reuse frozen MFE slices:

- MFE <4 ATR;
- MFE 4–8 ATR;
- MFE >=8 ATR.

## Evidence-state portability

Report without retuning:

- fraction of completed trend episodes obtaining a usable B3 event;
- P0 / P1 / P2 / P3 prevalence;
- P1 / P2 combined prevalence;
- P3 failed-acceptance prevalence;
- t+3 follow-through distribution.

This asks whether the evidence architecture itself remains populated on new asset classes.

Do not alter rules if one class produces fewer breakout states.

## Primary R0 portability questions

For R0 No De-risk report:

- equal-market and equal-class mean episode return;
- sign by each market;
- max drawdown;
- 5% ES;
- MFE<4 damage;
- MFE>=8 harvest;
- top-1%-winner concentration.

Allowed interpretation:

- broad positive portability;
- mixed / class-dependent portability;
- no portable economic edge detected.

Do not declare stable alpha.

## Warning-First portability questions

Relative to R0 No De-risk test whether frozen Warning-First still shows the expected risk-shaping semantics:

- MFE<4 harvest should improve;
- max drawdown and/or ES should improve;
- volatility should decrease;
- turnover may increase;
- MFE>=8 harvest may decrease.

Also report:

- equal-market delta;
- equal-class delta;
- market sign breadth;
- class sign breadth.

The study is testing whether the **shape of the tradeoff** transports, not whether Warning-First must win a single scalar score.

## Temporal diagnostics

Where history permits, retain the existing calendar slices:

- 2010–2014;
- 2015–2019;
- 2020–2026.

Markets without history in an era remain transparently unavailable; do not backfill or substitute them.

Do not treat unequal era coverage as equal evidence.

## Direction diagnostics

Report Markup / Markdown separately with unchanged rules.

No direction-specific tuning.

## Tail-dependence audit

For each market / policy report:

- share of positive episode harvest from the top 1% winners;
- result after removing the single best episode;
- result after removing the top 1% winning episodes.

Then aggregate equal-market and equal-class.

## OOS interpretation gates

### Strong portability

Supported only if:

- R0 economic value is not confined to one asset class;
- at least two of the three preregistered asset classes show positive equal-class mean episode return;
- the overall equal-class mean episode return is positive;
- no single market supplies the majority of aggregate positive result;
- the large-trend / failed-trend mechanism remains recognizable.

This is still not production approval.

### Mixed portability

Use this classification when:

- aggregate outcome is positive but concentrated in one class;
- class signs conflict materially;
- evidence-state prevalence changes enough to make the architecture sparse;
- or tail dependence becomes extreme.

### Portability failure

Use this classification when:

- equal-class mean episode return is non-positive;
- and/or positive result is isolated to one market / class with broad negative breadth.

Do not tune the architecture to rescue the failed OOS cohort.

### Warning-First

Treat Warning-First as portable defensive management only if its risk reduction remains broad across at least two asset classes without a catastrophic loss of R0 trend harvest.

No new 2 / 4 ATR threshold may be introduced if it fails.

## Stop rules

After this cohort is inspected:

- no market replacement;
- no dropping crypto because it is “too different”;
- no dropping metals because they are “macro special”;
- no SPX / NDX-specific parameter;
- no asset-class-specific R0 or Warning-First rule;
- no breakout-window change;
- no new Resume gate;
- no Warning-First v2;
- no ATR threshold search.

If the architecture fails:

> record the failure and diagnose semantics before any new hypothesis.

If it survives:

> freeze the surviving candidates and proceed to prospective or a separately preregistered second OOS cohort.

## Intended answer

> **Does the frozen Issue #78 evidence → participation → deterioration architecture transport from FX / sovereign yields into equity indices, precious metals, and crypto without any market-specific tuning?**

PR #80 remains Draft / open / unmerged.

Refs #78, #80, #76.
