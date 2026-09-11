# Issue #78 — Progressive Exposure State Machine First-Pass Finding

## Status

Discovery finding only. This is **not** OOS validation and does not select a production policy.

The first-pass progressive ladders were frozen before results were inspected. A second follow-up architecture, the damage latch, was also preregistered before its results were inspected.

Universe: accepted Issue #76 nine-market daily sample. Completed known-start trend episodes:

- Markup: 806
- Markdown: 818

Primary aggregation remains equal-market and cross-asset.

## 1. The basic trade-off is real

A pure Formal Hold keeps full directional exposure until the formal trend regime disappears. It maximizes participation in the largest trends, but pays a large terminal-reversal cost.

A progressive ladder reduces that terminal giveback and cuts failed-trend losses, but the price is lower participation during valid large trends plus resizing turnover.

There is no free exit.

## 2. Progressive de-risking materially reduces damage on small / failed trend episodes

Using episodes whose maximum favorable excursion never reached 4 entry ATR as a fixed diagnostic slice:

### Markup

- Formal Hold median retained directional move: **-1.98 ATR**
- Gentle + damage latch: **-1.67 ATR**
- Balanced + damage latch: **-1.40 ATR**

Median terminal giveback:

- Formal Hold: **2.95 ATR**
- Gentle + latch: **2.62 ATR**
- Balanced + latch: **2.12 ATR**

### Markdown

- Formal Hold median retained directional move: **-1.90 ATR**
- Gentle + damage latch: **-1.63 ATR**
- Balanced + damage latch: **-1.35 ATR**

Median terminal giveback:

- Formal Hold: **2.97 ATR**
- Gentle + latch: **2.62 ATR**
- Balanced + latch: **2.11 ATR**

Cross-market direction is broad rather than concentrated in one feed: on this small/failed-trend slice the latch variants reduce terminal giveback in almost every market, and loss reduction is positive in 8/9 to 9/9 markets depending on side / ladder.

This directly supports the original purpose of progressive sizing: **failed trends hurt less without requiring a binary stop at the first pullback.**

## 3. On very large trends, Formal Hold still captures more — but pays for it

For episodes that reached at least 8 entry ATR of favorable excursion:

### Markup, MFE >= 8 ATR

| Policy | Median harvested move | Median capture ratio | Median terminal giveback | Median average exposure | Mean turnover | Mean re-risk transitions |
|---|---:|---:|---:|---:|---:|---:|
| Formal Hold | 7.30 ATR | 52.1% | 7.07 ATR | 100% | 2.00 | 0.00 |
| Gentle + latch | 5.32 ATR | 44.4% | 4.51 ATR | 66.0% | 4.93 | 3.38 |
| Balanced + latch | 4.40 ATR | 37.9% | 3.32 ATR | 48.9% | 7.44 | 5.02 |

### Markdown, MFE >= 8 ATR

| Policy | Median harvested move | Median capture ratio | Median terminal giveback | Median average exposure | Mean turnover | Mean re-risk transitions |
|---|---:|---:|---:|---:|---:|---:|
| Formal Hold | 8.63 ATR | 59.2% | 6.95 ATR | 100% | 2.00 | 0.00 |
| Gentle + latch | 5.82 ATR | 39.2% | 4.73 ATR | 65.7% | 6.11 | 4.57 |
| Balanced + latch | 4.20 ATR | 30.6% | 3.46 ATR | 48.7% | 9.22 | 6.21 |

Thus the frontier is visible in the data:

> more protection from terminal reversal requires accepting less participation in valid large trends.

The balanced latch roughly halves large-trend terminal giveback versus Formal Hold, but also sacrifices a substantial fraction of the harvested move. The gentler latch preserves more trend participation at the cost of more giveback.

No winner is selected from this discovery sample.

## 4. Naive memoryless re-risking is too twitchy

The originally frozen memoryless ladders allow exposure to increase whenever current giveback crosses back into a healthier bucket. This is fully causal, but operationally very active.

On MFE >= 8 ATR trends:

- Gentle memoryless Markup: about **10.1** re-risk transitions per episode;
- Gentle memoryless Markdown: about **12.3**;
- Balanced memoryless Markup: about **13.9**;
- Balanced memoryless Markdown: about **16.6**.

This is exactly the behavioral problem the system is intended to solve: a theoretically sensible exposure map can still become practically unusable if it constantly asks the trader to resize.

## 5. The preregistered damage latch improves operational behavior

The damage latch does not re-risk merely because giveback temporarily improves. It restores Full exposure only after a new favorable close-path extreme is observed, with the restored exposure applying from the next bar onward.

This sharply reduces resize churn without adding an ATR threshold or N-bar confirmation parameter.

For MFE >= 8 ATR:

### Markup

- Gentle re-risk transitions: **10.10 -> 3.38** with latch
- Gentle turnover: **7.93 -> 4.93**
- Balanced re-risk transitions: **13.92 -> 5.02**
- Balanced turnover: **11.32 -> 7.44**

The latch also improved Markup harvested move versus the corresponding memoryless ladder in this sample.

### Markdown

- Gentle re-risk transitions: **12.35 -> 4.57**
- Gentle turnover: **9.12 -> 6.11**
- Balanced re-risk transitions: **16.59 -> 6.21**
- Balanced turnover: **13.09 -> 9.22**

For Markdown the latch reduces churn and giveback, but gives up more harvested trend than the memoryless ladder. This asymmetry is treated as observed market behavior, not as something to force into symmetry.

## 6. What this says about the intended product

The results support the exposure-state-machine framing more than a binary stop / exit framing.

A useful structure is increasingly clear:

1. **Formal regime identifies the opportunity environment.**
2. **Regime health controls how much risk remains justified.**
3. **Progressive de-risking limits damage when a trend is failing.**
4. **Re-risking must be deliberately less reactive than de-risking, otherwise resize whipsaw becomes excessive.**
5. **Formal regime loss is a final safety / termination condition, not an efficient primary exit signal.**

This does not yet prove a specific exposure ladder. It does show that a middle ground exists between two bad extremes:

- always stay full until Formal Exit;
- exit permanently at the first defensive trigger.

## 7. The unresolved problem is entry participation

Across **all** Markup / Markdown episodes, median final harvest remains negative for every policy because the sample contains many short failed trend episodes.

Therefore Issue #78 still has two coupled problems:

- **participation gate:** how to avoid sizing fully into trend states that fail quickly;
- **management frontier:** once a genuine trend develops, how to retain enough exposure while controlling giveback and resize churn.

Persistence evidence from Issue #76 can inform the first problem, but it must be tested causally rather than used as a hindsight filter.

## 8. Next research step

Do not optimize more exposure percentages yet.

The next useful experiment should combine a small causal **participation ramp** with the already-frozen health state machine. Example research question:

> Begin below Full exposure when a trend first appears, increase exposure only if the formal trend survives / confirms, then let regime-health deterioration control de-risking and the damage latch control re-risking.

The purpose is to test whether early failed-regime loss can be reduced without sacrificing too much of the large trends.

Any such participation ramp must be preregistered before results are viewed and must remain universal-first.

## Caveats

- discovery sample only;
- no transaction costs or slippage included yet;
- exposure-weighted close-to-close path is a management diagnostic, not broker-fill PnL;
- entry-ATR normalization is used for cross-market comparability;
- no asset-specific rules;
- no production classifier changes.

Refs #78 and #76.
