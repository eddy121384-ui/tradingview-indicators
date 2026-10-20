# VolFair-specific exposure control — results (2026-10-20)

**Status:** executed under the frozen prereg `research/volfair_exposure_control_prereg.md` at commit `802f6749e30d6f10b871ff61200011ebf965ab3b`; GPT review `#6285267068` approved execution. Research only, `production_authorized=false`. No Pine, no PR #201 edits, no merge.

- Parent: PR #201 head `2ee8fc99158f8a566d98168f757f6b3f1af5a931`; its frozen results are reused unchanged.
- Engine: `research/volfair_exposure_control.mjs`; mechanics: `research/test_volfair_exposure_control.mjs` (13/13 PASS); mirror: `research/volfair_exposure_control_mirror.mjs` (all OK). A separate fresh-code recomputation, with no engine import, reproduced every full-panel 2bp/10bp value within `9.1e-8` and every era/crisis value within `1.03e-7`.
- Panel: 714 consecutive months, 1967-03..2026-08; 2bp main / 10bp sensitivity; initial deployment free; 3 stale-factor months (2025-10, 2025-11, 2026-01). Revised-vintage, non-PIT. This is a targeted diagnostic chosen after #201, not a fresh out-of-sample test.

**Bottom line (descriptive):** VolFair+DH clears all three precommitted gates against VolCtrl (+0.055 Sharpe, +7.61pp MaxDD, +0.63pp CAGR), with 3/4 eras and 5/6 crises non-negative. Exceptions: E2 and 2020. The control uses full-sample `k`, so this is a hindsight mean-matched diagnostic, not a tradable or causal result.

## Control definition

```
k      = mean_714(w_vd) / mean_714(w_vol)
w_ctrl = min(1, k × w_vol)
```

- `k = 0.9109091063518062`; `mean(w_vol) = 0.9069392156862739`; `mean(w_vd) = 0.8261391904761918`; `mean(w_ctrl) = 0.826139190476198`; zero cap-binding months. `k` is recomputed from the frozen 6-decimal weight columns, not hardcoded.
- The control keeps VolFair's volatility-scaling shape and applies one uniform down-scale. It is **not** a constant 82.61% portfolio: its exposure still varies month to month.
- `k` uses the full 714-month sample, including the 3 stale months; they are not special-cased. The control is a **descriptive hindsight counterfactual, not an ex-ante or live-tradable strategy**.
- Matching is on the full-panel arithmetic mean only. It is not month-by-month, beta, volatility, or era-by-era matching. Residual exposure differences remain (see the era table), and the maximum month-by-month weight gap between VolFair+DH and VolCtrl is **41.09pp**.

## Headline (2bp, n=714)

| leg | CAGR | ann vol | Sharpe-like | MaxDD | worst month | avg equity | turnover/yr | switches |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| VolFair | 10.44% | 13.39% | 0.477 | −41.20% | −22.59% | 90.69% | 101.4% | 220 |
| VolCtrl | 9.98% | 12.20% | 0.477 | −37.51% | −20.53% | 82.61% | 92.4% | 220 |
| VolFair+DH | 10.61% | 11.96% | 0.532 | −29.90% | −18.48% | 82.61% | 103.7% | 257 |

Remaining full-period metrics (same 2bp panel):

| leg | up participation | down participation | missed upside | avoided loss | terminal wealth (×) |
|---|---:|---:|---:|---:|---:|
| VolFair | 90.80% | 90.49% | 206.8pp | 162.0pp | 367.37 |
| VolCtrl | 82.71% | 82.43% | 320.6pp | 241.2pp | 287.73 |
| VolFair+DH | 83.51% | 81.13% | 324.1pp | 276.8pp | 404.10 |

Participation is the mean equity weight in months with positive/negative equity returns. Missed upside / avoided loss are summed uncompounded gross-return shortfalls, not utility. First/last month and all raw fields are in the results JSON.

## Primary comparison: VolFair+DH vs VolCtrl (2bp)

| gate | threshold | observed | pass |
|---|---:|---:|---|
| ΔSharpe | ≥ +0.02 | **+0.0551** | yes |
| ΔMaxDD | ≥ +1.0pp | **+7.61pp** | yes |
| ΔCAGR | ≥ −0.10pp/yr | **+0.63pp/yr** | yes |

Consistency: **3/4 eras** with positive ΔSharpe (E1, E3, E4) and **5/6 crisis windows** with non-negative Δ compounded return (1973–74, 1987, 2000–02, 2007–09, 2022). Exceptions: E2 and 2020.

**Frozen verdict: `volfair_timing_value_descriptively_supported`.**

This means only that VolFair+DH beat this one precommitted, full-panel mean-exposure-matched uniform down-scale on the three economic gates in this historical sample. It is not statistical evidence, not causal proof of macro predictiveness, not independent replication, and not a tradability claim.

Accounting arithmetic on reported numbers (not causal attribution; nonlinear metrics do not decompose additively and must not be summed):

- VolFair → VolCtrl (pure uniform exposure scaling): ΔSharpe **+0.000003**, ΔMaxDD **+3.69pp**, ΔCAGR **−0.45pp**.
- VolCtrl → VolFair+DH (the residual gap): ΔSharpe **+0.0551**, ΔMaxDD **+7.61pp**, ΔCAGR **+0.63pp**.
- VolFair → VolFair+DH (total, consistent with #201): ΔSharpe **+0.0551**, ΔMaxDD **+11.31pp**, ΔCAGR **+0.18pp** (exact +0.177pp).

Uniform scaling alone is associated with drawdown reduction at a small CAGR cost and essentially no Sharpe improvement; the residual DH-vs-control gap is the additional Sharpe/MaxDD/CAGR difference in this sample.

## Eras (mandatory; within-era wealth reset)

| era | leg | CAGR | Sharpe-like | MaxDD | avg equity | n |
|---|---|---:|---:|---:|---:|---:|
| E1 1967-03..1979-12 | VolFair | 6.40% | 0.084 | −41.20% | 96.74% | 154 |
| E1 | VolCtrl | 6.48% | 0.084 | −37.51% | 88.12% | 154 |
| E1 | VolFair+DH | 8.16% | 0.206 | −26.99% | 82.92% | 154 |
| E2 1980-01..1999-12 | VolFair | 15.81% | 0.614 | −24.24% | 94.75% | 240 |
| E2 | VolCtrl | 15.12% | 0.615 | −22.04% | 86.31% | 240 |
| E2 | VolFair+DH | 14.67% | 0.594 | −19.83% | 87.33% | 240 |
| E3 2000-01..2019-12 | VolFair | 7.26% | 0.550 | −36.05% | 84.70% | 240 |
| E3 | VolCtrl | 6.81% | 0.551 | −32.88% | 77.15% | 240 |
| E3 | VolFair+DH | 7.69% | 0.626 | −29.90% | 78.10% | 240 |
| E4 2020-01..2026-08 | VolFair | 12.27% | 0.738 | −16.32% | 84.87% | 80 |
| E4 | VolCtrl | 11.47% | 0.738 | −14.88% | 77.31% | 80 |
| E4 | VolFair+DH | 12.32% | 0.768 | −14.56% | 81.44% | 80 |

ΔSharpe (VolFair+DH − VolCtrl): **E1 +0.121, E2 −0.020, E3 +0.076, E4 +0.030**.

The E2 exception is the long bull era: VolFair+DH ran slightly *higher* average exposure than the control (87.33% vs 86.31%) and gave back a small amount of Sharpe. E1 carries the largest positive gap (+0.121), with a much lower average exposure (82.92% vs 88.12%) and a much shallower drawdown. Because the control matches only the full-sample mean, these era exposure differences are part of the description, not something that was tuned away.

## Crises (mandatory; within-window wealth reset)

Cells are **compounded net return / within-window MaxDD / average equity**.

| crisis | n | VolFair | VolCtrl | VolFair+DH | Δ return (DH−Ctrl) |
|---|---:|---|---|---|---:|
| 1973–74 | 24 | −39.02% / −41.20% / 85.70% | −35.27% / −37.51% / 78.06% | −24.89% / −26.99% / 63.37% | **+10.38pp** |
| 1987-08..12 | 5 | −18.33% / −24.24% / 69.94% | −16.40% / −22.04% / 63.71% | −14.50% / −19.83% / 57.51% | +1.91pp |
| 2000-03..2002-10 | 32 | −26.50% / −34.75% / 65.11% | −23.63% / −31.69% / 59.31% | −20.65% / −29.32% / 54.11% | +2.99pp |
| 2007-10..2009-03 | 18 | −21.48% / −24.94% / 53.37% | −19.51% / −22.78% / 48.61% | −14.57% / −18.22% / 37.67% | +4.94pp |
| 2020-02..04 | 3 | −14.16% / −14.56% / 52.43% | −12.91% / −13.29% / 47.76% | −14.16% / −14.56% / 52.43% | **−1.24pp** |
| 2022 | 12 | −12.72% / −16.32% / 53.50% | −11.47% / −14.88% / 48.73% | −10.60% / −13.43% / 44.54% | +0.87pp |

The 2020 exception is mechanical: `s=1` throughout 2020-02..04, so VolFair+DH applied no additional macro de-risking and was identical to VolFair; the uniformly lower control lost less. In the other five windows the DH overlay ran below the control's average exposure and lost less. These are arbitrary predeclared calendar windows, not event-precision tests.

## 10bp cost sensitivity

| leg | CAGR | Sharpe-like | MaxDD | avg equity |
|---|---:|---:|---:|---:|
| VolFair | 10.35% | 0.471 | −41.29% | 90.69% |
| VolCtrl | 9.90% | 0.471 | −37.59% | 82.61% |
| VolFair+DH | 10.52% | 0.525 | −30.24% | 82.61% |

Primary gaps at 10bp: **ΔSharpe +0.0543, ΔMaxDD +7.35pp, ΔCAGR +0.62pp**. The era pattern (E1 +0.120, E2 −0.021, E3 +0.075, E4 +0.030) and crisis pattern (5/6 non-negative; 2020 −1.25pp) are unchanged. Full 10bp era and crisis tables are in the results JSON; every metric was repeated at 10bp.

## Supplementary context (descriptive, no gate)

- Months with `s<1`: **314 / 714 (44.0%)**. `s` distribution: min 0.5000, p25 0.8222, median 1.0000, mean 0.9043, p75 1.0000, max 1.0000.
- Mean exposure by era (VolFair / VolCtrl / VolFair+DH): E1 96.74 / 88.12 / 82.92; E2 94.75 / 86.31 / 87.33; E3 84.70 / 77.15 / 78.10; E4 84.87 / 77.31 / 81.44.
- Maximum month-by-month weight difference VolFair+DH vs VolCtrl: **41.09pp** (the two paths are mean-matched, not path-matched).

## Integrity and reproducibility

| check | result |
|---|---|
| VolFair recomputed from official daily factors vs `w_fair` | max abs diff `4.97e-5` (< `1e-4`) |
| `w_vd = w_vol × s_macro` vs `vol_dh`, all 714 rows | max abs diff `7.17e-7` (6-decimal storage rounding; tolerance `2e-6`) |
| `s_macro = min(1, E_DH/0.45)` | max abs diff `3.33e-7` |
| `E_DH` vs frozen matrix equity | max abs diff `5.55e-17` |
| Panel equity/cash vs original frozen inputs | exact (`0`) |
| Stale months | exactly 3: 2025-10, 2025-11, 2026-01; `s=1`; `w_vd=w_vol` |
| Control cap | zero binding months; `0<k<1`; `mean(w_ctrl)=mean(w_vd)` within `1e-9` (CSV-rounded difference `−9.1e-8`) |
| Determinism | two engine runs byte-identical (JSON and monthly CSV) |
| Mechanics tests | 13/13 PASS |
| Mirror | all OK |
| Independent fresh-code audit | PASS; full 2bp/10bp max diff `9.1e-8`; era/crisis max diff `1.03e-7`; primary ΔMaxDD pp diff `1.0e-6pp` from 6-decimal rounding |

Era rows follow the parent #201 convention: contiguous slices of the full-path net returns with wealth reset at era start. Supplementary era turnover/switches therefore include the boundary step; era consistency uses Sharpe only.

## Limitations

- `k` uses full-sample information → descriptive hindsight; the control could not have been traded with this `k`.
- The primary contrast was selected after seeing #201; no pristine out-of-sample claim, no multiplicity correction, no p-values.
- Full-panel mean matching is not month-by-month, beta, volatility, or era-by-era matching. Residual era exposure differences are shown above (E1 −5.20pp, E2 +1.02pp, E3 +0.95pp, E4 +4.13pp for DH vs control) and may contribute to the era results. The 41.09pp maximum weight gap shows the paths differ materially.
- No alternative control, no parameter sweep, no threshold search, no rule variant. The only robustness run is the 10bp cost sensitivity.
- Nonlinear metrics (CAGR, MaxDD, Sharpe) do not decompose additively; the accounting differences above are side-by-side arithmetic, not causal attribution.
- Revised-vintage research only: French/CRSP revisions, TB3MS/1200 cash-proxy timing, CIZ-era daily file, monthly rounding MAE 0.047pp/mo. No contemporaneous PIT certificate (#189: full PIT not identifiable); #183/#188 data are already-studied revised vintages.
- VolFair and VolFair+DH share vehicle/panel mechanics: expanding calibration, monthly close, no intra-month trades, no taxes/capacity/market impact. The 2bp/10bp cost proxy is approximate.
- No live-trading, capacity, publication, or production claim. `production_authorized=false`.

## Files and reproduction

- `research/volfair_exposure_control_prereg.md` (frozen prereg)
- `research/volfair_exposure_control.mjs` (engine)
- `research/test_volfair_exposure_control.mjs` (13 mechanics/determinism checks)
- `research/volfair_exposure_control_mirror.mjs` (independent CSV mirror)
- `generated/classic-equity-baselines/volfair-exposure-control-results.json` (full metrics, eras, crises, 10bp, integrity, verdict)
- `generated/classic-equity-baselines/volfair-exposure-control-monthly.csv` (714 rows: weights, exposure, nets at 2bp/10bp)
- `generated/classic-equity-baselines/volfair-exposure-control-finding.md` (this file)

Reproduce from the repository root:

```
node indicators/macro-pressure-map/research/volfair_exposure_control.mjs
node indicators/macro-pressure-map/research/test_volfair_exposure_control.mjs
node indicators/macro-pressure-map/research/volfair_exposure_control_mirror.mjs
```

`production_authorized=false`.
