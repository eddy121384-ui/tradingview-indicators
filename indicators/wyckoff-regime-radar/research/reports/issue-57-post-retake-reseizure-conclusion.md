# Issue #57 — Post-retake reseizure conclusion

**BEHAVIOR MAP COMPLETE — reseizure is not a reliable transition rescue signal. Existing v0.6 remains unchanged.**

Decision tag: `retake_damage_persists_reseizure_mostly_churn_not_clean_recovery`

## Plain-language conclusion

Once the old context stage retakes the lead after an initial handoff, the transition is usually damaged. A later new-stage reseizure is common, but it does **not** reliably restore a high-quality path toward the same-direction actionable regime.

- Old-context retake events: **89**.
- A pre-resolution reseizure occurred in **53** events; median-pair reseizure rate **58.82%**.
- Median-pair eventual same-direction completion was only **9.09%** with reseizure versus **0.00%** without reseizure.
- Reseizure beat no-reseizure on only **4/7** FX pairs.
- Fast reseizure was not a clean confirmation:
  - within +1 bar: **0.00%** completion when reseized vs **8.33%** when not yet reseized;
  - within +3 bars: **0.00%** vs **11.11%**;
  - within +5 bars: **0.00%** vs **0.00%**.

This means the sequence `new stage seizes -> old context retakes -> new stage reseizes` is usually **whipsaw / unresolved competition**, not a restored healthy transition.

## What this changes in our mental model

The strongest structural information remains the **first retake itself**:

- no old-context retake previously showed about **42.86%** median-pair same-direction completion;
- once the old context retook the lead, completion fell to about **10%**.

A later reseizure does not erase that damage.

## Next research question

Do not add a reseizure rule. Instead study **retake severity** without fitting thresholds:

1. how far the old context overtakes the carried stage at first retake (`context - carried` margin);
2. how many consecutive bars the old context remains in control;
3. whether shallow/brief retakes behave differently from deep/persistent retakes;
4. use continuous associations and descriptive bins fixed before reading outcomes, not post-hoc threshold shopping.

Boundary: reused-data structural research only; no production rule, entry signal, or independent OOS claim is established.
