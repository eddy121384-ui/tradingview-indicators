# Issue #66 Phase B-2 — Direction-Neutral Break Evidence Plan

Status: **preregistered before Phase B-2 measurement**

Parent: Phase B-1 reciprocal-safe representation core.

## Question

After Phase B-1 made the price representation reciprocal-safe, does replacing the explicitly non-isomorphic breakout / breakdown evidence path with one shared direction-neutral primitive materially reduce reciprocal error at the break-evidence layer?

This is an engineering symmetry experiment only. It must not use PnL, Sharpe, CAGR, drawdown, win rate, trade count, Strategy Tester results, Volume, MTF, Divergence, or HMM outputs.

## Frozen boundaries

Phase B-2 may change **only** the break-evidence primitive and its directly-derived gate.

It must not change:

- Phase B-1 log/geometric representation;
- raw range-break event definitions;
- v0.6 soft range-boundary strength calculations;
- range-continuation formulas;
- extension / continuation formulas;
- Stage 1–6 raw-score formulas or weights;
- Stage 1–6 gate formulas except through their existing use of `breakout_gate` / `explicit_breakdown_gate`;
- candidate conflict / coexist / evidence logic;
- persistence / confirmation logic;
- any frozen v0.5.2.1 source.

## Shared primitive

The current source contains asymmetric paths:

- range evidence scale: upside `0.70` vs downside `0.85`;
- recent range gate scale: upside `0.85` vs downside `0.90`;
- MA evidence: upside has generic recent-cross / above-MA evidence while downside additionally requires `panic_heat_dn` and `structure_weak` qualifiers and uses a different score/gate path.

Phase B-2 replaces those two hand-written paths with a single shared function applied with mirrored inputs.

For either direction:

```text
range_component = clamp(recent_range_break_strength, 0, 100)
ma_component = 70 if recent_ma_cross
               35 if price is on the directional side of the reciprocal-safe MA
                0 otherwise
break_score = 100 if breakout_mode else max(range_component, ma_component)
break_gate = clamp(break_score / 100, 0, 1)
```

Directional side means:

- up: `log_price > ma_log`
- down: `log_price < ma_log`

The constants `70` and `35` are inherited from the existing generic MA-evidence tiers; no new threshold sweep is allowed. The range component uses the existing 0–100 boundary strength directly rather than applying a direction-specific attenuation factor.

`panic_heat_dn` and `structure_weak` are deliberately removed from the break primitive. They remain elsewhere in the classifier where trend/structure semantics belong; they may not be reintroduced into only one direction of `break_evidence`.

## Primary engineering gate

Compare the Phase B-1 parent against Phase B-2 on the same frozen four-FX reciprocal fixtures.

Phase B-2 passes only if all of the following hold:

1. `breakout_score ↔ inverse explicit_breakdown_score` mean numeric MAE is lower than Phase B-1.
2. `explicit_breakdown_score ↔ inverse breakout_score` mean numeric MAE is lower than Phase B-1.
3. `breakout_gate ↔ inverse explicit_breakdown_gate` mean numeric MAE is lower than Phase B-1.
4. `explicit_breakdown_gate ↔ inverse breakout_gate` mean numeric MAE is lower than Phase B-1.
5. Phase B-1 representation invariants remain intact: reciprocal MA-cross Jaccard stays effectively 100% in both directions.
6. Raw range-break reciprocal Jaccard remains effectively 100% in both directions.

No Candidate/Formal/stage-vector metric is a tuning target for this phase. Those are downstream observations only.

## Interpretation rule

If the primary break-evidence gate passes but downstream stage symmetry barely improves, the next experiment should target the next source-level non-isomorphic family rather than tuning this primitive to improve Candidate/Formal metrics.

If the primary gate fails, diagnose the remaining asymmetry inside the break primitive inputs first. Do not compensate by changing Stage formulas or thresholds.
