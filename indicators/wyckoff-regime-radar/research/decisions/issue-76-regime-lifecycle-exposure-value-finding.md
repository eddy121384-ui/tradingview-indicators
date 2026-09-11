# Issue #76 — Cross-Asset Regime Lifecycle / Exposure-Value Finding

## Status

**Descriptive universal cross-asset research. No production policy is authorized yet.**

This phase follows the persistence finding and asks the medium/long-horizon question directly:

> While a formal regime is still alive, does the chart-variable direction retain a favorable conditional distribution, how does that change with regime age, and what happens as the regime deteriorates or exits?

The intended product remains one general-purpose cross-asset regime indicator. FX/rates labels are not policy branches. The primary aggregation is equal-market after causal `symATR` normalization. Asset slices may be used only as heterogeneity diagnostics.

No classifier thresholds, lifecycle memory, `confirmBars`, market-specific routing, stops, targets, or executable sizing rules are changed here.

## Sample and conventions

Same accepted Issue #76 nine-market 1D sample:

- 68,118 formal-stage bars;
- 2,494 reconstructed regime spells;
- 2,493 known-start spells after excluding the one left-censored opening spell;
- final open spells are treated as right-censored where future state is unknown.

Important distinction:

1. **Survival-conditioned path** asks what price/yield does if the same formal regime is still alive at a future landmark. This describes regime structure but uses future survival and is not itself an ex-ante entry rule.
2. **Causal state-following exposure** starts from the state known at the current close and holds until the state changes or a fixed study cap is reached. The move that causes the state change is therefore included, because the new state is only known at that next close.
3. **Stay vs exit step** isolates the one-bar return when the state remains alive from the one-bar return that triggers a formal exit.

The 10/20/40/60-bar landmarks are lifecycle measurement landmarks, not optimized holding periods.

## Finding 1 — trend-state survival is economically meaningful, not merely label persistence

The prior persistence finding already established that Markup and Markdown are the long-lived states: equal-market probability of still being in the same state after 20 bars is about 55.9% for Markup and 59.9% for Markdown; median spell duration is about 24 and 28 bars respectively.

The new result is that **when those states survive, their price/yield path becomes directionally coherent across markets.**

### Markup

From fresh entry, conditional on the state still being alive:

| Landmark | Equal-market survival | Median cumulative move | Markets with positive median |
|---|---:|---:|---:|
| +5 bars | 91.0% | +0.005 current-ATR | 4 / 9 |
| +10 bars | 74.8% | +0.581 current-ATR | **9 / 9** |
| +20 bars | 55.7% | +1.900 current-ATR | **9 / 9** |

Markup therefore does **not** look like a strong immediate-entry condition. The first few days are mixed. But a Markup state that survives toward two trading weeks becomes a much more credible cross-market positive-direction regime.

The effect is not simply an entry phenomenon. Conditional on already being in Markup for 10 bars, probability of remaining Markup for another 20 bars is about 55.8%, and the median move over those additional 20 bars among surviving spells is +1.609 current-ATR with 9/9 market medians positive. At age 20, another-20-bar survival is about 59.6%; survivor median remains +0.590 current-ATR with 8/9 positive.

### Markdown

Markdown confirms faster and remains directionally stronger:

| Landmark | Equal-market survival | Median cumulative move | Markets with negative median |
|---|---:|---:|---:|
| +5 bars | 90.6% | -0.283 current-ATR | 8 / 9 |
| +10 bars | 77.5% | -0.746 current-ATR | **9 / 9** |
| +20 bars | 59.8% | -1.530 current-ATR | **9 / 9** |

At age 20, probability of remaining Markdown another 20 bars is about 53.7% and the survivor median over those additional 20 bars is -1.761 current-ATR with 9/9 negative. At age 40, another-20-bar survival is still about 56.6% and the survivor median is -2.387 current-ATR, again 9/9 negative.

**Interpretation:** regime age is not an expiry clock. For trend states, survival itself is evidence that the regime is real. Markup needs more maturation before its direction becomes universal; Markdown becomes directionally coherent sooner.

## Finding 2 — the formal exit has a universal opposite-direction shock

One-bar behavior is very different depending on whether the state survives the next close.

| State | If state stays | If state exits |
|---|---:|---:|
| Markup | mean +0.011 ATR; 7/9 market means positive | mean **-0.370 ATR**; **9/9 negative** |
| Markdown | mean **-0.033 ATR**; **9/9 negative** | mean **+0.240 ATR**; 8/9 positive |

This is a crucial product fact. The trend states contain genuine directional drift while they remain alive, but the classifier only knows a formal exit after an opposite-direction move has already occurred. Therefore **formal state alone is not a precise exit timer**.

This also explains why fixed-horizon and whole-spell summaries can appear contradictory: long trend winners coexist with terminal giveback and failed short-lived spells.

## Finding 3 — expected value and median outcome are intentionally not the same thing

A causal state-following exposure study was run as a descriptive stress test: hold the chart direction implied by the current state until the formal state changes, capped at 20/40/60 bars. This is not a proposed strategy; it measures what the state itself can and cannot do as an exposure governor.

### Markup

From fresh Markup, equal-market mean normalized movement is approximately:

- 20-bar cap: +0.002 ATR;
- 40-bar cap: +0.045 ATR;
- 60-bar cap: +0.175 ATR.

The corresponding medians are negative. The distribution is trend-following-like: fewer large positive runs can lift expected value even though many spells eventually give back.

Once Markup has already survived 5–10 bars, the expected-value picture improves materially:

- age 5, 20-bar cap: mean +0.298 ATR; 8/9 market means positive;
- age 10, 20-bar cap: mean +0.374 ATR; 8/9 market means positive.

### Markdown

Markdown has a much stronger negative expected-value tilt from the start:

- fresh, 20-bar cap: mean -0.503 ATR;
- fresh, 40-bar cap: mean -0.655 ATR;
- fresh, 60-bar cap: mean -0.888 ATR.

After surviving 5 bars, the 20-bar-cap mean remains -0.487 ATR; after 10 bars it remains -0.377 ATR.

Longer-cap medians can turn positive even while means remain negative, because many spells eventually rebound but the persistent negative runs are much larger. This is exactly why a universal exposure map should not use hit rate or median alone when the user's objective is expected-value-aware positioning.

A sensitivity pass using the already-defined yield splice screen (one-day move >100 bp and >20 ATR) found only three obvious discontinuity bars. Removing windows crossing those bars changes magnitudes but not the core signs: for example fresh Markup 20-bar mean becomes about +0.172 ATR and fresh Markdown about -0.423 ATR. The main lifecycle conclusions are therefore not generated by those feed jumps.

## Finding 4 — short failed trends and mature trends are different populations

Completed-spell terminal movement is measured from the entry close to the final close that is still classified in the same state, excluding the next move that formally exits the state.

Across **all** completed Markup spells, the equal-market median terminal move is -0.925 entry-ATR; all 9 market medians are negative. Across all Markdown spells, it is +0.824 entry-ATR; all 9 market medians are positive. This looks backwards until spell maturity is conditioned explicitly.

When the spell has survived at least 20 bars:

- Markup terminal median becomes **+0.677 ATR**, positive in 8/9 markets;
- Markdown terminal median becomes **-0.917 ATR**, negative in 8/9 markets.

When the spell has survived at least 40 bars:

- Markup terminal median is **+2.656 ATR**, positive in 9/9;
- Markdown terminal median is **-4.989 ATR**, negative in 9/9.

Thus the apparent reversal is caused mainly by short failed trend spells. A trend label that persists for roughly a trading month is qualitatively different from a fresh label that dies quickly.

Even so, terminal giveback is substantial. Across all completed spells, median Markup intraregime MFE is about +2.338 entry-ATR and the median peak-to-final-same-state giveback is about 3.678 ATR. Markdown median intraregime MAE is about -2.534 ATR and the median trough-to-final-same-state rebound is about 3.938 ATR. Persistence improves regime validity but does not make formal-state exit timing sharp.

## Finding 5 — mature trend exits become more Wyckoff-like

The destination after a trend state changes depends on how mature the trend was.

For Markup spells ending before age 10:

- direct Markdown: ~37.9%;
- Distribution: ~24.5%;
- Accumulation: ~22.6%.

For Markup spells ending at age 40+:

- **Distribution rises to ~54.1%**;
- direct Markdown is ~34.6%.

For Markdown spells ending before age 10:

- Markup: ~35.7%;
- Distribution: ~31.1%;
- Accumulation: ~20.9%.

For Markdown spells ending at age 40+:

- **Accumulation rises to ~60.2%**;
- Markup falls to ~29.3%.

So short-lived trend labels are much more likely to behave like failed/whipsaw states, while mature trend regimes are more likely to exit through the textbook transition family. This is a lifecycle result, not an asset-specific rule.

## Finding 6 — ATR-normalized giveback is a very strong universal regime-health diagnostic

Because formal trend exits show large giveback, an exploratory fixed ATR grid was added using only information already observable inside the current regime:

- Markup health = drawdown from the running intraregime peak;
- Markdown health = rebound from the running intraregime trough.

The grid is deliberately coarse and round: `<0.5`, `0.5–1`, `1–2`, `2–4`, `4+` current ATR. It is exploratory; these are **not** authorized production thresholds.

### Markup drawdown from running peak

| Giveback | Next-bar exit hazard | Same Markup 10 bars later |
|---|---:|---:|
| <0.5 ATR | 0.66% | 89.3% |
| 0.5–1 ATR | 0.78% | 85.5% |
| 1–2 ATR | 1.90% | 77.4% |
| 2–4 ATR | 4.07% | 60.4% |
| 4+ ATR | **13.49%** | **36.0%** |

### Markdown rebound from running trough

| Giveback | Next-bar exit hazard | Same Markdown 10 bars later |
|---|---:|---:|
| <0.5 ATR | 0.35% | 89.5% |
| 0.5–1 ATR | 1.32% | 84.1% |
| 1–2 ATR | 1.78% | 78.2% |
| 2–4 ATR | 3.46% | 64.1% |
| 4+ ATR | **12.95%** | **42.0%** |

Most importantly, comparing `<0.5 ATR` with `4+ ATR`, **all 9/9 markets** show both the expected increase in next-bar exit hazard and the expected decrease in 10-bar state survival for Markup, and the same 9/9 consistency holds for Markdown.

At `4+ ATR` giveback, the directional 10-bar exposure value also becomes weak/mixed: Markup median is essentially flat and only 5/9 market means remain aligned; Markdown mean is near flat, median has flipped positive, and only 4/9 market means remain aligned.

This is the strongest new universal diagnostic in this phase: **regime health is better represented by path deterioration from the regime's own running extreme than by asset identity or a simple age-expiry rule.**

## What the data now says in trader language

The current evidence supports a universal hierarchy rather than asset-specific policies:

- Accumulation / Distribution: short-lived transition states with weak cross-market directional universality; treat primarily as uncertainty/transition information.
- Fresh Markup: plausible positive regime, but the first few days are a probation period; persistence materially increases confidence.
- Mature Markup: persistent positive-direction environment, but formal exit is sticky and can give back substantially.
- Markdown: negative-direction environment is stronger and becomes coherent earlier; expected-value tilt remains negative across long study caps.
- Markup or Markdown with small giveback from its running extreme: high probability the regime remains alive.
- Markup or Markdown after very large ATR-normalized giveback: sharply higher exit hazard and much weaker directional value, regardless of market identity.

This is much closer to the intended product than a fixed-horizon Buy/Sell signal. The evidence points toward a **universal state + persistence + state-health exposure governor**.

## Decision / next research gate

Do **not** freeze an executable exposure policy yet.

The new giveback/health relation was discovered in this same sample. It should first be preregistered as a universal hypothesis and attacked with additional heterogeneous evidence — ideally new asset classes (equity indices, commodities, possibly bond futures) and/or a weekly-timescale replication — without changing classifier parameters or ATR-health thresholds after seeing those results.

A future policy can then map universal state information into posture strength, but only if the relation survives that adversarial expansion.
