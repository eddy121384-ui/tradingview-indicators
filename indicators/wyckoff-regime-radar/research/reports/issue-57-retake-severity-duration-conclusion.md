# Issue #57 — Retake severity × duration conclusion

**BEHAVIOR MAP COMPLETE — severity is mildly informative; duration does not provide a stable rescue/failure gradient. Existing v0.6 remains unchanged.**

Decision tag: `first_retake_is_primary_damage_signal_severity_secondary_duration_not_stable`

## Plain-language conclusion

Once the old context stage retakes the lead after an initial handoff, the transition is already materially damaged. Splitting that retake into deeper/faster/persistent variants adds only limited extra information.

### Retake depth

- Pair-median Spearman between first-retake normalized margin and eventual same-direction completion: **-0.093**.
- Pair-median Spearman versus opposite-actionable failure: **+0.216**.
- Predictor-only within-pair severity terciles show a descriptive gradient:
  - low severity: **20.00%** pair-median same-direction completion;
  - mid severity: **0.00%**;
  - high severity: **0.00%**.

This suggests shallow retakes are less damaging than medium/deep retakes, but the continuous relationship is weak and does not justify fitting a production threshold.

### Retake duration

- Pair-median Spearman between first control-spell duration and same-direction completion: **-0.067**.
- Fixed duration bins are not monotonic:
  - 1 bar: **0.00%** success;
  - 2–3 bars: **0.00%**;
  - 4+ bars: **11.11%**.

Duration alone therefore does not cleanly separate healthy pullback from failed transition.

### Combined damage

`dominance_area` (depth accumulated through the first retake spell) has the strongest negative association with same-direction completion among the tested damage measures, but is still only **rho ≈ -0.242** at the pair median. The 3×3 severity × duration matrix is sparse and does not support selecting a rule.

## Updated mental model

The strongest structural distinction remains simple:

1. new stage seizes the lead;
2. if it holds through the early transition, the path is healthier;
3. if the old context retakes the lead, the transition is damaged;
4. later reseizure and finer retake microstructure do not reliably restore or classify it enough to justify additional thresholds.

Do not keep subdividing the indicator's own state transition indefinitely.

## Recommended next research question

Move from predicting the indicator's own future state to testing **external market behavior**.

At matched, observable checkpoints (for example +3 bars after a seizure), compare actual future directional return, MFE, and MAE for:

- healthy handoff: new stage has continuously held the lead;
- damaged handoff: old context has already retaken the lead.

This answers whether the structural transition-health label has useful information about price behavior, rather than only forecasting the indicator's internal state machine.

Boundary: reused-data exploratory research only; no independent OOS or trading-rule claim.
