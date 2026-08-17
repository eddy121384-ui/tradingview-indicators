# Issue #57 — Post-handoff hold-persistence conclusion

Status: **exploratory reused-data conclusion only; no production rule selected**.

## Result

The post-handoff lead carries useful early transition information, but the effect is **not monotonic in holding duration**.

Across 125 seizure events / 7 FX pairs:

- +1 bar, still unresolved: held lead median-pair completion <=20 = **20.00%** vs **0.00%** after losing the lead; hold wins on **6/7** pairs.
- +3 bars: **25.00%** vs **0.00%**; hold wins on **7/7** pairs.
- +5 bars: **20.00%** vs **9.09%**; hold wins on **5/7** pairs.
- +10 bars: **12.50%** vs **0.00%**; hold wins on **4/7** pairs.

Therefore the data do **not** support a story that 'the longer the carried stage holds, the more certain the transition becomes.' The useful information is concentrated in the early survival of the new lead, especially roughly the first 1–3 bars.

## Old-context retake

Old context retook/tied the carried stage before resolution in **89/125** seizure events. Median-pair retake rate was **71.43%**, with median first-retake lag **3 bars**.

- Same-direction completion <=20 after a retake: **10.00%**.
- Same-direction completion <=20 with no retake: **42.86%**.
- No-retake outperformed retake on **7/7** FX pairs.

Interpretation: an old-context retake is a strong descriptive warning that the attempted handoff is weakening. It is not proof of future price reversal and is not yet a trading exit rule.

## Working model after this study

The most defensible transition sequence is now:

1. semantic bridge appears;
2. one new-direction stage overtakes the old context stage;
3. the new stage must survive the old context's first counterattack, especially during the first few bars;
4. companion-stage development may add later confirmation, but is not the primary early signal;
5. full `2+3` / `5+6` completion remains the later confirmed state.

## Next research question

Characterize the **first counterattack itself**: among early retakes, what separates a temporary pullback that the new stage reclaims from a genuine failed handoff? Examine regain timing / margin recovery mechanically, without fitting numeric thresholds.
