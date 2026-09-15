# Issue #78 — Weekly opposition age / maturity diagnostic preregistration

## Objective

Test whether the **maturity of an already-established opposing weekly directional regime** helps distinguish a harmless local daily counter-trend from a daily trend that is genuinely taking over.

This follows two prior findings:

1. a static opposing weekly context often marks smaller / shorter fresh daily trend opportunities, especially for Markdown, but is too asymmetric and stale to justify a universal ongoing brake;
2. a *fresh weekly flip* against an already-active daily trend is extremely rare, so transition-at-weekly-flip is not a practical state variable.

This study therefore focuses only on **fresh daily Markup / Markdown entries that begin while an opposing weekly directional regime is already active**.

No production exposure rule is selected here.

## Frozen causal join

For each fresh daily trend entry, use only the latest completed native-1W bar satisfying:

`week_close_time <= daily_entry_time`

Weekly spell age is computed using completed weekly bars only. No unfinished weekly bar or future weekly state is visible.

## Frozen opposing-weekly definition

For a fresh daily **Markup** entry, opposing weekly directional states are:

- weekly Markdown
- weekly Redistribution

For a fresh daily **Markdown** entry, opposing weekly directional states are:

- weekly Markup
- weekly Reaccumulation

The opposing weekly spell is continuous while weekly states remain within the relevant directional family. A switch between Markdown and Redistribution does **not** reset bearish weekly spell age; a switch between Markup and Reaccumulation does **not** reset bullish weekly spell age.

## Frozen age buckets

No cut point will be optimized after results are viewed. Use simple calendar-motivated completed-week buckets:

- **Young**: 1–4 completed weeks
- **Intermediate**: 5–13 completed weeks
- **Mature**: 14+ completed weeks

Rationale:

- 1–4 weeks ≈ first month of a weekly directional regime;
- 5–13 weeks ≈ established one-to-three-month regime;
- 14+ weeks ≈ mature multi-month regime.

The exact bucket boundaries are frozen before outcome inspection.

## Frozen hypothesis

The study is intentionally two-sided and does not assume monotonicity as fact.

Working hypothesis:

> A daily counter-trend that begins against a **young / intermediate** opposing weekly regime may be more likely to fail because the weekly regime is still structurally active; a daily counter-trend against a **mature** weekly regime may have more room to become a genuine takeover or large reversal.

A contrary monotonic pattern is allowed and must be reported rather than rationalized away.

## Primary outcomes at fresh daily trend entry

Using the already-frozen daily `Persistence + Gentle` management logic, report by age bucket and daily direction:

- equal-market mean episode return;
- episode MFE;
- episode duration;
- MFE >= 4 ATR rate;
- MFE >= 8 ATR rate;
- positive-return rate;
- sample count and markets represented.

## Cross-market consistency

For adjacent comparisons (`Young vs Intermediate`, `Intermediate vs Mature`) and extreme comparison (`Young vs Mature`), report:

- number of markets with the same ordering in return;
- number with the same ordering in MFE;
- sample counts per market/bucket.

Primary conclusions are equal-market weighted. Pooled counts are descriptive only.

## Temporal stress

Report the same bucket summaries for:

- 2010–2014
- 2015–2019
- 2020–2026

These are stress diagnostics only. **Do not tune bucket definitions to rescue 2015–2019.**

## Promotion gate

Weekly opposition age is considered promising only if:

1. the ordering is economically meaningful rather than tiny;
2. the ordering is reasonably consistent across markets;
3. evidence exists in both daily Markup and Markdown, allowing magnitude asymmetry but not separate rule definitions;
4. the result is not created solely by one calendar era;
5. all three buckets have non-trivial representation.

If the signal is direction-specific or bucket counts are thin, record it as descriptive evidence only.

## Explicit non-goals

- no weekly Trendability rescue layer;
- no optimized age threshold;
- no asset-specific rules;
- no direction-specific production parameters;
- no classifier changes;
- no exposure cap selection;
- no production promotion from this discovery sample.
