# Issue #78 — Formal-Exit and Naive Giveback-Stop Baseline

## Status

Exploratory discovery baseline under the frozen Issue #78 research question. This is **not** a selected policy and not OOS evidence.

The accepted Issue #76 nine-market daily Pine logs are reconstructed into known-start, completed Markup / Markdown episodes. Direction is aligned so positive means favorable to the active trend. Cumulative moves are reconstructed from the Pine one-bar moves and normalized by the episode-entry ATR scale.

Completed known-start trend episodes:

- Markup: 806
- Markdown: 818

Primary aggregation is equal-market: calculate within each market first, then average market summaries.

## 1. Formal Exit is a deliberately expensive baseline

A pure `hold until formal regime loss` policy waits for the classifier to confirm that the trend regime is gone. That necessarily pays recognition delay.

Across all completed episodes, the equal-market median terminal directional move is negative:

- Markup: about **-1.17 entry ATR**
- Markdown: about **-0.93 entry ATR**

The equal-market median terminal giveback is large:

- Markup: about **3.53 entry ATR**
- Markdown: about **3.82 entry ATR**

This does **not** mean persistent trend episodes have no value. It means that many short/failed formal trend episodes reverse substantially before the formal state finally changes, so formal state loss alone is too late to function as an efficient stop/exit.

## 2. On genuinely large trends, Formal Exit captures roughly half — at a large giveback cost

Condition only on episodes that actually produced a large favorable move while the formal trend remained alive.

### Episode favorable excursion >= 4 entry ATR

- Markup: 270 episodes across all 9 markets
  - formal-exit capture ratio: ~**44%**
  - terminal giveback: ~**5.0 ATR**
  - retained terminal directional move: ~**3.2 ATR**
- Markdown: 294 episodes across all 9 markets
  - formal-exit capture ratio: ~**50%**
  - terminal giveback: ~**5.9 ATR**
  - retained terminal directional move: ~**4.6 ATR**

### Episode favorable excursion >= 8 entry ATR

- Markup: 128 episodes across all 9 markets
  - formal-exit capture ratio: ~**52%**
  - terminal giveback: ~**7.1 ATR**
  - retained terminal directional move: ~**7.3 ATR**
- Markdown: 180 episodes across all 9 markets
  - formal-exit capture ratio: ~**59%**
  - terminal giveback: ~**7.0 ATR**
  - retained terminal directional move: ~**8.6 ATR**

This is the first direct evidence for the trade-off Eddy described: a late exit can preserve participation in very large trends, but the price is substantial terminal giveback.

## 3. Naive tight giveback stops pay the opposite cost: whipsaw and missed continuation

As a diagnostic only, compare one-shot permanent exits when running giveback from the regime favorable extreme first reaches fixed frozen landmarks.

### 0.5 ATR defensive exit

- exits roughly **98%** of Markup and Markdown episodes;
- among those exits, roughly **57% of Markup** and **60% of Markdown** later make a new favorable extreme within the same formal trend episode;
- when that false exit occurs, the median missed later peak is approximately **4.5 ATR** for Markup and **4.8 ATR** for Markdown.

### 4 ATR defensive exit

- exits roughly **47%** of Markup and **49%** of Markdown episodes;
- false-exit rate conditional on exit falls to roughly **20%** / **26%**;
- but when the exit is false, the later missed favorable peak is very large: approximately **10.8 ATR** for Markup and **14.3 ATR** for Markdown.

Thus a tighter stop reduces terminal giveback only by paying more frequent premature exits; a looser stop lowers whipsaw frequency but can still abandon some of the largest continuation episodes.

No single threshold is selected from this table.

## 4. Persistence alone does not solve exit timing

Issue #76 showed that trend-regime survival itself is informative: Markup and Markdown commonly survive for weeks, and surviving trends have increasingly coherent directional paths.

However, entering only after fixed age landmarks (5 / 10 / 20 bars) and then still waiting for Formal Exit does not by itself repair the terminal-giveback problem. The median move from those delayed entries to final formal loss remains weak/negative in this discovery reconstruction.

Therefore two separate problems must be solved together:

1. **entry / participation:** avoid the short failed trend episodes without sacrificing too much of the large trends;
2. **damage / exit:** detect deterioration before the final formal regime switch, without converting normal trend pullbacks into constant whipsaw.

## 5. Research consequence

The current evidence supports a frontier view rather than an optimizer view:

> Formal Exit = low sensitivity / high giveback.
>
> Tight defensive exit = low giveback / high whipsaw and missed continuation.

Issue #78 should therefore map the middle ground using the already observed cross-market regime-health structure, with explicit accounting for capture, giveback, false exits, and re-entry cost.

The desired result is not `the perfect ATR stop`. It is a small, robust family of management policies whose unavoidable costs are visible and acceptable.

## Caveats

- Discovery sample only; any chosen policy is in-sample until frozen and challenged elsewhere.
- No transaction costs, slippage, or executable instrument mapping are included here.
- Close-to-close directional paths are reconstructed from the research Pine logger; this is a regime-management diagnostic, not a broker-fill backtest.
- No asset-specific parameters are introduced.

Refs #78 and #76.
