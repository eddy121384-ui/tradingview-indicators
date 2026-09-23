# Issue #105 preregistration — BCI-10 Intended-semantics v0.1

This is a repaired **intended-semantics** version of BCI-10. It is not the literal original.

## Frozen repairs

- Manufacturing PMI -> TradingView U.S. `BCOI`
- Services PMI -> TradingView U.S. `NMPMI`
- headline CPI YoY -> `IRYY`
- core CPI YoY -> `CIR`
- Core PCE level -> `CPCEPI`, then one 12-month YoY transform
- JOLTS openings -> `JTSJOR` rate
- JOLTS quits -> `JTSQUR` rate
- `R_hawk = -R_literal` so P and R share the same sign meaning

Everything else keeps the original default weights and 120-month Z-score window.

## Intended policy surface

`P > 0` = more hawkish/restrictive.

`R_hawk > 0` = more hawkish/tightening momentum.

`PS = 0.4P + 0.4R_hawk + 0.2(P×R_hawk)`.

Original ±0.3 / ±1.0 thresholds are retained.

## Major sample limitation

The wage series begins in March 2006.

Because the indicator first converts wages to 12-month YoY and then applies a 120-month Z-score, the full surface should not become populated before roughly February 2017.

With a two-month signal lag and EFFR known through December 2025, the primary validation window is expected to be approximately April 2017–June 2025.

That is a modern-sample test only.

## Validation

No model fitting.

Compare:
- P
- R_hawk
- PS_intended

against future 6-month Fed Funds change using signals lagged two months.

Also test the original Policy Pivot idea through PS zero-crossing event studies at +3/+6/+12 months.

No Treasury returns are allowed in this issue.
