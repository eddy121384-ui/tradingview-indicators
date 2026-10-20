# VolFair-specific exposure control — preregistration (2026-10-20)

**Status:** preregistered before calculating, inspecting, or writing any P&L for
the control leg. Research only, `production_authorized=false`.
This round writes the plan only: NO control backtest is executed.

## 0. Ordering attestation and scope

This is an independent follow-up to PR #201 (`macro_incremental_prereg.md`,
frozen at `c984f6d`; execution at `ffae7c6`; reporting fixes at `2ee8fc9`).
The PR #201 results are already known, so this diagnostic is **not** pristine
out-of-sample and must never be presented as such. What is frozen here is the
control definition, panels, metrics, and verdict mapping **before** the control
leg's P&L is computed.

One question only: **does VolFair+DH improve beyond simply holding a uniformly
lower VolFair equity exposure?** The test is a single, VolFair-specific,
average-exposure-matched control. No new macro rule, no new parameter, no
alternative control, no re-entry test, no Pine change, no edit to PR #201.

## 1. Frozen parents and inputs (read-only)

- PR #201 head `2ee8fc9` (branch `research/macro-incremental-prereg-20261016`),
  itself stacked on `research/equity-risk-classic-baselines-20261015` at
  `fdbd99c`.
- Rule definition: `research/macro_incremental_prereg.md` §§"Frozen macro legs"
  and "Frozen vehicles and panels" (relative rule, 714-month panel, 2bp costs,
  stale-factor carry in 2025-10, 2025-11, 2026-01).
- Frozen series (byte inputs, no recomputation drift):
  - `generated/classic-equity-baselines/macro-incremental-monthly.csv`
    (`volfair`, `vol_dh`, `E_DH`, `s_macro`, `stale` columns; 714 rows,
    1967-03..2026-08);
  - `generated/classic-equity-baselines/volatility-managed-monthly.csv`
    (`w_fair`; 714 rows);
  - `generated/classic-equity-baselines/daily-market-total-returns.csv`
    (official French daily factors, SHA `2f29e225…7db`);
  - `generated/issue-166/equity-monthly-total-returns.csv` (`equity_tr`);
  - `generated/issue-174/nine-sleeve-monthly-returns.csv` (`cash`);
  - `generated/issue-178/weight-matrix.csv` (neutral equity sum `0.45`);
  - `generated/issue-183/corrected-structural-monthly.csv` (B-2 applied states).
- VolFair remains exactly the frozen deployable leg: `w_vol[t] =
  min(1, Vbar[t-1]/RV2[t-1])`, expanding-mean RV from 1926, floor 0, one-month
  lag, no leverage.
- VolFair+DH remains exactly `w_vd[t] = w_vol[t] × s[t]`,
  `s[t] = min(1, E_DH[t]/0.45)`, including the 3 stale-carry months.

## 2. Frozen control leg (ONE definition, no variant)

Average-equity-matched VolFair control:

```
k      = mean_714(w_vd) / mean_714(w_vol)
w_ctrl = min(1, k × w_vol[t])
```

- `k` is a single scalar computed from the two frozen 714-month exposure series
  (`w_vol` = VolFair target weight, `w_vd` = VolFair+DH target weight).
  From the published #201 series: `mean(w_vol)=0.9069392156862739`,
  `mean(w_vd)=0.8261391904761918`, so `k≈0.9109091063518062`; the executed
  value is recomputed from the frozen CSV, not hardcoded. `k` is computed from
  the CSV's 6-decimal weight columns so the recorded value is reproducible; no
  higher-precision reconstruction is mixed in. The #201 audit found `s=1` in all
  three stale months; the control still uses the frozen 714-month mean and does
  not special-case them.
- Because `0 < k < 1` and `w_vol ≤ 1`, `k×w_vol < 1` every month: the `min(1,·)`
  floor never binds. Assert zero binding months; if any binds, BLOCK instead of
  adjusting `k`.
- The control keeps VolFair's own volatility-scaling shape and applies one
  uniform down-scale. It uses the same cash proxy, same monthly target-weight
  turnover convention, same 2bp cost (10bp sensitivity), and the same
  initial-deployment-free rule.
- **Exposure matching uses full-sample (714-month) information. The control is
  a descriptive hindsight counterfactual, NOT an ex-ante or live-tradable
  strategy.** Its mean exposure equals VolFair+DH by construction; residual
  differences are reported, never tuned away. "Mean exposure" is the arithmetic
  mean of monthly target weights (same convention as the frozen baselines);
  intra-month drift is not modeled.
- No second matching method (beta matching, vol matching, cap changes,
  expanding-window `k`, or month-by-month re-matching) is permitted in this
  study. Any such comparison requires a separate prereg.

## 3. Frozen evaluation panel and metrics

- Primary panel: the same 714 consecutive monthly payoffs 1967-03..2026-08,
  gross equity return `equity_tr`, cash `cash`, net return
  `w×equity + (1−w)×cash − 0.0002×|Δw|`, initial trade free.
- Three legs reported side by side: **VolFair**, **VolCtrl**, **VolFair+DH**.
- Full-period metrics for each leg: geometric CAGR, annualized vol (sample sd
  ×√12), Sharpe-like (`√12 × mean(net−cash)/sd(net)`), MaxDD on the cumulative
  net wealth index, worst month, mean equity exposure, annualized turnover,
  switches, up/down equity participation, summed missed-upside and
  avoided-loss (uncompounded), first/last month, n.
- Eras (same frozen bounds), each computed **within era** with wealth reset at
  era start: E1 1967-03–1979-12, E2 1980-01–1999-12, E3 2000-01–2019-12,
  E4 2020-01–2026-08. Report CAGR, Sharpe-like, MaxDD, mean exposure, and n.
- Crisis windows (same six, predeclared calendar windows, descriptive only):
  1973–74, 1987-08..12, 2000-03..2002-10, 2007-10..2009-03, 2020-02..04,
  2022. Report compounded net return, within-window MaxDD (wealth reset at
  window start), mean exposure, and n. These are arbitrary predeclared windows,
  not event-precision tests.
- Cost sensitivity: repeat every metric at 10bp per 100% target-weight change.
  This is the only robustness run; no rule/variant is added.

## 4. Frozen comparison and verdict (descriptive only)

Primary contrast: **VolFair+DH vs VolCtrl** (macro-timing gap at matched average
exposure). Context rows: VolFair vs VolCtrl (pure exposure-scaling gap) and
VolFair vs VolFair+DH (total, already reported in #201).

- Precommitted heuristic gates, same economic thresholds used in #201 for
  comparability (not statistical tests):
  - `ΔSharpe = Sharpe(VolFair+DH) − Sharpe(VolCtrl) ≥ +0.02`
  - `ΔMaxDD = MaxDD(VolFair+DH) − MaxDD(VolCtrl) ≥ +1.0pp`
  - `ΔCAGR = CAGR(VolFair+DH) − CAGR(VolCtrl) ≥ −0.10pp/yr`
- Era consistency: count eras with `ΔSharpe > 0` (E1–E4, no cherry-picking).
- Crisis consistency flag (descriptive, not a statistical test): count the six
  predeclared windows with `Δ` compounded net return ≥ 0.
- Verdict mapping (frozen before control P&L):
  - all 3 gates pass AND ≥3/4 eras with positive ΔSharpe AND ≥4/6 crisis
    windows non-negative → `volfair_timing_value_descriptively_supported`;
  - all 3 gates pass but either consistency check fails →
    `volfair_timing_value_mixed_by_era_or_crisis`;
  - 1–2 gates pass → `volfair_timing_value_mixed`;
  - 0 gates pass → `volfair_timing_value_not_descriptively_supported`.
- The crisis table and era table are mandatory alongside the verdict. The
  verdict is an economic heuristic summary, not proof of skill, statistical
  significance, or live tradability. No p-values, no multiple-testing
  correction, no claim that the control is investable.
- Decomposition: report the three legs side by side and label any
  `VolCtrl − VolFair` / `VolFair+DH − VolCtrl` differences as accounting
  arithmetic on reported numbers, not causal attribution. Nonlinear metrics
  (CAGR, MaxDD, Sharpe ratio) do not decompose additively; do not sum them.
- Supplementary context (descriptive, no gate): number of months with `s<1`,
  distribution of `s`, mean exposure by era for all three legs, and the
  maximum month-by-month weight difference between VolFair+DH and VolCtrl.

## 5. Integrity checks and stop conditions

Before any control P&L is computed, fail-stop asserts must verify:

1. Recompute VolFair from the frozen daily file and match `w_fair` in
   `volatility-managed-monthly.csv` on all 714 months (tolerance 1e-4).
2. Recompute `w_vd` from the frozen `volfair`/`s_macro` columns and match
   `vol_dh` on all 714 rows; confirm exactly 3 stale months at 2025-10,
   2025-11, 2026-01 and `w_vd = w_vol × s_last` there.
3. `k` computed from the frozen 714-month means; assert `0 < k < 1`,
   `mean(w_ctrl) = mean(w_vd)` within 1e-9, and zero `min(1,·)` binding months.
4. Date alignment: 714 months, 1967-03..2026-08, no dropped/concatenated
   months; all equity and cash returns finite and > −100%.
5. Determinism: run twice; output must be byte-identical.

If any check fails, or if the frozen #201 series cannot be reproduced exactly,
**BLOCK the control leg with the reason**; do not substitute a different
matching method or adjust `k`. Poor or unflattering results are reported as-is.

## 6. Limitations (frozen)

- `k` uses full-sample exposure information → descriptive hindsight, not an
  ex-ante strategy; the control could not have been traded with this `k`.
- Revised-vintage research only: French/CRSP revisions, TB3MS/1200 cash proxy
  timing, CIZ-era daily file, monthly rounding MAE 0.047pp/mo. No
  contemporaneous PIT certificate (#189: full PIT not identifiable). #183/#188
  data are already-studied revised vintages.
- PR #201 results are already known; this is a targeted diagnostic, not a
  fresh out-of-sample test, and no multiplicity correction is possible.
- VolFair and VolFair+DH are the same vehicle/panel; the control inherits all
  VolFair mechanics and limitations (expanding calibration, monthly close,
  no intra-month trades, no taxes/capacity/market impact).
- The 2bp/10bp cost proxy is approximate; no spread, borrow, or tax model.
- No live-trading, capacity, or publication claim. `production_authorized=false`.

## 7. Deliverables (execution round, not this round)

- `research/volfair_exposure_control_prereg.md` (this file).
- `research/volfair_exposure_control.mjs` (control + metrics + asserts).
- `research/test_volfair_exposure_control.mjs` (synthetic mechanics: `k`
  scaling, cap non-binding, mean-exposure equality, `w_ctrl < w_vol`,
  determinism).
- `generated/classic-equity-baselines/volfair-exposure-control-results.json`.
- `generated/classic-equity-baselines/volfair-exposure-control-monthly.csv`.
- `generated/classic-equity-baselines/volfair-exposure-control-finding.md`.
- No Pine, no new Issue, no modification of PR #201 artifacts, no merge.

## 8. Prohibitions

No tuning of `k` or of any VolFair/macro parameter; no alternative matching
methods or control variants; no threshold search; no changes to the 714-month
panel, eras, crisis windows, cost convention, or metric definitions; no
outcome-informed edits; no Pine changes; no production authorization; no merge.
`production_authorized=false`.
