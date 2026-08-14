# Issue #57 — Decay-warning exit policy conclusion

Status: **DECAY WARNING IS A REGIME-RISK ALERT, NOT A PROVEN HARD EXIT RULE**

Decision tag:

`decay_warning_state_change_alert_only_hard_exit_edge_not_established`

This study reuses the seven already-burned FX fixtures only to understand the existing v0.6 indicator. The indicator itself is not optimized or changed.

## What was compared

For each established actionable Top-2 episode that produced a first 2+ deterioration warning:

- same entry for both policies: next open after episode onset;
- early policy: exit next open after the warning;
- late policy: wait until the actionable regime visibly ends, confirm that change at the close of the first post-episode bar, then exit next open.

This creates a realistic close-known / next-open execution comparison rather than using a hindsight same-close exit.

## Result

58 warned episodes across all seven FX pairs were comparable.

- Warning exit beat regime-change exit in **53.45%** of pooled events.
- Median pair warning-exit win rate was exactly **50%**.
- Only **3 of 7** pairs had warning exit win a majority of events.
- Median pair mean benefit from warning exit was only about **+0.02%**.
- Continuing to hold after the warning changed return by only about **-0.02%** on a median-pair mean basis.

This is economically very small and inconsistent across pairs. There is no evidence here for a mechanical rule such as `2+ warnings => exit the trade`.

## The useful part: risk changes before return does

The warning did change the risk profile:

- exiting at warning reduced MAE by about **0.15%** on a median-pair mean basis;
- but it also sacrificed about **0.22%** of MFE;
- warning exit occurred about **3 daily bars earlier** than the confirmed regime-change exit.

So the warning behaves like a genuine **regime deterioration / uncertainty alert**: leaving earlier cuts some downside path exposure, but it also cuts at least as much favorable path opportunity. The return trade-off is roughly balanced rather than clearly favorable.

## Decision

Do **not** turn the 2+ decay warning into a hard production exit rule.

The current evidence supports a narrower interpretation:

> The decay warning says "the current classification is becoming unstable; reassess risk," not "price is about to reverse; close now."

Possible later uses such as position reduction, tighter discretionary risk control, or requiring additional price confirmation remain separate hypotheses and are not adopted by this study.

## Next research direction

Return to the first use case — regime formation — but stop studying only static strength or generic concentration speed.

The next behavior question should be structural:

> **Does the path that Candidate + Secondary take into a new actionable pair matter?**

Examples to distinguish descriptively:

- a bullish 2+3 regime emerging from an Accumulation-context pair containing stage 1;
- a bearish 5+6 regime emerging from a Distribution-context pair containing stage 4;
- a direct opposite-family flip;
- a mixed / unrelated precursor;
- whether one of the eventual Top-2 stages was already present before the new pair formed versus both arriving together.

This studies Wyckoff transition semantics rather than fitting another strength threshold.

PR #58 remains Draft. Issue #57 remains open. No production rule is changed.
