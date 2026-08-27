# Issue #66 Phase B-3 — Trend-Entry Gate Symmetry Plan

Status: preregistered before reading B-3 results.

## Parent

Accepted parent is Phase B-2. B-1 reciprocal-safe representation and B-2 direction-neutral break evidence are frozen for this experiment.

## Scope

Change one primitive family only: the fresh trend-entry gate that feeds Stage 2 Markup and Stage 5 Markdown.

Current non-isomorphism:

- Stage 2 fresh entry: `breakout_gate * structure_strong_gate * non_end_up_gate`
- Stage 5 fresh entry: `explicit_breakdown_gate * gate(panic_heat_dn, 40, 80) * structure_weak_gate`

B-3 canonical direction-neutral form:

```text
trend_entry_gate(direction) =
    break_gate(direction)
    * structure_gate(direction)
    * non_end_gate(direction)
```

where both directions use the existing Stage-2 non-end-risk mapping:

```text
non_end_gate(direction) = gate(100 - end_risk(direction), 35, 80)
```

Thus:

- Markup uses `breakout_gate`, `structure_strong_gate`, `non_end_up_gate`.
- Markdown uses `explicit_breakdown_gate`, `structure_weak_gate`, `non_end_dn_gate`.

No result-dependent tuning of 35/80 is allowed in B-3. These are inherited from the existing Stage-2 semantic gate rather than selected from B-3 data.

## Frozen boundaries

B-3 must not change:

- raw stage formulas;
- break-evidence formulas from B-2;
- extension gates;
- continuation gates;
- Stage 1/3/4/6 gates;
- candidate conflict, evidence, persistence, or lifecycle;
- any PnL / Sharpe / CAGR / drawdown / Strategy Tester logic.

## Primary engineering gate

On the same already-burned four-FX reciprocal fixtures:

1. `breakout_markup_gate ↔ inverse breakdown_markdown_gate` MAE must fall versus B-2.
2. reverse-direction MAE must also fall.
3. B-2 raw-range and B-1 MA-cross 100% reciprocal invariants must remain intact.
4. B-2 break score/gate reciprocal errors must not materially regress (tolerance `1e-12`).

Full Stage-gate/effective/probability/Candidate/Formal metrics are downstream observations only and may not be used to retune B-3.

No PnL is authorized.