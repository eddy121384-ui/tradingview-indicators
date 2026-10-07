# Issue #78 — A6 trigger-layer discovery preregistration (frozen Core-2 context)

Date: 2026-10-07 (frozen BEFORE any trigger-conditioned forward outcome is
computed). Discovery on recovered OOS3 ONLY. OOS4 must not be mined for
triggers; OOS5 untouched. No policy/sizing/production/Pine. PRs #80/#148
unmerged.

## Frozen context (verbatim, reused by import, never modified)

Core-2 from A4: dir_structure side/context, extension=|dir_velocity|,
prior-only expanding percentile `(less+0.5·equal)/N_prior`, 252-bar
minimum, hard 80/20 primary, 70/30 robustness, h10 primary, aligned
bull +1 / bear −1. Context attached is the causal Core-2 cell at the
confirmation close bar (never future, never backdated).

## Frozen structural level (one family only)

Lookback: prior 20 COMPLETED daily bars. Bullish level at bar t:
`prior_high_20(t) = max HIGH over bars t−20..t−1`. Bearish:
`prior_low_20(t) = min LOW over bars t−20..t−1`. Current bar excluded.
No lookback scan, no post-result change.

## Trigger families (frozen; CLOSE-only; mirror bull/bear)

- T0 raw break: close[t] > prior_high_20 (bull) / < prior_low_20 (bear).
  Knowable at close t. PRIMARY outcome from bar e=t+1 (next-bar
  actionable); same-close e=t recorded descriptive only.
- T1 acceptance: freeze L at t0; next 3 completed bars t0+1..t0+3;
  accepted iff ≥2 of 3 closes beyond L AND close[t0+3] beyond L.
  Timestamp t0+3 (never backdated). Primary e=t0+4; descriptive e=t0+3.
  Confirmation tax = accepted outcome vs raw-breakout outcome at
  equivalent actionable timing (descriptive).
- T2 pullback-reclaim: within next 5 completed bars after t0, price must
  FIRST close back inside L (≤L bull / ≥L bear), then a LATER bar in the
  same window closes beyond L; first such close is trigger time tr.
  Primary e=tr+1; descriptive e=tr. No shape/wick rules.
- T3 failure: raw break at t0 (close beyond level), freeze L; within next
  3 completed bars, first close back inside L confirms (bullish = failed
  breakdown, bearish = failed breakout; reversal semantics). Timestamp tf;
  primary e=tf+1; descriptive e=tf.

## Dedup state machine (frozen, parameter-free)

Per stock per side: a T0 fires at t iff condition(t) true AND condition(t−1)
false (no consecutive-bar repeats) AND no sequence active on that side.
One sequence yields at most one T1/T2/T3 derivation from its frozen L;
after resolve/expire the side is free (level recomputes every bar, so any
later qualifying bar is a new event). No new T0 on a side while its
sequence window is open.

## Context × trigger (restricted set only)

Continuation: bull_low/bull_high × bullish T0/T1/T2;
bear_low/bear_high × bearish T0/T1/T2. Failure: bull contexts × bullish
failed-breakdown T3; bear contexts × bearish failed-breakout T3. No other
interaction cells.

## Outcomes (frozen)

Forward clock starts AFTER confirmation (primary e as above). Aligned
h1/h5/h10(PRIMARY)/h20. Unit of analysis = EVENT (deduped triggers), one
row per trigger; one-stock-one-vote aggregation. Per trigger and per
context×trigger: event/stock counts, equal-stock mean, median-stock
median, positive-stock fraction, p5/p10/ES5, sleeves, sectors where
adequate, fixed blocks 2000–04/05–09/10–14/15–19/2020–26/ALL, tails.

## Incremental value (frozen baseline)

`incremental_mean = trigger_conditioned_mean − same_context_mean`, where
same-context mean is the COMMITTED A4 causal Core-2 cell mean (h10 ALL;
block-level secondarily). Also median-stock increment, fraction of stocks
positive-incremental, block/sleeve/sector splits. A trigger survives ONLY
by adding beyond context — raw positive mean is insufficient.

## Survivor rule (frozen; no near-pass)

KEEP_FOR_OOS / WEAK / REDUNDANT_WITH_CONTEXT / CONTRADICTED /
INSUFFICIENT_SAMPLE. KEEP_FOR_OOS requires ALL: (1) h10 incremental mean
> 0; (2) positive incremental in a clear majority of stocks (>55%);
(3) expected sign in ≥4/5 adequate blocks; (4) not one sleeve/sector/tail
only; (5) usable frequency (≥30 stocks with ≥5 trigger events at h10 ALL);
(6) clean causal timing (proven by tests); (7) no mirrored bull/bear
implementation asymmetry. Conceptual priority T1 > T3 > T2 > T0 is
interpretive only and never overrides results.

## Tests (frozen list)

Prior-20 excludes current bar; future rows can't alter past labels;
frozen L; T1 exactly 3 bars + majority + final-close rule; T2 order
pullback-then-reclaim; T3 window exactly 3; timestamp = knowable bar;
dedup blocks repeats; bull/bear mirrored; Core-2 imported unchanged;
deterministic real-data rerun.

Refs #78 #173 #170 #168 #162 #159 #156 #153 #148 #147 #138 #119 #80.
