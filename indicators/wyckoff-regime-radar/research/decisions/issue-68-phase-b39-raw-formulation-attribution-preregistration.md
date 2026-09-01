# Issue #68 Phase B3.9 — Raw Formulation Attribution Preregistration

Status: **PREREGISTERED / DIAGNOSTIC ONLY / NO PERFORMANCE**

## Why B3.9 exists

B3.8 localized the long-rates reversal-latency symptom to the raw-stage layer. Human review of FR10Y and JGB10Y showed that the eventual Bull state is recognized, but the Bull trend family often does not establish raw leadership early enough during the developing yield uptrend. B3.8 also showed that no single downstream Strong/Formal/Core gate explains the full lag.

The unresolved question is now narrower:

> When Bull Stage2/3 fails to lead at the raw layer, which exact raw stage is suppressing it, and is the Bull family internally being represented as fresh Markup (Stage2) or continuation/Reaccumulation (Stage3)?

B3.9 answers only this attribution question. It does not change any model rule.

## Frozen model boundary

Freeze Issue #66 C-2 exactly as used by B3.8:

- no classifier formula changes;
- no raw weights or thresholds changed;
- no gate or persistence changes;
- no Core Bias or Exposure changes;
- Volume / MTF / Divergence remain forced off;
- no Strategy Tester, PnL, return, Sharpe, drawdown, hit rate, stop, target, sizing, or transaction-cost analysis.

## Symmetric target definition

Bull audit:

- target family = Stage2 Markup / Stage3 Reaccumulation;
- fresh target = Stage2;
- continuation target = Stage3;
- exact competitors = Stage1 Accumulation, Stage4 Distribution, Stage5 Markdown, Stage6 Redistribution.

Bear audit is the reciprocal mirror:

- target family = Stage5 Markdown / Stage6 Redistribution;
- fresh target = Stage5;
- continuation target = Stage6;
- exact competitors = Stage4 Distribution, Stage1 Accumulation, Stage2 Markup, Stage3 Reaccumulation.

No economic turning-point date is used as a machine label.

## Mechanical attribution

For every scored bar after the existing rank warmup:

1. compute the target-family raw score as the maximum of its two target stages;
2. record which target substage wins internally: fresh vs continuation;
3. compare the target-family raw score separately against every non-target stage;
4. if target-family raw leadership fails, record the exact raw winner stage using the classifier's existing strict Stage1->Stage6 tie priority;
5. record pairwise suppression overlap because more than one competitor may exceed the target on the same bar;
6. report target-vs-competitor raw margins as descriptive diagnostics only, with no new threshold.

## Directional component carry-forward

B3.8 identified Structure and Break as the two most frequent largest negative weighted components in the generic Stage2-vs-Stage5 comparison. B3.9 carries only these two directional comparisons into the human TradingView artifact:

- BREAK: breakout evidence vs breakdown evidence;
- STRUCTURE: bull structure vs bear structure.

They are diagnostics, not gates, and are not changed.

## Engineering gates

B3.9 passes mechanically only if:

- exact raw-loss winner attribution is exhaustive (`unexplained = 0`);
- pairwise competitor suppression and exact-winner accounting are internally consistent;
- reciprocal Bull-vs-inverse-Bear boolean attribution agreement is >= 99%;
- exact raw-winner stage under reciprocal quotation matches the predefined stage mirror map at >= 99% on comparable scored bars;
- no performance metric is produced.

Stage mirror map:

- S1 <-> S4;
- S2 <-> S5;
- S3 <-> S6.

No per-component floating-point mirror threshold is introduced.

## Human TradingView artifact

Generate a no-strategy audit indicator with Audit Direction defaulting to Bull.

Required historical bands:

1. `RAW ADV` — target family beats every non-target stage;
2. `FRESH TARGET` — fresh trend stage beats continuation stage inside the target family;
3. `> S1` — target family beats Stage1 raw;
4. `> S4` — target family beats Stage4 raw;
5. `> S5` — target family beats Stage5 raw;
6. `> S6` — target family beats Stage6 raw;
7. `BREAK` — audited directional break evidence wins;
8. `STRUCTURE` — audited directional structure evidence wins.

The right-top table must also show current target substage and current exact raw winner stage.

For Bull review, green means the Bull target wins that comparison, red means the named competitor wins/ties, and gray means warmup/unavailable. `FRESH TARGET` green means Stage2 >= Stage3 for Bull; for Bear it means Stage5 >= Stage6.

## Locked rates review

Primary adverse case:

- FR10Y 1D, focus 2021–2024, Audit Direction = Bull.

Control:

- JGB10Y 1D, focus 2021–2024, Audit Direction = Bull.

Interpretation hierarchy:

- persistent `> S5` red during an emerging yield uptrend -> old Markdown raw remains too competitive;
- persistent `> S6` red -> Redistribution raw remains too competitive;
- persistent `> S1` / `> S4` red -> range-family raw suppresses new trend leadership;
- competitors are mostly beaten but `FRESH TARGET` is red -> Bull family is being represented mainly as Stage3 continuation instead of fresh Stage2;
- `BREAK` / `STRUCTURE` red alongside Stage5 suppression -> directional trend formulation remains the leading local suspect;
- `BREAK` / `STRUCTURE` green while a range stage suppresses target -> do not blame directional components; inspect range-family raw formulation next.

## Stop rule

B3.9 does not authorize any formula repair. After mechanical PASS and FR10Y/JGB10Y human review, record the smallest justified next forensic target. No threshold shopping and no performance testing.

PR #73 remains Draft. Issue #68 remains open. Do not merge or close without explicit Eddy approval.
