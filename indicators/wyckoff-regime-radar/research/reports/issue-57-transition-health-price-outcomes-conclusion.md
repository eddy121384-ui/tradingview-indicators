# Issue #57 — Transition health price-relevance conclusion

**BEHAVIOR MAP COMPLETE — +3 handoff health shows meaningful subsequent price relevance on reused FX data; independent validation is still required. Existing v0.6 remains unchanged.**

Decision tag: `transition_health_price_relevance_found_freeze_candidate_for_new_oos`

## Plain-language conclusion

The earlier transition-health work was not merely predicting the indicator's own later state. When the new carried stage had seized the lead and **still held it continuously through bar +3**, subsequent price behavior was generally better than when the old context stage had already retaken the lead by +3.

The observation point was frozen before outcomes and every price metric starts from the **+3 close**, so pre-checkpoint price movement is not counted as success.

Across 114 eligible unresolved handoff events (63 healthy / 51 damaged):

- **5 bars after +3**
  - aligned return: healthy **+0.06%** vs damaged **+0.05%**;
  - hit rate: **66.67%** vs **40.00%**;
  - healthy aligned return wins on **5/7** FX pairs.
- **10 bars after +3**
  - aligned return: healthy **+0.20%** vs damaged **+0.01%**;
  - hit rate: **62.50%** vs **42.86%**;
  - MFE-MAE: **+0.20%** vs **-0.11%**;
  - healthy wins aligned return, hit rate, and MFE-MAE on **6/7** FX pairs.
- **20 bars after +3**
  - aligned return: healthy **+0.23%** vs damaged **-0.17%**;
  - hit rate: **62.50%** vs **55.56%**;
  - healthy aligned return wins on **5/7** FX pairs.

The 10-bar horizon is descriptively the cleanest in this reused sample, but it must **not** be promoted as a selected production horizon from these data.

## What this changes

This is the first evidence in the Issue #57 transition research that a purely structural regime-health distinction also maps to subsequent real price behavior across most FX pairs.

The candidate mechanism is deliberately simple:

> initial handoff with carried stage > old context -> observe at +3 -> continuous lead still intact = healthy transition; any old-context retake by +3 = damaged transition.

No companion rule, severity threshold, reseizure rule, or additional tuning is needed.

## What this does NOT prove

- It does not prove a standalone profitable trading strategy.
- It does not establish a production entry/exit rule.
- It does not establish the +10 horizon as optimal.
- These seven FX fixtures have already been repeatedly used for research and cannot independently validate the now-frozen candidate.

## Next gate

**Stop tuning on the existing seven FX fixtures.** Freeze the +3 health classifier exactly as defined above and test it on untouched/new data.

Independent validation should retain the same fixed health definition and report all predeclared 5 / 10 / 20 bar price outcomes. The candidate passes only if healthy transitions continue to show broadly better aligned return / hit rate / price path across new samples, not merely one favorable pair or one horizon.
