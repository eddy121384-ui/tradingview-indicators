# Issue #57 — Transition formation / regime decay simple conclusion

Status: **BEHAVIOR MAP COMPLETE — descriptive transition structure found, no entry/exit edge established**

Decision tag:

`transition_dynamics_descriptive_structure_only_price_edge_not_established`

This uses the seven already-burned FX fixtures only to understand the existing v0.6 indicator. The indicator itself was not optimized or changed.

## 1. New-regime formation

The simple hypothesis was: if Candidate + Secondary suddenly strengthen together and the six-stage weight distribution becomes more concentrated, the newly formed actionable regime should be more durable and/or price should follow it better.

**Result: weak / mixed.**

- 263 actionable Top-2 episode onsets were observed.
- 144 onsets had both rising Top-2 strength and falling six-stage entropy over the prior 3 bars.
- These episodes survived slightly more often than other formations, but the continuous relationships were essentially flat:
  - 3-bar Top2 strength change vs episode duration: pair-median Spearman `0.006`;
  - entropy concentration change vs episode duration: `0.020`;
  - Top2 strength change vs 10-bar aligned return: `-0.004`;
  - entropy concentration change vs 10-bar aligned return: `-0.118`.
- Therefore, **"it suddenly concentrates" is not enough by itself to identify a strong entry / directional transition signal.**

## 2. Existing-regime decay

Three simple deterioration signs were observed while an actionable Top-2 episode was already alive:

1. Top-2 strength is lower than 3 bars earlier;
2. six-stage entropy is rising (weights are becoming less concentrated);
3. opposite structural pressure is rising.

When the first **2+ simultaneous warnings** appeared:

- 58 episode-level events were observed;
- pair-median probability that the actionable episode ended within 5 bars: **83.33%**;
- within 10 bars: **100%**;
- pair-median remaining life: **2 bars**.

The pattern was not driven by one FX pair. Across the seven pairs, first-2+ warning end-within-5 rates ranged from about **60% to 100%**; six pairs reached 100% end-within-10 and the remaining pair was about 92.9%.

So there is a real and fairly consistent **internal regime-decay structure**: weakening + dispersion + opposing pressure usually appears shortly before the indicator stops classifying the same actionable Top-2 regime.

## 3. Important limitation — this is not yet a "get out" signal

The decay warnings strongly predict **the indicator's own episode ending**, but that is partly structurally related to how the episode is defined. The economically important question is whether price also becomes meaningfully worse after the warning.

That evidence is not strong yet:

- first 2+ warning: pair-median 5-bar aligned return about **-0.10%** and adverse excursion about **0.71%**;
- zero-warning regime bars: pair-median 5-bar aligned return about **-0.22%** and adverse excursion about **1.02%**.

Therefore the current result does **not** justify saying "2 warnings = exit the trade". It says something narrower and still useful:

> **Two or more deterioration signs are a good warning that the current indicator regime is about to change, but we have not shown that exiting at that warning improves the trade outcome.**

## Simple conclusion

- **Entry / transition timing:** simple fast concentration is not enough; no clear directional edge found.
- **Regime monitoring:** promising. The indicator shows a clear pre-transition deterioration pattern before its current actionable state disappears.
- **Trading exit:** not proven. The next research question should compare actual price / drawdown outcomes for "exit at first decay warning" versus "continue holding until regime actually changes", rather than merely predicting the indicator's own state transition.

No production threshold or rule is changed from this study. PR #58 remains Draft and Issue #57 remains open.
