# VolFair+DH adversarial falsification — preregistration (2026-10-22)

**Status:** planning only. No new placebo or leave-one-crisis-out P&L has been
computed, inspected, or written for this study. This commit contains the
preregistration only. Research only, `production_authorized=false`.

- Base: PR #206 head `4996371b5a26e4fb4b54db3e629a1ace323ace4d`
  (`research/volfair-dh-lag-sensitivity-prereg-20261021`).
- New independent branch:
  `research/volfair-dh-falsification-prereg-20261022`.
- Stacked on PR #206; no merge, no Pine, no modification of PR #201/#204/#206
  artifacts.
- `outcome_data_loaded=false` for this study at prereg time.
- Only the original **L=0 VolFair+DH** is studied. L=1..3, especially L=2, are
  excluded. No strategy variant, parameter, or trading rule is added.
- MPM, VolFair, the DH matrix, B-2, the 45% neutral anchor, and all trading
  timing remain unchanged.
- Execution is blocked pending review of this prereg. The Draft PR contains no
  performance output.

## 0. Question and ordering attestation

The original claim under test is:

> The frozen L=0 VolFair+DH macro de-risking factor supplies timing-specific
> defensive value beyond a VolFair-shaped control with the same average equity
> exposure, and that value is not merely an artifact of arbitrary calendar
> alignment or a few crisis windows.

Two separate falsification tests are frozen below:

- **Experiment A:** Is the original macro de-risking timing clearly better than
  arbitrary circular misalignments of the same signal?
- **Experiment B:** Is the historical relative contribution concentrated in a
  few crisis windows, and does it remain positive after removing them?

Existing #201/#204 results and monthly series are known inputs. This study is
therefore **retrospective and in-sample**, not pristine out-of-sample. The
purpose is adversarial diagnosis, not strategy improvement, parameter search,
or a new publication claim. Issue #188 is a closed methodological reference
only; its different portfolio results are not used as evidence here.

## 1. Frozen lineage and inputs (read-only)

| Item | Frozen value | Use |
|---|---|---|
| PR #201 head | `2ee8fc99158f8a566d98168f757f6b3f1af5a931` | parent panel/rule |
| PR #204 execution | `6497c5436c8e8fd84cca5f685b810092b4b9d2a8` | VolCtrl definition |
| PR #206 head / base | `4996371b5a26e4fb4b54db3e629a1ace323ace4d` | L=0 freeze |
| #201 monthly panel | `macro-incremental-monthly.csv` | source/freeze check |
| #204 monthly panel | `volfair-exposure-control-monthly.csv` | primary A/B input |
| #204 results | `volfair-exposure-control-results.json` | `k` and replication check |

Frozen hashes:

- `macro-incremental-monthly.csv`:
  `a6c70ef676a9dae126564d0bd749ce694d6c130e7fe1d32f8ee5bdfeedf045fb`
- `volfair-exposure-control-monthly.csv`:
  `56d740c61745f669ef5cc22f9ea0f04d2cbaa2e0da5a9740ad3ad457e28f7905`
- `volfair-exposure-control-results.json`:
  `3a81f777e309dcb2c8a1134a76320b32b9399186cc274238e0329d022cd56190`

Primary panel: **714 consecutive calendar months, 1967-03..2026-08**. The
three stale factor months (2025-10, 2025-11, 2026-01) carry `s=1` and remain part
of the frozen applied series. Macro history is revised-vintage, not PIT.

The #204 definition is reused unchanged:

```
w_vol[t]  = volfair[t]
w_vd[t]   = w_vol[t] * s_macro[t]
k         = mean_714(w_vd) / mean_714(w_vol)
w_ctrl[t] = min(1, k * w_vol[t])
```

`k = 0.9109091063518062`; the cap never binds. For each placebo, the control
is recomputed from the frozen 6-decimal weights with that placebo's own
full-panel mean exposure; the original `k` is not reused.

## 2. Experiment A — circular-shift placebo test

### 2.1 Frozen placebo set

Let `N = 714` and index panel months `t = 0..713`. The original signal is
`s_orig[t]`. For each allowed offset `k`:

```
s_k[t] = s_orig[(t - k) mod N]
```

The placebo set is **all** offsets:

```
k = 12, 13, ..., 702          (691 offsets)
```

Equivalently, all nonzero circular offsets whose circular distance from the
original position is at least 12 months: distances 12..357, with both directions
where distinct. Of the 713 non-original offsets, the 22 near-neighbor offsets
are excluded, leaving 691. The original alignment (`k=0`) and distances 1..11
are excluded. No offset is added, dropped, or selected after seeing any outcome.

Each shift preserves the complete 714-value signal sequence, its values,
frequency, runs, and persistence, including the three stale `s=1` months. The
only change is the circular alignment with returns, which creates one artificial
seam per placebo. The seam is not trimmed or moved.

### 2.2 Legs, controls, and costs

For each placebo offset `k`:

```
w_p[t]      = w_vol[t] * s_k[t]
k_p         = mean_714(w_p) / mean_714(w_vol)
w_ctrl_p[t] = min(1, k_p * w_vol[t])
```

Because `0 <= s_k <= 1`, `k_p <= 1`; the cap must not bind. By construction,
`mean(w_ctrl_p) = mean(w_p)`. If the cap binds for any placebo, stop and report
a block; do not adjust `k_p`.

Net monthly returns use the same #204 convention:

```
r_t = w[t] * equity[t] + (1 - w[t]) * cash[t] - fee * |w[t] - w[t-1]|
```

The first month's trade is free for every leg. `fee = 0.0002` is the primary
cost; `fee = 0.001` is the only sensitivity. `w_vol`, `equity`, `cash`, the
VolFair base, and the initial-deployment convention are identical across the
original and all placebos. No VolFair, macro, equity, or cash component is
re-estimated; only the predeclared control scalar `k_p` is recomputed.

The original leg is the frozen #204 `VolFair+DH` series and its frozen `VolCtrl`.
Its metrics are recomputed from the frozen weights and returns as an integrity
check, but the frozen net columns are the primary source.

### 2.3 Metrics and placebo ranks

For every original/placebo leg and its own control, compute full-panel:

- **CAGR**: `(prod_t(1+r_t))^(12/714) - 1`.
- **Sharpe-like**: `sqrt(12) * mean(r_t - cash_t) / sd(r_t)`, sample `sd`.
- **MaxDD**: minimum of `W_t / max_{u<=t}(W_u) - 1`, where
  `W_t = prod_{j<=t}(1+r_j)`; report in percentage points.

Define, for each metric `m`:

```
Delta_m = metric_m(placebo leg) - metric_m(own VolFair-shaped control)
```

Higher is better for all three; for MaxDD, "higher" means less negative.
The original `Delta_m` is computed the same way against the frozen #204 VolCtrl.

For each metric, the original is ranked against the 691 placebo `Delta_m`
values. Define:

```
percentile_m = 100 * (# placebo worse + 0.5 * # ties) / 691
rank_m       = 1 + # placebo strictly better          (1 = best; ties share)
```

"Worse" means lower Delta for Sharpe/CAGR and more negative Delta for MaxDD.
Report the original Delta, placebo median, 5th/95th percentiles, min/max,
percentile, and rank for all three metrics. The full 691-value distribution is
reported; no best or worst placebo is selected.

At 10bp, repeat the entire placebo set and report the same ranks. The verdict
uses 2bp. If the original Delta's sign reverses at 10bp, disclose it; do not
retune or reclassify.

### 2.4 Frozen A verdict

These are precommitted economic heuristics, not statistical tests:

- **Support** — `Sharpe percentile >= 95` AND `MaxDD percentile >= 90` AND
  `CAGR percentile >= 75`.
- **Mixed** — not support, but at least two of:
  `Sharpe >= 75`, `MaxDD >= 75`, `CAGR >= 75`.
- **Weaken** — all remaining cases (fewer than two metrics at the 75th
  percentile).

Labels: `timing_specificity_supported_descriptively`,
`timing_specificity_mixed`, `timing_specificity_not_supported_descriptively`.
The support bar deliberately requires top-5% Sharpe, top-10% drawdown, and
top-quartile CAGR. Percentiles are empirical ranks, **not p-values**, and no
multiple-testing or iid claim is made.

### 2.5 A limitations (disclosed in every output)

- **Circular seam:** each placebo contains one artificial wrap; no trimming or
  seam-window exclusion is allowed.
- **Nonstationarity:** the 714-month history spans different regimes; placebo
  offsets are not iid draws and do not form a sampling distribution.
- **In-sample/retrospective:** #201/#204 outcomes are known; this is not OOS,
  not a live test, and not causal evidence.
- **Stale months:** the three stale `s=1` months are shifted as part of the
  frozen applied sequence; they are not re-estimated or specially handled.
- **Revised macro history:** inputs are not vintage PIT; data revision bias
  remains.
- No p-value, no significance claim, no "best placebo" claim.

## 3. Experiment B — crisis dependence

### 3.1 Fixed series and contribution metric

Use the frozen #204 monthly net series unchanged:

- `r_vd[t] = voldh_net_2bp[t]`
- `r_ctrl[t] = volctrl_net_2bp[t]`
- 10bp sensitivity uses `voldh_net_10bp` and `volctrl_net_10bp`.

No weights, costs, volatility scaling, or exposure-matching coefficient are
recomputed after excluding months. The full-sample #204 `VolCtrl` remains fixed.

Monthly relative log-return contribution:

```
c_t = ln(1 + r_vd[t]) - ln(1 + r_ctrl[t])
```

This is an additive monthly contribution, not a compounded return. No remaining
months are stitched into a continuous tradable wealth path.

### 3.2 Frozen crisis windows

Inclusive calendar windows, exactly as frozen in #204:

| Window | Dates | Months |
|---|---|---:|
| 1973–74 | 1973-01..1974-12 | 24 |
| 1987 | 1987-08..1987-12 | 5 |
| 2000–02 | 2000-03..2002-10 | 32 |
| 2007–09 | 2007-10..2009-03 | 18 |
| 2020 | 2020-02..2020-04 | 3 |
| 2022 | 2022-01..2022-12 | 12 |

The six windows are disjoint. Assert this and stop if it fails.

- **Leave-one-crisis-out:** remove each window separately.
- **Three-major-crisis exclusion (primary B falsification):** remove the union
  of 1973–74, 2000–02, and 2007–09 (74 months; 640 remaining).
- **All-six diagnostic:** remove the union of all six windows (94 months; 620
  remaining). This is reported as a concentration diagnostic, not an additional
  verdict gate.

### 3.3 Estimands and reporting

For the full sample and each exclusion variant, report:

```
n_used
S       = sum_t c_t                    (log points)
mean_bp = 10,000 * S / n_used          (bp per month)
hit     = #(c_t > 0) / n_used
```

Also report each window's `S_c` and, when `S_all > 0`, its share
`share_c = S_c / S_all`. Rank the six windows by `S_c` and by `share_c`; report
all six, not only the largest. For each leave-one-out, report `S_-c` and the
difference from `S_all`. Report the triple `S_-3` and the all-six `S_out`.

At 10bp, repeat all sums, means, hit rates, shares, and ranks. The verdict uses
2bp. Disclose any sign reversal at 10bp.

Do **not** compute CAGR, MaxDD, Sharpe, annualized return, or any compounded
path after exclusion. Do not stitch noncontiguous months. Do not exponentiate
the summed log contributions into a synthetic wealth curve. No p-values or
significance claims.

### 3.4 Frozen B verdict

Let:

- `S_all` = full-sample contribution.
- `S_-c` = contribution after removing crisis window `c` (six values).
- `S_-3` = contribution after removing the three major crises.
- `N_neg` = number of the six `S_-c` values that are `<= 0`.
- `share_c` = `S_c / S_all` when `S_all > 0`; otherwise undefined.
- `dominant` = window with the largest `share_c`; `S_-dom` its leave-one-out sum.

Evaluate exactly one label, in this order:

1. **Weaken** (`crisis_dependence_dominant`) if any of:
   - `S_all <= 0`; or
   - `S_-3 <= 0`; or
   - `N_neg >= 4`; or
   - `S_all > 0`, `share_dominant >= 0.50`, and `S_-dom <= 0`.
2. **Support** (`crisis_dependence_not_dominant`) if:
   - `S_all > 0`, `N_neg == 0`, and `S_-3 > 0`.
3. **Mixed** (`crisis_dependence_partial`) otherwise.

The triple exclusion is the primary falsification. `S_out` is reported to
quantify whether positive contribution exists outside all six windows; it is
not a verdict gate, because a defensive strategy may legitimately earn relative
return mainly in crises. A single crisis contributing at least half of `S_all`
is called out as concentrated even if its leave-one-out sum remains positive.

### 3.5 B limitations (disclosed in every output)

- The six windows are predeclared but arbitrary; they are not event-precision
  tests.
- 1987 (5 months) and 2020 (3 months) are small samples; report `n` everywhere.
- Removing months breaks continuity; the sums are **not** a tradable path and
  must not be converted to CAGR or MaxDD.
- The control is a full-sample, hindsight mean-exposure counterfactual; it is
  not reweighted or re-matched after exclusions.
- Macro history is revised-vintage, not PIT; no causal claim is made.
- No p-values, no bootstrap significance, no "crisis-proof" claim.

## 4. Combined interpretation

A and B test different necessary conditions of the same original claim. Do not
average the two labels or use one to rescue the other. Report both component
labels, then:

- **Overall support** only if A = support AND B = support.
- **Overall weaken** if A = weaken OR B = weaken.
- **Overall mixed** otherwise.

The combined labels are descriptive summaries of the frozen evidence, not proof
of skill, causality, live tradability, or publication merit.

## 5. Execution discipline, integrity checks, and stop conditions

This round is preregistration only. The next round, after external review, may
implement the deterministic engine and produce results. It must not change any
definition above after seeing outcomes; a definition change requires a new
preregistration.

Required checks before any result is accepted:

- Panel has exactly 714 rows, 1967-03..2026-08, and matches the frozen hash.
- Original #204 `k`, mean exposures, and full-panel 2bp/10bp metrics replicate:
  `k` and mean exposures within `1e-12`; monthly net returns within `1e-10`;
  full-panel metrics within `1e-7` (absolute, decimal units).
- All 691 placebo offsets are generated exactly; no offset is missing or added.
- Every placebo's `w_p <= w_vol` and `k_p <= 1`; no control cap binds.
- The six crisis windows are disjoint and contain the frozen month counts.
- The triple and all-six unions contain 74 and 94 months respectively.
- Deterministic reruns are byte-identical for the generated tables/JSON.
- No L>0 series, no alternative control, no parameter search, no best-placebo
  selection, no post-hoc window editing.

If any check fails: stop, report the failure, and do not silently repair or
redefine the study. No Pine changes, no merge, no production authorization.
`production_authorized=false`.

## 6. Planned execution artifacts (not created this round)

- `research/volfair_dh_falsification.mjs` — deterministic A/B engine.
- `research/test_volfair_dh_falsification.mjs` — synthetic mechanics tests.
- `generated/classic-equity-baselines/volfair-dh-falsification-placebo.csv`
- `generated/classic-equity-baselines/volfair-dh-falsification-crisis.csv`
- `generated/classic-equity-baselines/volfair-dh-falsification-results.json`
- `generated/classic-equity-baselines/volfair-dh-falsification-finding.md`

No performance output is produced in this round.
