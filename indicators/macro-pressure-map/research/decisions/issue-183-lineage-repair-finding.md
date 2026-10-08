# Issue #183 — Cash-bias leverage bug: corrected replay of #178 / #180 / #182 — Finding

- Issue: [#183](https://github.com/eddy121384-ui/tradingview-indicators/issues/183)
- Branch: `research/issue-183-allocation-lineage-repair`
- Required starting HEAD: `57852112ce95913d48297b35f803a1583cbab314` (#182 final)
- Repair-spec commit (FIRST, BEFORE any corrected result):
  `149bf0bc994b523033f540f60c286df51dcb4866`
  (`research/issue-183-lineage-repair-spec.md`)
- Formal verdicts: #178 `state_weight_policy_candidate_revalidated`;
  #180 `tradable_implementation_revalidated`;
  #182 `v66_tactical_overlay_candidate_supported`;
  overall `allocation_lineage_repair_complete`
- `production_authorized=false`
- Research only. No optimizer ran, no grid search, no parameter retuning, no Pine
  changed, no parent artifact touched, no merge. Do not merge.

## 1. Bottom line

The known #178 defect is exactly one wrong column read. It is repaired by
consuming the frozen `weight-matrix.csv` as ground truth (and by reusing #178's
own availability rule for the early partial-history months), with **no frozen
rule changed**. The proof is now airtight in both directions: the corrected
engine plus the frozen 2dp largest-remainder serialization reproduces the frozen
matrix **cell-for-cell (0 mismatches over 9 states x 9 columns)**, the defective
engine produces **17 mismatched cells** (both leveraged states, nothing else),
and the defective engine **reproduces #178's frozen return series exactly over
all 721 months** (max abs diff 0), so the old-vs-corrected comparison is a
like-for-like counterfactual.

Corrected results are worse, and they are reported as worse. Nothing was
restored by retuning:

- **#178** max-history (1966-05→2026-08, n=721) policy CAGR falls
  **8.8475% → 8.7547% (−0.093pp/yr)**; vol **7.2089% → 7.0848%**; Sharpe-like
  **0.59130 → 0.58843**; MaxDD **improves 0.33pp** (−17.370% → −17.038%);
  annual turnover **35.04% → 33.85%**; avg Cash **27.34% → 27.73%**.
  Every applied month now has gross exposure exactly 100% (was up to 109%) and
  Cash inside the frozen [2,60] band. Verdict holds:
  `state_weight_policy_candidate_revalidated`.
- **#180** corrected research baseline A is 0.29pp lower (8.048% → 7.755%); the
  primary tradable legs B/C are **byte-identical to #180** (the tradable
  implementation was already matrix-based). All six preservation gauges pass,
  two of them materially better. Verdict: `tradable_implementation_revalidated`.
- **#182** primary tradable panel is **numerically identical to #182 in every
  leg and all seven gate values** (C−A CAGR −0.3110pp/yr, Sharpe +0.0113,
  MaxDD +1.321pp, incremental turnover 21.18pp/yr, worst segment −0.651pp,
  worst state −0.669pp; all seven gates pass) →  `v66_tactical_overlay_candidate_supported`. The corrected **research** panel
  moves from C−A −0.574pp/yr to **−0.272pp/yr**; all seven gates still pass.
- **Where the old performance came from:** the accidental leverage is
  **+0.0946pp/yr of arithmetic excess (0.0927pp of CAGR)**, i.e. **99.97% of the
  entire repair effect**; the frozen 2dp matrix serialization contributes the
  remaining **+0.00002pp/yr**. The defect supplied **1.07%** of the old headline
  CAGR.
- **Material change to prior interpretation:** #182's finding §3(c) speculated
  that the −0.31pp tradable C−A was "mostly a base-correction artifact" and that
  the pure overlay effect was ≈−0.01pp/yr. **That speculation is refuted.** The
  tradable A leg came from #180 `implementation-monthly.csv` (already
  matrix-based), so no base correction was ever mixed into the tradable panel:
  **−0.311pp/yr is the true pure tactical effect**. The "base effect" #182
  computed was the *research-panel* correction and it was incorrectly
  transplanted onto the tradable panel, where it double-counted a correction
  that never existed. The research panel's overlay harm was inflated by the bug
  by 0.30pp/yr and is corrected here.

## 2. The defect (verbatim, frozen)

`indicators/macro-pressure-map/research/issue_178_backtest.mjs`, `loadTiers()`
line 40:

- defective: `cb[c[0]] = c[1]` → column 1 = `opportunity_score`
- correct: `cb[c[0]] = c[2]` → column 2 = `cash_bias`

Effect: `CMIN_BIAS[cbias[state]]` resolves to `undefined`, so the cash-bias
minimum scaling never fires; Cash falls to the residual floored at
`CASH_MIN=2` while non-cash weights remain unscaled. Consequence: total gross
exposure **103%** in `G_Low/I_Low` and **109%** in `G_Neutral/I_Low`
(cash 2% instead of the frozen minimum 5%). All other seven states are identical
to the frozen matrix (100% gross). This violates #178's own no-leverage
acceptance criterion, which is why #178/#180/#182 need repair.

## 3. Repair method (matrix-as-truth, no rule change)

1. `generated/issue-178/weight-matrix.csv` (the frozen, correct artifact) is the
   authoritative state allocation. Its rows sum to 100.00% and its three frozen
   zero cells are exactly 0. When **every** sleeve has history — every #178
   full-universe month and every #180/#182 month — the frozen row is applied
   **verbatim**.
2. Sleeve availability is governed **per parent, because the two frozen parents
   deliberately differ** — and Issue #183 must not silently unify them:
   - **#178 policy stream (Phase A).** The frozen rule is
     `issue_178_backtest.mjs computeWeights(state, available, …)`: unavailable
     sleeves are dropped and Cash is re-derived under the frozen `CASH_MAX=60`
     (available non-cash is scaled up to fill the remainder). This is applied
     with the correctly-read `cash_bias`. Result: applied gross exposure exactly
     100% with Cash in **[5, 60]** in every applied month.
   - **#180/#182 implementation streams (Phases B and C).** The frozen rule is
     `issue_180_backtest.mjs` lines 97/111-120: take the frozen matrix row
     verbatim and hold the weight of any sleeve whose **tradable proxy** has no
     history yet in Cash, with **no** `CASH_MAX` re-derivation — a proxy that
     does not exist cannot be bought. The matrix-derived columns
     (`alloc_state`, `impl_pre`, `impl_post`, `turnover`) of the corrected #180
     stream are therefore **byte-identical to the frozen
     `generated/issue-180/implementation-monthly.csv` across all 721 max-history
     months (0 differing cells)**, and only the research A leg (the repaired
     quantity) differs. Consequence, inherited from the frozen parent: the
     implementation stream holds up to 100% Cash in the pre-proxy era (before
     ~1990 almost no tradable proxy exists). On #180's own strict panel
     (2006-06+) no proxy is missing, so the implementation Cash band is
     **[5, 48.5]**, inside [2,60] as well. This is exactly why #180 defines a
     strict panel, and it is preserved rather than "fixed".
3. A corrected component engine (reads `cash_bias`) is built solely to *verify*
   the matrix and to attribute the defect; it is validated by exact matrix
   reproduction (§6).
4. B-2 confirmation, the ±10 bands, the frozen zero cells, baseline,
   multipliers, sleeve/family caps, cash 2/60, cash-bias minimums, the #180
   proxy map, 2bp primary costs / execution timing, the V6.6 bytes and ±5pp
   mapping, and all seven #182 gate thresholds are reused unchanged.
5. Replay scope: Phase A = #178 policy (max-history 1966-05+ and full-universe
   2000-09+); Phase B = #180 tradable implementation (strict panel 2006-06+);
   Phase C = #182 A/B/C (research and primary tradable, 2007-01+).

## 4. Corrected #178 (Phase A) — max-history n=721

| metric | old (buggy) | corrected | delta |
|---|---|---|---|
| CAGR | 8.8475% | **8.7547%** | −0.0927pp |
| vol (ann) | 7.2089% | 7.0848% | −0.1241pp |
| Sharpe-like | 0.59130 | 0.58843 | −0.00287 |
| MaxDD | −17.3700% | **−17.0381%** | +0.3319pp |
| worst month | −7.8592% | −7.8592% | 0 |
| positive months | 66.158% | 66.158% | 0 |
| turnover (ann) | 35.040% | 33.853% | −1.187pp |
| avg Equity / Rates / Real / Cash | 41.63 / 25.26 / 6.59 / 27.34 | **41.02 / 24.76 / 6.49 / 27.73** | −0.60 / −0.51 / −0.10 / +0.39 |
| applied gross exposure | ≤ 109% | **exactly 100% in all 721 months** | — |

Benchmarks are untouched (identity check 0 errors over 721 months, benchmark
series byte-equal): neutral CAGR 8.3311% / MaxDD −24.05%, cash 4.5828%. The
corrected policy's return edge over static-neutral narrows from
**+0.52pp/yr to +0.42pp/yr**, while its MaxDD advantage (**+7.01pp**, −17.04% vs
−24.05%) and Sharpe advantage (0.588 vs 0.474) are unchanged in substance.
Full-universe (2000-09→2023-06, n=274, all sleeves available): CAGR
**5.9916% → 5.9342%** (−0.057pp), vol 7.3107% → 7.1194%, Sharpe 0.6273 → **0.6345** (improves), MaxDD −17.37% → −17.04%.

**Panel provenance (recorded in `performance-178.json`).** The max-history panel
is `1966-05-01 → 2026-08-01`: **721 applied months out of a 724-month calendar
span**. The three absent months (`2025-10`, `2025-11`, `2026-01`) are skipped
because their macro/market inputs are non-finite — inherited frozen-parent
behaviour (`issue_178_backtest.mjs`), not introduced here. Because the parents
annualise on `12/721` rather than the calendar span, absolute CAGR levels are
overstated by ~0.038pp/yr on **both** sides (calendar-time: old 8.8092%,
corrected 8.7169%); the repair delta is 0.0927pp on the applied basis and
0.0923pp on the calendar basis, i.e. **robust to the annualisation choice**
(`delta_robust_to_annualization: true`).

Era table (corrected − old; CAGR / vol / MaxDD):

| era | n | CAGR old → new (Δpp) | vol old → new | MaxDD old → new |
|---|---|---|---|---|
| E1 1966-03–1979-12 (first applied month 1966-05) | 164 | 7.455% → 7.455% (0.000) | 5.702% → 5.702% | −6.354% → −6.354% |
| E2 1980-01–2007-12 | 336 | 10.155% → 10.167% (**+0.012**) | 7.277% → 7.217% | −17.348% → −16.493% |
| E3 2008-01–2019-12 | 144 | 7.148% → 7.033% (−0.115) | 7.263% → 7.016% | −16.382% → −16.046% |
| E4 2020-01–2026-08 | 77 | 9.364% → 8.661% (**−0.703**) | 9.291% → 8.950% | −12.438% → −12.438% |

The repair is era-concentrated: **E4 (2020+) carries 0.70pp/yr of the old
leverage** because the 2020–21 inflation shock repeatedly placed the economy in
the two affected states *while all nine sleeves had live history* — precisely
when the bug could lever up. E1 is untouched (missing sleeves kept Cash above
the bias minimum, so the defective table lookup never mattered). E4 and E2 are
the only eras where the policy's drawdown is unchanged or better; E3's MaxDD
improves 0.34pp.

## 5. Where the old performance came from (leverage quantification)

Arithmetic panel-wide difference (old buggy series − corrected), n=721:
**+0.09462pp/yr** (geometric CAGR difference 0.09271pp/yr). Decomposition:

- **Accidental leverage / missing cash-bias scaling: +0.09459pp/yr — 99.97% of
  the entire repair effect.** Computed as the buggy engine minus the
  full-precision corrected engine (the two differ only in the two affected
  states; all other states' weights are byte-identical, so the decomposition is
  exact and non-overlapping).
- **Frozen-matrix 2dp largest-remainder serialization: +0.000024pp/yr — 0.03%.**
  The frozen matrix differs from the full-precision engine by ≤0.0052pp in 3
  `sp500` cells (`G_Low/I_Low` 23.5149→23.52, `G_Neutral/I_Low` 31.0748→31.08,
  `G_High/I_Neutral` 30.4348→30.44), which is immaterial at portfolio level.
- `leverage_share_of_old_cagr` = **1.07%** — the old 8.85% headline was
  overstated by about one part in ninety-four by unintended leverage.

Per affected state (contribution to the panel-wide arithmetic difference):

| state | n | buggy gross | corrected gross | cash 2% → | return diff | vol diff | MaxDD diff | contribution |
|---|---|---|---|---|---|---|---|---|
| `G_Low/I_Low` | 60 | 103% | 100% | 5% | +0.354pp/yr | +0.300pp | −0.565pp | **+0.0295pp/yr** |
| `G_Neutral/I_Low` | 120 | 109% | 100% | 5% | +0.391pp/yr | +0.473pp | −1.075pp | **+0.0652pp/yr** |
| total (both) | 180 | — | — | — | — | — | — | **+0.0946pp/yr** |

The affected-state contributions sum to the panel-wide figure to within
0.00002pp (the serialization residual in `G_High/I_Neutral`). Full corrected
state table: `state-level-178.csv`. The two affected states were genuinely
leveraged, genuinely more volatile, and genuinely deeper-drawing than the frozen
policy intends; the second alone supplied 0.065pp/yr of the old headline.

## 6. Bug proof (multiple independent directions)

1. Corrected engine (reads `cash_bias`) + frozen `roundLR` 2dp
   largest-remainder **== `weight-matrix.csv`, 0 mismatches** (9 x 9 cells).
2. Defective engine (reads `opportunity_score`) → **17 mismatched cells**, all
   in `G_Low/I_Low` (8 sleeves+cash) and `G_Neutral/I_Low` (9): the defect is
   fully localised; no third state is contaminated.
3. Defective engine **reproduces the frozen #178 `backtest-monthly.csv` return
   series exactly over 721/721 months** (max abs diff 0.0, fail-stop in the
   replay) — so "old" is genuinely #178 and not a re-derivation.
4. Corrected applied stream: gross exposure **exactly 100.000% in all 721
   months** (old: up to 109%), applied Cash inside **[2, 60]** in every month
   (old minimum 2%).
5. The affected states do occur inside the #182 tradable window
   (`G_Low/I_Low` 29 months, `G_Neutral/I_Low` 43 months) — yet the tradable
   A/B/C legs are unchanged, because #180's `impl_pre` consumed the matrix
   directly and never used the defective engine (independently cross-checked,
   0/232 mismatches).
6. **Lineage identity (Phase B):** all four matrix-derived columns of the
   corrected #180 implementation stream are byte-identical to the frozen #180
   file over all 721 months — 0 differing cells, fail-stop in the replay — and
   its research A leg equals the corrected structural stream exactly (0
   mismatches, 721/721). The repair therefore touches the tradable
   implementation in **no** way.
7. **Lineage identity (Phase C):** the corrected overlay A/B legs and the ±5pp
   signal reproduce frozen #182 exactly on both the research and the primary
   tradable panel (`research_mismatches=0`, `tradable_mismatches=0`, 232 months
   each) — and both overlay streams stay at or below 100% gross.

## 7. Corrected #180 (Phase B) — strict panel 2006-06→2026-08, n=240, no dropped months

Corrected research structural A: CAGR **7.755%**, vol 7.501%, Sharpe 0.819,
MaxDD −17.038%. Tradable pre-cost B: 8.166% / 7.659% / 0.854 / −16.440%.
Post-cost C: 8.158% / 7.659% / 0.853 / −16.453%.
(The old #180 A leg was 8.048%; the corrected baseline is 0.293pp lower. All
#180 months are fully available, so the matrix row applies verbatim and B/C are
byte-identical to the frozen #180 files.)

Six preservation gauges (all pass; #180 original value in brackets):

| gauge | threshold | corrected | #180 | pass |
|---|---|---|---|---|
| g1 abs CAGR gap A vs B | ≤ 1.0pp | **0.4034pp** | 0.1106pp | ✓ |
| g2 tracking error | ≤ 2.5%/yr | **1.0137%** | 1.0845% | ✓ |
| g3 MaxDD gap | ≥ −5pp | **+0.5851pp** | +0.9169pp | ✓ |
| g4 cost drag | ≤ 0.4%/yr | **0.006946%** | same | ✓ |
| g5 best/worst state rank | kept | **kept** | kept | ✓ |
| g6 defensive-state vol worse | ≤ 2pp | **0.4526pp** | same | ✓ |

Verdict `tradable_implementation_revalidated` (0 fails). Implementation lives
entirely at the sleeve-proxy layer, so the cash-bias repair moves only the
research baseline it is compared against — it does not change the tradable
implementation's own numbers.

## 8. Corrected #182 (Phase C) — primary tradable n=232, research n=232

Primary tradable A/B/C (identical to #182):
A 8.134% / 7.778% / Sharpe 0.853 / MaxDD −16.440%;
B 7.835% / 7.299% / 0.865 / −15.102%;
C 7.823% / 7.299% / 0.864 / −15.119%.

Seven frozen gates — corrected **primary** values (identical to #182):

| gate | value | threshold | pass |
|---|---|---|---|
| g1 CAGR gap C−A | **−0.3110pp** | ≥ −0.50 | ✓ |
| g2 Sharpe gap | **+0.01133** | ≥ −0.05 | ✓ |
| g3 MaxDD gap | **+1.3210pp** | ≥ −3.0 | ✓ |
| g4 incremental turnover | **21.180pp/yr** | ≤ 40 | ✓ |
| g5 top-1 episode share | moot (`benefit_positive=false`) | ≤ 0.60 | ✓ |
| g6 worst segment (2023+) | **−0.6507pp** | ≥ −1.0 | ✓ |
| g7 worst state (n≥12) | **−0.6688pp** | ≥ −3.0 | ✓ |

→ `v66_tactical_overlay_candidate_supported`.

Corrected research panel: A 7.700% / B 7.441% / C 7.429%; C−A **−0.2717pp/yr**
(vs #182's buggy −0.5744pp/yr), Sharpe gap +0.01675, MaxDD gap +1.4766pp,
worst segment −0.6196pp, worst state −0.6696pp — all seven gates pass,
`v66_tactical_overlay_candidate_supported`.

Materially, the repair **halves** the research-panel overlay drag and removes
the spurious tail it had created: months with |C−A| > 50bp fall from 11.2% to
3.0%, A-vs-C correlation rises 0.99607 → 0.99716, top-1 episode share rises
18.5% → 21.4%. The primary panel was never affected (frac>50bp 3.45%, corr
0.99713, top-1 21.3% — all unchanged).

## 9. Corrected diagnostics (primary tradable unless noted)

- By V6.6 class (mean contribution/month): risk-on **+2.81bp** (n=35), risk-off
  **−4.44bp** (n=163), neutral **−0.13bp** (n=34) — unchanged from #182.
  Benefit is not risk-on timing; it is smaller risk-off losses/drawdown.
- Alignment: aligned 83 mo −5.63bp/mo vs divergent 149 mo −1.10bp/mo — unchanged.
- Transitions (±3-month union, 36 events): inside −3.58bp/mo (n=172) vs outside
  −0.25bp/mo (n=60) — unchanged; no transition-timing edge.
- Segments: pre-2020 −0.339pp/yr (n=155), 2020–22 **+0.160pp/yr** (n=36),
  2023+ **−0.651pp/yr** (n=41) — unchanged.
- Research panel (changed): class contributions risk-on +2.63bp, risk-off
  −3.99bp, neutral −0.13bp; aligned −5.26bp vs divergent −0.85bp.
- Sensitivities (descriptive only, primary retained): S1 budget 10pp → C 7.465%
  (−0.358pp vs primary C); S2 lag state(m−2) → 7.810% (−0.013pp);
  S3 costs 10bp → 7.774% (−0.049pp). No promotion, no search.

## 10. What changed vs prior interpretation (material)

1. **#182 §3(c) "pure overlay effect ≈−0.01pp/yr (tradable)" is refuted.**
   The tradable A leg was matrix-based (#180 `implementation-monthly.csv`,
   `impl_pre`), so the tradable C−A is the pure overlay effect and equals
   **−0.311pp/yr**. #182 subtracted a research-panel base correction from a
   tradable-panel measurement.
2. **#182's research-panel overlay harm was inflated by the bug**:
   −0.574pp/yr → **−0.272pp/yr**. The direction is unchanged (the overlay still
   costs return), but the magnitude roughly halves and no longer carries a
   spurious tail.
3. **#182's "no leverage" acceptance was satisfied only by luck of lineage.**
   The primary tradable legs were matrix-based and therefore ≤100% gross, but the
   research A leg was the buggy 103%/109% series. Post-repair both panels are
   exactly 100%.
4. **#178's headline was overstated by 0.093pp/yr of accidental leverage** (1.07%
   of the old 8.85% CAGR); essentially all of the old-vs-corrected gap (99.97%)
   is that defect, with the frozen 2dp matrix contributing 0.00002pp/yr. The
   methodology conclusion in #178 (the frozen policy beats static-neutral on
   risk) survives; its return edge over neutral shrinks from +0.52 to +0.42pp/yr,
   and the repair is concentrated in 2020+ (E4 −0.70pp/yr).
5. **No verdict flips.** All three verdicts are unchanged, now on a correct
   lineage: still candidate-only, still below any production threshold.

## 11. Limitations

- Repaired *diagnosis* only: this issue fixes the lineage, not the policy. The
  policy remains a **candidate**; `production_authorized=false`.
- The repaired return series is 0.093pp/yr worse on the max-history panel (no
  worse than that), 0.057pp/yr worse on the full-universe panel. Per Issue #183
  this is reported, not restored. No parameter was searched to recover it.
- The corrected max-history path mixes two frozen representations by necessity:
  the 2dp matrix where all sleeves have history, and #178's pre-rounding
  availability rule where they do not. Their portfolio-level divergence is
  0.000024pp/yr, measured and reported.
- The 2020+ concentration of the repair effect (E4 −0.70pp/yr) means the old
  headline was most flattered in the most recent era — relevant to anyone who
  read #178 as "the frozen policy performed in the 2020s".
- The ±5pp V6.6 overlay still costs return (−0.31pp/yr primary) and is justified
  only by drawdown/Sharpe improvement; risk-off months dominate (163/232);
  `G_High/I_Low` remains n=3 and unreadable.
- Sleeve proxy imperfections inherited from #180 (QQQ/IEF/GLD/USO differ
  materially at sleeve level, absorbed at portfolio level); revised (not vintage)
  macro and market data; no costs beyond turnover.
- **Inherited measurement caveats (disclosed, not fixed; all present in the frozen
  parents, none affects the comparative repair claim):**
  1. *Dropped months / annualisation.* The parents silently skip months with
     non-finite inputs, so the max-history headline CAGR annualises on `12/721`
     over a 724-month span and is overstated by ~0.038pp/yr on both sides. The
     repair delta survives re-annualisation (0.0927pp applied vs 0.0923pp
     calendar; `performance-178.json:panel_provenance`).
  2. *B-2 across data gaps.* When confirmation spans a gap it compares the last
     two *available* months rather than adjacent calendar months (e.g. 2025-12
     confirmed from 2025-09 vs 2025-08). Frozen parent semantics; 3 months of 721
     are affected.
  3. *S3-immediate sensitivity residual.* Its CAGR agrees with an independent
     recomputation only to 3.7e-7 (n=722 vs n=721 agree exactly; S1/S2 exact) — an unimportant sensitivity-row artifact, 1.6e-5pp.
  4. `summary.inputs_sha256` keys are now recorded with the `generated/` prefix
     so they resolve to real workspace paths (they were bare `issue-*/` before
     the fix). The frozen #182 pin lookup still uses #182's own unprefixed keys,
     as published by #182.
  5. The test suite must not be run against a half-edited worktree: it compares
     on-disk artifacts with a fresh replay run, so editing the replay without
     regenerating produces a spurious failure. Both the author and the
     independent auditor observed this once; two consecutive runs of the same
     revision are byte-identical.
- **Pre-existing parent-test defects (disclosed, not fixed):** a full
  `python -m unittest discover` over the whole research tree runs **191 tests
  with 2 failures**, both in frozen parent test files that this issue does not
  touch (`git diff 5785211 HEAD` and `git status` are both empty for them):
  1. `test_issue_182_overlay.py::test_cash_floor_blocks` — its fixture builds a
     synthetic row summing to 88%, not 100% (`base_weights(cash=3.0)`).
  2. `test_issue_171_divergence_autopsy.py::test_greedy_window_ties_and_reuse` — its expected tie-break window list disagrees with the implementation
     (`('2000-06-01','2000-03-01')` vs `('2000-06-01','2000-09-01')`).
  Neither affects any result here: `issue_182_overlay.py` is separately
  exercised by the passing #182 Node mirror and by this issue's independent
  overlay reconstruction against `overlay-weights.csv` (max |diff| 0.0043, i.e.
  within the frozen file's own 2dp rounding), and #171's divergence layer
  supplies nothing to the #178/#180/#182 allocation lineage. Per Issue #183
  these frozen parent artifacts were left untouched.
- The `#182` era-stability file's *key names* differ from this issue's
  (`contrib` vs `contrib_C`, plus a new `cagr_B`); the shared values are
  identical for the primary tradable panel.

## 12. Artifacts (all `issue-183` unless noted)

- Specification (committed first): `issue-183-lineage-repair-spec.md`
- Replay: `issue_183_replay.mjs` (single self-contained matrix-as-truth
  Phase A/B/C replay, 2x in-process determinism check, 30 generated artifacts)
- Frozen primitives: `issue_183_repair.py`; tests `test_issue_183_repair.py`
  (13 py), `test_issue_183_mirror.mjs` (10), `test_issue_183_asserts.mjs`
  (58 independent assertions, does not import the replay)
- Generated: `manifest.json` (SHA manifest, parent-commit pins, policy
  constants, matrix-reproduction proof), `lineage-diff.json`,
  `summary.json` (incl. `verdict_basis_178`), `determinism.json`,
  `test-results-183.json`, `corrected-structural-monthly.csv` (with
  `applied_cash`), `old-vs-corrected-178.csv`, `performance-178.json`,
  `comparison-178.json`, `era-178.json`, `state-level-178.csv`,
  `leverage-isolation-178.json`, `turnover-178.json`, `sensitivity-178.json`,
  `corrected-implementation-monthly.csv`, `performance-180.json`,
  `preservation-180.json`, `sensitivity-180.json`, `state-implementation-183.csv`,
  `corrected-overlay-monthly.csv`, `performance-183-controlled-182.json`,
  `gates-182.json`, `v66-diagnostics-183.json`, `state-diagnostics-183.csv`,
  `transition-183.json`, `alignment-183.json`, `era-182-183.json`,
  `sensitivity-183.json`, plus the spec §6 deliverable-name aliases
  `state-diagnostics.csv`, `era-report.json`, `transition-alignment.json`
- This finding.

## 13. Tests / determinism / bugs

- `python -B -m unittest test_issue_183_repair` — 13 tests OK (CPython 3.12).
- `node test_issue_183_mirror.mjs` — 10 assertions ALL PASS.
- `node test_issue_183_asserts.mjs` — **58 assertions, 0 fail**. It
  re-implements the frozen policy independently and covers all 17 mandatory
  checks: matrix reproduction (corrected vs defective), rows=100%, gross exactly
  100% and applied Cash in [2,60] in every corrected month, defective-engine
  reproduction of the frozen #178 return series, no negatives, frozen zeros,
  B-2 unchanged, #180 proxy map unchanged, #180 cost identity
  (`post == pre − turnover x 2bp`), execution timing, V6.6 gzip+csv SHA, V6.6
  classification re-derivation, ±5pp budget vs frozen `overlay-weights.csv`,
  m-1 tactical timing (plus a look-ahead detector), the seven frozen #182
  thresholds and verdict mapping, parent-artifact integrity, determinism
  (byte-for-byte rerun), no Pine/production change, verdict-set and
  `production_authorized=false` checks.
- Parent regression: `test_issue_177_policy`, `test_issue_178_policy`,
  `test_issue_180_policy` all OK; Node mirrors #177/#178/#180/#182 ALL PASS; a
  full `unittest discover` over the whole research tree is 191 tests / 2
  failures, both the pre-existing frozen parent-test defects disclosed in §11.
- Determinism: the replay computes the whole result twice in-process
  (`determinism.json`: `byte_identical=true`, 30 artifacts) and the independent
  suite re-runs it as a child process and confirms **every** generated artifact
  is byte-identical.
- Parent integrity: all 37 pinned #177/#178/#180/#182 artifacts report
  `unmodified_since_parent=true`; V6.6 payload gzip SHA256
  `6087d7ec…beda2` and csv SHA256 `1d039235…0719` (388 rows) unchanged;
  `tactical-timeline.csv` git-blob SHA equals the #182 pin
  `e314bb85…ded62` (the worktree-byte SHA differs only by CRLF, as documented in
  `manifest.sha_convention`).
- **Bugs found and fixed during this repair:**
  1. The #178 cash-bias column read — the subject of this issue, **not** repaired
     in the frozen parent, worked around by matrix-as-truth and verified by exact
     matrix reproduction and exact reproduction of the frozen return series.
  2. **Two defects in this issue's own corrected replay**, both caught before
     publication and both now fixed:
     - **(a) An invented availability rule for the #178 policy stream.** The
       first version zeroed missing sleeves and **added their weight to Cash**
       with no `CASH_MAX` guard. That is not what the frozen #178 policy does — `issue_178_backtest.mjs computeWeights` skips unavailable sleeves and
       re-derives Cash with the frozen 60% cap, scaling available non-cash up to
       fill the remainder — and it drove applied Cash to 70.5% in early-history
       months, breaching the frozen `CASH_MAX=60`. Caught by the spec §2
       applied-month Cash assert and by the resulting collapse of the #178
       verdict to `..._with_limitations`. Fixed by reusing #178's own rule for
       partial-history months (§3.2). Impact: #178 max-history CAGR 8.6670% → 8.7547%, i.e. the true repair effect is 0.093pp/yr rather than the
       0.181pp/yr the defective version reported, and the leverage attribution
       becomes ~100% rather than ~50% of the total.
     - **(b) A wrongly unified availability rule across parents.** The same
       first version applied the #178 policy rule to the **#180/#182
       implementation** streams too. But `issue_180_backtest.mjs` lines
       97/111-120 document a deliberately different rule for tradable legs
       (matrix row verbatim; missing **proxy** weight → Cash; no `CASH_MAX`
       re-derivation). Fixed by giving the implementation streams their own
       frozen rule. Independent confirmation that (b) was a real defect: the
       auditor's cross-check found 52 turnover mismatches and diverging
       `impl_pre` values against the frozen #180 stream; after the fix all four
       matrix-derived columns match the frozen #180 file across **721/721
       months (0 differing cells)** and only the repaired research A leg differs.
     **Impact on headline results: none.** #180 and #182 results, all six
     preservation gauges and all seven gate values were unchanged by both fixes
     (those panels are fully proxy-available, so they always took the matrix row
     verbatim); only the #178 max-history numbers moved, via fix (a).
  3. A fixture error in `test_issue_183_repair.py::test_leverage` (the
     constructed row summed to 97, so no gross-exposure error was produced — now
     forced to 109%).
  4. A manifest ambiguity where the V6.6 classification worktree SHA (CRLF) sat
     next to a pinned git-blob SHA — now both are recorded, with
     `classification_matches_pin`.
- **Independent audit.** A separate agent audited the corrected replay against
  the frozen parents and re-derived every result from scratch (own engines, own
  B-2 timeline, own overlay, own cost/timing checks). It **verified**: the bug
  mechanism and its 17 mismatched cells; all frozen constants, gate thresholds
  and the absence of any optimizer; parent-artifact integrity (0 unmodified
  violations); panel/look-ahead/cost identities; the committed #178 corrected
  headline (`0.08754741451678028 / 0.07084768698676548 / −0.17038136359474054 /
  33.85277035521045`); the leverage decomposition (`0.09461641256530147 =
  0.09459275232860459 + 0.000023660237`, residual 1e-17); the #178 verdict basis
  and the overall verdict mapping; and cross-process determinism (all 31 on-disk
  hashes unchanged before/after a full rerun). It **refuted** one claim: the
  superseded revision's 0.0941pp/yr "2dp-matrix serialization" was a mislabel
  (true rounding effect ~3e-5pp/yr); that label is corrected in the final
  revision. It also **independently found** defect 2(b) (availability-rule
  unification) via 52 turnover mismatches against frozen #180. Its remaining
  findings — panel label, annualisation/dropped months, B-2 across gaps,
  `inputs_sha256` key prefix, hardcoded `semanticUnresolved`, and the
  spec-§4 basis missing its sensitivity operand — were all fixed in the final
  revision and are recorded above and in §11. Audit items it could not verify
  and that remain caveats: cross-process determinism in a *fresh* clone; the
  #174/#176 hardened return series, the DH composite states and the V6.6
  classification (all treated as frozen inputs); and whether #182 gate 5's
  substantive concentration test can ever bind (`top1_share` is `null` because
  the overlay's benefit is not positive, so the gate passes as moot under #182's
  own frozen expression).
- Firewall disclosure: after the first replay result, only *correctness and
  additive* changes were made — the two availability-rule fixes (2a/2b), the
  matrix-reproduction proof (§6), the defective-engine identity check (§6.3),
  the frozen-#180 implementation identity (§6.6), the full-precision
  fixed-engine series used for the leverage/serialization decomposition (§5),
  panel provenance (`performance-178.json`), the explicit `verdict_basis_178`
  record and its literal spec-§4 operands (including sensitivity stability and
  *no new* cap/cash violation), derived `semanticUnresolved`, the
  CRLF-vs-git-blob classification SHA fields, resolvable `inputs_sha256` keys,
  and the three spec §6 deliverable-name aliases. The bug statement, the replay
  scopes, the verdict mappings and every frozen rule/threshold were **not**
  altered. The only headline values that moved were the #178 max-history numbers
  affected by fix (2a); every #180/#182 value and all three verdicts were
  re-verified unchanged after each change.

## 14. Explicit confirmations

- `production_authorized=false`. No merge, `main` untouched, no production Pine
  changed (`git diff 5785211 -- '*.pine'` empty; no untracked Pine files).
- No optimizer, grid search, or parameter scan exists anywhere in the corrected
  replay; the only knobs are the three pre-registered descriptive sensitivities
  (S1 ±10pp, S2 lag-2, S3 10bp) plus #178's own frozen S1/S2/S3 variants.
- No frozen rule, benchmark, proxy, cost, timing, V6.6 byte, or gate threshold
  was modified. `Growth_DH`/`Inflation_DH`, the ±10 bands, the three frozen zero
  cells, the #178 baseline/multipliers/caps/cash rules/B-2, the #180 proxy map
  and costs, the #182 budget/mapping and the seven thresholds are all reused
  verbatim and SHA-pinned.
- History is read-only: every #177/#178/#180/#182 artifact is byte-identical to
  its parent commit; this issue adds only `issue-183` artifacts.
- Corrected results are worse on return. They are reported as worse. Nothing was
  tuned to restore the old numbers.
