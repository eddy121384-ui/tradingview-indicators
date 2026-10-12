# Issue #184 — V6.6 overlay specificity — Preregistration (frozen)

- Issue: [#184](https://github.com/eddy121384-ui/tradingview-indicators/issues/184)
- Branch: `research/issue-184-v66-overlay-specificity`
- Base (pre-prereg) HEAD: `411835cc9e3a00d0f5d998df9fb2058d8a917e96` (#183 final)
- This prereg is the FIRST Issue #184 research commit on this branch.
- Status: PREREGISTRATION — frozen before any C/D control performance
  (return, CAGR/Sharpe/MaxDD, placebo rank, or B-vs-C gap) is computed or viewed.
- `outcome_data_loaded=false` (at prereg commit; no C/D return exists)
- `production_authorized=false`
- `revised_macro_history=true`
- `real_time_vintage_claim=false`

## 0. Ordering attestation (firewall)

The CURRENT GitHub Issue #184 body was read in full (authoritative).
Parent artifacts were read as frozen INPUTS only. Pre-prereg work was limited to
UNCONDITIONAL input verification + WEIGHTS-ONLY exposure arithmetic:

- parent file presence + parent commit hashes;
- frozen matrix / V6.6 timeline / B-2 timeline code reading;
- frozen #183 tradable panel date list (date column only; no return inspected
  for C/D, no C/D metric computed);
- B average-Equity exposure from WEIGHTS ONLY (structural matrix + overlayW +
  DH B-2 states + V6.6 signals; zero return files touched for the exposure calc).

No C/D monthly return, no C/D CAGR/vol/Sharpe/MaxDD, no placebo distribution,
no B-vs-C gap was computed or viewed. A/B frozen #183 values are quoted below
as parent inputs (already published), not as new computations.

Sequence (mandatory):

1. read Issue #184;
2. verify #183 lineage inputs (no C/D metrics);
3. compute/freeze B average exposure weights-only;
4. freeze §§1–12 below;
5. commit this prereg;
6. record prereg SHA;
7. ONLY THEN compute C/D control returns.

Any later parameter change requires a NEW issue.

## 1. Frozen parents (verified pre-prereg)

- #183 final `411835cc9e3a00d0f5d998df9fb2058d8a917e96` (required base; HEAD here).
- Parent finals: #177 `bc652bd615f2c5e9137050d01c666dbcd9528cd3`,
  #178 `10dcdce0ec86b0493d6df6b916b720eba46dcbe6`,
  #180 `ac251ad5149d9f550d82dfb34b3551fe01032367`,
  #182 `57852112ce95913d48297b35f803a1583cbab314`.
- Frozen bytes (worktree SHA256 per #183 manifest):
  - `generated/issue-178/weight-matrix.csv`
    `5d3778eddf6205ee996fcf0fa4560647f9982f8ce33c75924a16cb9e4eadd368`
  - `generated/issue-182/tactical-timeline.csv`
    `a7f60836fe91918f8549958b10d44a42915df145a56516d8633fa48a08022223`
  - V6.6 gzip `6087d7eceff168147b4db2e8688ce308dc12aa6b4187ff0c18f1d5e51e4beda2`,
    csv `1d03923503e7fe82a69b033897484c48aa646279ecf70164d090ed62a5a70719`
    (388 rows, 1994-05-31 → 2026-08-31).
  - `generated/issue-180/proxy-map.csv`
    `8909c300646162d7c071ea4e595343302d9489fd0312eb846030b170bc8091f7`
  - `generated/issue-180/proxy-monthly-returns.csv`
    `b11fbf8bb9fde8b5cb0bc45fd0ea2d8494511a458691639165c86328755a27e4`
  - `generated/issue-183/corrected-overlay-monthly.csv`
    `ed3da50b20d7a666fd33365e2b2beafc60b386cefa160bf21aa1c270974f1669`
- Frozen policy constants (verbatim #177/#178/#180/#182):
  ORDER sp500/nasdaq/russell/treasury2y/treasury10y/longtreasury/gold/oil;
  EQ = sp500/nasdaq/russell; sleeve caps 35/20/15/15/25/15/12/8;
  family caps equity 60 / rates 50 / real 15; CASH_MIN 2, CASH_MAX 60;
  bias minimums low 5 / neutral 10 / high 20; B-2 confirmation;
  proxies SPY/QQQ/IWM/SHY/IEF/TLT/GLD/USO + T-bill cash;
  primary cost 0.0002, alt 0.0010; V6.6 budget ±5pp; bands ±10.
- V6.6 rule (verbatim #182 §3): risk-on iff Growth High AND Inflation != High;
  risk-off iff Growth Low OR Inflation High; else neutral.
  Pro-rata non-zero Equity scaling; structural zeros preserved
  (Low-Low oil, Neutral-High russell, High-Low gold); timing V6.6 state(m-1).
- No parameter may change in this issue.

## 2. Structural baseline A and actual overlay B (frozen, exactly reproduced)

- A_184 (structural baseline) = corrected #178/#180 structural portfolio, no
  tactical overlay, B-2 timing, 100%-gross frozen matrix rows verbatim.
  Frozen source: `generated/issue-183/corrected-overlay-monthly.csv`,
  `panel=tradable`, column A (pre-cost structural). Post-cost A_post = A_pre
  minus structural turnover × 0.0002 (turnover from weights only, §6).
- B_184 (actual V6.6 overlay) = frozen corrected #182 post-cost overlay.
  Frozen source: same file, `panel=tradable`, column C (post-cost, already
  net of B-turnover × 0.0002). Column B (pre-cost overlay) reported as
  diagnostic only. B weights = overlayW(base, sig, 5) verbatim #182/#183.
- A/B month set, weights, timing, costs are NOT recomputed with new logic;
  the replay MUST assert byte-reproduction of frozen A_pre/B_pre/C(=B_post)
  vs #183 before building controls (0 mismatches tolerance 1e-12).
- Primary comparison uses POST-cost series for A, B, C (like-for-like).
  Pre-cost series reported as diagnostics; #182-style C−A cost-drag convention
  is preserved as a diagnostic, not the primary gate basis.

## 3. Evaluation panel (frozen)

- Tradable common panel = the 232 dates present in frozen
  `corrected-overlay-monthly.csv` with `panel=tradable`.
- First month `2007-02-01`, last month `2026-08-01`, N = 232.
- Research panel dates are IDENTICAL (232/232 match, verified date-column only).
- Signal counts on this panel: risk-on 35 (15.09%), risk-off 163 (70.26%),
  neutral 34 (14.66%). Counts preserved by every D shift.
- B-2 DH timeline total 721 months (1966-05 → 2026-08); panel is its
  2007-02+ honest V6.6/proxy-available subset with 0 additional drops
  (every proxy has history from 2006-06 strict panel; asserted 0 NaN in A/B).
- Missing-data rule (verbatim #178/#180/#182): a month is dropped from ALL
  legs if any HELD sleeve (weight != 0) lacks a return; structural zeros skip
  the lookup. Asserted 0 drops inside 2007-02 → 2026-08 tradable panel.
- Segments (frozen): pre-2020 (< 2020-01-01), 2020–2022
  (2020-01-01 → 2022-12-01), 2023+ (>= 2023-01-01).
- Transition windows: frozen ±3-month union around B-2-confirmed structural
  allocation-change months from `generated/issue-182/transition.json`
  (reused verbatim; never rebuilt). Inside-vs-outside reported.

## 4. B average-exposure freeze (weights-only, no returns used)

Method (frozen): over the §3 232-panel, with base = SW.get(dhState),
wB = overlayW(base, sig, 5), average total Equity = mean over months of
sum(sp500+nasdaq+russell) in wB; average Cash likewise. Return files were
NOT read for this calc; panel dates came from the frozen CSV date column only.

Frozen values (weights-only, full double precision; display rounded):

- A avg Equity `45.67784482758621` %, A avg Cash `19.09051724137931` %.
- B avg Equity `42.62612068965516` %, B avg Cash `22.14224137931035` %.
- B−A Equity delta `−3.051724137931045` pp (B carries less Equity).
- Matrix feasibility: per-state Equity min 22.50 (Low-High), max 60.00;
  Cash min 5.00, max 48.50. B Cash max 53.50 < 60; C Cash max ≈ 51.55 < 60;
  C Equity min ≈ 19.45 > 0. No cap/floor breach by construction.
- These four averages are FROZEN. The replay MUST recompute them weights-only
  and assert match within 1e-9 pp before building C.

## 5. C construction (exposure-matched constant de-risk, frozen, no V6.6 info)

- Constant reduction `d = 3.051724137931045` pp (Aeq − Beq, §4, full precision).
- For EVERY panel month, with base = frozen structural row wA:
  `cut = min(d, E)` where E = sum of non-zero Equity sleeves in wA;
  each non-zero Equity sleeve `wC[s] = wA[s] − d × wA[s]/E`;
  `wC[cash] = wA[cash] + (wA_E − wC_E)` (= +d up to floating error);
  all non-Equity sleeves unchanged; structural zeros stay exactly 0;
  no sleeve-cap re-derivation (reduction cannot breach caps);
  no CASH_MAX re-derivation (verbatim #182 risk-off behavior; §4 shows max
  ≈ 51.55 < 60 so the rule is inert here but frozen either way).
- C uses NO V6.6 information: same `d` every month regardless of signal,
  regime, return, date, or state. V6.6 timeline MUST NOT be read by the C
  builder (assert by code path: C builder imports only DH states + matrix).
- C returns: pre-cost from proxy returns with §6 missing-data rule;
  post-cost C_post = C_pre − turnover_C × 0.0002 (§6). Primary is post-cost.
- Exposure-match acceptance (frozen): `|avgEq(C) − avgEq(B)| ≤ 0.01` pp
  over the 232-panel (weights-only comparison). Fail = control invalid,
  reported, no silent fix.
- Turnover note (frozen expectation, not a gate input): C turnover equals
  structural turnover up to floating error (constant cancels month-to-month),
  so B turnover − C turnover ≈ tactical incremental ≈ 21pp/yr (parent value).

## 6. D construction (timing-placebo null, frozen, all non-zero shifts)

- Take the frozen 232-signal sequence in panel chronological order
  (35 risk-on / 163 risk-off / 34 neutral, §3).
- For k = 1..231 (ALL non-zero circular shifts, N−1 = 231 placebos):
  month i (0-based panel order) receives signal `S[(i − k) mod 232]`.
  (Direction frozen here; the set of 231 placebos is direction-invariant.)
- For each shifted signal timeline: weights = overlayW(base, shifted_sig, 5)
  verbatim; timing V6.6-state(m−1)→month m preserved structurally (the shift
  IS the placebo); budget ±5pp, pro-rata, zeros, caps/floor, costs, baseline,
  missing-data rule ALL identical to B. No weight/threshold alteration.
- Each D_k produces pre Gentoo? — pre-cost and post-cost series with §7 cost
  convention (post-cost primary). Every shift evaluated; none selected,
  none dropped, none optimized. Wrap-boundary run break is the ONLY
  structural difference vs B (accepted by design).
- Count check (frozen): 231 D series + B = 232 total alignments of the same
  multiset. Signal counts preserved in every shift by construction.

## 7. Costs, turnover, metrics (frozen, verbatim #183)

- Turnover (one-way, fraction units): for a final-applied weight stream W,
  `to(m) = 0.5 × Σ_s |W(m)[s] − W(m−1)[s]| / 100`, first panel month 0.
  Annualized = `sum(to)/n × 12`. Structural turnover uses wA stream;
  B/C/D turnover use their own final streams. Incremental = B − A(C) annualized.
- Costs: primary rate 0.0002 (2bp × turnover). Post-cost = pre-cost − to × rate.
  Same rate for A_post, B_post, C_post, every D_k post. S3-style 10bp alt-cost
  reported as diagnostic only (not a gate).
- Cash series for excess: T-bill accrual (research backbone cash), identical
  for research/tradable by construction.
- Per-series metrics (verbatim `metrics()` + turnover/extras):
  CAGR, ann vol (biased-sd × √12), Cash excess ann, Sharpe-like
  (ann mean excess / ann std excess), MaxDD on cumulative index, worst month,
  positive-month fraction, downside vol (√mean(min(r,0)²) × √12, #174),
  turnover ann, avg Equity/Cash weights.
- B-vs-C extras: CAGR diff, vol diff, MaxDD diff, worst-month diff,
  downside-vol diff, Sharpe-like diff, turnover diff, monthly return
  correlation (Pearson on post-cost series).
- Per-D_k metrics at minimum: CAGR, ann vol, Sharpe-like, MaxDD, worst month,
  downside vol (+ turnover/n for audit).
- Placebo ranks for actual B (post-cost tradable): percentile within 231 D
  for CAGR, Sharpe-like, MaxDD (higher/less-negative better), downside vol
  (lower better), worst month (less-negative better).
  Rank definition (frozen): higher-better metric → `100 × #(D ≤ B)/231`;
  lower-better (downside vol) → `100 × #(D ≥ B)/231`. Ties count for B.
  Also report median placebo, 10/25/75/90th percentiles, fraction of shifts
  B beats per metric.

## 8. Interpretation gates (frozen; thresholds never move post-result)

Higher-better unless noted. All diffs B−C or B−A on POST-cost tradable panel,
pp = percentage points (×100), Sharpe unitless, turnover pp/yr.

- S1 risk-benefit retained (all three must hold):
  `vol(B) < vol(A)` AND `MaxDD(B) > MaxDD(A)` AND `downside(B) < downside(A)`.
- S2 not materially worse than exposure-matched (both must hold):
  `Sharpe(B) − Sharpe(C) ≥ −0.02` AND `MaxDD(B) − MaxDD(C) ≥ −1.0pp`.
- S3 timing tail (strong): B rank ≥ 90 on AT LEAST TWO of
  {Sharpe-like, MaxDD, downside vol, worst month} (§7 rank def).
  Partial (for suggestive path): B rank ≥ 75 on at least one of the four.
- S4 turnover: `turnover(B) − turnover(C) ≤ 40pp/yr` (same scale as #182 G4).
- S5 no catastrophe (both must hold):
  min over {pre-2020, 2020–2022, 2023+} of ann (B−C) CAGR ≥ −1.0pp/yr AND
  min over DH states with n ≥ 12 of ann (B−C) ≥ −3.0pp/yr.

Verdict tree (exactly one; evaluated in order):

1. if S1 ∧ S2 ∧ S3 ∧ S4 ∧ S5 → `v66_overlay_specific_information_supported`
2. else if ¬S1 ∨ ¬S4 ∨ ¬S5 → `v66_overlay_not_supported_after_controls`
   (no risk benefit, or turnover/catastrophe failure).
   Exception: if ¬S5 alone with S1∧S2∧S3∧S4 holding, verdict is still
   `v66_overlay_not_supported_after_controls` (catastrophe dominates).
3. else if S1 ∧ S2 ∧ S4 ∧ S5 ∧ ¬S3
   → `v66_overlay_risk_control_supported_but_timing_not_specific`
   (risk benefit without timing specificity).
4. else if S1 ∧ S4 ∧ S5 ∧ (S2 ∨ partial-S3)
   → `v66_overlay_specificity_suggestive` (mixed).
5. else → `v66_overlay_not_supported_after_controls`.

CAGR superiority over A is NOT required (risk-control candidate).
Thresholds/percentiles MUST NOT move after results.

## 9. Conditional + state diagnostics (frozen, diagnostics only, no new rule)

- B-vs-C post-cost CAGR/vol/MaxDD/contribution/turnover by
  pre-2020 / 2020–2022 / 2023+ (§3 bounds).
- B-vs-C inside vs outside frozen transition windows (§3) + class frequencies.
- Per DH state for A/B/C post-cost: mean return, vol, downside vol, count.
  No optimization by state. No new rule from diagnostics in this issue.

## 10. Deliverables (all paths contain `issue-184`)

- `research/issue-184-v66-specificity-prereg.md` (this file)
- `research/issue_184_specificity.py` (frozen stdlib: overlayW/C/D/metrics/ranks/gates)
- `research/test_issue_184_specificity.py` (+ executed Node mirror test)
- `research/issue_184_build.mjs` (A/B reproduction + C/D streams + placebo dist)
- `research/generated/issue-184/manifest.json` (parent/hash/panel manifest)
- `research/generated/issue-184/exposure.json` (weights-only §4 recomputation)
- `research/generated/issue-184/control-monthly.csv` (A/B/C post+pre per month)
- `research/generated/issue-184/placebo-distribution.csv` (231 D_k metrics)
- `research/generated/issue-184/percentile-ranks.json`
- `research/generated/issue-184/comparison-ABC.json`
- `research/generated/issue-184/segment-diagnostics.json`
- `research/generated/issue-184/transition-diagnostics.json`
- `research/generated/issue-184/state-diagnostics.csv`
- `research/generated/issue-184/summary.json`
- `research/decisions/issue-184-v66-specificity-finding.md`
- Builder MUST pin parent SHAs, reproduce A/B exactly, assert §4 exposure
  within 1e-9 pre-C, evaluate all 231 shifts, never touch Pine/parents/main.

## 11. Firewall

After this prereg commit and the first C/D result, do NOT change: parents,
A/B definitions, panel, d, C/D construction, costs, timing, metrics, ranks,
gates, thresholds, verdict tree, segments, windows. Failure is REPORTED, never
repaired here. Forbidden: structural/V6.6/budget/timing edits, shift selection
or dropping, grids, optimization, leverage, shorts, proxy/cost changes,
duration/gold/oil tactical additions, equity rotations, pristine-OOS claims,
Pine changes, merging.

## 12. Product boundary

Research only. Verdict ∈ (`v66_overlay_specific_information_supported`,
`v66_overlay_risk_control_supported_but_timing_not_specific`,
`v66_overlay_specificity_suggestive`, `v66_overlay_not_supported_after_controls`).
Finding MUST contain `production_authorized=false`. Do not merge.
