# Issue #68 Phase B3.17 — Global False-Release / Churn Audit preregistration

Status: diagnostic shadow only / frozen production C-2 / no performance use.

## Question

B3.16 confirmed that stale old-direction range memory is a local causal brake in the strict event-selected population. B3.17 asks the necessary safety question before any semantics redesign:

> If the exact same release rule is applied globally to every eligible stale-overlap bar, does it mostly advance coherent handoffs, or does it create false early flips and churn?

This is not a parameter search.

## Frozen shadow rule

Reuse the exact B3.16 counterfactual with no change:

- condition: current MA relation is target-side AND old-direction range memory is active;
- remove only the old-direction range-memory source from the old Break score;
- recompute the old Break score through the existing mode / MA / range hierarchy;
- target Break evidence unchanged;
- all five non-Break raw components unchanged;
- Break weight, MA lengths and `breakoutBars` unchanged.

Apply this rule to **all eligible bars**, not only known Break-final-blocker events.

## Global populations

For each frozen FX pair and reciprocal quotation, classify every target-side MA run into observed vs shadow raw behavior.

Required populations:

1. eligible stale-overlap bars;
2. bars where observed raw <= 0 and shadow raw > 0 (`raw advance`);
3. shadow target flips that are later followed by observed target handoff within the same MA-side run;
4. shadow target flips that revert before any observed target handoff (`false release`);
5. one-bar shadow target runs;
6. repeated shadow flip-flop within one MA-side run.

Do not define success using returns.

## Primary outputs

Report aggregate and per pair:

- total eligible stale-overlap bars;
- total raw-advance bars and distinct raw-advance episodes;
- episode lead to observed target handoff where one occurs;
- durable-advance episodes versus false-release episodes;
- one-bar false-release share;
- median / p75 shadow target-run duration before observed handoff or reversion;
- observed raw-transition count versus shadow raw-transition count;
- transition-count ratio;
- number of MA-side runs with 0 / 1 / >1 shadow flip-flops;
- fraction of raw advances occurring with target new-range evidence already present;
- reciprocal agreement for eligibility, raw-advance labels, episode outcome and transition counts.

## Durability semantics

No new tunable horizon is allowed.

Use only structural clocks already in the frozen classifier:

- an advance is `followed by observed handoff` if observed raw becomes target-positive later in the **same contiguous target-side MA run**;
- a `false release` is a shadow target-positive episode that ends before observed raw ever becomes target-positive in that same MA run;
- `one-bar` means exactly one bar, descriptive only, not a threshold for acceptance.

## Engineering gates

- exact B3.16 shadow reconstruction retained;
- reciprocal eligibility / raw-advance agreement >=99%;
- reciprocal episode-outcome agreement >=99%;
- unexplained accounting = 0;
- no performance keys in report.

There is deliberately no gate requiring fewer or more transitions.

## Decision rule

- If global raw advances are usually followed by observed handoffs in the same MA run and transition/churn inflation is modest, the B3.16 release semantics survives the safety gate and can move to a formal semantics-design comparison against frozen C-2.
- If false releases or one-bar flip-flops dominate, reject direct stale-memory invalidation as a production rule even though B3.16 local causality remains true.
- If the result is mixed by context, next research should localize the missing contextual condition without tuning existing parameters.

## Human review after mechanical gate

If mechanical gates pass, generate one TradingView audit showing:

- observed raw sign;
- shadow raw sign;
- stale overlap;
- raw advance;
- observed handoff;
- false-release episode marker;
- shadow flip-flop marker.

Locked visual set remains FR10Y, JGB10Y, US10Y, EURUSD and S&P 500, Bull / 1D.

## Hard boundary

No PnL, no Strategy Tester interpretation, no `breakoutBars` tuning, no Break-weight / MA-length / threshold search, no production C-2 modification, no Volume / MTF / Divergence / HMM rescue.
