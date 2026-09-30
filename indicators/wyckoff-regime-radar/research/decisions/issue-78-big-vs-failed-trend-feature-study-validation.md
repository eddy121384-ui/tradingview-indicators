# Issue #78 — Big Trend vs Failed Trend Feature Study validation

Date: 2026-09-17

## Scope

This note independently validates the existing Big Trend vs Failed Trend outputs against the frozen preregistration at commit `e803efda8656da1bbd75cc44fc1fbc41735607fb`.

It does **not** change the preregistration, optimize the frozen `< 4 ATR` / `>= 8 ATR` labels, select a production threshold, alter the frozen classifier, or merge PR #80.

The question is deliberately narrow:

> Which preregistered features show stable separation between Failed / Small trends (`final MFE < 4 entry ATR`) and Large trends (`final MFE >= 8 entry ATR`) across markets, quintiles, and time?

## Validation conclusion

The stable survivors are overwhelmingly **post-entry causal price-proof features**, not entry-close context features.

The two clearest survivors are:

1. **Cumulative direction-aligned move after the probe is live** (`e5_cum_atr`, especially `e10_cum_atr`).
2. **Directional path efficiency after the probe is live** (`e5_dir_eff`, especially `e10_dir_eff`).

Early MFE is statistically strong as well, but it is mechanically close to the final MFE label and should be treated as corroborating evidence rather than a novel standalone predictor. Low early giveback is directionally useful and cross-market consistent, but weaker and less cleanly monotonic than cumulative proof / directional efficiency.

No E0 feature meets the same standard of evidence. Structural range location and medium-horizon directional displacement contain some signal, but their temporal evidence is too thin or unstable to justify an entry gate.

The resulting architecture remains:

> **probe first; increase participation only after the trend earns it with causal price proof.**

E5 / E10 are therefore eligible only for post-entry sizing research, never for rewriting entry classification.

## Cross-market validation

All-years equal-market results:

| Feature | Info set | Mean AUC | Median AUC | Markets AUC > 0.50 | Assessment |
| --- | --- | ---: | ---: | ---: | --- |
| cumulative aligned move | E5 | 0.776 | 0.789 | 9/9 | strong survivor |
| directional path efficiency | E5 | 0.755 | 0.765 | 9/9 | strong survivor |
| early MFE | E5 | 0.763 | 0.766 | 9/9 | strong but label-adjacent |
| low giveback | E5 | 0.675 | 0.687 | 9/9 | secondary survivor |
| cumulative aligned move | E10 | **0.842** | **0.843** | **9/9** | strongest survivor |
| directional path efficiency | E10 | **0.815** | **0.814** | **9/9** | strong survivor |
| early MFE | E10 | 0.820 | 0.835 | 9/9 | strong but label-adjacent |
| low giveback | E10 | 0.681 | 0.671 | 9/9 | secondary survivor |

The entry-close leaders are much weaker:

| Feature | Info set | Mean AUC | Markets AUC > 0.50 | Assessment |
| --- | --- | ---: | ---: | --- |
| 252-bar direction-aligned range location | E0 | 0.610 | 8/9 | weak/moderate, lower coverage |
| 126-bar direction-aligned range location | E0 | 0.606 | 9/9 | best broad E0 context, not a gate |
| 63-bar directional displacement / ATR | E0 | 0.592 | 9/9 | modest context only |
| 63-bar range location | E0 | 0.589 | 8/9 | modest context only |
| 63-bar range escape / ATR | E0 | 0.589 | 7/9 | modest context only |
| 63-bar direction-aligned efficiency | E0 | 0.577 | 8/9 | modest context only |

The preregistered absolute Efficiency Ratio family does not survive (`ER20 0.524`, `ER63 0.494`, `ER126 0.438`). Recent stage-change counts, fresh-trend-entry counts, and trend occupancy are also approximately noise or wrong-signed under the preregistered orientation and should not be rescued by post-hoc window changes.

## Quintile validation

The cleanest ordering is E10 cumulative aligned move. Within-market quality quintiles show:

| Quintile | Large share | Failed share | Equal-market P+G return |
| ---: | ---: | ---: | ---: |
| Q1 | 6.8% | 87.8% | -0.864 ATR |
| Q2 | 9.0% | 76.7% | -0.182 ATR |
| Q3 | 17.2% | 64.6% | +0.415 ATR |
| Q4 | 27.4% | 45.0% | +1.405 ATR |
| Q5 | 49.9% | 16.5% | +2.244 ATR |

All three diagnostics move monotonically in the expected direction.

E10 directional efficiency is similarly clean: Large-share rises `5.2% -> 11.0% -> 22.9% -> 26.3% -> 45.3%`, while Failed-share falls `88.3% -> 75.2% -> 59.3% -> 46.3% -> 21.3%`. Its equal-market P+G return also rises from `-0.848 ATR` in Q1 to `+2.188 ATR` in Q5.

E5 cumulative proof and E5 directional efficiency show the same strong endpoint separation and mostly monotonic class-share ordering, although their P+G return paths are noisier in the middle quintiles. This supports E5 as useful earlier evidence, with E10 providing cleaner confirmation.

Low giveback separates the endpoints but has noticeably less clean middle-quintile ordering, so it should remain secondary evidence rather than the central quality axis.

E0 range location has real endpoint separation but not the same quality of ordering. For 126-bar range location, Large-share is `7.9%, 17.9%, 19.9%, 19.1%, 21.8%` and Failed-share is `82.1%, 64.6%, 66.2%, 64.2%, 64.9%`. That is useful context, not a stable monotonic gate.

## Temporal validation

The key falsification is whether early-proof features still separate Large from Failed **within** the frozen eras, especially 2015–2019.

### Cumulative aligned move

| Era | E5 mean AUC | Markets > 0.50 | E10 mean AUC | Markets > 0.50 |
| --- | ---: | ---: | ---: | ---: |
| 2010–2014 | 0.777 | 7/7 | 0.856 | 7/7 |
| 2015–2019 | 0.767 | 4/4 | **0.905** | 4/4 |
| 2020–2026 | 0.723 | 6/7 | 0.778 | 7/7 |

### Directional path efficiency

| Era | E5 mean AUC | Markets > 0.50 | E10 mean AUC | Markets > 0.50 |
| --- | ---: | ---: | ---: | ---: |
| 2010–2014 | 0.765 | 7/7 | 0.835 | 7/7 |
| 2015–2019 | 0.747 | 4/4 | **0.858** | 4/4 |
| 2020–2026 | 0.733 | 6/7 | 0.764 | 7/7 |

This passes the important 2015–2019 falsification: the signal is not merely identifying a bad calendar regime. It separates eventual Large and Failed trends inside that regime among eligible observations.

By contrast, E0 temporal evidence is not strong enough for a survivor claim. For example, 126-bar range location is `0.693` in 2010–2014, `0.556` in 2015–2019, and `0.596` in 2020–2026, but the stress slice has only **one eligible market** under the preregistered minimum-count rule. The 252-bar version is even sparser and reverses below 0.50 in that same one-market stress sample. The 63-bar displacement feature has better coverage but fades to `0.516` in 2020–2026. These are context features, not stable entry-quality discriminators.

## Direction robustness

The early-proof result is not carried by only Markup or Markdown episodes.

For cumulative aligned move, E5 AUC is `0.779` in Markup and `0.778` in Markdown; E10 is `0.874` and `0.834` respectively. Directional path efficiency is likewise balanced: E5 `0.770 / 0.758`, E10 `0.844 / 0.807`.

This gives no empirical reason to create separate long / short quality policies, consistent with the preregistered guardrail.

## Interpretation limits

Two caveats matter.

First, E5 / E10 are **not entry predictors**. They are information observed after the initial probe. The result supports conditional participation sizing, not filtering the original entry signal.

Second, the final Large label is defined by eventual MFE, so early MFE and cumulative favorable progress are mechanically related to the outcome. The useful result is therefore operational, not miraculous forecasting: after several completed daily moves, high-quality trends already tend to show measurable directional progress and efficient path behavior.

E10 also conditions on episodes that remain observable through ten completed moves. The E10 Failed count is lower than E5 (`703` versus `946` in the separation table), so E10 should be interpreted as a sizing diagnostic for surviving probes, not as a universal classifier of every original entry.

## Research decision

Promote the following to the next **separately preregistered** post-entry sizing study:

- cumulative direction-aligned move at E5 / E10;
- directional path efficiency at E5 / E10;
- low giveback as secondary confirmation;
- early MFE only as a transparent benchmark / corroborating feature because of label adjacency.

Keep 126-bar range location and 63-bar directional displacement as descriptive E0 context variables only. Do not promote them to hard entry gates from this evidence.

Reject absolute ER and simple regime-churn families for this feature-study branch. Do not retune their windows after seeing these results.

No composite Trend Quality score, threshold, optimizer, market-specific parameter, direction-specific policy, or production classifier change is authorized by this validation.
