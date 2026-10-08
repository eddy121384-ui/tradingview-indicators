# Issue #78 — A9 Market Structure Dimension Audit Finding
## Do Compression/Expansion and Path-Efficiency/Chop survive as new Atlas dimensions?

Date: 2026-10-08. Child issue: **#181**. Discovery: **OOS3** (300 FIGIs).
OOS4: **not contacted** (frozen §11 condition not met). OOS5: untouched.
No Pine, no production code, no merge, PRs #80/#148 unmerged.

## Scope

This finding executes the frozen preregistration
`issue-78-market-structure-a9-preregistration.md` (A9-r2, commit
`df160addf8b363eba05c076a3372ab95f475d838`, file sha256
`65f0ab85f7c1c7f4143a713204a046170f6c96956757bd2aba22f1fbe93d87a3`).

A9 asked whether two candidate coordinates are **independent, causal,
interpretable market-structure dimensions** that measurably change the
distribution of **future path shape**:

- **D3 — Compression / Expansion**: `rv20` (primary, 20-day realised
  volatility of log returns) and `natr20` (robustness, gap-safe Wilder
  ATR20 / close), each through the frozen causal 252-prior percentile;
- **D4 — Path Efficiency / Chop**: `ER20` = |close[t] − close[t−20]| /
  Σ|Δclose| over the same 20 bars, through the same causal percentile.

The question was explicitly **not** "which state makes the most money". A
small HMM benchmark was included as a benchmark only.

An earlier compression study (`issue-78-compression-structure-stage1-finding.md`,
`...-stage1b-finding.md`) tested a *pre-breakout box* definition of compression
and found "narrower" unsupported. A9 deliberately does not reuse that geometry:
D3 is a continuous causal volatility-state percentile, and D4 is a continuous
path-quality percentile. A9 is a state-map question, not a breakout-event
question, and it did not reopen trigger/failed-break work.

## Preregistration integrity

All revisions were made **before any A9 forward-path statistic existed**:

| commit | content |
|---|---|
| `ee019f1` | A9-r1 preregistration |
| `df160ad` | A9-r2 preregistration (amendments a–h, all pre-outcome) |
| `951c93f` | analyzer + 19 causal proofs |
| `f196d0a` | analyzer/gate alignment with the frozen §7/§9/§10 text + 3 further proofs |
| `1c1ed15` | frozen HMM variances/scaler recorded for OOS4 transport |
| run code revision | `1c1ed15721765132d3cff1a537a857d6fa45f82d` |

The one prior A9 execution was aborted inside HMM fitting and wrote **no
artifact directory**; no A9 outcome table was ever produced before the freeze.
Amendments a–h are listed with reasons in §12 of the preregistration
(descriptive bins 0.30/0.70; D3 primary = rv20; eligibility unified on the A2
`base_ready` bar set; gap-safe ATR recursion; HMM K ∈ {2,3,4,5}; MFE/MAE
normalised by the frozen canonical `sym_atr`; added continuation/reversal/path
outcomes; numeric gates and an explicit HMM verdict ladder).

## Cohorts used (exact)

| role | cohort | use |
|---|---|---|
| discovery | OOS3 `artifacts/issue78_equity_proof_policy_oos3/snapshot/` | all A9 statistics |
| secondary replication | OOS4 `artifacts/issue78_factorized_classifier_oos4/snapshot/` | **not contacted** — no OOS3 KEEP candidate existed |
| untouched | OOS5 | never contacted |

OOS3 identity (recorded in `summary.json` and `bundle_hashes.json`):

- universe `issue119_bbg_oos2_universe_manifest.csv`, 300 FIGIs,
  `figi_set_sha256 = 017e9360402afa002dc0970088649e7c411c4f02333dec550f2432be3c0dd701`,
  byte sha256 `f6753c46788accf4a90e8d917fe2863a96e2c70006355ee5fdd1c326d4cb7712`;
- raw manifest `issue119_bbg_oos2_raw_manifest.json`, completed 300, 0
  failures, byte sha256 `8c836bf71b034a96a37fdaa865099d64f469616882e7fa2da9af60b24d02e09a`;
- raw bars 300 files, 1,533,352 rows, 1998-01-02…2026-08-31;
- eligible bar set: `base_ready` = 859,256 rows; **`atlas_ready` = 790,629 rows**
  (all four coordinates present, same bar set for D1…D4);
- 5 era blocks (2000-2004 … 2020-2026) and 3 sleeves (large / mid / small).

OOS3 is deliberately reused discovery under the 2026-10-05 amendment; it is
**not** fresh out-of-sample evidence. OOS4 was already contacted by A5 for
Core-2, so it was never pristine either — and it was not needed here.

## Frozen method (summary)

- **D1** `dir_structure` and **D2** `extension = |dir_velocity|` are reused by
  import from A1/A2/A4 (never modified).
- **Causal percentile** (A4 `causal_prior_pct`): count of strictly prior ready
  bars below + 0.5 × ties, divided by prior count, same stock, current bar
  excluded from the reference set but its own value is the measured quantity;
  NaN until 252 prior ready bars.
- **Descriptive bins** LOW ≤ 0.30 / MID / HIGH ≥ 0.70; Core-2 hard 0.20/0.80
  cells used for conditioning only.
- **Outcomes**: h1/h5/h10/h20 of aligned log return, absolute move, forward
  realised volatility, MFE, MAE (ATR-normalised, canonical `sym_atr`), plus
  continuation/reversal, forward 20-bar efficiency ratio, raw log MFE/MAE and
  sleeve-level cells. The h10 gate property set was frozen as
  `{fwd_10, lret_10, abs_10, fvol_10, mfe_10, mae_10, cont_10, rev_10, futer_20}`.
- **§7 separation rule**: per stock Δ = mean(HIGH) − mean(LOW) with ≥ 5 bars per
  side; Δ = equal-stock mean; separated iff |Δ| ≥ 0.10 × pooled sd, the sign is
  shared by ≥ 60 % of stocks, and the sign survives 1 % top/bottom trimming.
- **Gates**: G1 novelty (|mean Spearman| < 0.50 **and** mean MI < 0.10 nats vs
  both D1 and D2), G2 breadth, G3 temporal + sleeve stability, G4 ≥ 2
  separated properties at ALL scope, G5 Core-2 hard-cell conditioning, G6 OOS4
  direction (conditional). First match:
  INSUFFICIENT → REJECT_REDUNDANT → REJECT_UNSTABLE →
  KEEP_AS_ATLAS_DIMENSION → KEEP_AS_DESCRIPTIVE_ONLY.
  D3 is classified at the **weaker** of its primary and robustness levels.
- **HMM**: pooled diagonal-Gaussian EM in numpy (no hmmlearn), K ∈ {2,3,4,5}
  by training BIC, train `date < 2015-01-01`, per-stock per-run sequences
  (never across stocks or gaps), frozen scaler, Viterbi decode, no refit on
  evaluation, explicit reproducibility/persistence/drift rules and an explicit
  verdict ladder.

## Required tests

`test_issue78_market_structure_a9.py` — **24 tests passing**
(`research\.venv119\Scripts\python.exe -m pytest -q`), covering all 16 frozen
proofs plus gap-safe ATR, frozen-constant/prereg-token checks, a deterministic
real-data rebuild, the HMM diagnostic definitions, the HMM verdict ladder, the
dimension gate ladder, the OOS4 G6 rule and the frozen-model round trip.

All 16 required proofs are present: Core-2 reuse (1), causal self-exclusion (2),
D3 causality (3–4), ER exact fixture and frozen lookback (5–6), D4 causality
(7), append-future invariance for all four coordinates (8), stock-boundary
preservation (9), exact bin boundaries (10), strictly-forward outcomes (11),
exact MFE/MAE windows (12), HMM sequence boundaries (13), BIC without outcomes
(14), train/eval chronology (15), deterministic rebuild + vectorised-vs-scalar
EM equivalence (16).

## Result 1 — Novelty / redundancy (G1) is where both candidates fail

`redundancy_summary.csv`, ALL scope, equal-stock mean over 265 stocks
(`equal_stock_mean_mi_nats` is the frozen plug-in + Miller–Madow estimate on the
3×3 frozen bins, nats):

| candidate | vs | mean Spearman | mean \|Spearman\| | share \|ρ\| ≥ 0.50 | mean MI (nats) | G1 |
|---|---:|---:|---:|---:|---:|---|
| D3 `rv20` | D1 structure | −0.240 | 0.269 | 0.023 | **0.185** | **fail** |
| D3 `rv20` | D2 extension | +0.096 | 0.113 | 0.004 | **0.146** | **fail** |
| D3 `natr20` | D1 structure | −0.371 | 0.388 | 0.245 | **0.245** | **fail** |
| D3 `natr20` | D2 extension | +0.052 | 0.077 | 0.008 | **0.143** | **fail** |
| D4 `ER20` | D1 structure | +0.031 | 0.068 | 0.000 | 0.089 | pass |
| D4 `ER20` | D2 extension | **+0.607** | 0.613 | **0.977** | **0.346** | **fail** |

Two further frozen-pair diagnostics for context:

- D3 `rv20` vs D3 `natr20`: ρ = **+0.797**, MI = 0.679 — the "robustness"
  measure is nearly the same coordinate as the primary, so the anti-cherry-pick
  rule changes nothing (both reject).
- D3 vs D4 (the preregistered compression × efficiency pair): ρ = −0.061,
  MI = 0.146.

D3 is therefore **not** rejected because it tracks D1 or D2 *monotonically*
(|ρ| = 0.24 and 0.10); it is rejected because the frozen nonlinear-dependence
threshold is failed on both Core-2 axes. That is the preregistered rule and it
was applied without rescue.

## Result 2 — D3 Compression/Expansion: strong path-risk separation, rejected as an independent dimension

**Classification: `REJECT_REDUNDANT`** (D3 primary `rv20` and robustness
`natr20` both `REJECT_REDUNDANT`; headline = weaker = `REJECT_REDUNDANT`).

G1 is the **only** failed gate. Everything else passed:

- **G2 breadth**: 261 stocks with ≥ 5 bars in both extreme bins; LOW = 254,938
  bars (32.2 % of `atlas_ready`), HIGH = 223,628 bars (28.3 %) — pass.
- **G3 temporal + sleeve stability**: pass for `abs_10` (5/5 blocks, 3/3
  sleeves same sign), `fvol_10` (5/5, 3/3), `mfe_10` (5/5, 3/3), `mae_10`
  (4/5 blocks, 3/3 sleeves).
- **G4 path separation**: **11 properties** separated at ALL scope, including
  4 of the 9 frozen h10 gate properties (`abs_10`, `fvol_10`, `mae_10`,
  `mfe_10`); the remaining separated rows are h1/h5/h20 descriptive properties
  (never used for the gate).
- **G5 Core-2 conditioning**: 4 adequate hard cells (bull/bear × high/low) and
  4/4 same sign for `abs_10`, `fvol_10`, `mae_10`, `mfe_10` — pass.

D3 `rv20`, ALL scope, Δ = mean(HIGH) − mean(LOW), 261 stocks
(`separation_summary.csv`; `abs Δ/sd` is in units of the pooled sd of that
property, `sd` column of the same file):

| property | Δ | abs Δ / sd | stocks same sign |
|---|---:|---:|---:|
| `fvol_10` | +0.00879 | **0.642** | 93.1 % |
| `fvol_20` | +0.00823 | **0.643** | 91.1 % |
| `fvol_5` | +0.00919 | 0.616 | 94.6 % |
| `abs_1` | +0.00829 | 0.458 | 96.9 % |
| `abs_5` | +0.01531 | 0.402 | 95.0 % |
| `abs_10` | +0.01947 | 0.373 | 90.8 % |
| `abs_20` | +0.02510 | 0.346 | 88.8 % |
| `mfe_10` | −0.21021 | 0.142 | 80.1 % |
| `mfe_20` | −0.40126 | 0.202 | 81.9 % |
| `mae_10` | +0.19052 | 0.105 | 72.4 % |
| `mae_20` | +0.37975 | 0.139 | 79.9 % |
| `fwd_10` (not separated) | −0.00428 | 0.002 | 52.9 % |
| `lret_10` (not separated) | +0.00247 | 0.035 | 57.5 % |
| `cont_10` / `rev_10` (not separated) | −0.024 / +0.024 | 0.047 | 69.3 % |

Read together: the expansion state (HIGH) has **more two-sided movement**
(higher forward volatility, larger absolute moves, larger MAE) and **smaller
favourable excursion** (lower MFE), while the **direction/return** properties
are flat. The `natr20` robustness measure gives the same picture with larger
standardised gaps (`fvol_10` 0.806 sd, `abs_1` 0.575 sd, `mfe_20` −0.153 sd,
`mae_20` +0.178 sd, and additionally `lret_20` 0.133 sd, `cont_20`/`rev_20`
0.114 sd).

**Interpretation.** Compression/Expansion is a real, causal, interpretable
*path-risk shape* coordinate: it changes how much the market travels and how
much of that travel is adverse, without changing directional expectation. It is
not an orthogonal *dimension* of the frozen Core-2 map — its information is
already reachable from the structure/extension coordinates at the frozen
nonlinear-dependence threshold.

## Result 3 — D4 Path Efficiency/Chop: no future-path separation at all

**Classification: `REJECT_REDUNDANT`.** D4 fails G1 against D2
(ρ = +0.607, MI = 0.346 nats over 265 stocks) and passes G1 only against D1
(ρ = +0.031, MI = 0.089). Unlike D3, D4 also fails everything else:

- **G2 breadth**: pass (263 stocks, LOW 234,870 bars / HIGH 240,423 bars).
- **G3**: **false** — there is no separated property to test for temporal or
  sleeve stability (`G3_detail = {}`).
- **G4**: **false** — **zero** of the 9 gate properties is separated at ALL
  scope (`G4_separated_properties = []`).
- **G5**: **false** — no separated property to condition on.

D4 `ER20`, ALL scope, 263 stocks — the *largest* standardised gap in the whole
gate set is 0.088 sd (`abs_20`), i.e. every property sits far below the frozen
0.10 sd bar:

| property | Δ | abs Δ / sd | stocks same sign |
|---|---:|---:|---:|
| `abs_20` | −0.00636 | 0.088 | 65.8 % |
| `abs_10` | −0.00403 | 0.077 | 68.8 % |
| `fvol_20` | −0.00078 | 0.061 | 64.6 % |
| `mfe_10` | −0.05984 | 0.040 | 59.7 % |
| `fwd_10` | −0.01160 | 0.005 | 53.2 % |
| `lret_10` | −0.00067 | 0.009 | 49.0 % |

**Interpretation.** On this 300-stock daily cohort, "efficient travel vs
choppy travel" adds nothing measurable to the future-path distribution once the
frozen 0.10 sd / 60 % sign rule is applied, and it is largely a monotone
transform of the extension coordinate (ρ 0.61, 97.7 % of stocks with |ρ| ≥ 0.5).
D4 would be rejected by the separation gates alone; the redundancy rejection is
recorded first because that is the frozen order.

## Result 4 — Future-path distributions and the 2D maps (Q3)

The preregistered 2D maps (`map_summary.csv`, 3×3 descriptive bins) contain
four cross-pairs: structure × extension, structure × efficiency,
extension × compression, compression × efficiency, each over the 9 gate
properties × h10/h20. They are descriptive only and were **not** used to rescue
any candidate.

For example, `map_compression_x_efficiency_fwd_10` (ALL, h10) shows
equal-stock mean forward 10-bar return within a narrow band across all nine
cells (0.027 to 0.139 log units, all with ~52–56 % positive-fraction per
stock); the compression axis moves forward *volatility*, not expected return.
No cell was promoted to a rule, and no near-pass rescue exists in the frozen
gate ladder.

Stability of the D3 evidence across the frozen partitions is reported in
`separation_summary.csv` (block and sleeve rows) and in `gate_eval.json`
(`G3_detail`): direction is shared by 5/5 era blocks and 3/3 sleeves for the
main volatility properties, with `mae_10` at 4/5 blocks.

## Result 5 — HMM benchmark

Selection (training BIC, no outcomes used):

| K | BIC | train logL | n_params | iters |
|---|---:|---:|---:|---:|
| 2 | 2,731,663.8 | −1,365,712.9 | 19 | 21 |
| 3 | 2,578,849.6 | −1,289,224.4 | 32 | 39 |
| 4 | 2,378,053.6 | −1,188,732.5 | 47 | 49 |
| **5** | **2,327,865.6** | −1,163,532.0 | 64 | 69 |

K = 5 is selected by the frozen minimum-BIC rule.

Diagnostics on the 2015-01-01 split (`hmm_state_summary.csv`, 790,629 decoded
bars):

- 4 of 5 states are **reproducible** (training and eval occupancy ≥ 0.05, eval
  persistence ≥ 0.80, train↔eval centroid drift ≤ 1.0 sd); state 2 fails the
  persistence bar (0.741 < 0.80), its train↔eval centroid drift being 0.211
  (inside the 1.0 bar).
- Eval persistence per state: 0.919, 0.926, 0.741, 0.806, 0.888; mean decoded
  run length 3.9–13.4 bars.
- **C = 0.25**: only 1 of the 4 reproducible states keeps the same dominant
  Atlas bin from training to evaluation, below the frozen 2/3 convergence bar.
- **NMI(state; dominant Atlas bin) = 0.632** — high *information* overlap:
  decoded states carry about 63 % of the normalised mutual information with the
  explicit Atlas binning.
- No state pair passes the adds-structure test: `hmm_pair_separation.csv` is
  empty (no two reproducible states with the same dominant Atlas bin separate
  ≥ 2 gate properties with train/eval sign agreement).

**Verdict (frozen ladder): `HMM_UNSTABLE`** — "dominant-bin agreement 0.250,
NMI 0.632". Substantively: the latent model recovers a state partition that is
strongly *associated* with the explicit Atlas in-sample (NMI 0.63) but whose
identity is not reproducible across the frozen time split, and it adds no
stable separation beyond the explicit dimensions. The Atlas therefore stays
primary, and the HMM stays a benchmark — it is not promoted to the classifier
from this study.

## Decision answers

**Q1. Does Compression / Expansion survive as an independent dimension?**
No. `REJECT_REDUNDANT` (both `rv20` and `natr20`). It clears breadth, temporal,
sleeve, path-separation and Core-2-conditioning gates, but fails the frozen
novelty gate against **both** Core-2 axes (MI 0.185 / 0.146 nats for `rv20`;
0.245 / 0.143 for `natr20`).

**Q2. Does Path Efficiency / Chop survive as an independent dimension?**
No. `REJECT_REDUNDANT`. It is largely the extension coordinate (ρ = 0.607,
97.7 % of stocks ≥ 0.5) and it separately fails G3/G4/G5 with **zero**
separated properties at ALL scope.

**Q3. Are either meaningfully associated with different future path
distributions?**
D3 **yes, for path-risk shape only**: expansion states have higher forward
volatility (0.64 sd), larger absolute moves (0.35–0.46 sd), larger adverse
excursion (0.11–0.14 sd) and smaller favourable excursion (−0.14 to −0.20 sd),
stable across 5/5 era blocks and 3/3 sleeves, while directional outcomes stay
flat (≤ 0.04 sd). D4 **no**: nothing exceeds 0.088 sd for any gate property.

**Q4. Does HMM discover essentially the same structure?**
Essentially yes in information terms (NMI 0.632 with the dominant Atlas bin),
but not reproducibly: C = 0.25, so the mapping between latent states and Atlas
bins is not stable across the frozen split.

**Q5. Does HMM reveal a clearly additional, stable state structure that
explicit dimensions miss?**
No. No reproducible pair separates ≥ 2 gate properties with train/eval sign
agreement (`hmm_pair_separation.csv` empty). Verdict `HMM_UNSTABLE`.

**Q6. What dimensions should advance to the next Market Structure Atlas
build?** Neither D3 nor D4 as an orthogonal dimension. See Q7.

**Q7 (derived: A10 construction recommendation).** A10 should build on the
**frozen Core-2 atlas** and must not add D3/D4 as new orthogonal dimensions.
Two concrete, preregisterable directions are recorded for A10 — neither is
selected from these outcomes, and each needs its own fresh pre-outcome freeze:

1. **D3 as an explicit risk/conditioning overlay, not an axis.** The A9
   evidence shows a real, stable, causal *path-risk* coordinate. If A10 wants
   it inside the map, the honest construction is a separately labelled
   volatility/expansion gauge (or conditioning layer over Core-2 cells), with
   the orthogonality claim dropped. If A10 instead wants to test a genuinely
   orthogonal volatility axis, it must pre-specify a *residualised* construction
   (e.g. the volatility percentile residualised against D1/D2 before gating)
   and a novelty threshold calibrated to the 3×3 binning resolution, because
   the frozen 0.10-nat MI bar is met by any coordinate that meaningfully
   rearranges the 3×3 grid.
2. **D4 is not advanced.** Path efficiency should not consume A10 design space
   in this form; if path quality is revisited it should be posed as a different
   question (for example a *forward-path* property of a specific event), not as
   a fourth static state coordinate.

Also carried into A10 governance: an HMM must not become the production
classifier from this evidence; no post-outcome feature shopping; the trigger /
failed-break side branch (A6–A8) stays frozen; OOS5 stays untouched; any A10
dimension must clear the same pre-outcome novelty, breadth, temporal, sleeve
and conditioning bars; and A10 should state its claim as a distributional
path-shape claim, not an edge claim.

## Deliverables map

| # | deliverable | artifact |
|---|---|---|
| 1 | preregistration + SHA | `issue-78-market-structure-a9-preregistration.md` (`df160ad…`) |
| 2 | candidate definitions | preregistration §2–§4; `summary.json:frozen` |
| 3 | redundancy / independence tables | `redundancy_summary.csv`, `redundancy_sleeve_summary.csv`, `redundancy_per_stock.csv` |
| 4 | future-path distribution tables | `path_summary.csv`, `path_scope_summary.csv`, `separation_summary.csv`, `conditional_summary.csv` |
| 5 | conditional 2D map artifacts | `map_summary.csv`, `map_per_stock.csv` |
| 6 | temporal / sleeve robustness | block + sleeve rows in `separation_summary.csv`; `gate_eval.json:G3_detail` |
| 7 | HMM benchmark | `hmm_models.csv`, `hmm_centroids.json`, `hmm_transition.csv`, `hmm_state_summary.csv`, `hmm_path_summary.csv`, `hmm_pair_separation.csv`, `hmm_atlas_overlap.csv`, `hmm_verdict.json` |
| 8 | final finding | this document |
| 9 | keep/reject classification | `gate_eval.json:classification`, `summary.json:classification` |
| 10 | A10 recommendation | Q7 above |
| 11 | issue comments | #181 and #78 |

Bundle: `artifacts/issue78_market_structure_a9/` (28 files) + zip; the 6 large
per-stock tables and the run log are left on disk untracked per repo
convention; `bundle_hashes.json` records SHA-256 for all 27 non-hash files plus
the prereg commit and the frozen cohort SHAs. Key hashes:

- `summary.json` `9318cebc70dc6e43669b7131762e99e4afe847a55952d10a64428ad9a1989895`
- `gate_eval.json` `591328355bc1f8adf5736acffd09706e6901379e96e02e9fa6fe7ae0559eae2e`
- `hmm_verdict.json` `026f4e20070797e81a50e5a7f47157ba480a4fa8639efa9391386d582ff31f00`
- `hmm_centroids.json` `d7dea164dd78d626d1e4bf2d5d41fd4e91c28eb2ea232f3ccf8dd79a0085e002`

The conditional OOS4 secondary stage was implemented
(`analyze_issue78_market_structure_a9_oos4.py`, with the frozen G6 rule and a
frozen-parameter HMM transport) but **not executed**: frozen §11 makes it run
only if ≥ 1 of D3/D4 reaches KEEP on OOS3, which did not occur. OOS4 was not
contacted and `oos4_touched: false` is recorded in the bundle.

## Boundary statement

A9 claims only that on its frozen cohort: (a) neither candidate clears the
frozen independence gate; (b) Compression/Expansion is a stable causal
path-risk-shape coordinate that does not change directional expectation;
(c) Path-Efficiency/Chop adds no measurable future-path separation and is
largely redundant with extension; (d) the HMM benchmark is unstable and adds no
stable structure beyond the explicit dimensions. This is not fresh
out-of-sample evidence (OOS3 is reused discovery; OOS4 was already contacted by
A5), not a strategy, not an edge claim, and not production guidance. No Pine,
no production code, no merge, no OOS5.

Refs #78 #181 #175 #173 #170 #168 #162 #159 #156 #153 #148 #147 #138 #119 #80
