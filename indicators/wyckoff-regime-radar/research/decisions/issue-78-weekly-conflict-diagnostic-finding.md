# Issue #78 — Weekly conflict diagnostic finding

Status: discovery / in-sample diagnostic only. No production policy selected.

Preregistration: `issue-78-weekly-conflict-diagnostic-preregistration.md`.

## Data integrity

- accepted Issue #76 daily rows: 68,118
- native 1W Issue #78 rows: 16,372
- completed known-start daily trend episodes: 1,624
- causal join: latest weekly close satisfying `week_close_time <= daily_event_time`
- no classifier or episode reconstruction changes

## Main finding

The static completed-weekly context does **not** produce a robust universal brake taxonomy across both daily Markup and Markdown.

The important asymmetry is:

- weekly conflict is meaningfully adverse for daily Markdown;
- the same concept is not reliably adverse for daily Markup;
- therefore a symmetric universal weekly brake is not justified from this sample.

### Daily-bar forward behavior

Equal-market directional outcomes:

#### Daily Markup

| Weekly context | N bars | fwd 10 | fwd 20 | 10-bar survival |
|---|---:|---:|---:|---:|
| Aligned directional | 9,233 | -0.070 | -0.126 | 0.748 |
| Other / neutral | 11,554 | +0.067 | -0.054 | 0.707 |
| Turn-risk conflict | 1,380 | +0.253 | +0.310 | 0.745 |
| Directional conflict | 4,350 | +0.144 | +0.227 | 0.711 |

For Markup, neither frozen conflict family is consistently adverse. Directional conflict is worse than Other on 10-bar forward move in only 3/8 comparable markets.

#### Daily Markdown

| Weekly context | N bars | fwd 10 | fwd 20 | 10-bar survival |
|---|---:|---:|---:|---:|
| Aligned directional | 13,405 | +0.128 | +0.267 | 0.759 |
| Other / neutral | 13,234 | +0.402 | +0.616 | 0.746 |
| Turn-risk conflict | 992 | -0.184 | -0.574 | 0.704 |
| Directional conflict | 2,646 | +0.031 | +0.053 | 0.654 |

For Markdown the conflict information is much clearer:

- Directional conflict vs Other: 10-bar forward move worse in 7/9 markets; 10-bar survival worse in 9/9.
- Turn-risk conflict vs Other: 10-bar forward move worse in 6/8 comparable markets.

This is realized directional asymmetry, not permission to create separate long/short parameters.

## Fresh daily trend entry

Using the frozen Persistence + Gentle daily management policy:

### Markup entry

| Weekly context | Entries | mean return | mean MFE | mean duration | MFE >= 8 |
|---|---:|---:|---:|---:|---:|
| Aligned directional | 165 | +0.364 | 4.57 | 41.2 | 17.1% |
| Other / neutral | 361 | +0.298 | 5.46 | 32.9 | 17.2% |
| Turn-risk conflict | 42 | +1.020 | 5.87 | 50.3 | 24.1% |
| Directional conflict | 238 | -0.013 | 3.52 | 29.3 | 12.8% |

Directional conflict at fresh Markup entry does reduce subsequent opportunity size: MFE is lower than Other in 7/8 comparable markets and MFE >= 8 is lower in 6/8. However the return ordering is only 5/8 versus Other and is not robust versus Aligned.

### Markdown entry

| Weekly context | Entries | mean return | mean MFE | mean duration | MFE >= 8 |
|---|---:|---:|---:|---:|---:|
| Aligned directional | 230 | +0.339 | 5.46 | 40.6 | 20.6% |
| Other / neutral | 368 | +0.834 | 6.22 | 38.3 | 22.2% |
| Turn-risk conflict | 53 | -0.122 | 4.48 | 31.0 | 8.8% |
| Directional conflict | 167 | -0.006 | 3.89 | 28.0 | 15.0% |

Directional conflict is lower-return than Other in 8/9 markets, lower-MFE in 7/9 and shorter-duration in 8/9.

## Weekly Trendability severity split

The inherited `wtrend > 66.67` split is too thin to support a conclusion inside directional conflict:

- fresh Markup entries: 10 high-trendability conflict cases
- fresh Markdown entries: 16 high-trendability conflict cases

No `MFE >= 8` episode occurred in those 26 cases, but the sample is too small and sparse across markets to promote this as a brake rule.

## Temporal stress

The entry-return ordering is not stable across 2010–2014, 2015–2019 and 2020–2026. In particular, Directional conflict is not uniformly worse than Other / neutral in all eras. Therefore the static weekly state is not a stable solution to the 2015–2019 failure regime.

## Decision

**Do not promote any current static weekly-context bucket into a universal ongoing exposure brake.**

The data support a narrower descriptive statement:

> An opposite weekly directional context often marks smaller / shorter fresh daily trend opportunities, especially for Markdown, but a static weekly state is too stale and asymmetric to justify continuously capping exposure.

The next preregistered diagnostic asks whether a **new weekly flip into opposition** is more informative than merely being in an already-opposite weekly state. If fresh opposition events are too rare, that hypothesis should be rejected on sample-size grounds without tuning.
