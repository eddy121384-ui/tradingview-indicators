# Macro incremental value — results (2026-10-16)

- Prereg (frozen before any macro-augmented P&L): `research/macro_incremental_prereg.md`, commit `c984f6d`. Reviews `#6208853986`, `#6211025620` addressed.
- Engine: `research/macro_incremental_backtest.mjs`; mechanics: `research/test_macro_incremental.mjs` (10 checks PASS); mirror: `research/macro_incremental_mirror.mjs` (CAGR/MaxDD recomputed from monthly CSV, all OK within CSV-rounding tolerance; stale months and `w_aug<=w_base` verified).
- Baselines reused byte-identical: SMA10/MOM12 recomputed 714/714 zero-disagreement vs `monthly-signals.csv`; VolFair `w_fair` recomputed vs `volatility-managed-monthly.csv` (max diff <1e-4); BH reproduced (CAGR 10.91%).
- Panel: primary 714 consecutive months 1967-03..2026-08 with disclosed stale-factor carry in 2025-10, 2025-11, 2026-01 (`w_aug=w_base*s_last`); 711 observed-macro months secondary diagnostic only. Costs 2bp main / 10bp sensitivity, initial deployment free.
- Research only, revised-vintage, non-PIT. `production_authorized=false`. No Pine, no merge, no new rule variants.
- Amendment 2026-10-20 (reporting only, review `#6280467496`): 711-month secondary restricted to noncompounding fields; scorecard gate counts corrected to SMA 2/4, MOM 1/4, Vol 4/4; 714-month primary results, strategy, thresholds and prereg unchanged.

## Headline (primary 714, 2bp)

| leg | CAGR | Sharpe-like | MaxDD | avg equity | turnover/yr |
|---|---:|---:|---:|---:|---:|
| BH | 10.91% | 0.456 | −50.31% | 100.00% | 0% |
| SMA10 | 10.28% | 0.518 | −24.24% | 74.93% | 147.9% |
| SMA10+DH | 9.87% | 0.520 | −19.83% | 69.89% | 149.7% |
| MOM12 | 10.16% | 0.500 | −28.31% | 72.41% | 82.4% |
| MOM12+DH | 9.95% | 0.515 | −28.31% | 67.58% | 87.3% |
| VolFair | 10.44% | 0.477 | −41.20% | 90.69% | 101.4% |
| VolFair+DH | 10.61% | 0.532 | −29.90% | 82.61% | 103.7% |
| DH-equity-only (budget ref) | 8.12% | 0.550 | −17.63% | 43.06% | 18.6% |

10bp sensitivity CAGR: SMA 10.15 / SMA+DH 9.73; MOM 10.09 / MOM+DH 9.88; Vol 10.35 / Vol+DH 10.52. Ordering unchanged.

## Incremental diffs (augmented minus baseline, 2bp)

| pair | Sharpe diff | MaxDD diff (pp) | CAGR diff (pp/yr) | vs matched-fixed Sharpe |
|---|---:|---:|---:|---|
| SMA10+DH − SMA10 | +0.002 | +4.40 | −0.41 | 0.520 ≥ 0.456 |
| MOM12+DH − MOM12 | +0.015 | +0.00 | −0.21 | 0.515 ≥ 0.456 |
| VolFair+DH − VolFair | +0.055 | +11.31 | +0.18 | 0.532 ≥ 0.456 |

Descriptive scorecard (thresholds ≥+0.02 / ≥+1.0pp / ≥−0.10pp + Sharpe≥matched; heuristics only): SMA 2/4 gates (MaxDD and matched-fixed Sharpe pass; Sharpe and CAGR fail), MOM 1/4 (matched-fixed Sharpe only; MaxDD 0.00pp, Sharpe and CAGR fail), VolFair 4/4. Neither SMA nor MOM satisfies all four conjunctive requirements, so overall: **mixed (1/3)** — descriptively favourable in one of three correlated controls only. This count is not statistical evidence, not proof of an incremental edge, and not a tradability claim.

Secondary 711-month diagnostic (noncompounding only — observed-month Sharpe, annualized vol from monthly dispersion, mean monthly net, mean exposure; the three missing months are listed explicitly and CAGR/compounded MaxDD/terminal wealth are excluded because the filtered stream is non-contiguous): Sharpe SMA 0.515/0.516, MOM 0.497/0.511, Vol 0.474/0.529 (within ~0.003 of primary). Stale carry does not drive the reading; all compounding metrics remain the primary 714-month figures above.

## Eras and crises (plain tables, no cherry-picking)

Era CAGR: E1 — SMA 7.89/SMA+DH 7.55, MOM 8.55/8.26, Vol 6.40/Vol+DH 8.16; E2 — SMA 13.95/13.22, MOM 14.20/13.64, Vol 15.81/14.67; E3 — SMA 7.84/7.62, MOM 6.89/6.97, Vol 7.26/7.69; E4 — SMA 11.48/11.27, MOM 11.36/11.44, Vol 12.27/12.32. Augmented trails its baseline in the long E2 bull era (lower exposure); elsewhere mixed and small.

Crisis compounded: 1973–74 SMA −7.87/−5.32, MOM +6.56/+6.56, Vol −39.02/−24.89; 1987 SMA −20.45/−16.33, MOM −20.45/−16.33, Vol −18.33/−14.50; 2000–02 SMA −6.68/−3.95, MOM −6.56/−2.65, Vol −26.50/−20.65; 2007–09 SMA −1.44/−1.44, MOM −7.70/−7.70, Vol −21.48/−14.57; 2020-02..04 identical (SMA −7.91, MOM −20.21, Vol −14.16 — macro adds nothing when baseline already positioned); 2022 SMA −10.70/−9.66, MOM −13.02/−10.47, Vol −12.72/−10.60. Defensive help is crisis- and baseline-dependent, not uniform.

## Earlier defense / re-entry drag (no gate; 8 #186 troughs)

Months from trough to first ≥95% equity (median; never=0 for all legs):

- SMA10 4 vs SMA10+DH 8; MOM12 9 vs MOM12+DH 10; VolFair 5 vs VolFair+DH 8.
- No augmented leg ever re-enters earlier than its baseline (mechanical `w_aug<=w_base` holds, gap months included). The statistic measures re-entry drag/cost. Largest drag at the 1982-07 trough (augmented lags 21–31 months vs baseline 0–4). Troughs are S&P-dated while the vehicle is French broad market (≤2-month reference mismatch, disclosed).

## Limitations

Revised vintages (French/CRSP, TB3MS proxy timing, CIZ-era daily, monthly rounding MAE 0.047pp/mo); macro inputs are revised reconstructions without contemporaneous PIT (#189: full PIT not identifiable); #183/#188 data already studied; SMA10/MOM12/VolFair are correlated long/cash controls on one vehicle/panel, not independent replications; exposure-matched fixed controls use full-sample hindsight (descriptive only); constant-mix cost caveat as in baselines; 711-month metrics are a non-continuous diagnostic, never a live record.

The fixed-weight exposure match does not fully isolate incremental macro timing conditional on VolFair: VolFair+DH gains Sharpe/MaxDD while mean equity falls 90.69%→82.61%. An exposure-matched **VolFair-specific** control would be a *separately preregistered future diagnostic*, not an addition to this frozen study; nothing here should be read as that comparison.

## Files

- `generated/classic-equity-baselines/macro-incremental-results.json` (full metrics, eras, crises, scorecard with per-gate booleans, re-entry tables, 711 noncompounding secondary)
- `generated/classic-equity-baselines/macro-incremental-monthly.csv` (714 rows: weights, E_DH, s_macro, stale flag, nets)
- Engine + `test_macro_incremental.mjs` + `macro_incremental_mirror.mjs` (all PASS)

`production_authorized=false`.
