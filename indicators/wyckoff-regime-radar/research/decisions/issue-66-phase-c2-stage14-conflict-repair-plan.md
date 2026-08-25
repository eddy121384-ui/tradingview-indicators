# Issue #66 Phase C-2 — Stage 1/4 Candidate-Conflict Symmetry Repair

Status: **preregistered repair / reused frozen data / no PnL**

## Parent evidence

Phase C v3 proved the inherited persistence state machine is structurally reciprocal-symmetric and replay-exact.

Phase C-1 then localized candidate-conflict mismatch by mirrored top-stage family. Among bars whose top stage was already correctly mirrored:

- Stage 1 Accumulation ↔ Stage 4 Distribution: 933 mismatch bars (100.00%);
- Stage 2 Markup ↔ Stage 5 Markdown: 0;
- Stage 3 Re-accumulation ↔ Stage 6 Re-distribution: 0.

The preregistered >=90% dominance gate therefore PASSed. Stage 1/4 is the only eligible repair family.

## Existing non-isomorphism

Current Stage 1 conflict clause:

```python
(top_id == 1)
& (resistance_holding >= cfg.absorb_threshold)
& (rebound_failure_gate > 0.50)
& ~markup_cont_override
```

Current Stage 4 conflict clause:

```python
(top_id == 4)
& (support_holding >= cfg.absorb_threshold)
& (downside_exhaustion >= cfg.absorb_threshold)
& ~markup_cont_override
```

The Stage 1 clause is not the reciprocal mirror of Stage 4: it substitutes `rebound_failure_gate` for the mirrored exhaustion primitive and uses the same markup override rather than the mirrored markdown override.

## Preregistered C-2 repair

Treat the existing Stage 4 clause as the canonical generic exhaustion/holding conflict pattern. Do not change Stage 4.

Replace **only** Stage 1 with its reciprocal mirror:

```python
(top_id == 1)
& (resistance_holding >= cfg.absorb_threshold)
& (upside_exhaustion >= cfg.absorb_threshold)
& ~markdown_cont_override
```

No threshold changes are permitted.

## Frozen in C-2

- all raw scores and gates from B-1 through B-7;
- Stage 2/5 and Stage 3/6 candidate-conflict clauses;
- Stage 4 candidate-conflict clause;
- `candidate_display_id` construction;
- strong/weak candidate thresholds;
- chaos/coexist/fast-switch logic;
- Issue #57 Phase-B stale-pressure persistence;
- confirmation bars and stale-pressure horizon;
- all strategy/PnL concepts.

## Primary gate

On the same frozen four-FX reciprocal audit:

1. candidate-conflict mirror agreement must improve versus B-7;
2. attributable Stage 1/4 candidate-conflict mismatch bars (with top stage already mirrored) must decrease versus B-7;
3. Stage 2/5 and Stage 3/6 attributable candidate-conflict mismatch bars must remain exactly zero;
4. all registered B-7 numeric classifier metrics (raw/gate/effective/probability and prior repaired primitive metrics) must remain unchanged to numerical tolerance, because C-2 changes only downstream conflict eligibility.

No minimum Formal improvement is preregistered. Formal/transition/persistence results are downstream observations only.

## Secondary observations — not tuning targets

Report:

- candidate-conflict mirror agreement;
- strong-stage mirror agreement;
- candidate-display mirror agreement;
- Formal mirror agreement;
- Formal transition mirror agreement;
- stale-pressure reason/bars mirror agreement;
- mismatch counts and state-carry share.

If the primary gate passes, the symmetric Stage 1/4 conflict repair becomes the accepted C-2 research parent. If it fails, do not alter thresholds or persistence to rescue it.
