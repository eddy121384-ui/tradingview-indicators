# Issue #68 — Cross-Market Formal-Path Attribution

Status: **DISCOVERY ATTRIBUTION / CORE VALIDITY GATE PAUSED / NO PNL / NO TUNING**

## Why this attribution exists

The Core Semantic Validity discovery audit showed that the same obvious 2022–2023 10Y yield-rise regime is not treated uniformly by the frozen classifier:

- FR10Y: extreme adverse Core behavior (0% aligned in the shared discovery window);
- JP10Y: severe delayed recognition;
- DE10Y / IT10Y: materially lighter but non-zero delayed/mismatched intervals;
- GB10Y / AU10Y / US10Y: substantially cleaner recognition in the same window.

This falsifies the simple narrative that the failure is merely caused by "leaving a low-rate / negative-rate / YCC regime." Germany and Italy experienced the same broad 2022 European rate shock without reproducing the FR10Y failure magnitude.

The next question is therefore upstream and comparative:

> At which frozen classifier layer does FR10Y / JP10Y first diverge from the cleaner cross-market paths: RAW, TOP, STRONG, or FORMAL?

## Discovery-only status

All markets and group labels below were selected after viewing Core outcomes. Therefore this phase is **burned discovery attribution**, not a new validation sample and not an acceptance gate.

It must not be used to tune thresholds or claim out-of-sample performance.

Shared chart window, all 1D:

- `2022-01-03 -> 2023-12-29`
- expected semantic direction: **Bull** for the displayed 10Y yield series.

Comparison set:

- extreme adverse: FR10Y;
- severe adverse: JP10Y;
- intermediate: DE10Y, IT10Y;
- lower-error comparison: GB10Y, AU10Y, US10Y.

The labels are descriptive only and are not test classes.

## Frozen layer definitions

No layer is redefined for this phase.

### RAW

RAW is the strict-greater winner among the existing six frozen raw stage scores:

- S1 `accRaw`
- S2 `markupRaw`
- S3 `reaccRaw`
- S4 `distRaw`
- S5 `markdownRaw`
- S6 `redistRaw`

Tie priority remains the production Stage1 -> Stage6 strict-greater order used in prior B3.8 attribution.

Direction mapping:

- Bull = S2 / S3;
- Bear = S5 / S6;
- Neutral/range = S1 / S4.

### TOP

TOP uses the existing frozen `topId` after classifier ranking. Direction mapping is the same S2/S3 Bull, S5/S6 Bear, S1/S4 neutral.

### STRONG

STRONG is the existing TOP direction only when the frozen `strongCandidate` gate passes; otherwise neutral.

No gate threshold is altered.

### FORMAL

FORMAL is the existing frozen `formalId`, mapped to Bull/Bear/neutral by the same stage-family rule.

## Descriptive measurements

For each layer inside the fixed shared window, record only semantic path diagnostics:

- Bull occupancy %;
- Bear occupancy %;
- first Bull-family arrival delay from window start;
- longest continuous non-Bull run.

The visual audit also renders the four layer paths so the same dates can be compared across markets.

No numeric PASS/FAIL threshold is introduced in this attribution phase.

## Attribution logic

Interpretation is hierarchical:

1. **RAW already late / mostly non-Bull in FR/JP while controls become Bull early**
   - problem originates in raw formulation / feature competition;
   - only then is component-level comparison (Break / Heat / Structure / Extension / Continuation / Trace) justified.

2. **RAW becomes Bull comparably early, but TOP remains late**
   - ranking / stage competition is the first divergence layer.

3. **TOP becomes Bull comparably early, but STRONG remains late**
   - Strong gate formation is the first divergence layer.

4. **STRONG becomes Bull comparably early, but FORMAL remains late**
   - persistence / formalization is the first divergence layer.

5. If no single layer cleanly separates adverse from comparison markets, record a distributed path failure rather than forcing a single-cause story.

## Hard boundaries

- no Strategy Tester / PnL / returns / Sharpe / drawdown / hit-rate;
- no threshold search;
- no weight changes;
- no MA-length changes;
- no `breakoutBars` changes;
- no Strong / Formal persistence changes;
- no production C-2 change;
- no Exposure A/B/C selection while the upstream Core question remains unresolved;
- do not reinterpret this post-hoc comparison as validation.

## Stop rule

This phase ends after the first divergence layer is identified or the evidence is explicitly classified as distributed/ambiguous.

Do **not** automatically proceed into component tuning. If RAW is identified as the first divergence layer, the next allowed step is a frozen cross-market component attribution only.

PR #73 remains Draft / Open. Issue #68 remains Open until Eddy explicitly approves otherwise.
