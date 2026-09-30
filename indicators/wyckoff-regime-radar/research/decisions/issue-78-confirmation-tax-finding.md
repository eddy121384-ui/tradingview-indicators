# Issue #78 — Confirmation Tax / Time-to-Proof Finding

## Scope

This finding executes the frozen preregistration in
`issue-78-confirmation-tax-preregistration.md`.

The question was:

> **How much directional price proof should be required before increasing exposure, and how much trend opportunity is consumed while waiting for that proof?**

No proof threshold, time bucket, exposure percentage, classifier setting, or market-specific parameter was changed after results were inspected.

Accepted sample:

- 9 daily markets;
- 68,118 accepted Issue #76 event rows;
- 1,624 completed known-start Markup / Markdown episodes;
- 1,058 failed/small episodes with final MFE <4 entry ATR;
- 308 large episodes with final MFE >=8 entry ATR.

All results remain in-sample discovery evidence.

## Result 1 — Stronger proof filters more weak trends, exactly as expected

Equal-market share of all completed episodes that ever reach each proof level:

- +0.5 ATR: **71.5%**
- +1.0 ATR: **63.2%**
- +2.0 ATR: **50.0%**

Among failed/small episodes with final MFE <4 ATR, the proof-hit rates fall materially:

- +0.5 ATR: **57.5%**
- +1.0 ATR: **45.2%**
- +2.0 ATR: **25.5%**

So stronger proof clearly reduces the number of weak episodes that ever earn Full exposure.

Every MFE >=8 ATR episode necessarily reaches all three thresholds by construction. That fact is not evidence of predictive power. The relevant large-trend question is how much opportunity remains by the time proof is reached.

## Result 2 — Confirmation tax rises smoothly with proof strength

For the MFE >=8 ATR large-trend slice:

| Proof threshold | Mean bars to proof | Mean total MFE already consumed | Mean total MFE still remaining |
|---|---:|---:|---:|
| +0.5 ATR | 4.0 | 9.8% | 90.2% |
| +1.0 ATR | 5.5 | 13.1% | 86.9% |
| +2.0 ATR | 9.7 | 20.6% | 79.4% |

Even +2 ATR does not generally arrive after the whole trend is gone; large trends still have substantial favorable opportunity left. But it is meaningfully later than +0.5 or +1 ATR.

The frozen 25%-probe-then-Full audit makes the tax economically visible.

For large trends, equal-market mean Formal-Hold harvest is +10.725 entry ATR. Probe-then-Full retains:

- +0.5 ATR proof: **+9.527 ATR** = about **88.8%** of Full-at-entry harvest;
- +1.0 ATR proof: **+9.183 ATR** = about **85.6%**;
- +2.0 ATR proof: **+8.457 ATR** = about **78.9%**.

The stronger the proof requirement, the more front-end trend harvest is surrendered.

## Result 3 — The same confirmation tax buys real false-start protection

For failed/small MFE <4 ATR episodes, Full-at-entry loses an equal-market mean **-2.249 ATR** through formal regime end.

Probe-then-Full changes that to:

- +0.5 ATR proof: **-1.769 ATR**, about **21.4% less damage**;
- +1.0 ATR proof: **-1.645 ATR**, about **26.9% less damage**;
- +2.0 ATR proof: **-1.325 ATR**, about **41.1% less damage**.

The trade-off is exceptionally consistent cross-market:

- failed/small-episode harvest improves versus Full-at-entry in **9/9 markets** for all three proof thresholds;
- large-trend harvest is lower than Full-at-entry in **9/9 markets** for all three thresholds.

This is a genuine frontier rather than a pooled-sample artifact.

## Result 4 — +0.5 / +1 / +2 ATR form a smooth frontier, not a magic cutoff

There is no discontinuity that says one threshold is uniquely correct.

The three frozen proof levels behave as expected:

- **+0.5 ATR:** lowest confirmation tax, weakest false-start filter;
- **+1.0 ATR:** intermediate confirmation tax and intermediate protection;
- **+2.0 ATR:** strongest false-start protection, largest large-trend participation cost.

The study therefore does **not** identify a universal optimum threshold.

This is an important result: the add-risk problem is fundamentally an exposure frontier, not a hidden perfect trigger.

## Result 5 — Proof speed is interesting, but not stable enough to become a second gate

The preregistered time-to-proof buckets test whether reaching the same proof magnitude quickly leaves better continuation than reaching it slowly.

Full-sample evidence is most suggestive at +2 ATR.

At +2 ATR, proof reached in 1–5 moves versus 6–10 moves has roughly:

- **+2.02 ATR** more remaining favorable excursion on an equal-market basis;
- about **+10.2 percentage points** higher probability of another +2 ATR favorable excursion;
- about **+7.3 percentage points** more of total MFE still remaining.

The fast-versus-6–10 favorable-excursion difference is positive in **8/9 markets**.

However, the speed relationship is not temporally stable. When split into 2010–2014, 2015–2019, and 2020–2026, the ordering changes materially and several cells become sparse. In particular, 2015–2019 does not preserve a clean fast-proof advantage.

Therefore:

> **Do not promote time-to-proof into a second live add-risk gate yet.**

It remains a useful diagnostic, but the evidence is not strong enough for a universal rule.

## Result 6 — The proof frontier survives direction and broad era checks, but profitability remains regime-dependent

Proof-hit rates are similar in both directions:

- Markdown: about 73.6% / 65.0% / 50.7% for +0.5 / +1 / +2 ATR;
- Markup: about 69.5% / 61.7% / 49.4%.

The broad threshold ordering is also visible in 2010–2014, 2015–2019, and 2020–2026.

This does not repair the previously documented 2015–2019 economic weakness of the overall strategy. The confirmation study is about exposure timing, not proof of stable alpha.

## Research decision

The evidence supports a simple interpretation:

> **Directional progress is a valid causal way for a trend to earn more exposure, but stronger proof always carries a measurable confirmation tax.**

There is no evidence for a magic universal proof threshold.

Current architecture:

`Probe -> price proves itself -> increase exposure`

remains justified.

But the next candidate design should preserve the frontier rather than pretending one threshold is universally optimal.

The cleanest next experiment is therefore not to optimize another threshold. It is to preregister a small fixed **progressive proof ladder** using the already frozen landmarks, for example:

`25% -> 50% -> 75% -> 100%`

with exposure earned progressively at existing +0.5 / +1 / +2 ATR proof levels, then compare that ladder with the existing one-step proof policies and Full-at-entry.

That test would answer whether spreading the confirmation tax across several steps dominates waiting for one binary Full-exposure trigger.

Time-to-proof should remain diagnostic only unless separately validated on new evidence.

## Guardrail conclusion

Do not:

- search intermediate ATR thresholds after seeing this frontier;
- optimize proof speed buckets;
- create separate Markup / Markdown thresholds;
- tune 2015–2019 away;
- call any current threshold a production optimum.

Refs #78, #80 and #76.
