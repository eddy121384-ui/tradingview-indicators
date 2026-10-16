# Volatility-managed equity — replication preregistration (2026-10-16)

**Status:** preregistered before calculating, inspecting, or writing any volatility-scaled P&L. Research only, `production_authorized=false`. Literature-first, replication-first; not pristine out-of-sample (weights fitted on revised history; full-sample `c` is ex-post by construction).

## Paper anchor (verified 2026-10-16 against published sources)

Moreira & Muir, *Volatility-Managed Portfolios*, JF 2017 (NBER WP 22208 Apr 2016;
published PDF https://amoreira2.github.io/alan-moreira.github.io/VolPortfolios_published.pdf;
slides https://amoreira2.github.io/alan-moreira.github.io/SlidesVol.pdf;
DOI https://doi.org/10.1111/jofi.12513):

- Managed excess factor: `f_sigma[t+1] = (c / RV2[t]) * f[t+1]`, where `f` is the
  buy-and-hold factor **excess** return and `RV2[t]` is the previous month's
  realized variance. One-month implementation lag; known at end of month t.
- Realized variance (paper eq. 2): biased sample variance of **daily** factor
  returns within month t, i.e. `(1/22)*sum((r_d - mean)^2)` (ddof=0, divisor 22
  regardless of trading-day count — frozen as published).
- Normalization: `c` chosen so the managed portfolio has the **same
  unconditional standard deviation** as the unmanaged factor (full-sample,
  ex-post by construction — always labeled as such, never described as ex-ante).
- Weights are **unconstrained** in the baseline (paper Table 5: market median
  weight near 1; p75/p90/p99 1.6/2.6/6.4 — substantial leverage in calm periods).
- Paper alternatives: realized-vol scaling (99th pct ~3), AR(1) expected
  variance, hard caps at **1.0 (no leverage)** and **1.5 (50% margin)**; Sharpe
  unchanged under caps, alphas lower. Evaluation: regression
  `f_sigma[t] = alpha + beta*f[t] + eps`, appraisal/Sharpe ratios.
- This study replicates the **market-factor leg only** on the common payoff
  panel below (not SMB/HML/MOM/carry/MVE; no VAR/utility/IRF sections).

## Frozen inputs (verified this round, no substitution)

- Daily: official French `F-F_Research_Data_Factors_daily_CSV.zip`
  (SHA256 `2f29e22546069914890a712680a6f81f3680ebc3543b52864484d209ca13a7db`;
  26,317 rows 19260701..20260831; committed as
  `generated/classic-equity-baselines/daily-market-total-returns.csv`).
- Daily→monthly chaining reconciled vs repo `issue-166` monthly totals:
  **800 overlap months, MAE 0.047pp/mo, max |diff| 0.181pp (1989-05)**,
  no era bias, no 2025+ CIZ break (all ±0.1bp). Consistent with file-decimal
  precision plus component aggregation/rounding. No forcing; suitable as a
  variance-signal input (monthly level diffs immaterial to daily variances).
- Cash: repo TB3MS/1200 proxy (same file/column as classic baselines; same
  publication-lag caveat, not live PIT). Costs: 2bp per 100% target-weight
  change, 10bp sensitivity, initial deployment free (same conventions).

## Leg 1 — paper-faithful replication (factor space, leverage allowed)

- `f[t]` = monthly market **excess** return compounded from official daily
  `(1+Mkt-RF_d)` within month t (self-consistent chain; repo monthly totals
  used only for the reconciliation above, never mixed into P&L).
- `RV2[t]` = biased variance (`/22`) of that month's daily **excess** returns
  in decimals. First payoff month needs February 1967 variance → first payoff
  **1967-03**, matching the common panel exactly.
- `c` = SD(f)/SD(f/RV2) over the FULL panel (ex-post label mandatory).
- Managed excess: `(c/RV2[t-1]) * f[t]`, weights unconstrained (report median,
  p75/p90/p99, max, fraction of months >1.0 and >1.5 — expect paper-like 1.6/2.6/6.4).
- Evaluation (descriptive, no success threshold): regression alpha/beta vs own
  unmanaged factor, Sharpe both, turnover, break-even trading cost, era splits
  (E1–E4 as preregistered), crisis windows (same six). Compare magnitudes with
  paper's market results qualitatively; do NOT claim exact replication (different
  sample end 2026 vs 2015, CIZ-era data, our compounding).

## Leg 2 — deployable fair comparison (total-return space, no leverage)

- Weight: `w[t] = min(1, Vbar[t-1]/RV2[t-1])`, where `Vbar[t-1]` = expanding
  mean of monthly RV over **all months strictly before t back to 1926**
  (no lookahead; adaptive, no fixed target, no sample-informed constants).
  Floor 0 (RV>0 always so no division-by-zero path; assert RV>0 else BLOCK).
- Applied to equity **total** return with `(1-w)` in the same cash proxy:
  directly comparable with SMA10/MOM12 legs, same 2bp/10bp costs, same
  1967-03..2026-08 panel, same era/crisis splits and metric set (CAGR, vol,
  Sharpe-like, MaxDD, worst-1m, switches→months-at-zero, turnover, mean
  exposure, upside/downside participation, missed-upside/avoided-loss sums).
- Plus a descriptive hindsight exposure-matched fixed control at Leg 2's
  realized mean exposure (same method/explicit hindsight label as baselines).
- No AR(1)/GARCH forecasting, no vol-target grids, no cap variants beyond the
  frozen [0,1].

## Reporting rules and stop conditions

- Paper-faithful and fair legs reported in **separate tables**; never blend
  ex-post-normalized numbers into deployability claims. Full-sample `c`,
  expanding-window calibration, and leverage exposure stated next to every
  number they touch.
- If RV=0/non-finite occurs, or daily/monthly reconciliation deteriorates on
  re-pull, BLOCK that leg with reason instead of patching.
- No threshold search, no re-normalization variants, no macro overlay, no
  outcome-informed edits, no parent-result modification. GPI/IPI/FCPI tests
  remain out of scope until a separate prereg.
