# Issue #57 — Consensus formation and Formal-lag diagnostic

**Burned-data / price-only hypothesis development only. Not independent OOS.**

Action-compatible pairs are fixed as 2+3 bullish and 5+6 bearish. The user's 90% threshold remains the primary reference.

## v05 — strength monotonicity

| Strength | H | Median aligned return | Median hit rate | Origins | Positive pairs |
|---|---:|---:|---:|---:|---:|
| <70 | 5 | 0.40% | 50.00% | 2 | 1/7 |
| <70 | 10 | 0.07% | 50.00% | 2 | 1/7 |
| <70 | 20 | -0.08% | 50.00% | 2 | 1/7 |
| <70 | 60 | 5.85% | 100.00% | 1 | 1/7 |
| 70-<80 | 5 | -0.10% | 53.57% | 17 | 3/7 |
| 70-<80 | 10 | 0.20% | 67.86% | 17 | 3/7 |
| 70-<80 | 20 | -0.02% | 42.86% | 14 | 2/7 |
| 70-<80 | 60 | 1.84% | 100.00% | 13 | 4/7 |
| 80-<90 | 5 | 0.08% | 50.00% | 21 | 4/7 |
| 80-<90 | 10 | 0.19% | 87.50% | 21 | 5/7 |
| 80-<90 | 20 | -0.17% | 50.00% | 19 | 3/7 |
| 80-<90 | 60 | 2.11% | 87.50% | 17 | 4/7 |
| 90-<95 | 5 | -0.02% | 54.76% | 24 | 2/7 |
| 90-<95 | 10 | 0.06% | 66.67% | 24 | 4/7 |
| 90-<95 | 20 | 0.39% | 80.36% | 22 | 6/7 |
| 90-<95 | 60 | 2.36% | 100.00% | 22 | 6/7 |
| >=95 | 5 | -0.13% | 46.67% | 1133 | 1/7 |
| >=95 | 10 | -0.18% | 46.06% | 1133 | 2/7 |
| >=95 | 20 | -0.44% | 40.91% | 1123 | 1/7 |
| >=95 | 60 | -1.07% | 45.98% | 1091 | 1/7 |

Continuous strength Spearman (pair median):

| H | Median rho | Positive pair rhos |
|---:|---:|---:|
| 5 | -0.122 | 1/7 |
| 10 | -0.186 | 1/7 |
| 20 | -0.257 | 1/7 |
| 60 | -0.329 | 0/7 |

## v05 — Top2 >=90% by Formal relationship

| Formal relationship | H | Median aligned return | Median hit rate | Origins |
|---|---:|---:|---:|---:|
| formal_aligned | 5 | -0.13% | 47.59% | 1137 |
| formal_aligned | 10 | -0.19% | 46.67% | 1137 |
| formal_aligned | 20 | -0.43% | 41.72% | 1125 |
| formal_aligned | 60 | -1.05% | 46.55% | 1093 |
| formal_transition_or_neutral | 5 | -0.61% | 25.00% | 11 |
| formal_transition_or_neutral | 10 | -0.52% | 33.33% | 11 |
| formal_transition_or_neutral | 20 | -0.55% | 0.00% | 11 |
| formal_transition_or_neutral | 60 | -0.03% | 50.00% | 11 |
| formal_opposite | 5 | -0.26% | 33.33% | 9 |
| formal_opposite | 10 | -0.41% | 33.33% | 9 |
| formal_opposite | 20 | -0.83% | 0.00% | 9 |
| formal_opposite | 60 | -1.01% | 16.67% | 9 |

Formal adoption after non-aligned Top2 >=90%:

| Origin relationship | Origins | Adopt <=5 | Adopt <=10 | Adopt <=20 | Median adoption lag |
|---|---:|---:|---:|---:|---:|
| formal_transition_or_neutral | 11 | 66.67% | 75.00% | 100.00% | 1.250 |
| formal_opposite | 9 | 87.50% | 100.00% | 100.00% | 1.250 |

## v05 — 90% consensus persistence event sensitivity

| Required streak | H | Median aligned return | Median hit rate | Origins |
|---:|---:|---:|---:|---:|
| 1 | 5 | -0.16% | 37.50% | 237 |
| 1 | 10 | -0.04% | 48.28% | 237 |
| 1 | 20 | -0.12% | 45.71% | 235 |
| 1 | 60 | 0.09% | 56.67% | 225 |
| 2 | 5 | -0.10% | 42.31% | 152 |
| 2 | 10 | -0.10% | 50.00% | 152 |
| 2 | 20 | -0.21% | 42.86% | 150 |
| 2 | 60 | -0.39% | 47.83% | 144 |
| 3 | 5 | -0.08% | 45.45% | 121 |
| 3 | 10 | -0.19% | 40.00% | 121 |
| 3 | 20 | -0.30% | 47.37% | 118 |
| 3 | 60 | -0.52% | 50.00% | 114 |

## v06 — strength monotonicity

| Strength | H | Median aligned return | Median hit rate | Origins | Positive pairs |
|---|---:|---:|---:|---:|---:|
| <70 | 5 | 0.40% | 50.00% | 2 | 1/7 |
| <70 | 10 | 0.07% | 50.00% | 2 | 1/7 |
| <70 | 20 | -0.08% | 50.00% | 2 | 1/7 |
| <70 | 60 | 5.85% | 100.00% | 1 | 1/7 |
| 70-<80 | 5 | -0.10% | 53.57% | 18 | 3/7 |
| 70-<80 | 10 | 0.20% | 67.86% | 18 | 3/7 |
| 70-<80 | 20 | -0.02% | 42.86% | 15 | 2/7 |
| 70-<80 | 60 | 1.63% | 87.50% | 14 | 4/7 |
| 80-<90 | 5 | 0.12% | 60.00% | 26 | 4/7 |
| 80-<90 | 10 | 0.39% | 88.89% | 26 | 6/7 |
| 80-<90 | 20 | -0.02% | 63.33% | 24 | 3/7 |
| 80-<90 | 60 | 1.02% | 63.33% | 22 | 5/7 |
| 90-<95 | 5 | 0.18% | 67.50% | 28 | 4/7 |
| 90-<95 | 10 | 0.14% | 64.58% | 28 | 4/7 |
| 90-<95 | 20 | 0.48% | 75.00% | 26 | 5/7 |
| 90-<95 | 60 | 1.69% | 90.00% | 26 | 5/7 |
| >=95 | 5 | -0.14% | 45.79% | 1230 | 1/7 |
| >=95 | 10 | -0.18% | 46.94% | 1230 | 1/7 |
| >=95 | 20 | -0.40% | 41.76% | 1220 | 1/7 |
| >=95 | 60 | -0.98% | 46.99% | 1185 | 1/7 |

Continuous strength Spearman (pair median):

| H | Median rho | Positive pair rhos |
|---:|---:|---:|
| 5 | -0.157 | 2/7 |
| 10 | -0.134 | 1/7 |
| 20 | -0.186 | 1/7 |
| 60 | -0.267 | 0/7 |

## v06 — Top2 >=90% by Formal relationship

| Formal relationship | H | Median aligned return | Median hit rate | Origins |
|---|---:|---:|---:|---:|
| formal_aligned | 5 | -0.14% | 46.93% | 1237 |
| formal_aligned | 10 | -0.19% | 47.95% | 1237 |
| formal_aligned | 20 | -0.39% | 42.63% | 1225 |
| formal_aligned | 60 | -0.81% | 47.28% | 1190 |
| formal_transition_or_neutral | 5 | -0.23% | 50.00% | 12 |
| formal_transition_or_neutral | 10 | -0.38% | 50.00% | 12 |
| formal_transition_or_neutral | 20 | -0.54% | 25.00% | 12 |
| formal_transition_or_neutral | 60 | -0.04% | 50.00% | 12 |
| formal_opposite | 5 | -0.16% | 50.00% | 9 |
| formal_opposite | 10 | -0.49% | 25.00% | 9 |
| formal_opposite | 20 | -0.91% | 0.00% | 9 |
| formal_opposite | 60 | -1.19% | 0.00% | 9 |

Formal adoption after non-aligned Top2 >=90%:

| Origin relationship | Origins | Adopt <=5 | Adopt <=10 | Adopt <=20 | Median adoption lag |
|---|---:|---:|---:|---:|---:|
| formal_transition_or_neutral | 12 | 100.00% | 100.00% | 100.00% | 1.250 |
| formal_opposite | 9 | 75.00% | 91.67% | 100.00% | 1.000 |

## v06 — 90% consensus persistence event sensitivity

| Required streak | H | Median aligned return | Median hit rate | Origins |
|---:|---:|---:|---:|---:|
| 1 | 5 | -0.15% | 39.29% | 263 |
| 1 | 10 | -0.02% | 46.43% | 263 |
| 1 | 20 | -0.14% | 46.43% | 261 |
| 1 | 60 | -0.10% | 52.78% | 254 |
| 2 | 5 | -0.07% | 43.75% | 153 |
| 2 | 10 | -0.10% | 50.00% | 153 |
| 2 | 20 | -0.16% | 47.37% | 151 |
| 2 | 60 | -0.69% | 42.86% | 148 |
| 3 | 5 | -0.06% | 45.00% | 123 |
| 3 | 10 | -0.13% | 47.06% | 123 |
| 3 | 20 | -0.10% | 47.06% | 120 |
| 3 | 60 | -0.71% | 44.44% | 118 |

## Interpretation boundary

Do not choose a threshold or persistence rule because one row looks best. The purpose is to determine whether a stable monotonic or Formal-lag structure exists at all. Any promising rule must be frozen before a new untouched sample is acquired.
