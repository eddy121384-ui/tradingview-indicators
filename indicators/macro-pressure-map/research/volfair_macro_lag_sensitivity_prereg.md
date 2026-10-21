# VolFair+DH macro-factor lag sensitivity — preregistration (2026-10-21)

**Status:** planning only. No new P&L has been calculated, inspected, or written
for this study. Research only, `production_authorized=false`. Draft PR, stacked
on PR #204; no merge, no Pine, no modification of PR #201/#204 artifacts.

## 0. Question and ordering attestation

One question only:

> If the already-applied macro defensive factor is delayed by an additional
> **L = 1, 2, or 3 calendar months**, does VolFair+DH still show a historical
> advantage over (a) classic VolFair and (b) a VolFair-shaped control with the
> same full-panel mean equity exposure?

This is a **publication/availability delay stress test on the frozen applied
factor**. It is *not* a point-in-time (PIT) reconstruction, does not delay or
re-estimate the underlying macro data, does not re-run B-2, and cannot repair
historical data-revision bias.

The study is deliberately narrow: four predeclared lag points `L = 0,1,2,3`
only. No tuning, no alternative rule, no best-lag selection, no new strategy
variant.

## 1. Prior evidence and frozen lineage (read-only)

This prereg follows the literature-first / replication-first requirement and
uses the following frozen parents without editing them:

| parent | frozen role | relevant fact |
|---|---|---|
| PR #201 head `2ee8fc9` | macro-vs-trend incremental study | 714 consecutive months 1967-03..2026-08; VolFair+DH vs VolFair: ΔSharpe +0.055, ΔMaxDD +11.31pp, ΔCAGR +0.18pp; 2bp main / 10bp sensitivity |
| PR #204 head `6497c54` | VolFair-specific exposure control | frozen VolCtrl: `k=0.9109091063518062`, `w_ctrl=min(1,k*w_vol)`; VolFair+DH vs VolCtrl: ΔSharpe +0.0551, ΔMaxDD +7.61pp, ΔCAGR +0.63pp; 3/4 eras and 5/6 crises non-negative |
| Issue #183 final `411835c` | corrected allocation lineage | B-2 **already executed** applied-state timeline `corrected-structural-monthly.csv`, 721 applied months 1966-05..2026-08, with 3 inherited calendar gaps; the 9-sleeve holdings are the frozen matrix row for each applied `alloc_state` |
| Issue #189 conclusion (2026-10-14) | PIT feasibility | full nine-state PIT replay **No-Go / not identifiable**: G5 has no continuous first-reported vintage; I3/I4 are not equivalent; I5 matches at the tested tolerance with a residual SA-basis caveat; only revised-vintage research is possible |

Frozen inputs (paths relative to `indicators/macro-pressure-map/research/`):

- `generated/classic-equity-baselines/macro-incremental-monthly.csv` — 714-row
  frozen #201 panel (`volfair`, `vol_dh`, `E_DH`, `s_macro`, `stale`, `equity`,
  `cash`).
- `generated/classic-equity-baselines/volfair-exposure-control-monthly.csv` and
  `volfair-exposure-control-results.json` — #204 L=0 replication target.
- `generated/issue-183/corrected-structural-monthly.csv` — #183 B-2 applied
  states, used only for warm-up and stale-month provenance; B-2 is not re-run.
- `generated/issue-178/weight-matrix.csv` — frozen 9x9 matrix; neutral equity
  anchor `0.45`.
- `generated/classic-equity-baselines/volatility-managed-monthly.csv`,
  `daily-market-total-returns.csv`, `generated/issue-166/equity-monthly-total-returns.csv`,
  `generated/issue-174/nine-sleeve-monthly-returns.csv` — integrity/replication
  inputs only.

The #183 `alloc_state` timeline is consumed read-only as the already-executed
B-2 applied-state timeline. For any month, the frozen 9-sleeve holdings are the
matrix row for that `alloc_state`; no B-2 step is re-run, re-confirmed, or
shifted. This study uses only the aggregate equity weight `E_DH`; the 9-sleeve
holdings are provenance, not a separately traded portfolio here. No later data,
no new sample, no new macro series, no re-estimation.

## 2. Frozen strategy (unchanged)

Everything except the lag `L` remains exactly as frozen in #201/#204:

- VolFair target: `w_vol[m] = min(1, Vbar[m-1] / RV2[m-1])`, expanding-mean
  realized variance from 1926, floor 0, one-month lag, no leverage.
- DH matrix, B-2 confirmed applied states, `0.45` neutral equity anchor, and
  `s[m] = min(1, E_DH[m]/0.45)`.
- VolFair+DH at `L=0`: use the frozen #201 `vol_dh[m]` column (the 6-decimal
  stored product), which is validated against `w_vol[m] * s[m]` at `2e-6`.
  This is the exact #204 replication point, including the three frozen
  stale-carry months. For `L>0`, `w_L[m]` is the product defined in §3.
- Same single broad-US equity total-return vehicle, same cash proxy, same
  monthly decision/execution timing, same 2bp primary cost and 10bp sensitivity,
  same initial-deployment-free convention, same eras and crisis windows.

The only experimental variable is the additional delay of the already-applied
factor `s`. VolFair's own timing, the DH matrix, B-2, the 45% anchor, costs,
and the 714-month panel are not changed.

## 3. Lag definition (the only experimental variable)

Let `A[m]` denote the frozen #201 `s_macro` series at payoff month `m`.
`A[m]` is the factor actually applied to month `m`; it already includes the
frozen B-2 confirmation and data-availability timing. The shift is applied to
this applied factor, **not** to the `signal_month` column, so it cannot add a
second B-2 or availability lag. For lag `L`:

```
s_L[m] = A[m - L]          (calendar months, not row offsets)
w_L[m] = w_vol[m] * s_L[m]
```

where `m` is the payoff month and `L in {0,1,2,3}`. The subtraction is calendar
month arithmetic (`year*12 + month`), never a row-index shift and never a
compression of the calendar.

Timing examples (all values are the frozen applied factor at that month):

| payoff month `m` | `L=0` | `L=1` | `L=2` | `L=3` |
|---|---|---|---|---|
| 1967-03 | `s[1967-03]` | `s[1967-02]` | `s[1967-01]` | `s[1966-12]` |
| 1967-04 | `s[1967-04]` | `s[1967-03]` | `s[1967-02]` | `s[1967-01]` |
| 1967-05 | `s[1967-05]` | `s[1967-04]` | `s[1967-03]` | `s[1967-02]` |

- `L=0` is the replication point and must reproduce PR #204 exactly.
- For `L>0`, the factor is older, so no future information is introduced.
- This shifts only the applied factor. It does **not** delay the state timeline,
  re-run B-2, re-estimate `E_DH`, or change VolFair's own trade timing.

### 3.1 Warm-up (existing history only)

For the first `L` panel months, `m-L` falls before 1967-03. Use only the
existing #183 warm-up tail `1966-05..1967-02`:

```
E_DH[x] = (sp500[x] + nasdaq[x] + russell[x]) / 100   from the frozen matrix
s[x]    = min(1, E_DH[x] / 0.45)
```

for the #183 B-2 applied `alloc_state` at calendar month `x`. Validate this
reconstruction against the frozen `s_macro` on all **overlapping observed #183
months (711 of 714)** at `max abs diff < 2e-6`; the three stale months are
checked separately against the frozen carry rule. For `L=3`, the earliest
needed month is 1966-12; all needed warm-up months exist. If any required
warm-up month is missing or inconsistent, **BLOCK**; do not extend the sample,
splice a different series, or use a future state.

### 3.2 Missing months (frozen stale carry, no compression)

The #183 source has three inherited missing calendar months: **2025-10,
2025-11, 2026-01**. The frozen #201 `s_macro` already carries `s_last` in those
months and flags them `stale=1` (all three happen to be `s=1`). For any
`m-L` equal to one of those months:

- use the frozen stored `s` value **as-is** (the last valid factor);
- do not interpolate, do not substitute a later observation, do not drop the
  month, and do not compress the calendar;
- keep the current month's VolFair weight and its normal turnover/cost timing.

If `m-L` falls outside `1966-05..2026-08`, **BLOCK**; do not extrapolate. The
714-month payoff calendar remains continuous in all legs.

## 4. Per-lag exposure-matched control (one per L)

For each `L`, define one scalar using the full 714-month sample:

```
k_L       = mean_714(w_L) / mean_714(w_vol)
w_ctrl,L  = min(1, k_L * w_vol)
```

- The control preserves VolFair's own volatility-scaling shape and applies one
  uniform down-scale; it is not a constant-weight portfolio.
- `k_L` uses full-sample information. It is a **descriptive hindsight
  counterfactual**, not an ex-ante or live-tradable strategy.
- All calculations use full-precision target weights derived from the frozen
  6-decimal inputs; the monthly CSV stores weights at 6 decimals for audit.
  `L=0` uses the frozen `vol_dh` column for exact #204 replication.
- No alternative matching method is permitted (no beta, volatility,
  month-by-month, expanding-window, or era-by-era matching).
- Because `0 < s_L <= 1`, expect `mean(w_L) <= mean(w_vol)` and
  `0 < k_L < 1`. Assert zero `min(1,.)` cap-binding months and
  `|mean(w_ctrl,L) - mean(w_L)| < 1e-9`; if either fails, **BLOCK** rather than
  redefining the control.
- `L=0` must reproduce #204: `k_0` equals
  `0.9109091063518062` within `1e-12`, and `w_ctrl,0` matches #204 `vol_ctrl`
  within `2e-6` (6-decimal CSV storage).
- The control is never used to choose `L`. It exists only to ask whether the
  delayed macro factor adds anything beyond a uniform exposure reduction.

## 5. Evaluation panel and metrics (same as #201/#204)

Primary panel: **714 consecutive months, 1967-03..2026-08**. Net return for a
target weight `w`:

```
net[m] = w[m]*equity[m] + (1-w[m])*cash[m] - fee*|w[m]-w[m-1]|
fee    = 0.0002 (2bp main) or 0.0010 (10bp sensitivity)
initial deployment free (turnover[first] = 0)
```

All P&L uses full-precision target weights; the monthly CSV is a 6-decimal
audit output, not a separate return series.

Report for every leg (`VolFair`, each `VolCtrl,L`, each `w_L`):

- full period: geometric CAGR, annualized vol (sample sd x sqrt(12)),
  Sharpe-like (`sqrt(12)*mean(net-cash)/sd(net)`), MaxDD on cumulative net
  wealth, worst month, mean equity exposure, annualized turnover, switches,
  terminal wealth, up/down participation, missed-upside and avoided-loss sums;
- eras: E1 1967-03..1979-12, E2 1980-01..1999-12, E3 2000-01..2019-12,
  E4 2020-01..2026-08; each within-era wealth reset;
- crises: 1973-74 (1973-01..1974-12), 1987-08..12, 2000-03..2002-10,
  2007-10..2009-03, 2020-02..04, 2022-01..12; each within-window wealth reset;
- every metric repeated at 10bp.

Mandatory comparisons, all reported side by side for every `L`:

1. `w_L` vs classic **VolFair** (total effect, including exposure reduction);
2. `w_L` vs its own **VolCtrl,L** (residual macro-timing effect at matched
   full-panel mean exposure);
3. `w_L` vs `w_0` (decay relative to the PR #204 replication point);
4. `L=0` vs #204 (replication gate).

Nonlinear metrics are reported as arithmetic differences, never summed or
decomposed causally.

## 6. Precommitted descriptive criteria (no best-lag selection)

All criteria are frozen before any new P&L.

### 6.1 Per-lag gates vs its own control

For each `L` independently:

| gate | threshold |
|---|---:|
| `Delta Sharpe = Sharpe(w_L) - Sharpe(w_ctrl,L)` | `>= +0.02` |
| `Delta MaxDD = MaxDD(w_L) - MaxDD(w_ctrl,L)` | `>= +1.0pp` |
| `Delta CAGR = CAGR(w_L) - CAGR(w_ctrl,L)` | `>= -0.10pp/yr` |

Consistency checks, also per `L`:

- at least **3/4 eras** with positive `Delta Sharpe`;
- at least **4/6 crises** with non-negative `Delta` compounded net return.

The gates are defined only against the matched control. Comparisons against
classic VolFair are reported descriptively with the same metrics; they are not
a separate gate and are never used to select a lag.

### 6.2 Per-lag verdict mapping

- all 3 gates pass and both consistency checks pass ->
  `lag_L_timing_value_descriptively_supported`;
- all 3 gates pass but either consistency check fails ->
  `lag_L_timing_value_mixed_by_era_or_crisis`;
- 1-2 gates pass -> `lag_L_timing_value_mixed`;
- 0 gates pass -> `lag_L_timing_value_not_descriptively_supported`.

### 6.3 Overall lag-robustness label

- `lag_robust_descriptively_supported` iff **all** of `L=1,2,3` pass all three
  gates and both consistency checks;
- `lag_partially_supported` iff at least one but not all of `L=1,2,3` pass that
  full set;
- `lag_not_descriptively_supported` iff none of `L=1,2,3` pass the full set.

This label is a descriptive summary, not a statistical test. It is not chosen
by the best-performing lag; every lag is reported whether favourable or not.

### 6.4 Decay and crisis-defense disappearance

- **Decay:** report `Delta_L - Delta_0` for Sharpe, MaxDD, and CAGR vs the
  matched control, plus absolute `metric_L - metric_0`. Report whether the
  advantage decays monotonically in `L` as a description only; monotonicity is
  **not** a gate and is never used to select a lag.
- **Crisis defense:** for crisis `c`, define
  `D_L,c = ret(w_L,c) - ret(w_ctrl,L,c)`. A defense is "present" at `L` when
  `D_L,c >= 0`. It "disappears" at `L>0` when `D_0,c >= 0` but `D_L,c < 0`.
  A reduction with the same sign is reported as "weakened" (descriptive, no
  separate gate). Report the full 6x4 matrix of `D_L,c` and the disappearance
  set for each `L`. Also report `ret(w_L,c) - ret(VolFair,c)` as secondary
  context. Do not cherry-pick a crisis or a lag.

## 7. Integrity checks and stop conditions

Before any new P&L is accepted:

1. **L=0 replication.** Reconstruct all 714 `L=0` weights from the frozen
   `vol_dh` column and the #204 control; recompute 2bp/10bp net returns. Match
   #204 monthly CSV (`max abs diff <= 1e-6` for net returns, `<= 2e-6` for
   weights) and #204 results JSON full/era/crisis metrics (`<= 1e-9`). The
   #204 verdict and gate values must also reproduce. If not, **BLOCK** before
   evaluating any `L>0`.
2. **Frozen identities.** `vol_dh` vs `volfair*s_macro` `<= 2e-6`;
   `s_macro` vs `min(1,E_DH/0.45)` `<= 2e-6`; `E_DH` vs matrix equity
   `<= 5e-5`; exactly the three stale months 2025-10, 2025-11, 2026-01.
3. **Panel integrity.** Exactly 714 rows, first 1967-03, last 2026-08, every
   consecutive calendar month present exactly once, all equity/cash returns
   finite and `> -100%`.
4. **Lag availability.** For every `L`, every `m-L` maps to an existing month
   in `1966-05..2026-08`; all 714 mappings resolve; every shifted factor is
   finite and within `[0.5,1]`; warm-up overlap check passes; no future month is
   used.
5. **Control integrity.** For every `L`: `0 < k_L < 1`, zero cap-binding
   months, mean exposure equality `<1e-9`, `0 <= w_L <= w_vol <= 1`.
6. **B-2 provenance.** The #183 `alloc_state` timeline is consumed as-is; no
   re-run, no re-confirmation, no state shift. The warm-up reconstruction is
   validated against the frozen `s_macro` on the full overlap.
7. **Determinism.** Two engine runs must produce byte-identical JSON and CSV.

Any failure stops the study with a documented reason. No substitution of data,
no adjustment of `k`, no dropping of months, no redefinition of the control.

## 8. Limitations and required disclaimer

- This is a **revised-vintage, non-PIT** exercise. #189 found full nine-state
  PIT not identifiable: G5 has no continuous first-reported vintage, I3/I4 are
  not equivalent, and I5 matches at the tested tolerance with a residual
  SA-basis caveat. There is no contemporaneous vintage certificate.
- The experiment delays **only the already-applied factor**. It does not delay
  the underlying macro releases, re-estimate states, re-run B-2, or reconstruct
  what an investor could have known. It is a publication/availability delay
  stress test, **not** a point-in-time backtest.
- It **cannot repair** historical data-revision bias. It also does not model
  release-day timing, vintage revisions, benchmark revisions, or real-time
  publication calendars.
- `k_L` uses full-sample information and is a descriptive hindsight
  counterfactual, not a tradable control. The analysis is not out-of-sample:
  #201/#204 results are already known; multiple looks and correlated controls
  mean no p-values or multiplicity correction are claimed.
- Revised-vintage data limitations from #201/#204 remain (French/CRSP
  revisions, TB3MS/1200 cash-proxy timing, CIZ-era daily file, monthly rounding).
  No live-trading, capacity, tax, or publication claim.

## 9. Deliverables (execution round only) and prohibitions

Planned execution artifacts, only after review approval:

- `research/volfair_macro_lag_sensitivity.mjs` (engine + asserts);
- `research/test_volfair_macro_lag_sensitivity.mjs` (synthetic mechanics:
  calendar shift, warm-up, stale carry, L=0 identity, per-L control,
  determinism);
- `research/volfair_macro_lag_sensitivity_mirror.mjs` (independent CSV mirror);
- `generated/classic-equity-baselines/volfair-macro-lag-sensitivity-results.json`;
- `generated/classic-equity-baselines/volfair-macro-lag-sensitivity-monthly.csv`;
- `generated/classic-equity-baselines/volfair-macro-lag-sensitivity-finding.md`.

Prohibitions: no tuning of any frozen parameter; no additional lag points or
strategy variants; no alternative control; no changes to the 714-month panel,
eras, crises, costs, or metric definitions; no outcome-informed edits; no
best-lag selection; no Pine changes; no modification of PR #201/#204; no merge.
`production_authorized=false`.
