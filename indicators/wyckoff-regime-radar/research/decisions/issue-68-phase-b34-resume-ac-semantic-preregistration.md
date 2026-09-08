# Issue #68 Phase B3.4R — Resume A-vs-C Exposure Semantic Gate

Status: **RESUMED EXISTING B3.4 / NO PNL / NO NEW CANDIDATE / CLASSIFIER FROZEN**

## Why this gate resumes now

B3.4 originally separated slow **Core Bias** from executable **Exposure** and preregistered three exposure translations. Cross-market human review then exposed suspicious upstream reversal latency on FR10Y/JGB10Y, so the unresolved exposure selection was paused while B3.5–B3.17 localized the classifier behavior.

That forensic detour is now closed. B3.16 confirmed stale old-range memory as a local causal brake, while B3.17 rejected direct global stale-range invalidation because false releases and churn were too high. No production classifier change follows.

Therefore this phase resumes the original B3.4 question rather than opening B3.18:

> Given the same frozen Core Bias, which existing exposure lifecycle is semantically more coherent: A or C?

## Frozen lineage

The following remain unchanged:

- Issue #66 C-2 price-only classifier and production parameters;
- B3.3 Core Bias memory;
- Formal, Flat Action, Pace, persistence, MA lengths, Break weight and `breakoutBars`;
- all A/B/C exposure formulas from the original B3.4 preregistration.

No Volume / MTF / Divergence / HMM rescue is allowed.

Candidate B remains available in the original artifact but is **not reopened as the active decision gate**. The resumed decision scope is the previously unresolved A-vs-C comparison.

## Candidate A — Formal trend-family exposure

Exact original semantics:

- Bull Core Bias + Formal 2/3 => Long;
- Bear Core Bias + Formal 5/6 => Short;
- otherwise => Flat.

A is intentionally simple and stateless at the exposure layer.

## Candidate C — Stateful Flat Action entry + Pace defensive flat

Exact original semantics:

Entry / re-entry from Flat:

- Bull Core Bias requires Flat Action F2/F3 to enter Long;
- Bear Core Bias requires Flat Action F4/F5 to enter Short.

Holding:

- while Core Bias remains aligned, exposure persists unless an existing mirrored Pace defensive / observe state returns it to Flat.

Frozen Pace defensive mappings:

- Long defensive / observe: Pace 0, 40, 70, 71, 75;
- Short defensive / observe: Pace 0, 15, 70, 71, 74.

Bias reversal:

- an existing position first returns to Flat;
- no direct Long-to-Short or Short-to-Long executable flip;
- later same-direction Flat Action authorization is required for re-entry.

## Hard directional invariant

For both A and C:

- Core Bias +1 may produce only Long or Flat;
- Core Bias -1 may produce only Short or Flat;
- Core Bias 0 must produce Flat;
- exposure must never oppose Core Bias.

## What this gate is allowed to judge

The comparison is conditional on the **same frozen Core Bias**. It asks only whether A or C translates that Bias into a more coherent lifecycle.

Primary semantic questions:

1. During a sustained Core Bias regime, does the candidate spend meaningful time exposed in the aligned direction?
2. Do broad range / ambiguous periods recover genuine Flat / Observe intervals rather than forced exposure?
3. Are Flat intervals purposeful, or do they fragment a coherent trend unnecessarily?
4. Does the candidate avoid pathological one-bar active/flat churn?
5. After a defensive Flat inside an unchanged Core Bias, does re-entry occur in a semantically sensible way?
6. Does the candidate ever oppose Core Bias? Any such violation is a hard failure.

## Explicit non-question

This phase does **not** ask whether A or C repairs delayed Core Bias reversal.

If Core Bias itself remains stale through a market reversal, both exposure candidates inherit that upstream limitation. A/C are not penalized or rewarded for solving a problem they are architecturally forbidden to solve.

## Descriptive diagnostics allowed

No performance metrics are allowed. Descriptive semantic counters may include:

- active vs Flat occupancy within each Core-Bias run;
- exposure transition count;
- one-bar active episodes;
- one-bar Flat episodes;
- Flat-to-active reacquisition within unchanged Core Bias;
- opposite-Bias violation count;
- reciprocal / mirror agreement when mechanically available.

These statistics describe lifecycle behavior only; they do not optimize profitability.

## Locked human review order

First gate:

- **EURUSD 1D** — original B3.4 semantic reference market.

Cross-market lifecycle controls after EURUSD:

- **FR10Y 1D**
- **JGB10Y 1D**
- **US10Y 1D**

Rates charts are reviewed conditionally on Core Bias. Known classifier reversal latency is not an A-vs-C scoring criterion.

## Stop rule

This gate may end in:

- select A as the cleaner exposure lifecycle;
- select C as the cleaner exposure lifecycle;
- remain unresolved if neither is semantically adequate.

If unresolved, record the limitation. Do **not** invent Candidate D, add a durability threshold, tune Pace mappings, search parameters, or use PnL to break the tie.

## Hard boundary

- no Strategy Tester / PnL / returns / Sharpe / drawdown / hit-rate;
- no classifier repair;
- no threshold or parameter search;
- no new exposure candidate;
- no production change during this human semantic gate;
- PR #73 stays Draft / Open;
- Issue #68 stays Open.
