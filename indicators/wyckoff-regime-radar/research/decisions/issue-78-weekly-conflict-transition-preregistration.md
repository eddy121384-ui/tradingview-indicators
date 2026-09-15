# Issue #78 — Weekly conflict transition diagnostic preregistration

## Why this follow-up exists

The preregistered static weekly-context taxonomy did not produce a clean monotonic ordering across both daily Markup and Markdown. In particular, a weekly state that is already opposite the daily trend may be stale information rather than a useful new brake signal.

Before inspecting transition outcomes, freeze the narrower hypothesis:

> **Change may matter more than level.** A newly completed weekly flip into an opposing directional regime may be more informative than a weekly opposing regime that has already persisted for one or more completed weeks.

This remains diagnostic only. No exposure rule is selected here.

## Frozen directional-conflict definition

Use the same six-state semantics as the prior preregistration.

For daily Markup, opposing weekly directional states are:

- weekly Markdown
- weekly Redistribution

For daily Markdown, opposing weekly directional states are:

- weekly Markup
- weekly Reaccumulation

No asset-specific remapping.

## Frozen conflict-age classification

At any daily decision, use only the latest completed weekly bar (`week_close_time <= daily_event_time`) and its immediately preceding completed weekly bar.

- **Fresh directional conflict**: latest weekly state is opposing directional, previous weekly state was not opposing directional.
- **Persistent directional conflict**: latest weekly state is opposing directional and previous weekly state was also opposing directional.
- **No directional conflict**: latest weekly state is not opposing directional.

No Trendability threshold is added to this study.

## Primary event test — conflict arrives during an active daily trend

For each completed weekly bar that newly creates `Fresh directional conflict`, identify the first subsequent daily bar for the same market that:

1. occurs after that weekly close;
2. is still in the conflicting daily Markup / Markdown direction;
3. occurs before the next completed weekly close.

Use at most one daily observation per market × weekly conflict-flip event.

Measure directional normalized:

- next 1 / 5 / 10 / 20-bar move;
- same daily trend survival 5 / 10 / 20 bars.

Compare to observations sampled under `Persistent directional conflict` and `No directional conflict` using the same first-daily-bar-after-weekly-close convention.

## Secondary entry test

At fresh daily Markup / Markdown entry, classify the latest completed weekly context as:

- fresh directional conflict;
- persistent directional conflict;
- no directional conflict.

Compare frozen Persistence + Gentle episode return, MFE, duration, MFE >=4 ATR and MFE >=8 ATR rate.

## Weighting and stress tests

Primary aggregation is equal-market. Report Markup and Markdown separately; magnitude asymmetry is allowed, but no separate parameter sets may be invented.

Report 2010–2014, 2015–2019 and 2020–2026 only as stress slices. Do not tune to 2015–2019.

## Promotion gate

A fresh weekly flip is promising only if it is materially more adverse than both persistent conflict and no-conflict observations, with reasonably consistent cross-market ordering in both daily directions and non-trivial sample size.

If the signal is strong only for Markup or only for Markdown, record realized asymmetry but do not create direction-specific production parameters on this discovery sample.

## Non-goals

- no exposure cap percentages;
- no threshold optimization;
- no Trendability rescue layer;
- no asset-specific or direction-specific tuning;
- no classifier changes;
- no production promotion from this in-sample diagnostic.
