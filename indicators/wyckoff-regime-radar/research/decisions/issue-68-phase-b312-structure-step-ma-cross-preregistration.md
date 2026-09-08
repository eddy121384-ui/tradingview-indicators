# Issue #68 Phase B3.12 — Structure Step / MA-Cross Audit Preregistration

Status: preregistered diagnostic only. Frozen C-2 classifier and B3.3 Core Bias remain unchanged. No performance use.

## Motivation

B3.10 mechanical handoff attribution identified Structure as the most frequent final blocker (140 / 373) and the dominant fresh-raw handoff driver (279 / 373). B3.11 demoted Trace to a secondary stale residual.

The inherited current Structure primitive is discrete:

- Bull Structure = +50 if close > MA50, +50 if close > MA200
- Bear Structure = +50 if close < MA50, +50 if close < MA200

Therefore the S2-vs-S5 weighted Structure edge can only occupy three principal states:

- -17: below both moving averages
- 0: between the two moving averages
- +17: above both moving averages

(the Bear audit is the exact reciprocal orientation).

## Question

Are S5->S2 / S2->S5 raw handoffs disproportionately caused by these discrete MA-relation steps, such that the classifier waits for price to cross MA50 and/or MA200 after Break evidence has already turned toward the new direction?

## Frozen diagnostics

For every burned FX pair and reciprocal representation:

1. classify the oriented Structure state as old-side / split-neutral / target-side from the existing C-2 values;
2. identify exact raw old->new handoff events using the unchanged six-component S2-vs-S5 duel;
3. at each handoff, record whether Structure improves on the handoff bar;
4. identify whether the improvement corresponds to a target-side crossing of the current MA50 relation, MA200 relation, both, or neither;
5. report Break direction at t-1 and t;
6. measure the consecutive target-positive Break run already present at t-1 when the handoff occurs;
7. measure the consecutive target-positive Structure run at t-1;
8. report the Structure transition matrix around handoffs (-17/0/+17 oriented states);
9. preserve the six-component reconstruction identity.

No new score threshold is introduced. Structure state categories use the exact existing discrete values/MA relations.

## Engineering gates

- six-component reconstruction error <= 1e-9;
- reciprocal exact-handoff event agreement >= 99%;
- reciprocal Structure-improvement-at-handoff agreement >= 99% pooled;
- reciprocal MA50-cross / MA200-cross attribution agreement >= 99% pooled comparable handoffs;
- no unexplained Structure transition category.

## Human follow-up

Only after the mechanical audit passes, generate a minimal TradingView audit for FR10Y and JGB10Y showing:

- S2 vs S5 raw winner;
- Break direction;
- Structure state;
- price-vs-MA50 relation;
- price-vs-MA200 relation;
- raw handoff marker.

The visual question is whether a visibly established yield uptrend spends a long interval with Break already Bull but Structure still split/old-side until a later MA crossing.

## Boundary

B3.12 may diagnose Structure timing but may not change MA lengths, replace binary Structure with a continuous score, alter Structure weight, tune Break, or evaluate PnL.