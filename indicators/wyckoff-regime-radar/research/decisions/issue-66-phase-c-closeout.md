# Issue #66 — Phase C Formula-Repair Closeout

Status: **classifier-formula repair STOPPED; C-2 accepted as the parity baseline**

This decision is based on the preregistered Phase C-3 residual forensic. It is not a PnL, Sharpe, CAGR, MaxDD, or strategy-performance decision.

## Accepted classifier baseline

The accepted Issue #66 price-only classifier for downstream implementation parity is **Phase C-2**, i.e. the accepted B-7 core plus the single Stage-1 candidate-conflict repair that mirrors the frozen Stage-4 clause.

C-2 observed reciprocal symmetry on the frozen EURUSD / USDJPY / GBPUSD / AUDUSD fixtures:

- Candidate-display mirror: 99.65%
- Strong-stage mirror: 99.33%
- Formal mirror: 99.73%
- Formal-transition mirror: 99.59%
- Formal mismatch bars: 18
- Strong-stage mismatch bars: 44

The actual Issue #57 stale-pressure persistence state machine replays exactly and is symmetric under explicitly mirrored synthetic inputs.

## Why formula repair stops here

Phase C-3 explains every remaining strong-stage mismatch bar; unexplained residual = 0.

Residual overlap:

- candidate conflict: 32 / 44
- top-gap threshold: 14 / 44
- top-stage / argmax: 6 / 44
- probability validity: 0
- dominant threshold: 0
- evidence threshold: 0

Within the 28 remaining Stage-1/Stage-4 conflict mismatches where top stage is already mirrored:

- holding-threshold predicate mismatch: 27
- exhaustion-threshold predicate mismatch: 1
- continuation-override-only mismatch: 0

The Stage-1 and Stage-4 conflict formulas are already explicit reciprocal mirrors in C-2. The remaining mismatches therefore do not identify another directional source-code asymmetry. Moving `absorbThreshold`, `topGapMin`, or other thresholds now would be historical-sample score chasing, not structural repair.

Formal residual is also small and concentrated: EURUSD 0, GBPUSD 0, USDJPY 9, AUDUSD 9; aggregate state-carry share is 61.11%.

## Frozen boundary after this decision

Until Pine↔Python implementation parity is established:

- do not move classifier thresholds to improve reciprocal agreement;
- do not alter C-2 formulas because of TradingView parity errors;
- do not introduce Volume, MTF, Divergence, HMM, or strategy/PnL logic;
- do not modify frozen v0.5.2.1 source;
- do not merge PR #67 or close Issue #66 without explicit approval.

Implementation-parity defects may be fixed only when they are demonstrated as translation/runtime semantic differences between the accepted C-2 Python reference and the Issue #66 Pine harness.

## Handoff

Proceed to **Phase D — Pine↔Python parity**. Use C-2 as the reference implementation and TradingView OHLC as Python input so feed differences are removed from the implementation-parity question.
