# Issue #78 — A9 market-structure dimension audit preregistration

Date: 2026-10-08. **Status: frozen BEFORE any A9 forward-path outcome is
computed.** This document is A9-r2; it replaces A9-r1 (commit `ee019f1`).
Both revisions were written before any A9 outcome table existed: the only
prior A9 execution (`artifacts/issue78_market_structure_a9_run.log`,
2026-10-08 13:06) was aborted inside HMM fitting and wrote **no artifact
directory**; no A9 forward-path statistic was ever produced, printed, or
inspected. Every change vs r1 is listed with its reason in §12 and is a
pre-outcome correction, not a post-result search.

Discovery cohort: recovered **OOS3** only. **OOS4** is contacted ONLY in the
conditional secondary stage (§11), after this freeze, and only if at least
one candidate reaches KEEP on OOS3. No OOS5. No triggers, entries, sizing,
failed-break work, production, or Pine. PRs #80/#148 unmerged.

The question is NOT "which state makes the most money". It is: do
Compression/Expansion and Path-Efficiency/Chop describe genuinely different
market structures, and do those structures lead to meaningfully different
**future paths**?

## 0. Frozen Core-2 (reused by import, never modified)

D1 = `dir_structure` (frozen A1 MA-leg difference), D2 = `extension` =
`|dir_velocity|`, causal prior-only percentiles (A4), 252 minimum, hard
80/20 cells and 70/30 robustness. Core-2 is a conditioning input and the
redundancy baseline in A9 — never a gate, never redefined. `a4.causal_prior_pct`,
`a4.add_causal_ranks`, `a2.build_sd_frame`, `a2.add_within_stock_ranks`,
`a1._tail_stats` / `append_cell` / `aggregate_a1_cells` / `paired_deltas`,
`a1.BLOCKS` are imported verbatim.

## 1. Eligibility and the A9 coordinate bar set (frozen)

- `base_ready` = frozen A2 `ready`, unchanged: valid OHLC, price ≥ \$5,
  60-bar median dollar volume ≥ \$5M, ≥252 prior valid bars, date inside
  2000-01-03…2026-08-31, and all A2 redundancy scores finite.
- All four dimensions are evaluated on the same bar set. **A9 uses
  `base_ready` (not bare valid-OHLC) as the eligibility gate**, so D3/D4
  percentiles reference only bars that Core-2 itself admits.
- `atlas_ready` = A4 `causal_ready` AND `d3_ready` AND `d4_ready`. Every
  redundancy, path, map and HMM statistic in A9 is computed on
  `atlas_ready` bars only, so the four coordinates always coexist.

## 2. D3 — Compression / Expansion (frozen)

**Primary**: 20-day realised volatility of daily log returns

`rv20[t] = stdev(ddof=1)` of the 20 increments
`{log c[i] − log c[i−1] : i = t−19 … t}`; requires all 21 closes finite and
positive (equivalent to `t ≥ 20`).

**Robustness (exactly one, never chosen after outcomes)**: `natr20[t] =
wilder_atr20[t] / c[t]`, where

- true range uses the **last known close** carried across missing bars:
  `TR[t] = max(h[t]−l[t], |h[t]−c_prev|, |l[t]−c_prev|)` with `c_prev` the
  most recent finite close strictly before `t` (NaN at `t = 0` or when OHLC
  is missing);
- `ATR` is Wilder's RMA, `α = 1/20`, seeded by the SMA of the first 20
  finite TRs, with the running state **carried across missing bars** (a
  missing bar emits NaN and does not erase the state).

Both measures then get the identical inherited causal percentile:
`rank_c_d3[t] = pct(t) = (count_prior_strictly_less + 0.5·count_prior_equal)
/ N_prior`, same stock, prior `d3_meas_ready` observations only, current bar
excluded, future excluded, `N_prior ≥ 252`, with
`d3_meas_ready = base_ready & isfinite(measure)` and
`d3_ready = d3_meas_ready & isfinite(rank_c_d3)`. The robustness percentile
is `rank_c_d3_rob` on `natr20` with the same rule.

Low percentile = compression / quiet; high percentile = expansion /
volatile.

## 3. D4 — Path efficiency / chop (frozen)

`ER20[t] = |c[t] − c[t−20]| / Σ_{i=t−19…t} |c[i] − c[i−1]|` on raw close,
0…1; denominator 0 or any non-finite input → NaN. Exactly a 20-bar
lookback, no scan, ever. `d4_meas_ready = base_ready & isfinite(ER20)`,
`rank_c_d4` via the same causal percentile (252 prior), `d4_ready`.

## 4. Descriptive bins and conditional cells (frozen)

- Descriptive bins for D1…D4 (maps and HMM Atlas overlap):
  `LOW: rank ≤ 0.30`, `MID: 0.30 < rank < 0.70`, `HIGH: rank ≥ 0.70`.
  Not tunable from outcomes.
- Hard Core-2 conditioning cells keep the accepted 80/20 definition
  (`bull_low`: D1 ≥ .80 & D2 ≤ .20; `bull_high`: D1 ≥ .80 & D2 ≥ .80;
  `bear_low`: D1 ≤ .20 & D2 ≤ .20; `bear_high`: D1 ≤ .20 & D2 ≥ .80).
  They are used ONLY to condition D3/D4 tables, never as A9 states.

## 5. Q1 — is it actually a new dimension? (frozen tests)

Per stock over `atlas_ready` bars:

- Spearman rank correlation for the pairs `rv20×D1`, `rv20×D2`,
  `er20×D1`, `er20×D2`, `rv20×er20`, plus the robustness pairs
  `natr20×D1`, `natr20×D2`.
- Discrete mutual information: 10 rank-bins per variable (average-rank
  percentile, floor, clipped), natural log, Miller–Madow correction
  `+ (nonzero − 1)/(2n)`, per stock.
- Aggregation: equal-stock mean and median.
- Temporal stability of redundancy: the same Spearman re-computed per fixed
  block (2000-2004, 2005-2009, 2010-2014, 2015-2019, 2020-2026).
- Sleeve stability: the same statistics aggregated per sleeve
  (large / mid / small).

**Novelty thresholds (frozen)**: |equal-stock mean Spearman| < 0.50 against
BOTH D1 and D2, AND equal-stock mean MI < 0.10 nats against BOTH. The
headline uses the D3 primary (`rv20`); the robustness (`natr20`) must satisfy
the same thresholds or D3 is classified at the robustness level (§9).

## 6. Q2 — future-path outcomes (frozen, h ∈ {1, 5, 10, 20})

All outcomes are strictly post-observation. `scale[t] = sym_atr[t]` is the
frozen canonical ATR already used by A2 `fwd_h` (known at `t`).

1. `fwd_h[t] = (log c[t+h] − log c[t]) / scale[t]` — frozen A2 signed
   forward return in ATR units (reused by import).
2. `lret_h[t] = log c[t+h] − log c[t]` — raw log return.
3. `abs_h[t] = |lret_h[t]|` — absolute forward move.
4. `fvol_h[t] = stdev(ddof=1)` of the one-bar log returns over `t+1…t+h`
   (NaN for `h = 1`).
5. `mfe_h[t] = max_{i=1…h}(log c[t+i] − log c[t]) / scale[t]`.
6. `mae_h[t] = min_{i=1…h}(log c[t+i] − log c[t]) / scale[t]`.
   `mfe_raw_h` / `mae_raw_h` repeat 5/6 without normalisation (secondary).
7. `trail20[t] = sign(log c[t] − log c[t−20])` (known at `t`);
   `cont_h` = fraction of bars with `trail20 ≠ 0` and `lret_h ≠ 0` where
   `sign(lret_h) == trail20`; `rev_h` = the opposite indicator. Reported as
   per-cell means.
8. `futer20[t]` = ER of the forward path `c[t…t+20]` (20 strictly future
   one-bar steps, anchored at the known `c[t]`), reported at h = 20.

Cells are reported through the frozen A1 `_tail_stats` /
`aggregate_a1_cells` machinery (equal-stock aggregation, `MIN_CELL_BARS = 5`,
`MIN_AGG_STOCKS = 30`).

**Gate property set (frozen)**: the classification gates (§9) and the HMM
adds-structure test (§10) read the nine h10 properties
`{fwd_10, lret_10, abs_10, fvol_10, mfe_10, mae_10, cont_10, rev_10,
futer20}`. h1/h5/h20 are reported descriptively (horizon tables) and never
substituted into a gate.

## 7. Shared path-separation rule (frozen, used by gates and HMM)

For dimension X and property P (LOW vs HIGH bins, or state s vs state s′):

- per stock, `Δ_stock = mean_P(high) − mean_P(low)` over `atlas_ready`
  bars, requiring ≥5 bars in each side; ≥30 contributing stocks required;
- `Δ` = equal-stock mean of `Δ_stock`;
- `sd` = pooled per-bar stdev of P over the cohort's `atlas_ready` bars;
- **P is separated iff** `|Δ| ≥ 0.10·sd` AND `sign(Δ)` is shared by ≥60% of
  contributing stocks AND the sign is unchanged when the top and bottom 1%
  of P inside each bin are trimmed before recomputing `Δ_stock` (tail
  insensitivity: no single-cell tail artefact).

## 8. Descriptive maps (frozen)

2D fixed-bin tables on h10 facts (signed `fwd_10`, `lret_10`, `abs_10`,
`fvol_10`, `mfe_10`, `mae_10`, `cont_10`, `rev_10`, plus `futer20`):
Structure×Extension, Extension×Compression, Structure×Efficiency,
Compression×Efficiency. No 81-cell four-dimensional table is a headline.
Maps are descriptive; they are not threshold-tuned.

## 9. D3 / D4 classification gates (frozen; no near-pass rescue)

Exactly one outcome per candidate: `KEEP_AS_ATLAS_DIMENSION`,
`KEEP_AS_DESCRIPTIVE_ONLY`, `REJECT_REDUNDANT`, `REJECT_UNSTABLE`,
`INSUFFICIENT`. Gates, evaluated from the frozen artifact tables:

- **G1 novelty** — §5 thresholds (D3 primary AND robustness; D4 primary).
- **G2 breadth** — LOW and HIGH each contain ≥30 adequate stocks (≥5
  `atlas_ready` bars) and ≥5% of the cohort's `atlas_ready` bars.
- **G3 temporal + sleeve stability** — for ≥2 separated properties, `sign(Δ)`
  is identical in ≥4 of the 5 blocks with ≥30 contributing stocks and in
  every sleeve with ≥30 contributing stocks.
- **G4 path separation** — ≥2 of the nine h10 gate properties (§6) are
  separated by §7 at ALL scope.
- **G5 Core-2 conditioning** — for those separated properties, ≥2 of the 4
  hard Core-2 cells are adequate (≥30 contributing stocks) and the sign is
  identical in ≥⌈2/3⌉ of the adequate cells for ≥2 properties.
- **G6 OOS4 direction** — only in the conditional secondary stage (§11):
  recomputed on OOS4 with frozen definitions; ≥⌈2/3⌉ of the separated
  properties keep the same sign and no adequate OOS4 property reverses with
  `|Δ| ≥ 0.20·sd_OOS4`.

Rule (first matching wins):

1. `INSUFFICIENT` — measure not computable causally for the cohort, or G2
   impossible.
2. `REJECT_REDUNDANT` — G1 fails.
3. `REJECT_UNSTABLE` — G1 and G2 pass, G3 fails.
4. `KEEP_AS_ATLAS_DIMENSION` — G1–G5 pass and (G6 passes or G6 is
   technically unavailable and documented as such).
5. `KEEP_AS_DESCRIPTIVE_ONLY` — otherwise (novel and stable, but the
   future-path / conditioning evidence is not there).

D3 headline classification = its primary (`rv20`) classification; **if the
robustness measure (`natr20`) fails any gate the primary passes, D3 is
classified at the robustness level.** No rescue, no switch after seeing
results.

## 10. HMM benchmark (frozen; Atlas primary, HMM benchmark only)

- **Inputs**: the four causal coordinates only
  (`rank_c_struct`, `rank_c_ext`, `rank_c_d3`, `rank_c_d4`) at `atlas_ready`
  bars. No returns, no triggers, no failed-break variables, no
  outcome-driven feature selection.
- **Sequences**: one sequence per stock per contiguous `atlas_ready` run.
  Never a transition from the end of one stock to the start of another, and
  never across a gap.
- **Scaling**: pooled TRAINING mean/std (ddof = 0); the frozen scaler is
  applied unchanged to evaluation and OOS4.
- **Split (chronological)**: training = `date < 2015-01-01`; evaluation =
  `date ≥ 2015-01-01` (OOS3 only). No bar is in both.
- **Model**: pooled diagonal-Gaussian HMM, own numpy EM, K ∈ {2, 3, 4, 5},
  deterministic init (`default_rng(7)`, means at the 0.05…0.95 quantile grid
  of pooled training data, shared variances = pooled training variance),
  ≤200 iterations, relative log-likelihood tolerance 1e-6. No external HMM
  library (none installed).
- **K selection**: minimise `BIC = −2·logL_train + n_params·ln(N_train)`,
  `n_params = (K−1) + 2·K·D + K·(K−1)`, `D = 4`; exact ties → smaller K.
  Training data only; no outcome ever enters fitting or selection.
- **Decoding**: the selected model plus the frozen scaler decode all
  histories (train, eval, OOS4) without refit. Viterbi, per contiguous run.
- **Diagnostics reported**: BIC by K, train logL, state occupancy
  (share of decoded eval bars), persistence (diagonal of the empirical eval
  transition matrix from decoded paths inside runs), mean run length, model
  transition matrix `A` (train), raw-percentile feature centroids (train and
  eval), per-block occupancy and centroid drift, per-sleeve occupancy,
  largest single-state share, and Atlas overlap.
- **Reproducible state (R)**: eval occupancy ≥ 0.05, train occupancy ≥ 0.05,
  eval persistence ≥ 0.80, and `max_j |mu_eval[s,j] − mu_train[s,j]| ≤ 1.0`
  in training-standardised units.
- **Dominant Atlas bin**: per-state modal joint descriptive bin
  (D1,D2,D3,D4 ∈ {LOW,MID,HIGH}). `C` = share of R states whose train and
  eval dominant bins agree.
- **Atlas overlap**: `NMI(state;Atlas) = I(state; dominant joint bin) /
  H(state)`, plug-in, uncorrected, on eval bars.
- **Adds-structure test**: exists a pair `(s,s′) ∈ R` with the same dominant
  Atlas bin and ≥2 properties separated by §7 between the two states' bar
  sets, with `sign(Δ)` identical in the train-period and eval-period bars of
  those states.
- **Verdict (exactly one, first matching wins)**:
  1. `HMM_INSUFFICIENT` — selected K has <2 states with train occupancy
     ≥ 0.05, or one state holds > 0.95 of eval bars.
  2. `HMM_UNSTABLE` — `|R|/K < 2/3`.
  3. `HMM_ADDS_STABLE_STRUCTURE` — adds-structure test holds.
  4. `HMM_CONVERGES_WITH_ATLAS` — `C ≥ 2/3` and `NMI ≥ 0.25`.
  5. otherwise `HMM_UNSTABLE`.
- States are described by feature centroids only. No state may be named from
  returns; no HMM result may promote a dimension.

## 11. OOS4 conditional secondary stage (frozen)

Runs IFF ≥1 of D3/D4 is a KEEP candidate on OOS3 (i.e. the OOS3 gates would
award KEEP subject only to G6). Then, with definitions reuse by import and
no threshold/formula/K change: recompute D3/D4 redundancy, path separation,
temporal/sleeve stability and the 2D maps on the existing OOS4 snapshot
(300 FIGIs, zero overlap with OOS2/OOS3), evaluate G6, and transport the
frozen OOS3 HMM (frozen scaler + frozen model, no refit) to OOS4 as a
transport-only readout. If no KEEP candidate exists on OOS3, the OOS4 stage
is skipped by rule and recorded as such. OOS4 is a **secondary replication**
cohort, never pristine: it was already contacted by A5 for Core-2. A9 is
not a final untouched production validation.

## 12. Amendment log vs A9-r1 (all pre-outcome)

| # | r1 | r2 | reason |
|---|----|----|--------|
| a | descriptive bins 0.20/0.80 | 0.30/0.70 for D1–D4 maps/HMM overlap; hard 80/20 cells retained for conditioning only | Issue #181 explicitly prefers 0.30/0.70 descriptive bins; Core-2 hard cells untouched |
| b | D3 primary = NATR20, robustness = RV20 | D3 primary = **rv20**, robustness = **natr20** | Issue #181 prefers the simplest measure (20-day realised vol of log returns); both are reported and D3 is classified at the weaker level (anti-cherry-pick) |
| c | D3/D4 eligibility = bare valid OHLC | eligibility unified on frozen A2 `base_ready` (liquidity, price, event-range, prior-valid filters) | all four coordinates must live on the same bar set; otherwise D3/D4 "novelty" could merely reflect a different sample |
| d | Wilder ATR recursion used `atr[t−1]` unconditionally | running ATR state carried across missing bars | r1's recursion died permanently after the first interior NaN: AMZN/COST/JKHY lost every NATR value after the single 2001-09-11 NaN bar (658 of 6,936 bars survived) |
| e | HMM K ∈ {2..6}; scalar EM | K ∈ {2, 3, 4, 5}; mathematically equivalent vectorised EM (equivalence proven by test vs the scalar reference), split frozen at 2015-01-01, explicit numeric verdict rules | Issue #181 fixes the candidate set at 2–5; the scalar pass did not finish within a session |
| f | MFE/MAE normalised by ATR20 | normalised by the frozen canonical `sym_atr` (same normaliser as A2 `fwd_h`), with raw log-space MFE/MAE as secondary | avoids defining an outcome with the D3 measure itself |
| g | outcomes: sret/abs/fvol/mfe/mae | + `cont`, `rev`, `futer20`, raw MFE/MAE, sleeve-level cells | Issue #181 requires continuation, reversal and path-smoothness evidence |
| h | qualitative gates | numeric thresholds, first-match classification rule, explicit HMM verdict ladder, and an explicit h10 gate property set (h1/h5/h20 stay descriptive) | removes reviewer discretion ("no near-pass rescue") |

## 13. Cohort manifest (exact, frozen)

Discovery (OOS3), root
`indicators/wyckoff-regime-radar/research/artifacts/issue78_equity_proof_policy_oos3/snapshot/`:

- universe: `issue119_bbg_oos2_universe_manifest.csv`
  (300 FIGIs, `figi_set_sha256 = 017e9360402afa002dc0970088649e7c411c4f02333dec550f2432be3c0dd701`,
  byte sha256 `f6753c46788accf4a90e8d917fe2863a96e2c70006355ee5fdd1c326d4cb7712`)
- raw manifest: `issue119_bbg_oos2_raw_manifest.json` (completed 300, 0
  failures; byte sha256
  `8c836bf71b034a96a37fdaa865099d64f469616882e7fa2da9af60b24d02e09a`)
- raw bars: `raw/<figi>.csv.gz`, 300 files, 1,533,352 rows,
  1998-01-02…2026-08-31; 746,413 rows before 2015-01-01 and 786,939 from
  2015-01-01 (296/300 stocks have ≥252 post-2015 rows); the A2 event window
  starts 2000-01-03.
- sleeves: `large` / `mid` / `small` (3 sleeves).

Replication (OOS4, conditional stage only), root
`.../artifacts/issue78_factorized_classifier_oos4/snapshot/`: universe
`issue119_bbg_oos2_universe_manifest.csv`
(`figi_set_sha256 = b0c9423a6e3e5cbd61dcd17dc1a9c5a0fc50b8bc00286ba3a5b86f560209ca49`),
manifest `issue119_bbg_oos2_raw_manifest.json`, raw `raw/` (300 files,
1,549,692 rows), zero FIGI overlap with OOS2/OOS3.

Frozen classifier blob and the cohort SHAs are asserted at runtime exactly as
in A4/A5.

## 14. Required tests (frozen list, 16)

1. Core-2 import/reuse unchanged (module identity + call sites).
2. Core-2 causal percentile excludes the current bar.
3. D3 measurement uses only current/past data.
4. D3 percentile excludes current and future observations.
5. D4 ER exact on a deterministic fixture (straight line = 1, round trip = 0,
   flat = NaN).
6. D4 uses exactly the frozen 20-bar lookback (no scan).
7. D4 percentile excludes current and future observations.
8. Append-future invariance for all four dimensions.
9. Stock boundaries preserved (per-stock percentiles and HMM sequences).
10. 2D/1D bin assignments exact at the frozen boundaries.
11. Forward outcomes begin strictly after the state observation (h1…h20).
12. MFE/MAE windows exact.
13. HMM sequence boundaries prevent cross-stock transitions.
14. HMM K selection uses no future outcomes.
15. HMM train/test chronology exact (no shared bar).
16. Deterministic rebuild from the frozen data (bit-identical repeat) and
    vectorised-vs-scalar EM equivalence.

## 15. Artifacts and reproducibility

`artifacts/issue78_market_structure_a9/` (written by
`run_issue78_market_structure_a9_auto.py`, zipped alongside): cohort manifest,
coverage, redundancy per-stock/summary/per-block/per-sleeve, D3 path tables
(per-stock + summary + blocks + sleeves), D4 path tables, conditional-delta
tables, 2D map tables, temporal and sleeve robustness, D3/D4 gate evaluation,
HMM BIC table, HMM centroids, HMM transition matrices, HMM state/path
summary, HMM Atlas overlap, HMM verdict, `summary.json`, and a
`bundle_hashes.json` recording per-artifact SHA-256 plus the prereg commit
SHA and the frozen cohort SHAs. Determinism is tested, and the bundle is
committed.

## 16. Boundary statement

Even if a dimension is KEEP, A9 claims only that it is a **stable, novel,
causally-computable coordinate that conditionally changes the distribution of
future path shape**. A9 is not a strategy, not fresh out-of-sample evidence
(OOS3 is deliberately reused discovery under the 2026-10-05 amendment; OOS4
was already contacted by A5), and not production guidance. No Pine, no
production code, no merge, no OOS5.

Refs #78 #181 #175 #173 #170 #168 #162 #159 #156 #153 #148 #147 #138 #119 #80
