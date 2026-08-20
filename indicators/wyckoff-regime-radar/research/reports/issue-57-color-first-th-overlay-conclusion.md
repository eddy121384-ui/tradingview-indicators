# Issue #57 — Color-first + Transition Health risk overlay conclusion

Status: **REUSED-DATA STRATEGY-PROXY RESULT; NO PRODUCTION TRADING RULE**.

The preregistered comparison was executed without changing the Formal mapping, +3 checkpoint, block/re-risk rule, position size, or 2 bp cost sensitivity.

## Mechanical setup

- Formal stages 1/2/3 = bullish color direction.
- Formal stages 4/5/6 = bearish color direction.
- Formal 0 = flat.
- Signal is observed at close and applied to the next close-to-close return.
- `color_only`: follow Formal color continuously.
- `color_plus_th_gate`: enter from Formal color immediately; a matching Early Damaged event blocks the position; a later matching Healthy event can re-risk; color-family change resets the old block.

## Result — development 7 FX

305 color entries, 41 Early-Damaged blocks, 4 Healthy re-risks.

Median-pair gross metrics:

| Variant | Ann return | Sharpe | Max DD | Exposure |
|---|---:|---:|---:|---:|
| color_only | -1.80% | -0.262 | -21.04% | 52.90% |
| color_plus_th_gate | -1.51% | -0.223 | -18.66% | 47.69% |

Managed wins across 7 pairs:

- gross return: 5/7;
- gross Sharpe: 3/7;
- gross max drawdown: 4/7;
- 2 bp return: 5/7;
- 2 bp Sharpe: 3/7;
- 2 bp max drawdown: 4/7.

## Result — later reused 5 FX, 2022–2026

171 color entries, 29 Early-Damaged blocks, 6 Healthy re-risks.

These five pairs were independent for the previously frozen +3 Transition Health hypothesis, but they are **not independent for this newly proposed color-first trading overlay**.

Median-pair gross metrics:

| Variant | Ann return | Sharpe | Max DD | Exposure |
|---|---:|---:|---:|---:|
| color_only | -2.96% | -0.254 | -24.97% | 94.41% |
| color_plus_th_gate | -1.38% | -0.108 | -20.31% | 89.41% |

Managed wins across 5 pairs:

- gross return: 5/5;
- gross Sharpe: 5/5;
- gross max drawdown: 2/5;
- 2 bp return: 5/5;
- 2 bp Sharpe: 5/5;
- 2 bp max drawdown: 3/5.

## Combined descriptive result — 12 FX

476 color entries, 70 Early-Damaged blocks, 10 Healthy re-risks.

Median-pair metrics:

| Variant | Gross ann return | Gross Sharpe | Gross max DD | Net 2bp ann return | Net 2bp Sharpe | Net 2bp max DD | Exposure |
|---|---:|---:|---:|---:|---:|---:|---:|
| color_only | -2.11% | -0.258 | -21.09% | -2.30% | -0.288 | -22.08% | 53.36% |
| color_plus_th_gate | -1.45% | -0.179 | -19.44% | -1.68% | -0.213 | -19.97% | 51.10% |

Managed wins across 12 pairs:

- gross return: **10/12**;
- gross Sharpe: **8/12**;
- gross max drawdown: **6/12**;
- 2 bp return: **10/12**;
- 2 bp Sharpe: **8/12**;
- 2 bp max drawdown: **7/12**.

## Interpretation

Two conclusions should be separated.

### 1. Early Damaged contains useful risk-management information

Using Early Damaged as a block generally improves the naive color strategy's return and Sharpe, especially in the later 2022–2026 five-pair cohort. This is consistent with the earlier structural evidence that an old-context reclaim materially weakens a handoff.

Healthy is not useful as a delayed primary entry in this design. Its role is secondary: when a prior Early-Damaged block has removed exposure, a later same-direction Healthy event can permit re-risking. Only 10 such re-risks occurred across the combined sample, so this role is small.

### 2. The naive Formal-color long/short engine is not good enough

The primary color-only strategy proxy has a negative median return and negative median Sharpe in both cohorts. The TH gate improves a weak base but does not turn it into a profitable strategy.

Therefore this result does **not** support publishing `Formal green = long / Formal red = short` as a trading rule. Formal stage color remains useful descriptive regime information, but its six-state semantics are not equivalent to a mechanically profitable binary long/short mapping.

## Product implication

The most defensible current role split is:

- **Formal background color:** primary persistent market-state visualization;
- **Early Damaged:** candidate risk-warning / transition-quality downgrade;
- **Healthy +3:** confirmation / descriptive hold-quality marker, not a delayed entry trigger.

Do not add a production auto-trading rule yet.

## Next research question

If trading utility remains a goal, the next justified question is not to tune the TH gate. It is to ask whether the six Formal stages should have different trading semantics rather than forcing all 1/2/3 stages long and all 4/5/6 stages short.

A natural hypothesis is that transition stages (`Accumulation`, `Distribution`) and trend stages (`Markup`, `Markdown`, plus re-accumulation / redistribution) may require different position rules. That hypothesis must be preregistered before another outcome comparison and all currently inspected samples are reused evidence.
