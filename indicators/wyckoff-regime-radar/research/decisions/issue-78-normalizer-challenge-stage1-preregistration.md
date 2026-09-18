# Issue #78 — Normalizer Challenge Stage 1 Preregistration

## Purpose

Test whether the apparent usefulness of post-entry directional progress is specific to the current episode-entry ATR denominator, or whether the information survives under conceptually different ex-ante scale estimators.

This study changes **only the denominator used to express progress**. The underlying price-path numerator and the formal Markup / Markdown opportunity regime remain frozen.

Primary question:

> **Is directional progress itself informative, or did the earlier Issue #78 findings depend materially on choosing entry ATR as the measuring stick?**

## Critical fairness correction

The existing Large / Failed labels are defined using final MFE in **entry-ATR units**:

- Failed / small: final MFE <4 entry ATR;
- Large: final MFE >=8 entry ATR.

Those labels are useful legacy diagnostics, but they are ATR-dependent and therefore cannot be the sole primary outcome in a study whose purpose is to challenge ATR as the normalizer.

Primary outcomes in this study are therefore **scale-free future outcomes**.

The old Large / Failed contrast may still be reported as a secondary legacy bridge, but it may not determine the research decision.

## Frozen sample

Reuse the accepted Issue #76 nine-market daily sample:

- 68,118 accepted event rows;
- 1,624 completed known-start Markup / Markdown episodes;
- no classifier change;
- no market-specific rule;
- causal information only.

## Frozen normalizers

All scales are fixed at episode entry and remain constant for the episode.

### N1 — Entry ATR baseline

Existing Issue #78 denominator:

- FX / price representation: entry `scale`;
- yield-level representation: entry `scale × 100`, matching existing logger semantics.

This is the frozen benchmark.

### N2 — Pre-entry 20-move realized sigma

Use the 20 completed one-bar `move1` observations immediately preceding the fresh trend-entry row.

Requirements:

- prior event bars must be consecutive;
- no current-entry or post-entry move may enter the estimate;
- sample standard deviation (`ddof=1`);
- scale must be finite and strictly positive.

The 20-move window is frozen before outcomes are inspected.

### N3 — Pre-entry 20-move median absolute move

Use the same 20 strictly pre-entry consecutive `move1` observations.

Scale:

`median(abs(move1))`

This is a robust move-size estimator available from the accepted logger without inventing OHLC / true-range data that are not present.

The 20-move window is identical to N2 and is frozen before outcomes are inspected.

## Eligibility

An episode is eligible for the primary three-way comparison only if:

- all three normalizers are finite and positive;
- 20 consecutive pre-entry moves are available;
- the episode has at least 10 completed post-entry moves for the 10-move checkpoint analysis.

A separate 5-move checkpoint may use episodes with at least 5 completed post-entry moves, subject to the same normalizer-availability rule.

No imputation.

## Frozen progress feature

For an active trend episode and checkpoint `k`:

`progress_k = direction_aligned_cumulative_move_from_entry / entry_fixed_normalizer`

Compute at:

- first 5 completed post-entry moves;
- first 10 completed post-entry moves.

The numerator is identical for N1 / N2 / N3. Only the denominator changes.

## Primary scale-free future outcomes

At each checkpoint, using only path **after** the checkpoint:

### O1 — Future favorable-extreme recovery / extension

Binary:

> Does the same formal episode later make a new favorable cumulative close-path extreme above the running favorable extreme known at the checkpoint?

This outcome uses no ATR / sigma / range threshold.

### O2 — Positive future net move

Binary:

> Is the direction-aligned cumulative move from checkpoint close to formal regime end positive?

No magnitude normalizer is used.

### O3 — Remaining life >=20 completed moves

Binary:

> Does the formal trend remain active for at least 20 additional completed moves after the checkpoint?

This is a duration outcome independent of price scale.

### O4 — Remaining life

Continuous count of completed moves after the checkpoint.

Used descriptively for rank / quintile gradients.

## Secondary legacy outcome

Report the prior ATR-defined Large-vs-Failed contrast only as a bridge to earlier Issue #78 work.

It must be labeled explicitly as **ATR-dependent legacy diagnostic**.

It cannot be used to select the preferred normalizer.

## Primary comparison methods

### 1. Cross-market AUC

For each normalizer × checkpoint × binary scale-free outcome:

- compute AUC within each market;
- report equal-market mean AUC;
- report median AUC;
- report count of markets with AUC >0.5.

No pooled-only conclusion.

### 2. Within-market quintiles

Within each market, rank normalized progress into quintiles.

For Q1→Q5 report equal-market means of:

- favorable-extension probability;
- positive-future-net probability;
- remaining-life>=20 probability;
- mean remaining life.

A useful normalizer should create an ordered gradient without market-specific thresholds.

### 3. Temporal robustness

Repeat the AUC and Q5-v-Q1 direction in:

- 2010–2014;
- 2015–2019;
- 2020–2026.

2015–2019 remains a required stress era.

### 4. Direction robustness

Report Markup and Markdown separately as diagnostics only.

No separate direction-specific normalizer may be selected.

## Normalizer ranking stability

Because all three features share the same numerator, report:

- Pearson correlation;
- Spearman rank correlation;
- share of episodes assigned to the same quintile;
- share assigned within one quintile.

This answers whether changing the denominator materially changes which episodes appear to have strong proof.

## Stage-1 decision logic

ATR is considered **not special** if:

- sigma20 and / or median-abs20 produce very similar cross-market AUCs;
- quintile gradients remain ordered;
- temporal and direction behavior remain broadly similar;
- episode rankings remain highly correlated.

In that case the correct general statement is:

> directional progress is the information-bearing feature; ATR is mainly one practical normalization choice.

A challenger is considered worth promoting to Stage 2 economic policy testing only if it shows:

- materially stronger scale-free outcome separation than ATR;
- improvement in a clear majority of markets;
- no obvious direction dependence;
- no collapse in 2015–2019.

No production decision is allowed from Stage 1.

## Stage 2 if warranted

Only after Stage 1 results are frozen may surviving normalizers be converted into matched-confirmation-cost live sizing rules and audited for:

- confirmation tax;
- normalized return;
- volatility;
- Sharpe / Sortino;
- drawdown;
- left tail;
- turnover;
- equal-vol return.

Thresholds for challenger normalizers must be calibrated mechanically to matched confirmation cost rather than optimized on PnL.

## Guardrails

- no alternate 10 / 15 / 30 / 60-day normalizer lookback search;
- no alternative robust-statistic search after results;
- no EWMA lambda search;
- no GARCH fitting;
- no market-specific thresholds;
- no direction-specific normalizers;
- no classifier changes;
- no use of future `rv5/rv10/rv20` logger fields in entry-scale construction;
- no treating the ATR-defined Large / Failed label as a neutral primary target;
- no policy / Sharpe optimization in Stage 1.

## Intended answer

> **When the same directional price progress is measured with ATR, pre-entry realized sigma, or a robust pre-entry move scale, do we learn essentially the same thing about future trend continuation?**

Refs #78, #80, #76.
