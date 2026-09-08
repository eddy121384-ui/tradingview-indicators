# Issue #68 Phase B3.17 — Human Closeout / Return to B3.4

Status: **HUMAN CONFIRMED / CLASSIFIER FORENSIC STOP-GATE CLOSED / NO PRODUCTION CHANGE**

## Scope

This memo closes the classifier-forensic detour that began after B3.4 cross-market human review exposed suspiciously slow regime reversals on long-rate markets, especially FR10Y and JGB10Y.

The B3.17 visual audit used the locked Bull / 1D review set:

- JGB10Y
- FR10Y
- US10Y
- EURUSD
- S&P 500

The review was diagnostic only. It did not use Strategy Tester, returns, PnL, Sharpe, drawdown, hit-rate, costs, stops, targets, or sizing.

## Mechanical result retained

The frozen B3.16 counterfactual removed only the old-direction range-memory source from Break during `MA target-side + old range memory active`. B3.17 then applied that exact shadow globally.

Global result:

- eligible stale-overlap bars: **1,523**
- raw-advance bars / episodes: **69 / 51**
- later observed handoff in the same MA-side run: **25 / 51**
- false-release episodes: **26 / 51 = 51.0%**
- one-bar false releases: **20 / 26 = 76.9%**
- observed raw transitions: **746**
- shadow raw transitions: **793 = 1.063x**
- MA-side runs with more than one advance episode: **5**

Engineering checks passed on the preregistered hard gates. Transition-count reciprocal agreement of 97.619% remains recorded as a diagnostic only and was not a preregistered hard gate.

## Human review result

The TradingView review did not reveal a classification or rendering bug capable of rescuing the global rule.

Observed visually:

- useful local raw advances do exist, consistent with B3.16;
- false-release confirmations are also real and episodic rather than a bookkeeping artifact;
- US10Y visibly contains a repeated-advance / flip-flop case;
- rates and non-rates controls both show that stale-range release is not a rates-only defect;
- the global release does not repair the broad FR10Y reversal-lag history and introduces extra local instability.

## Final classifier-forensic decision

Retain:

`confirmed_local_causal_stale_range_brake`

Reject:

`global_stale_range_invalidation_as_production_semantics`

Therefore:

1. stale old-range memory is a real **local causal handoff brake**;
2. direct global invalidation is **not safe enough** to promote into production C-2;
3. production C-2 remains unchanged;
4. no B3.18 parameter, threshold, context, MA, Break-weight, or `breakoutBars` search is opened;
5. the classifier-forensic detour is closed at B3.17.

## Return to the original Issue #68 path

Issue #68 now returns to the existing B3.4 lifecycle / Exposure question.

The frozen architectural separation remains:

- **Core Bias** = slow directional regime memory;
- **Exposure** = executable Long / Flat / Short state layered on top of the same Core Bias.

Exposure must **not** be graded on whether it fixes Core Bias or classifier reversal timing. A delayed Core reversal is an accepted classifier limitation for this lifecycle comparison.

The resumed decision is the previously unresolved **A-vs-C exposure semantic comparison**. Candidate formulas remain exactly as preregistered; no new candidate or numeric threshold is introduced.

Resume preregistration:

`indicators/wyckoff-regime-radar/research/decisions/issue-68-phase-b34-resume-ac-semantic-preregistration.md`

PR #73 must remain Draft / Open. Issue #68 must remain Open until Eddy explicitly approves otherwise.
