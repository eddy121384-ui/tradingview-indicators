# Issue #66 Phase A — Reciprocal Symmetry Decomposition

Status: **reused frozen data / no PnL**

This report reruns the frozen v0.6 Phase-B price-only classifier on each canonical FX fixture and its reciprocal OHLC quotation. It measures semantic/inversion symmetry only.

## Baseline reproduction

| Layer | Reciprocal metric |
|---|---:|
| Raw range break up → inverse down | Jaccard 100.00% |
| Raw range break down → inverse up | Jaccard 100.00% |
| MA cross up → inverse down | Jaccard 92.43% |
| MA cross down → inverse up | Jaccard 93.64% |
| Breakout mode up → inverse breakdown | Jaccard 95.64% |
| Breakdown mode down → inverse breakout | Jaccard 96.35% |
| Candidate-display stage | mirror 74.32% |
| Formal stage | mirror 76.11% |

## Six-stage vector decomposition

Lower MAE is more symmetric. Raw/effective/probability values are on 0–100-like scales; gates are on 0–1.

| Layer | Mean reciprocal MAE |
|---|---:|
| Raw stage scores | 3.880591 |
| Stage gates | 0.068596 |
| Effective stage weights | 5.294190 |
| Stage probabilities | 9.239240 |

## Persistence / transitions

Candidate transition-pair mirror agreement: **67.84%**  
Formal transition-pair mirror agreement: **73.36%**

## Per pair

| Pair | Range U→D | MA U→D | Candidate | Formal | Formal transition | Prob-vector MAE |
|---|---:|---:|---:|---:|---:|---:|
| EURUSD | 100.00% | 91.86% | 76.41% | 80.49% | 78.05% | 8.457434 |
| USDJPY | 100.00% | 91.36% | 69.18% | 69.12% | 66.38% | 10.909724 |
| GBPUSD | 100.00% | 92.31% | 74.65% | 75.14% | 72.28% | 9.192841 |
| AUDUSD | 100.00% | 94.20% | 77.02% | 79.70% | 76.72% | 8.396961 |

## Interpretation boundary

This phase does not choose or repair any formula. The decomposition is evidence for Phase B ordering only. In particular, arithmetic moving-average / ATR representation can break reciprocal symmetry upstream of explicitly unequal bull/bear constants, while the raw range-break event itself remains exactly mirrored on the frozen fixtures.
