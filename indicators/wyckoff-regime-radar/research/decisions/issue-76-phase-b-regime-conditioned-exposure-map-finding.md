# Issue #76 — Phase B Regime-Conditioned Exposure Map Finding

## Status

**Phase B descriptive exposure-map pass completed on the accepted nine-market daily sample.**

This is not an executable strategy, not a PnL backtest, and not an OOS profitability claim. The purpose is to answer a different question:

> Given the current formal regime, how does the forward distribution change versus that market's own normal distribution, and what directional/risk posture does that change support?

No symmetry requirement is imposed on bullish versus bearish behavior.

## Run integrity

The Phase-B analyzer consumed the nine TradingView Pine-log exports already accepted by Issue #76.

- formal-stage event rows: **68,118**;
- fixed horizons: **1 / 5 / 10 / 20 daily bars**;
- asset classes kept separate: **FX** and **10Y yield levels**;
- regime-age buckets: fresh, 1–4, 5–9, 10–19, 20+ bars;
- DE10Y retains the explicit possible 10,000-log early-history truncation caveat;
- 10 TradingView `rv5 / rvn5 = NaN` cases were deterministically reconstructed from contiguous one-bar close moves; all reconstructed RMS values were zero;
- one DE10Y row at the truncated sample start has unknown regime age and is excluded only from age-bucket slices, not occupancy.

### Historical yield-feed discontinuity sensitivity

The raw historical TVC yield feeds contain three obvious one-day discontinuities that can dominate normalized means:

- DE10Y event bar 4837;
- FR10Y event bar 1155;
- GB10Y event bar 2620.

They were identified by a representation-level diagnostic independent of regime outcome:

`abs(one-day yield move) > 100 bp AND abs(one-day normalized move) > 20 event-time ATR`.

The **primary sample remains untouched**. A second `splice_screened` sensitivity view removes only forward windows crossing those three bars. Median, hit-rate, tail and most qualitative regime conclusions remain stable; some rate-regime mean magnitudes change materially, especially Distribution. Therefore the exposure interpretation below gives more weight to medians, cross-market consistency and tails when raw means are feed-sensitive.

## Headline exposure map

The current classifier is not producing one universal symmetric Long / Short rule. Its useful information is materially asset-class-specific.

| Asset class | Regime | Current descriptive posture | Main reason |
|---|---|---|---|
| FX | Accumulation | **Reduced Long / Neutral; weak short caution** | 5–20 day mean and median shift below baseline; not strong enough for an aggressive standalone short. |
| FX | Markup | **Normal Long allowed; do not add risk from regime alone** | Forward mean/median stay close to baseline; downside tail and adverse excursion improve modestly while future volatility is slightly lower. |
| FX | Distribution | **Long / Strong Long candidate** | Contrary to the label, the current FX classifier state is the strongest upside continuation state in this sample, especially at 10–20 days. |
| FX | Markdown | **Fresh Short, then rapidly decay toward Neutral** | Fresh entry has a clear bearish 10-day shift, but the advantage largely disappears during days 1–19; mature occupancy is only mildly bearish. |
| Rates | Accumulation | **Neutral duration; mature state shifts toward Reduced Duration** | Overall yields still drift lower, but relative to each market's baseline the long-duration advantage weakens; mature Accumulation shifts yields higher. |
| Rates | Markup | **Short Duration / Pay Rates, strongest during days 1–9** | All six rate markets shift upward versus baseline at the 10-day horizon; the clearest yield-up window is age 1–9. |
| Rates | Distribution | **Long Duration / Receive Rates; relatively clean** | Yields shift lower, upside-yield tail contracts, and future volatility is below baseline. This behaves like a cleaner long-duration setup. |
| Rates | Markdown | **Long Duration / Receive Rates; strongest early, size down when mature** | Yields continue lower, especially during days 1–9, but mature Markdown carries higher future volatility and wider tails. |

Reaccumulation and Redistribution remain too sparse for a serious exposure-policy conclusion.

## FX — occupancy results

Equal-market, splice-screened normalized outcomes:

| Regime | Horizon | Mean | Median | Positive rate | Mean lift vs baseline | Median lift vs baseline |
|---|---:|---:|---:|---:|---:|---:|
| Accumulation | 10d | -0.088 | -0.110 | 51.0% | -0.094 | -0.164 |
| Accumulation | 20d | -0.122 | -0.138 | 48.4% | -0.126 | -0.228 |
| Markup | 10d | +0.016 | +0.002 | 50.0% | +0.011 | -0.052 |
| Markup | 20d | +0.026 | +0.033 | 50.4% | +0.021 | -0.057 |
| Distribution | 10d | **+0.244** | **+0.368** | **57.3%** | **+0.239** | **+0.314** |
| Distribution | 20d | **+0.579** | **+0.792** | **62.3%** | **+0.574** | **+0.703** |
| Markdown | 10d | -0.060 | +0.027 | 50.6% | -0.065 | -0.026 |
| Markdown | 20d | -0.160 | -0.007 | 49.8% | -0.165 | -0.096 |

### FX interpretation

**Distribution is the surprise.** At 20 days all three FX markets have mean, median and positive-rate outcomes above their own baselines. The equal-market downside q10 improves by about **+0.656 ATR**, mean adverse excursion improves by about **+0.282 ATR**, and future realized volatility is slightly lower than baseline. In the current classifier this state behaves much more like sustained upside continuation than an immediate top/short state.

That is a semantic observation, not authorization to rename or retune the classifier inside Issue #76.

**Markup is not a strong add-risk state.** Its expected forward move is close to baseline. Its more useful property is mild risk improvement: lower downside tail / adverse excursion and slightly lower future volatility. Operationally this supports holding an already-valid long more than opening a larger long solely because the regime says Markup.

**Markdown is age-sensitive.** Fresh Markdown has a much stronger bearish distribution than generic occupancy.

At the 10-day horizon:

- fresh: mean **-0.306 ATR**, median **-0.362 ATR**, positive rate **44.7%**;
- age 1–4: mean +0.022, median +0.111;
- age 5–9: mean +0.003, median +0.220;
- age 10–19: mean +0.072, median +0.041;
- age 20+: mean -0.134, median -0.040.

All three FX markets have fresh-Markdown 10-day median and positive-rate results below baseline. Thus the useful bearish information is concentrated at the transition itself; a permanent full short throughout the entire Markdown occupancy is not supported by this sample.

## Rates — remember the sign

The observed series is the **10Y yield level**:

- yield up = economically short duration / pay rates;
- yield down = economically long duration / receive rates.

Do not read the signed yield result as a bond-price sign.

Equal-market, splice-screened normalized outcomes:

| Regime | Horizon | Mean yield move | Median yield move | Yield-up rate | Mean lift vs baseline | Median lift vs baseline |
|---|---:|---:|---:|---:|---:|---:|
| Accumulation | 10d | -0.086 | -0.107 | 47.8% | +0.050 | +0.074 |
| Accumulation | 20d | -0.131 | -0.177 | 48.5% | +0.146 | +0.179 |
| Markup | 10d | +0.062 | -0.042 | 49.4% | **+0.198** | **+0.140** |
| Markup | 20d | +0.005 | -0.225 | 48.1% | **+0.281** | **+0.131** |
| Distribution | 10d | -0.211 | -0.227 | 46.4% | -0.076 | -0.046 |
| Distribution | 20d | **-0.481** | **-0.552** | **43.4%** | **-0.205** | **-0.196** |
| Markdown | 10d | **-0.294** | **-0.315** | **45.5%** | **-0.158** | **-0.134** |
| Markdown | 20d | **-0.498** | **-0.482** | **45.6%** | **-0.222** | **-0.126** |

### Rates interpretation

**Markup is a short-duration / pay-rates state relative to normal, but the useful window is not the fresh bar.** At the 10-day horizon:

- age 1–4: mean yield move **+0.247 ATR**, median **+0.222**, yield-up rate **52.7%**;
- age 5–9: mean **+0.282**, median **+0.138**, yield-up rate **51.4%**.

For both age 1–4 and age 5–9, all six rate markets have the 10-day median above their own baseline; the positive-rate lift is also positive in all six. Future volatility is slightly below baseline. This is the cleanest evidence for reducing duration / paying rates during a mature-enough Markup rather than immediately on the first classification bar.

**Distribution and Markdown both support long duration, but the risk geometry differs.**

Distribution at 20 days has mean yield move **-0.481 ATR**, median **-0.552**, with five of six markets showing median and yield-up probability below baseline. Its equal-market q90 yield tail shifts down by about **-0.882 ATR** and future volatility is about **-0.066 ATR-normalized units** below baseline. That is a comparatively clean receive-rates / long-duration environment.

Markdown is more aggressively yield-down but becomes bumpier with age. At 10 days:

- fresh: mean -0.290, median -0.263;
- age 1–4: **-0.498 / -0.407**;
- age 5–9: **-0.448 / -0.395**;
- age 20+: -0.260 / -0.311.

The mature 20+ bucket still favors lower yields, but future realized volatility is about **+0.097** above baseline and both tails widen. That argues for keeping the directional long-duration bias while reducing risk size as the Markdown becomes old, rather than mechanically holding maximum size forever.

**Accumulation is mixed and age-dependent.** Generic occupancy still has lower absolute yields ahead because the rates sample itself has a historical downward-yield baseline. Relative to that baseline, however, the shift becomes less dovish / more yield-up. The mature 20+ bucket is clearest: at 10 days mean yield move is **+0.095 ATR**, median **+0.144**, and five of six markets have median and yield-up-rate lifts above baseline. The practical interpretation is Neutral duration early, then Reduced Duration / mild pay bias if Accumulation persists unusually long.

## What changed versus Phase A

Phase A asked whether any stage transition could be treated as a direct fixed-horizon directional signal. That framing highlighted fresh Markdown -> bearish continuation.

Phase B asks a broader trader question: **what exposure is preferable in the current state?** Under that framing the result is materially richer:

1. FX Distribution is the strongest long-supporting state in this sample despite its classical name.
2. FX Markup is more useful as a risk-permission state than as a return-enhancement signal.
3. FX Markdown is useful mainly when fresh; its short bias should decay quickly rather than stay permanently maximum.
4. Rate Markup supports short duration after the state survives roughly 1–9 bars.
5. Rate Distribution supports cleaner long duration.
6. Rate Markdown supports stronger long duration early, but mature Markdown deserves smaller size because volatility rises.
7. Accumulation is not a universal reversal-buy state; in both FX and rates its practical meaning depends on age and asset class.

## Current decision

**Issue #76 now supports a regime-conditioned exposure map, not a symmetric signal system.**

The next research step should not optimize entries, stops or arbitrary sizing. It should translate the descriptive map into a small number of frozen exposure postures — for example Strong / Normal / Reduced / Flat in the economically correct direction — using these distributional findings, and then only after that policy is frozen should profitability be tested OOS.

No production classifier change is authorized by this finding.
