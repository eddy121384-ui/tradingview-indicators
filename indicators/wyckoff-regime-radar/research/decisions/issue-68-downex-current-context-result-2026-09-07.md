# Issue #68 — DownEx Current-Context Discovery Result (2026-09-07)

Status: discovery result only. Production C-2 remains frozen.

Window: FR10Y / DE10Y 1D, 2022-01-03 through 2023-12-29, expected Bull yield regime.

## FR10Y

| Metric | PROD | PROD+CTX | SI | SI+CTX |
| --- | ---: | ---: | ---: | ---: |
| S1 gate avg | 0.76 | 0.51 | 0.81 | 0.51 |
| S1 EFF avg | 57.97 | 38.72 | 64.90 | 40.65 |
| S2 EFF > S1 | 21.48% | 59.96% | 6.25% | 59.38% |
| S1 TOP | 74.22% | 35.55% | 89.45% | 36.13% |
| Bull TOP | 21.48% | 59.77% | 6.25% | 59.18% |
| TOP changed vs baseline | 0% | 38.67% | 0% | 53.32% |

Context diagnostics:

- current bear gate avg: 0.67;
- production background gate / average trace advantage: 1.00 / 0.33;
- share with production background gate above current context: 85.94%;
- production DownEx gate avg -> context-bound: 0.85 -> 0.60;
- support-invariant DownEx gate avg -> context-bound: 0.91 -> 0.60;
- production DownEx capped share: 73.05%;
- support-invariant DownEx capped share: 74.22%.

## DE10Y

| Metric | PROD | PROD+CTX | SI | SI+CTX |
| --- | ---: | ---: | ---: | ---: |
| S1 gate avg | 0.63 | 0.55 | 0.76 | 0.60 |
| S1 EFF avg | 48.31 | 42.18 | 62.21 | 48.87 |
| S2 EFF > S1 | 36.13% | 53.52% | 4.30% | 46.68% |
| S1 TOP | 57.81% | 40.43% | 91.80% | 49.41% |
| Bull TOP | 36.13% | 53.52% | 4.30% | 46.68% |
| TOP changed vs baseline | 0% | 17.38% | 0% | 42.38% |

Context diagnostics:

- current bear gate avg: 0.82;
- production background gate / average trace advantage: 1.00 / 0.18;
- share with production background gate above current context: 66.21%;
- production DownEx gate avg -> context-bound: 0.75 -> 0.68;
- support-invariant DownEx gate avg -> context-bound: 0.91 -> 0.74;
- production DownEx capped share: 38.67%;
- support-invariant DownEx capped share: 62.11%.

## Finding

The preregistered current-context cap materially improves the adverse FR10Y discovery case and also improves DE10Y rather than damaging it. FR shows the larger effect because historical bearish maturity trace exceeds current bearish context much more often and by a larger average amount.

The support-invariant slope shadow had previously collapsed both markets into S1. Applying the same current-context cap removes most of that collapse: SI+CTX Bull TOP rises to 59.18% in FR and 46.68% in DE.

This is strong causal evidence that historical bearish memory is being allowed to keep the direct DownEx eligibility route active after current bearish/down-leg context has faded. The result supports the repair family, but does not authorize production modification.

## Required next step

Run the frozen cross-market control audit on JP10Y, US10Y and GB10Y before any production proposal. If those controls do not fail, run a separate true-S1 / fresh-exhaustion preservation check. No tuning or PnL is authorized.