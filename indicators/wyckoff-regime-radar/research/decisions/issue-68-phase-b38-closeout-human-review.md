# Issue #68 Phase B3.8 — Mechanical Closeout / Human Audit Lock

Status: **MECHANICAL PASS / HUMAN RATES REVIEW NEXT / NO PERFORMANCE**

## What B3.8 established

B3.8 decomposes the frozen Issue #66 C-2 raw-stage ranking without changing any classifier formula, weight, threshold, gate, persistence rule, Core Bias rule, Exposure rule, or strategy-performance assumption.

Formal four-FX engineering result:

- raw-loss observations, bull+bear: **7,620**;
- raw winner = precursor range: **2,232 (29.3%)**;
- raw winner = opposite range: **2,232 (29.3%)**;
- raw winner = opposite trend: **3,156 (41.4%)**;
- unexplained raw winner: **0**;
- Stage2-vs-Stage5 component reconstruction max error: **2.842e-14**;
- minimum reciprocal boolean attribution agreement: **99.818%**.

When Markup raw0 is below Markdown raw0, the largest negative weighted directional component is most often:

1. **Structure — 1,223 observations**;
2. **Break — 1,103**;
3. Heat — 325;
4. Continuation — 17;
5. Trace — 9;
6. Extension — 7.

This generic burned-FX baseline does not prove that Structure or Break causes the FR10Y/JGB10Y economic reversal lag. It establishes what to inspect on those specific rates episodes.

## Engineering-gate correction

The first B3.8 run incorrectly added an unregistered requirement that every per-component reciprocal numeric MAE be <= 1e-6.

That assertion was too strict for rolling/event/history components and was not part of the preregistered research question. The residual diagnostic showed:

- Structure: exact 0;
- Heat / Extension: floating-point zero;
- Break: max MAE **0.0594 points**;
- Continuation: **0.0261**;
- Trace: **0.0218**.

The residuals remain visible in the report but do not serve as a model acceptance gate. Hard B3.8 acceptance is limited to exhaustive attribution, exact raw0 reconstruction, and >=99% reciprocal boolean attribution agreement.

No model parameter was changed to make the gate pass.

## Locked human review

Use:

`indicators/wyckoff-regime-radar/research/generated/wyckoff-issue68-phase-b38-raw-feature-attribution-audit.pine`

Priority charts:

1. **FR10Y 1D, 2021–2024** — primary adverse reversal case;
2. **JGB10Y 1D, 2021–2024** — control case.

Set **審計方向 / Audit Direction = Bull**.

Read the nine bands from top to bottom:

1. `RAW ADV` — Bull Stage2/3 raw family beats every other stage;
2. `> RANGE` — Bull target beats Stage1/4 range family;
3. `> OPP TREND` — Bull target beats Stage5/6 bear trend family;
4. `BREAK` — breakout evidence beats breakdown evidence;
5. `HEAT` — bull heat beats downside panic heat;
6. `STRUCTURE` — bull structure beats bear structure;
7. `EXTENSION` — bullish trend extension beats bearish extension;
8. `CONT` — bullish continuation beats bearish continuation;
9. `TRACE` — accumulation precursor trace beats distribution precursor trace.

Green means the audited Bull side wins that comparison; red means it loses; gray means unavailable during warmup.

The right-top table also reports the current raw winning Stage.

## Human-review decision tree

Focus on the visually obvious yield-uptrend reversal interval rather than every historical bar.

- `RAW ADV` red and `> RANGE` red for most of the developing uptrend -> range-family raw formulation is suppressing trend recognition.
- `RAW ADV` red, `> RANGE` green, `> OPP TREND` red -> old bear-trend raw remains dominant too long.
- `RAW ADV` red with Structure persistently red -> Stage2/5 directional structure primitive is the principal local drag.
- `RAW ADV` red with Break persistently red -> break evidence is the principal local drag.
- Structure/Break green while RAW ADV remains red -> inspect combined smaller components and Stage3/6 competition before changing any formula.
- If FR10Y and JGB10Y show materially different blockage patterns, treat FR10Y as a rates-specific adverse case rather than generalizing from the generic FX baseline.

## Hard boundary

Until the FR10Y/JGB10Y B3.8 human review is recorded:

- do not change C-2 formulas, weights, thresholds, gates, or persistence;
- do not resume Exposure A-vs-C selection;
- do not inspect Strategy Tester / PnL / Sharpe / drawdown;
- do not add Volume / MTF / Divergence / HMM;
- do not merge PR #73 or close Issue #68 without explicit Eddy approval.
