# Issue #61 — v0.6 reciprocal / bull-bear symmetry audit

**No PnL. Reused frozen FX data. Diagnostic only.**

## Aggregate

| Layer | Mirror metric |
|---|---:|
| Raw range break up → inverse down | Jaccard 100.00% |
| Raw range break down → inverse up | Jaccard 100.00% |
| MA cross up → inverse down | Jaccard 92.43% |
| MA cross down → inverse up | Jaccard 93.64% |
| Breakout mode up → inverse breakdown mode | Jaccard 95.64% |
| Breakdown mode down → inverse breakout mode | Jaccard 96.35% |
| Candidate-display stage | bar mirror 74.32% |
| Formal stage | bar mirror 76.11% |
| Human-review lifecycle position | bar mirror 86.44% |

## Known source-level asymmetries (not repaired in this audit)

- upside breakout range-evidence scale 0.70 vs downside 0.85
- upside recent-range gate scale 0.85 vs downside 0.90
- downside MA breakdown evidence has panic_heat_dn/structure_weak qualifiers unlike upside MA path
- Stage-2 breakout gate and Stage-5 breakdown gate use non-isomorphic confirmation products

## Per pair

| Pair | Range U→D Jaccard | Range D→U Jaccard | MA U→D Jaccard | MA D→U Jaccard | Candidate mirror | Formal mirror | Lifecycle mirror |
|---|---:|---:|---:|---:|---:|---:|---:|
| EURUSD | 100.00% | 100.00% | 91.86% | 94.12% | 76.41% | 80.49% | 90.03% |
| USDJPY | 100.00% | 100.00% | 91.36% | 93.83% | 69.18% | 69.12% | 78.18% |
| GBPUSD | 100.00% | 100.00% | 92.31% | 89.55% | 74.65% | 75.14% | 82.01% |
| AUDUSD | 100.00% | 100.00% | 94.20% | 97.06% | 77.02% | 79.70% | 95.56% |

## Reading the result

If raw range-break Jaccard is near 100% but MA/score/state/lifecycle symmetry degrades later, the asymmetry is introduced by representation and classifier design rather than by changing the historical market path.
