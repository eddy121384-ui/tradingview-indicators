# Issue #182 — V6.6 tactical overlay — Preregistration (frozen)

- Issue: [#182](https://github.com/eddy121384-ui/tradingview-indicators/issues/182)
- Branch: `research/issue-182-v66-tactical-overlay`
- Base (pre-prereg) HEAD: `ac251ad5149d9f550d82dfb34b3551fe01032367` (#180 final)
- This prereg is the FIRST Issue #182 research commit on this branch.
- Status: PREREGISTRATION — frozen before any tactical-overlay portfolio
  performance (CAGR/Sharpe/MaxDD or any leg) is computed or viewed.
- `outcome_data_loaded=false` (at prereg commit; no overlay return exists)
- `production_authorized=false`
- `revised_macro_history=true`
- `real_time_vintage_claim=false`

## 0. Non-contamination attestation (ordering mandate)

The CURRENT GitHub Issue #182 body was read in full via webfetch
(authoritative; no cached copy). Parent artifacts (#178 weights/policy/backtest
mechanics, #180 proxies/costs/timing, #160/#171/#133 lineage notes) were read
as frozen INPUTS only. Pre-prereg work was limited to UNCONDITIONAL input
verification: parent file presence, #178 timing-code reading, exact-V6.6 byte
extraction with dual-SHA verification (both match; no metric computed).
No A/B/C return, no overlay performance, no state-conditioned overlay result
was computed or viewed.

Sequence (mandatory):

1. read Issue #182;
2. read frozen parent artifacts as inputs;
3. verify parent hashes + exact-V6.6 bytes (no metrics);
4. freeze §§1–12 below;
5. commit this prereg;
6. record prereg SHA;
7. ONLY THEN generate overlay weights and performance.

Any later parameter change requires a NEW issue.

## 1. Frozen parents (verified pre-prereg, pinned by SHA at build)

- #178 final `10dcdce0`: weight matrix (9 states × 9 sleeves, rows sum 100.00;
  zeros: Low-Low Oil, Neutral-High Russell, High-Low Gold), neutral baseline
  (25/12/8/8/14/8/6/4/15), multipliers (0/0.5/1.0/1.75), sleeve caps
  (35/20/15/15/25/15/12/8), family caps (60/50/15), Cash min 2/max 60 with
  bias minimums low 5/neutral 10/high 20, 2dp largest-remainder normalization,
  B-2 confirmation (allocation for month m from DH states through m−1;
  hold on unconfirmed months), turnover = 0.5×Σ|Δtarget| (fraction units).
- #180 final `ac251ad0`: ETF proxies (SPY/QQQ-labeled-Nasdaq-100/IWM/SHY/IEF/
  TLT/GLD/USO + identical T-bill cash), primary cost = turnover×0.0002 (2bp),
  alternate cost 0.0010, month-end-close execution, strict panel 2006-06+.
- Deep-History: ±10 bands, 9 states, frozen episodes/eras. No trajectory.
  No V6.6 in structural legs. #169 recovery trigger NOT used (failed).

## 2. Exact V6.6 input (frozen bytes, verified pre-prereg)

- Source: `origin/research/issue-133-state-trajectory:` 
  `indicators/macro-pressure-map/research/data/issue-133-exact-monthly.csv.gz.b64`
- Gzip SHA256 `6087d7eceff168147b4db2e8688ce308dc12aa6b4187ff0c18f1d5e51e4beda2` ✓
- Decoded CSV SHA256 `1d03923503e7fe82a69b033897484c48aa646279ecf70164d090ed62a5a70719` ✓
- Schema `date,gpi,ipi,regime`; 388 rows; month-END dates 1994-05-31 →
  2026-08-31; continuous (builder asserts zero missing calendar months).
- Month key = calendar month of the month-end date (1994-05-31 → 1994-05).
- State mapping (frozen, same ±10 rule): v66_growth = band(GPI),
  v66_inflation = band(IPI); Low < −10 ≤ Neutral ≤ +10 < High.
- Construction (components/weights/windows/smoothing/scaling) UNCHANGED —
  bytes reused verbatim; nothing rebuilt, nothing retuned.
- PRIMARY evaluation window: exact-V6.6 lineage window 2007-01-01+
  (consistent with #160 preregistered exact window; pre-2007 partial-component
  history excluded). Both return bases run 2007-01 → 2026-08.

## 3. Frozen primary tactical rule (±5pp, Equity ↔ Cash only)

Classify V6.6 month state S:
- risk-on iff `Growth == High AND Inflation != High`
- risk-off iff `Growth == Low OR Inflation == High`
- else neutral.
(Deterministic over all 9 V6.6 states; risk-off takes precedence by
construction of the conditions — note High/High → NOT risk-on since
Inflation==High excludes it, and IS risk-off. No manual exceptions.)

Given frozen structural weights (equity sleeves E = {sp500,nasdaq,russell}
with weights e_i, sum E; cash C) for the B-2-confirmed DH state:
- risk-on: add = min(5, max(0, C − 2), 60 − E, Σ_{i:e_i>0}(cap_i − e_i));
  each non-zero equity sleeve += add × e_i / E (single pass; per-sleeve cap
  enforced; any blocked remainder stays in Cash); cash −= (add − blocked).
- risk-off: cut = min(5, E); each non-zero equity sleeve −= cut × e_i / E;
  cash += cut. (E ≥ 5 in every frozen state; verified arithmetically from
  the matrix: minimum E = 22.5 in Low-High.)
- neutral: no change.
Tier-0 sleeves stay 0 (never activated). Relative equity composition stays
structural (pro-rata). No leverage, no shorts. Caps/floor: equity family 60,
sleeve caps per #178, cash floor 2 preserved via the C−2 term.

## 4. Frozen timing (conservative, no look-ahead)

- V6.6 state observed for month t is known at month-t close at the earliest.
- Structural allocation for month m uses DH info through m−1 (frozen B-2).
- Overlay for month m uses V6.6 state(m−1) — same information cutoff.
- First overlay month: 2007-02-01 (needs V6.6 2007-01; structural B-2 needs
  DH from 1966 — satisfied).
- First return month receiving overlay: the same month m (weights applied to
  month-m returns, exactly as #178/#180 timing).
- Alternate sensitivity lag (S2): overlay(m) uses V6.6 state(m−2).

## 5. Frozen panels, legs, costs

- Panel R (research-backbone): 2007-01 → 2026-08; returns = #178 backbone
  semantics (hardened S&P with flagged French fallback post-2023-06,
  investable oil, #174 others; month dropped (all legs) if a held sleeve
  lacks a return — same rule as #178).
- Panel T (tradable): 2007-01 → 2026-08; returns = #180 ETF proxies
  (SPY/QQQ/IWM/SHY/IEF/TLT/GLD/USO + T-bill cash); same missing-data rule.
- Legs: A = frozen structural weights, no overlay (must reproduce #178
  research_ret on Panel R and #180 impl_pre on Panel T exactly — self-check
  gates); B = + overlay, pre-cost; C = B − total-turnover × rate
  (primary rate 0.0002; turnover = 0.5×Σ|Δ final applied weights|, same
  frozen definition). Incremental turnover = turnover(B) − turnover(A).
- Missing V6.6 month → overlay neutral for any month needing it as state(m−1)
  (no proxy-fill; asserted zero occurrences in 2007+).

## 6. Frozen metrics (A/B/C on each panel)

CAGR, ann vol (biased-sd ×√12), Cash excess ann, Sharpe-like
(ann mean excess / ann std excess), MaxDD on cumulative index, worst month,
positive-month fraction, downside vol (√mean(min(r,0)²)×√12, #174 convention),
turnover (ann one-way), incremental tactical turnover, tactical changes count,
avg Equity/Cash weights, risk-on/off/neutral month fractions.
Incremental: (B−A)/(C−A) CAGR, vol/MaxDD/worst/Sharpe diffs, cost drag,
A-vs-C corr, |C−A|>50bp fraction, top-1/top-3 contribution-episode shares
(episodes = maximal runs of identical tactical class; shares of Σ positive
episode contributions; n/a reported if total ≤ 0).

## 7. Frozen conditional diagnostics

- Per structural DH state (n, A, C, contribution, vol diff).
- Per V6.6 tactical class (risk-on/off/neutral) + underlying 3×3 counts.
- Alignment (frozen rule): aligned iff DH Growth band == V6.6 Growth band
  (diagnostic only; never a trading rule).
- Transitions (frozen window t−3..t+3 around B-2-confirmed structural
  allocation-change months; union of overlapping windows; inside-vs-outside
  mean contribution + class frequencies).
- Time segments (frozen): pre-2020 (<2020-01), 2020–2022, 2023+ (2023-01→end);
  A-vs-C CAGR/vol/MaxDD/contribution/turnover per segment.

## 8. Frozen pass/fail gates (numeric, multidimensional)

1. post-cost CAGR impact (C−A) ≥ −0.50pp/yr.
2. Sharpe-like change (C−A) ≥ −0.05.
3. MaxDD deterioration (C−A) ≥ −3pp.
4. incremental turnover ≤ 40pp/yr (0.40 one-way annualized).
5. benefit concentration: C−A ≤ 0 → moot-pass (failure captured by gate 1);
   else top-1 episode share ≤ 60%.
6. worst-segment (C−A) ≥ −1.0pp/yr across §7 segments.
7. no catastrophic state degradation: min over DH states with n≥12 of
   annualized (C−A) ≥ −3.0pp/yr.
Verdict mapping (frozen): all pass → `v66_tactical_overlay_candidate_supported`;
(C−A > 0 AND gate3 passes AND gate7 passes AND ≤2 total fails) →
`suggestive`; else `not_supported`. Gates evaluated on PRIMARY tradable
panel; research panel reported alongside. Thresholds never move post-result.

## 9. Frozen sensitivities (single-factor, descriptive, never promoted)

- S1: tactical budget ±10pp (same rule structure, 10 for 5).
- S2: alternate execution lag (V6.6 state(m−2)).
- S3: alternate cost 10bp (#180 alternate rate).
No grids, no combinations, no promotion.

## 10. Deliverables (all paths contain `issue-182`)

- `research/issue-182-v66-tactical-prereg.md` (this file)
- `research/issue_182_overlay.py` (frozen stdlib: classify/overlay/caps/timing/gates)
- `research/test_issue_182_overlay.py` (+ executed Node mirror test)
- `research/issue_182_build.mjs` (V6.6 manifest + classification timeline + overlay weights + audits)
- `research/issue_182_backtest.mjs` (A/B/C panels, preservation, state/V6.6/alignment/transition/era, sensitivity)
- `research/generated/issue-182/v66-input-manifest.json`
- `research/generated/issue-182/tactical-timeline.csv`
- `research/generated/issue-182/overlay-weights.csv`
- `research/generated/issue-182/performance.json`
- `research/generated/issue-182/incremental.json`
- `research/generated/issue-182/state-diagnostics.csv`
- `research/generated/issue-182/v66-diagnostics.json`
- `research/generated/issue-182/alignment.json`
- `research/generated/issue-182/transition.json`
- `research/generated/issue-182/era-stability.json`
- `research/generated/issue-182/sensitivity.json`
- `research/generated/issue-182/overlay-policy.json`
- `research/generated/issue-182/summary.json`
- `research/decisions/issue-182-v66-tactical-overlay-finding.md`

Builders MUST pin parent SHAs, reproduce A legs exactly (0 mismatches vs
#178 research_ret and #180 impl_pre), assert V6.6 continuity + CSV SHA,
never overwrite other issues' artifacts, never touch Pine, never optimize.

## 11. Firewall

After this prereg commit and the first overlay result, do NOT change: V6.6
bytes/mapping, budget, pro-rata rule, cap handling, zeros, timing, costs,
panels, metrics, gates, sensitivities, or any frozen parent. Failure is
REPORTED, never repaired here. Forbidden: structural/macro/V6.6 edits,
budget/timing searches, sleeve/duration/gold/oil rotation, leverage, shorts,
grids, #169-trigger-as-validated, pristine-OOS claims, Pine changes, merging.

## 12. Product boundary

Research only. Verdict ∈ (`v66_tactical_overlay_candidate_supported`,
`v66_tactical_overlay_candidate_suggestive`, `v66_tactical_overlay_not_supported`).
Finding MUST contain `production_authorized=false`. Do not merge.
