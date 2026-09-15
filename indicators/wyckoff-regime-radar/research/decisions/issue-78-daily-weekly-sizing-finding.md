# Issue #78 — Daily Trigger × Weekly Sizing Context finding

Date: 2026-09-15

Status: **discovery / in-sample finding**. This is not out-of-sample validation and does not authorize production parameter changes.

## Question

Does native weekly context improve the current daily medium-horizon trend-management candidate, or does it mainly make the equity path look calmer by suppressing too much participation?

Frozen daily benchmark:

- Daily formal trend trigger.
- Persistence participation ramp: 25% / 50% / 75% / 100% at age 0 / 5 / 10 / 20 bars.
- Gentle damage latch.

Preregistered weekly overlays:

1. **Weekly Direction**
   - same weekly formal direction: cap 100%
   - opposite weekly formal direction: cap 25%
   - other / non-trend weekly state: cap 50%

2. **Weekly Direction + Trendability**
   - opposite direction: cap 25%
   - other / non-trend: cap 50%
   - same direction but weekly Trendability <= 66.67: cap 50%
   - same direction and weekly Trendability > 66.67: cap 100%

Weekly context is native 1W and joined causally only when `week_close_time <= daily_event_time`. No incomplete weekly bar is visible to a daily decision.

## Evidence quality

All nine frozen markets were exported successfully:

- OANDA:EURUSD
- OANDA:GBPUSD
- OANDA:USDJPY
- TVC:US10Y
- TVC:DE10Y
- TVC:FR10Y
- TVC:GB10Y
- TVC:AU10Y
- TVC:JP10Y

Weekly rows accepted: **16,372**.

Daily accepted formal-stage rows remain **68,118** and completed known-start trend episodes remain **1,624** (806 Markup, 818 Markdown).

For every daily trend-episode bar used by this study, a causally completed weekly observation was available: weekly-missing fraction = **0**.

## Primary result

Equal-market aggregate across all 1,624 completed trend episodes:

| Policy | Mean episode return (entry-ATR) | Positive markets | Median PF | Mean max DD | Bootstrap 95% | Top-1%-winner removal mean |
|---|---:|---:|---:|---:|---:|---:|
| Daily Persistence + Gentle | **+0.3322** | 8/9 | **1.260** | 37.35 | +0.135 to +0.532 | +0.0497 |
| + Weekly Direction | +0.2536 | 8/9 | 1.220 | **31.13** | +0.097 to +0.416 | +0.0325 |
| + Weekly Direction + Trendability | +0.2344 | 8/9 | 1.216 | **29.56** | +0.088 to +0.389 | +0.0178 |

Relative to the daily benchmark:

- Weekly Direction retains **76.3%** of mean return, while reducing mean max drawdown by **16.6%** and turnover by **29.6%**.
- Weekly Direction + Trendability retains **70.5%** of mean return, while reducing mean max drawdown by **20.9%** and turnover by **38.6%**.
- Paired equal-market bootstrap delta versus the daily benchmark is negative for both preregistered weekly overlays:
  - Weekly Direction: **-0.0786 ATR**, 95% CI **[-0.1448, -0.0172]**.
  - Weekly Direction + Trendability: **-0.0978 ATR**, 95% CI **[-0.1704, -0.0309]**.

So the weekly overlays are not free improvements. They buy a smoother / lower-turnover path by giving up expected trend harvest.

## Where the trade-off comes from

### Short / failed trend episodes (`MFE < 4 ATR`)

The weekly overlays help materially.

Equal-market mean improvement versus the daily benchmark:

- Weekly Direction: **+0.1513 ATR**, paired bootstrap 95% CI **[+0.1289, +0.1741]**.
- Weekly Direction + Trendability: **+0.1931 ATR**, 95% CI **[+0.1691, +0.2177]**.

For Markup, mean retained move improves from -1.043 to -0.898 / -0.857 ATR.
For Markdown, it improves from -1.028 to -0.869 / -0.826 ATR.

### Genuine large trends (`MFE >= 8 ATR`)

The same overlays suppress too much upside/downside participation.

Equal-market mean loss versus the daily benchmark:

- Weekly Direction: **-1.1748 ATR**, 95% CI **[-1.6124, -0.8062]**.
- Weekly Direction + Trendability: **-1.4348 ATR**, 95% CI **[-1.8733, -1.0687]**.

Markup large-trend harvest:

- Daily: **5.32 ATR**
- Weekly Direction: **3.97 ATR**
- Weekly Direction + Trendability: **3.80 ATR**

Markdown large-trend harvest:

- Daily: **5.88 ATR**
- Weekly Direction: **4.89 ATR**
- Weekly Direction + Trendability: **4.61 ATR**

This is the core economic result: weekly context is useful at suppressing failed trends, but the current symmetric `same / other / opposite` cap architecture over-suppresses real large trends.

## Temporal stress

Equal-market mean episode return by era:

| Era | Daily | + Weekly Direction | + Weekly Direction + Trendability |
|---|---:|---:|---:|
| 2010–2014 | **+0.7273** (8/9 positive) | +0.6314 (8/9) | +0.5401 (8/9) |
| 2015–2019 | **-0.0975** (2/9) | -0.0598 (4/9) | -0.0501 (4/9) |
| 2020–2026 | +0.0981 (5/9) | **+0.1105** (5/9) | +0.1019 (5/9) |

The 2015–2019 weakness is not solved. Weekly context makes it less bad and broadens positive-market breadth from 2/9 to 4/9, but expectancy remains negative.

The 2010–2014 period pays a clear opportunity cost from weekly suppression. The 2020–2026 period gets only a small improvement from direction alone.

## Direction is informative; Trendability does not earn its extra restriction

At fresh daily trend entry, grouping the *daily benchmark outcome* by the last completed weekly context shows:

Markup:

- weekly opposite direction: equal-market mean about **-0.013 ATR**
- weekly same direction, Trendability > 66.67: **+0.226 ATR** (n=23)
- weekly same direction, Trendability <= 66.67: **+0.371 ATR**
- weekly other / non-trend: **+0.306 ATR**

Markdown:

- weekly opposite direction: about **-0.001 ATR**
- weekly same direction, Trendability > 66.67: **+0.113 ATR** (n=33)
- weekly same direction, Trendability <= 66.67: **+0.399 ATR**
- weekly other / non-trend: **+0.725 ATR**

The very small `same + high Trendability` entry cohorts do not justify treating `>66.67` as a full-size confirmation gate. In this discovery sample, weekly Trendability adds restriction without showing compensating economic value.

The stronger diagnostic is simpler: **explicit weekly opposition is bad; weekly non-trend / other is not automatically bad.**

## Post-hoc diagnostic — not preregistered

After seeing the preregistered result, one explanatory diagnostic was run:

> Keep the daily policy unchanged except cap exposure at 25% only when the completed weekly formal trend is explicitly opposite. Do not cap neutral / other weekly states.

This is **post-hoc and must not be promoted as a validated policy**.

Discovery aggregate:

- mean episode return: **+0.3284 ATR** vs +0.3322 daily baseline
- median PF: **1.251** vs 1.260
- mean max drawdown: **36.05** vs 37.35
- 2020–2026 mean: **+0.1301** vs +0.0981
- but 2015–2019 mean becomes **-0.1162**, worse than the baseline -0.0975

So an opposition-only brake is useful for understanding the mechanism, but it is not the answer to the 2015–2019 failure regime.

## Decision

**Do not replace the daily candidate with either preregistered weekly overlay.**

Current evidence supports a narrower role for weekly context:

- Weekly direction can be a **risk / confidence modifier**, especially when it explicitly conflicts with the daily trend.
- Weekly `other / non-trend` should not automatically be treated as weak evidence requiring a 50% cap.
- Weekly Trendability >66.67 should **not** be promoted to a production full-size gate from this sample.
- The daily classifier remains the better primary participation engine for harvesting large trends.

The next research question should therefore be **whether a sparse, asymmetric weekly conflict modifier can improve failure protection without taxing neutral-weekly large trends**, and that rule must be preregistered before comparison. The unresolved 2015–2019 regime should remain an explicit adversarial test rather than something to tune away.
