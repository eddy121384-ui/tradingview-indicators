# Issue #78 — Post-Proof Deterioration Signal Finding

## Scope

This finding executes the frozen preregistration in
`issue-78-post-proof-deterioration-preregistration.md`.

The diagnostic starts only after an episode has first earned +1.0 entry ATR of directional progress. This isolates management deterioration from initial-entry failure.

Accepted sample:

- 68,118 Issue #76 event rows;
- 1,624 completed known-start Markup / Markdown episodes;
- 1,031 episodes remain alive after first reaching +1.0 ATR proof and are eligible for post-proof deterioration analysis.

No deterioration threshold, stall horizon, classifier input, or exposure percentage was changed after outcomes were inspected.

## Result 1 — Giveback severity has a clean recovery gradient

At the first post-proof crossing of each frozen giveback landmark, equal-market recovery probability to a new favorable close-path extreme before formal regime loss is:

| First giveback | Event rate among +1-ATR-proved episodes | Recovery probability | Regime ends before recovery | Mean bars from proof to event |
|---|---:|---:|---:|---:|
| 0.5 ATR | 98.6% | 68.0% | 32.0% | 3.4 |
| 1.0 ATR | 98.0% | 58.6% | 41.4% | 6.3 |
| 2.0 ATR | 92.7% | 42.1% | 57.9% | 12.8 |
| 4.0 ATR | 63.3% | 25.1% | 74.9% | 26.3 |

The recovery ordering is fully monotone in **9/9 markets**.

Interpretation:

- 0.5–1 ATR giveback is common normal trend damage; most such episodes still recover.
- 2 ATR is the first frozen severity level where non-recovery becomes more common than recovery.
- 4 ATR is a substantially damaged state: about three quarters fail to recover before formal regime loss.

## Result 2 — Mild giveback is too common to justify aggressive de-risking

Almost every +1-ATR-proved episode eventually experiences at least 0.5 or 1 ATR of close-path giveback before the formal regime ends.

Therefore these mild thresholds are poor binary-exit candidates.

They may still be useful as **warning / stop-add** states, because they indicate deterioration without implying that the trend is more likely than not to be dead.

This supports separating:

- "do not add more right now"
from
- "actively cut existing exposure."

## Result 3 — Severe giveback still contains a recovery tail

Even after 4 ATR of giveback:

- recovery to the prior favorable extreme still occurs about **25.1%** of the time;
- probability of at least +2 ATR additional favorable excursion from the event close remains about **42.5%**;
- equal-market mean future favorable excursion is about **4.60 ATR**, although the equal-market median is only about **1.77 ATR**.

The large mean-versus-median gap is important: a minority of damaged trends still produce substantial rebounds / resumed trends.

Therefore this diagnostic does **not** support an automatic all-or-nothing exit at 4 ATR. Progressive defensive exposure remains more consistent with the observed tail behavior.

## Result 4 — Stall duration also works, but it is slower

For the first post-proof event with no new favorable extreme for the frozen 5 / 10 / 20-move horizons:

| Stall duration | Event rate | Recovery probability | Regime ends before recovery | Mean bars from proof to event |
|---|---:|---:|---:|---:|
| 5 moves | 95.9% | 54.5% | 45.5% | 9.8 |
| 10 moves | 86.3% | 38.7% | 61.3% | 20.3 |
| 20 moves | 49.3% | 24.7% | 75.3% | 38.7 |

The recovery ordering is also fully monotone in **9/9 markets**.

So stall is a valid deterioration family, not noise.

However, it reaches roughly comparable recovery-risk states later than giveback.

### Comparable severity examples

- 2 ATR giveback: 42.1% recovery, detected about 12.8 moves after proof.
- 10-move stall: 38.7% recovery, detected about 20.3 moves after proof.

And:

- 4 ATR giveback: 25.1% recovery, detected about 26.3 moves after proof.
- 20-move stall: 24.7% recovery, detected about 38.7 moves after proof.

The 2-ATR giveback arrives earlier than the 10-move stall in **9/9 markets** on a market-average timing basis.

The 4-ATR giveback arrives earlier than the 20-move stall in **8/9 markets**.

## Result 5 — Cross-era and direction robustness is good

### Giveback recovery probabilities

2010–2014:
- 0.5 / 1 / 2 / 4 ATR: **67.8% / 58.8% / 41.0% / 30.8%**

2015–2019:
- **63.9% / 50.3% / 29.3% / 17.1%**

2020–2026:
- **65.4% / 53.9% / 36.3% / 17.0%**

The severity gradient survives all three preregistered eras.

### Direction split

Markup:
- **68.1% / 58.4% / 38.0% / 22.0%**

Markdown:
- **67.7% / 58.7% / 46.2% / 28.4%**

No separate directional deterioration rule is justified.

Stall duration also preserves the broad recovery decline across eras and both directions, though the 2020–2026 10-vs-20 stall distinction is weaker than the giveback gradient.

## Research decision

**Promote giveback from the running favorable close-path extreme as the primary deterioration family for the next de-risk-policy study.**

Keep stall duration as a diagnostic / possible secondary confirmation only. Do not add it as another live gate yet.

The evidence supports a three-level semantic interpretation:

1. **Mild damage (0.5–1 ATR):** warning / stop-add territory. Recovery remains common.
2. **Material damage (around 2 ATR):** first credible progressive de-risk territory. Most episodes no longer recover to the prior extreme.
3. **Severe damage (around 4 ATR):** strong defensive territory, but not necessarily an automatic flat because recovery / rebound tails remain material.

These are action semantics, not yet exposure percentages.

## Implication for the next pass

The next preregistered policy should test a **warning-first damage latch**:

- mild giveback can block further exposure upgrades without cutting existing earned exposure;
- material giveback can reduce exposure progressively;
- re-risking should remain latched until a new favorable close-path extreme, rather than reacting to every bucket improvement.

The policy should be tested against both frozen add-risk benchmarks:

- +1 ATR one-step add-risk;
- 25/50/75/100 progressive proof ladder.

No new ATR threshold is needed.

Refs #78, #80 and #76.
