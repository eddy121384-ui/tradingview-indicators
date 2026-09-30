# Issue #78 — Retest / Acceptance Path Challenge Stage 1 Finding
## Immediate expansion vs retest-hold vs reclaim vs failed acceptance

## Scope

This finding executes the frozen preregistration in
`issue-78-retest-acceptance-path-stage1-preregistration.md`.

The study reused the exact Breakout Quality Stage 1 event definition and the already-validated three-bar post-breakout evidence window.

No later continuation outcome was used to label a retest as successful.

Every B3-eligible breakout was classified at the close of t+3 into one of four mutually exclusive causal paths:

- **P0 — No-touch / Immediate Expansion**
- **P1 — Wick Retest / Hold**
- **P2 — Close Re-entry / Reclaim**
- **P3 — Failed Acceptance**

Future outcomes begin only after t+3.

## Sample and path prevalence

B3-eligible breakout events: **997**.

Pooled counts:

- P0 No-touch: **411**;
- P1 Wick Retest / Hold: **110**;
- P2 Close Re-entry / Reclaim: **126**;
- P3 Failed Acceptance: **350**.

Equal-market prevalence:

- P0: **38.1%**;
- P1: **13.2%**;
- P2: **12.4%**;
- P3: **36.2%**.

So both retest states have enough support for cross-market inference.

## Result 1 — Failed acceptance is a materially worse re-expansion state

Equal-market future outcome rates:

| Path | Re-expand 5 | Re-expand 10 | Remaining >=20 | Mean remaining life |
|---|---:|---:|---:|---:|
| P0 No-touch | 66.0% | 78.4% | 77.2% | 42.3 |
| P1 Wick Hold | 64.3% | 74.0% | 68.8% | 35.0 |
| P2 Reclaim | 67.4% | 77.1% | 64.2% | 33.9 |
| P3 Failed Acceptance | **35.3%** | **49.6%** | **50.8%** | 32.4 |

The largest distinction is not “retest vs no retest.”

It is:

> **accepted / reclaimed outside the old range vs still accepted back inside it.**

## Result 2 — Wick retest / hold strongly beats failed acceptance

P1 minus P3:

- re-expand within 5 moves: **+29.0 pp**, positive in **9/9 markets**;
- re-expand within 10: **+24.4 pp**, **9/9**;
- remaining life >=20: **+18.0 pp**, positive in 8/9;
- mean remaining life: +2.5 moves, only 4/9;
- positive net move to formal regime end: essentially flat (-0.8 pp).

This means a clean boundary test that never loses closing acceptance is a strong **near/intermediate continuation state**, although it does not guarantee a better terminal episode close.

## Result 3 — Close re-entry followed by reclaim also strongly beats failed acceptance

P2 minus P3:

- re-expand 5: **+32.1 pp**, **9/9 markets**;
- re-expand 10: **+27.5 pp**, **9/9**;
- remaining life >=20: +13.4 pp, 6/9;
- mean remaining life: +1.5 moves, 5/9;
- positive future net: -4.9 pp.

So a temporary close back inside the box is **not automatically a failed breakout**.

What matters is whether the boundary is causally reclaimed by the end of the frozen evidence window.

## Result 4 — Reclaim still matters at comparable retest depth

To avoid merely rediscovering that P3 retests are deeper, P2 and P3 were compared inside within-market quintiles of deepest wick penetration.

Eligible: 9 markets / 18 cells.

P2 reclaim minus P3 failed acceptance:

- re-expand 5: **+20.0 pp**, positive in 7/9 markets;
- re-expand 10: **+16.3 pp**, 6/9;
- remaining life >=20: +8.0 pp, 6/9;
- mean remaining life: approximately flat;
- future net: -5.7 pp.

Therefore reclaim contains information beyond retest depth alone.

## Result 5 — Clean retest / hold is surprisingly close to immediate expansion for re-expansion

Raw P1 minus P0:

- re-expand 5: **-1.7 pp**;
- re-expand 10: **-4.4 pp**;
- remaining life >=20: -8.4 pp;
- mean remaining life: -7.3 moves.

Immediate expansion tends to be the more durable regime state.

But it also begins much stronger.

Average immediate breakout overshoot:

- P0 No-touch: **+1.33 ATR**;
- P1 Wick Hold: **+0.33 ATR**;
- P2 Reclaim: +0.39 ATR;
- P3 Failed Acceptance: +0.49 ATR.

So P0's advantage is partly a different market-behavior path, not simply “retest is bad.”

## Result 6 — At comparable three-bar follow-through, retest / hold is roughly equal to no-touch on near-term re-expansion

Within market × follow-through quintile, compare P1 vs P0.

Eligible: **9 markets / 17 cells**.

P1 minus P0:

- re-expand 5: **+2.3 pp**, 5/9;
- re-expand 10: **-1.4 pp**, 4/9;
- remaining life >=20: -2.4 pp, 5/9;
- mean remaining life: **-9.8 moves**, 2/9;
- future net: -8.2 pp.

Interpretation:

> **Once early directional progress is comparable, a clean retest / hold is not materially worse than immediate expansion for the next re-expansion event.**

However immediate expansion still tends to live longer as a formal regime.

That supports P1 as a valid continuation / possible second-entry state without claiming it is superior to P0.

## Result 7 — Retest / hold is not just a strong-breakout artifact

Average three-bar geometry:

### P0 No-touch
- breakout overshoot: +1.33 ATR;
- follow-through: +1.27 ATR;
- t+3 acceptance margin: +2.60 ATR.

### P1 Wick Hold
- breakout overshoot: only +0.33 ATR;
- follow-through: +0.51 ATR;
- t+3 acceptance: +0.84 ATR.

### P2 Reclaim
- breakout overshoot: +0.39 ATR;
- follow-through: +0.47 ATR;
- t+3 acceptance: +0.86 ATR.

### P3 Failed Acceptance
- breakout overshoot: +0.49 ATR;
- follow-through: **-1.59 ATR**;
- t+3 acceptance: **-1.09 ATR**.

Notably P3 starts with a slightly larger average breakout overshoot than P1 or P2.

Therefore the superior P1/P2 continuation is not explained by a stronger breakout bar.

## Result 8 — Temporal evidence broadly supports the path distinction

### P1 vs P3 — re-expansion 5 / 10

- 2010–2014: +12.2 pp / +2.8 pp;
- 2015–2019: **+51.4 pp / +59.3 pp**;
- 2020–2026: +15.5 pp / +5.9 pp.

The effect varies in magnitude but does not show the 2015–2019 collapse seen in the old compression variables.

### P2 vs P3

- 2010–2014: approximately flat on re-expand-5, +18.2 pp on re-expand-10;
- 2015–2019: **+59.6 pp / +56.3 pp**;
- 2020–2026: +10.7 pp / +6.6 pp.

Smaller era cells limit precision, but there is no evidence that reclaim is merely a recent-era effect.

## Result 9 — Direction behavior is broadly consistent

P1 vs P3 re-expansion:

- Markdown: +30.2 pp / +23.9 pp;
- Markup: +26.7 pp / +25.8 pp.

P2 vs P3:

- Markdown: +28.8 pp / +24.4 pp;
- Markup: +33.8 pp / +29.1 pp.

No direction-specific path definition is justified.

## Research decision

### Promote P0 as a valid healthy path

Immediate expansion is a distinct healthy path:

> strong breakout → no meaningful early retest → continued acceptance.

It should not be forced to wait for a retest that may never occur.

### Promote P1 as a valid retest-continuation state

A boundary wick retest with all closes remaining outside the old box passes the admission gate as a genuine continuation state.

It:

- strongly outperforms failed acceptance;
- works in both directions;
- does not collapse in 2015–2019;
- remains near P0 on near-term re-expansion after matching three-bar progress.

This supports the trader intuition that a clean retest / hold can be a high-quality continuation setup.

### Promote P2 as a recovery / reclaim state, with weaker semantics than P1

A temporary close back inside the old box followed by reclaim by t+3 also strongly improves future re-expansion versus remaining inside.

The reclaim effect survives partial control for retest depth.

However:

- durability advantage is weaker;
- terminal future-net advantage is absent.

So P2 is a meaningful recovery state, but it is not yet equivalent to a clean P1 hold.

### P3 is confirmed negative evidence

Remaining accepted inside the old box at t+3 is the clearest false-breakout state in this path taxonomy.

## Important nuance

The data do **not** support the simplistic rule:

> “Any retest is better than no retest.”

Instead they support:

> **Retest is acceptable if the old boundary holds or is causally reclaimed. Failure to regain outside-range acceptance is the problem.**

There are therefore at least two legitimate healthy breakout paths:

1. **Immediate Expansion**
2. **Retest / Hold or Reclaim**

## What this still does not prove

A “second entry” normally implies one more event:

> after the retest / reclaim, price **resumes** in the breakout direction.

This Stage 1 intentionally did not use future resume to label the path.

Therefore it has not yet identified the best executable second-entry trigger.

## Next research gate

The next non-redundant study should be:

> **Resume Trigger Challenge — after P1/P2 retest states are known, what causal re-expansion event should earn the second add-risk step?**

Candidate event families should be frozen before outcomes:

- first close beyond the pre-retest favorable close/extreme;
- first new favorable close-path extreme after the retest;
- possibly FVG / imbalance interaction as a separate later challenger.

The economic sizing test should still wait until the resume trigger is defined and its confirmation tax measured.

Refs #78, #80, #76.
