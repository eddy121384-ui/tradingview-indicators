# Issue #57 — Transition Health independent OOS conclusion

**INDEPENDENT OOS REPLICATION — directional price separation reproduced on new FX pairs and a new market era; production trading value is not yet established.**

Decision tag: `transition_health_directional_separation_replicated_independent_oos_risk_path_not_uniform`

## Frozen validation

The candidate was frozen before this sample was read:

- handoff onset requires the carried stage to take a strict lead over the old context stage;
- Healthy Transition requires that strict lead to remain intact through +3 bars;
- Damaged Transition means the old context retook the lead by +3;
- outcomes begin from the +3 close;
- no Top2 threshold, companion condition, Formal filter, price filter, retake-severity threshold, or rescue rule was allowed.

Independent sample:

- NZDUSD, EURGBP, GBPJPY, AUDJPY, CADJPY;
- score era 2022-01-01 through 2026-08-14;
- 81 eligible events: 45 Healthy / 36 Damaged.

## Result

Directional separation reproduced outside the development sample.

At +10 bars:

- median-pair aligned return: Healthy **+0.09%** vs Damaged **-0.42%**;
- median-pair hit rate: Healthy **53.33%** vs Damaged **37.50%**;
- Healthy aligned return beat Damaged on **5/5** comparable FX pairs;
- Healthy hit rate beat Damaged on **4/5**.

At +20 bars:

- median-pair aligned return: Healthy **+0.92%** vs Damaged **-0.61%**;
- median-pair hit rate: Healthy **62.50%** vs Damaged **37.50%**;
- Healthy aligned return beat Damaged on **4/5** pairs;
- Healthy hit rate beat Damaged on **4/5**.

At +5 bars the separation was weaker but still directionally favorable on aligned return: Healthy **+0.11%** vs Damaged **-0.04%**, with Healthy return wins on **3/5** pairs.

## Important limitation

Price-path quality did **not** replicate as cleanly as directional separation.

- Healthy MFE-minus-MAE beat Damaged on only 3/5 pairs at each horizon.
- At +10, median-pair MFE-minus-MAE was Healthy **-0.25%** vs Damaged **-0.05%**, so the Healthy group did not have uniformly cleaner excursion behavior even though its close-to-close directional outcome was materially better.

Therefore the evidence supports Transition Health as a **directional regime-transition discriminator**, not yet as a complete entry/exit or risk-management rule.

## What is now supported

The earlier development interpretation survived a genuinely new sample:

> After a new stage takes the lead, preserving that lead through the next three bars contains information about subsequent price direction. An early old-context retake is a meaningful negative transition-health signal.

This is stronger than the earlier findings for static Top2 strength, Formal labels, companion progression, reseizure, or retake duration/severity because it reproduced on new pairs and a new 2022–2026 era without tuning.

## Next justified step

Do **not** reopen checkpoint or threshold optimization on this OOS sample.

The next work should be productization/interpretability rather than more micro-tuning:

1. expose the frozen +3 Transition Health state in the v0.6 research/Pine visualization as an observational label or diagnostic;
2. verify Pine/Python parity for that label on real TradingView data;
3. then run a separate executable trading-policy study if desired, with entry/exit/execution/cost rules preregistered before evaluating performance.

Existing v0.6 production logic remains unchanged by this conclusion.
