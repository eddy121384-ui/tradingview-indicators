# Issue #188 — Deep History edge attribution — Preregistration (frozen)

- Issue: [#188](https://github.com/eddy121384-ui/tradingview-indicators/issues/188)
- Branch: `research/issue-188-deep-history-edge-attribution`
- Base (pre-prereg) HEAD: `e61b9a31feb08ab757d34d77cc841fda70c77bcc` (#187 final)
- This prereg is the FIRST Issue #188 research commit on this branch.
- Status: PREREGISTRATION — frozen before ANY new control/ablation/placebo
  portfolio performance is computed or viewed.
- `outcome_data_loaded=false` (at prereg commit; no candidate outcome exists)
- `production_authorized=false`
- `revised_macro_history=true` (DH inputs reconstructed, NOT vintage PIT)
- `real_time_vintage_claim=false`

## 0. Ordering attestation (firewall)

The GitHub Issue #188 body was read in full (authoritative). Parent findings,
baseline/return provenance, and available series were read as frozen INPUTS.
Pre-prereg work was limited to the prereg firewall's explicit permissions:

- baseline reproduction: corrected DH (A) on P-MAX/P-FULL/P-ETF with 0
  mismatches vs frozen files; original static-neutral (B) reproduction matching
  frozen 8.3311%/−24.05%; metric reads from frozen JSON (no new outcomes);
- weights-only feasibility: per-panel D time-average targets, E1 projection
  legality (zero/cap), E2 basket feasibility, Low-episode/state counts;
- panel continuity checks (month counts, missing-month list).

No control/ablation/placebo/shifted return, gap, percentile, bootstrap, or
stress number was computed or viewed. Sequence: read issue → audit inputs →
freeze §§1–12 → commit → record SHA → ONLY THEN run analysis. Any later
definition change requires a NEW issue.

## 1. Frozen parents, baselines, panels (verified pre-prereg)

- Parents: #177 `bc652bd`, #178 `10dcdce0`, #180 `ac251ad`, #183 `411835cc`,
  #184 `a3c6dbb` (V6.6 EXCLUDED here), #186 `a83836c` (events/prices),
  #187 `e61b9a3` (required base; its rule NOT reused — no demonstrated benefit).
- Reproduced pre-prereg (0 mismatches, tol 1e-12):
  P-MAX DH 8.7547% CAGR / 7.0848% vol / −17.038% MaxDD (n=721);
  P-FULL DH 5.9342% / 7.1194% / −17.038% (n=274);
  P-ETF DH-impl 8.1658% / 7.6593% / −16.440% (n=240, vs frozen impl_pre);
  P-MAX static-neutral-orig 8.3311% / 8.1298% / −24.049% (n=721).
  Non-comparability note (frozen here): DH uses availability-adjusted weights
  while B redistributes missing sleeves — E0a exists precisely to price this.
- Panels: P-MAX 1966-05→2026-08, 721 applied months; exactly 3 inherited
  missing calendar months 2025-10/2025-11/2026-01 (724 − 3; never claim 724).
  P-FULL 2000-09→2023-06, 274 months, all 9 sleeves present. P-ETF 2006-06→
  2026-08, 240 months, 0 drops expected (asserted, never filled).
- Constants verbatim #178/#183: ORDER 9 sleeves; BASE 25/12/8/8/14/8/6/4/15;
  MULT 0/0.5/1.0/1.75; caps 35/20/15/15/25/15/12/8; family 60/50/15;
  CASH 2/60; bias-min low5/neutral10/high20; ±10 bands; B-2 (month m from DH
  through m−1, hold unconfirmed); turnover 0.5Σ|Δ|/100 first-month-0;
  costs: P-ETF 2bp; long-history 10bp + 25bp HYPOTHETICAL sensitivities
  (labeled, never claimed as 1970s costs); identical conventions all legs
  incl. fixed-leg rebalance turnover (§2).
- Investability limits (reported, never interpolated): pre-1971 gold
  (limitation), 1975 US private-ownership constraint note, oil investable
  2000-09, Nasdaq/Russell price-only, 2023 S&P French fallback, 1987–1993
  long-Treasury gap, QQQ≠Nasdaq Composite, no pre-ETF backfill claims.
- Macro data are revised reconstructions: separate RECONSTRUCTED
  calendar-specific information from actionable-at-the-time; +1/+2/+3 stress
  (§10) is a bound, not vintage validation. Sample-in-sample warning: #177/#178
  weights come from the same history — even strong placebo alignment is NOT
  pristine-OOS proof (labeled on every placebo output).

## 2. E0a legs A–F (frozen; equal calendar + return source per comparison)

- A (frozen DH, frozen availability): corrected #183 engine verbatim
  (matrixW: full row iff all sleeves have history else #178 computeWeights on
  available with correct cash_bias); month dropped from ALL legs iff a HELD
  sleeve (weight≠0) lacks a backbone return. A never modified.
- B (static-neutral + ORIGINAL redistribution, monthly rebalance): nominal
  BASE/15 targets; unavailable sleeve weight redistributes over available
  (÷availTot, verbatim `benchNeutral`); same missing-month drops. Reproduced
  pre-prereg (§1).
- C (static-neutral + CASH rule): identical nominal targets; unavailable
  weight → Cash (100% maintained); otherwise identical months/rebalance/drops.
  NEW leg (post-prereg compute).
- D (exposure-matched, in-sample diagnostic, NOT ex-ante): fixed portfolio =
  applied time-average of frozen DH TARGET rows per panel (weights-only,
  recorded below), monthly rebalanced, static-redistribution availability.
  Tolerance: |avgEq(D) − avgEq(DH-applied)| ≤ 0.05pp per panel (weights-only
  check before D performance). P-MAX targets:
  sp500 25.044 / nasdaq 11.623 / russell 6.143 / 2Y 7.639 / 10Y 11.002 /
  long 7.631 / gold 4.835 / oil 3.592 / cash 22.491 (applied avg Eq 42.810).
  P-FULL: 25.317/12.152/6.308/7.037/10.826/6.796/5.314/3.414/22.838 (Eq 43.777).
  P-ETF: 26.228/12.253/6.907/7.559/11.267/7.467/5.161/3.436/19.721 (Eq 45.388).
  (Full-target vs applied averages are identical here — targets ARE applied
  rows; the distinction is moot and recorded as such.)
- E (retrospective risk-matched neutral+Cash; labeled NON-EXECUTABLE): scale
  neutral targets by k = σ_DH/σ_neutral from FROZEN baseline metrics, remainder
  to Cash; redistribution availability. k: P-MAX 0.871443 (cash 12.8557%),
  P-FULL 0.892116 (cash 10.7884%), P-ETF 0.939216 (cash 6.0784%).
- F (fixed 60/40): 60% French-market equity + 40% 10Y backbone (verbatim
  `runFrench` wEq=0.6; same unit as #178 balanced6040), redistribution
  availability, monthly rebalance. Declared reference, not DH mix.
- Fixed-leg rebalance turnover (frozen): each month, drifted weights =
  prev-target × (1+returns), renormalized; turnover = 0.5Σ|target − drifted|/100.
- 2×2 decomposition (policy × availability), Shapley 2-factor, P-MAX primary:
  cells A=(DH,orig) frozen, B=(static,orig) frozen, C=(static,cash) new,
  A'=(DH,cash-rule) HYPOTHETICAL counterfactual (DH targets with unavailable
  weight → Cash instead of subset recompute; prominent hypothetical label; DH
  policy itself never modified — A' is a separate leg).
  Policy effect PE = ½[(A−C) + (A'−B)], availability effect AE = ½[(A−A') +
  (C−B)] (CAGR pp), interaction INT = (A−A') − (C−B); shares of |PE|+|AE|.
  Era splits (frozen §1 bounds; focus E1/P-FULL/P-ETF) use the same formulas.

## 3. E0b placebo (frozen; joint-sequence circular shifts, descriptive only)

- Genuine alignment: frozen applied DH TARGET-weight sequence (B-2 states →
  matrix rows; FULL target rows, availability-independent) on the common panel.
- Placebos: ALL N−1 nonzero circular shifts of the complete joint
  state/weight sequence (P-MAX 720, P-FULL 273, P-ETF 239); frequencies,
  order/autocorrelation except wrap, zeros, caps, durations preserved; macro
  NEVER recomputed on future data; none dropped/selected.
- Per shifted month, availability is recomputed with the SAME frozen rule and
  may change applied exposure: record mismatch months + max gross delta; if
  >5% of months mismatch OR max |Δgross| > 2pp → percentile flagged
  AVAILABILITY-CONFOUNDED (reported + labeled, gate G3 auto-fails safe).
- Same returns/months/costs; metrics §7; favorable percentile frozen:
  100×(#{placebo strictly worse} + 0.5×#{ties})/N per metric (higher-better
  orientation fixed per metric). NOT iid significance / OOS proof (labeled).

## 4. E1 ablations (frozen; remove axes, no fitting)

- E1-infl-minimal (policy): base = nominal neutral; B-2-CONFIRMED I_High
  (applied DH state's inflation band == High, 269/721 P-MAX months) moves ALL
  of 2Y+10Y+Long weight → Cash/T-bill, others frozen; redistribution
  availability (benchmark-consistent, full coverage); no leverage/reweight.
- E1-growth-only (policy): 3 Growth rows = P-MAX applied-state-frequency
  aggregates (weights-only, FROZEN counts: G_Low 60/49/84 n=193; G_Neutral
  120/87/123 n=330; G_High 55/81/62 n=198). Rows (sums 100.00, caps ok):
  G_Low E34.38/cash27.23, G_Neutral E43.41/cash20.73, G_High E50.03/cash20.81.
  Applied by B-2-confirmed Growth band; redistribution availability. Zero-cell
  dilution (e.g. Low-Low oil→2.76) DISCLOSED as aggregation artifact, unrepaired.
- E1-infl-projection (NONPOLICY diagnostic): per-sleeve MEDIAN over the 3
  growth rows per inflation band (predetermined "median/canonical" choice).
  I_Neutral clean; I_Low violates Low-Low/oil + High-Low/gold zeros; I_High
  violates Neutral-High/russell zero → I_Low/I_High instances are NONPOLICY
  diagnostics (computed, labeled, never called portfolios, never silently
  repaired); caps hold everywhere.
- Per-leg exposure controls (D-method: time-average + same availability as
  that leg) for the two policy legs; joint-shift placebos NOT rerun per leg
  (axis-ablated shifts would create implausible macro histories — frozen scope
  decision; joint shift across axes preserved per issue).

## 5. E2 fixed-Equity defensive basket (frozen TEST CANDIDATE, not DH)

- Equity ALWAYS 45 = 25/12/8 sp500/nasdaq/russell (frozen neutral proportion).
- Non-equity 55: duration basket 2Y8/10Y14/Long8/Gold6/Oil4/Cash15 (neutral
  split, sums to 55); inflation-defense basket 2Y10/Gold10/Oil5/Cash30/10Y0/
  Long0 (sums to 55). B-2-confirmed I_High → defense, else duration. No
  technical fallback, no grids. Redistribution availability (E1-consistent).
- Feasibility verified weights-only pre-prereg: E45≤60; defense rates10≤50,
  real15≤15 (AT cap, allowed), sleeves 10≤12/5≤8/10≤15; duration rates30,
  real10; totals 100. NO clip/project needed; if a month breaks a constraint,
  HALT and report (never silently repair).

## 6. Metrics, attribution, episodes (frozen formulas)

- Base (verbatim #183, applied-month annualization ×12/n_valid): CAGR net/gross,
  ann vol, cash-excess Sharpe-like, MaxDD, worst month, downside vol, turnover,
  costs. Cash reference: backbone T-bill accrual (research panels), bill proxy
  (ETF panel).
- Ulcer Index = 100×sqrt(mean(dd_t²)), dd_t = cum_t/peak_t − 1 (≤0) on the
  path's valid months. UPI = (CAGR − cashCAGR)/Ulcer; Ulcer==0 → null (no
  undefined denominators). CDaR95: threshold = 5th percentile of dd_t;
  CDaR95 = −100×mean(dd_t | dd_t ≤ threshold); <20 valid months → null.
- Worst rolling-12m: min Π(1+r)−1 over windows of 12 CONSECUTIVE valid months
  in path order (gap breaks window). Longest underwater: max consecutive valid
  months below prior peak; ends-underwater → value + censored=true.
- Exposures: mean Eq/Rates/Gold/Oil/Cash + duration proxy (10Y+Long share);
  monthly pp differences; applied-state frequencies.
- Attribution: Σ_month (w_DH − w_ctrl)×r_sleeve by family + Cash/duration
  splits; remainder (costs + compounding interaction) disclosed, never hidden.
- Episodes: 4 frozen eras (§1) + 6 crises with FROZEN windows
  1973-01→1975-12, 1987-01→1988-12, 2000-01→2003-12, 2007-01→2010-12,
  2020-01→2020-12, 2021-01→2023-12 (== #186 case windows) + 2008 mechanism
  audit from applied weights (Cash/duration/Equity moves + timing, no
  narratives-alone). Top-3 share: contributions Σ(B−C... define: monthly
  (DH−C) sums within the 8 #186 peak→recovery spans + "outside" bucket; shares
  of Σ positive spans (null-safe).

## 7. Robustness: bootstrap + LOOO + stress (frozen)

- Circular block bootstrap on PAIRED monthly diffs (DH − C, common valid
  months): block 24 panel-months, B=5000, seed 188 (mulberry32, frozen impl in
  primitives); per-replicate CAGR_DH* − CAGR_C* (own compounding,
  applied-month annualization); 90% CI = 5th/95th percentiles. Descriptive.
- Leave-one-episode-out: drop each of 1973-74 / 2007-09 / 2020 / 2022 windows
  (§6), recompute DH−C CAGR diff. Report all four + any CI including zero +
  small-sample instability note. No p-hacking: thresholds frozen (§8).
- +1/+2/+3 DH-availability stress: shift G/I maps (value(t)=orig(t−k)), rerun
  DH leg verbatim (signals…= same B-2/matrix code path); report coverage,
  returns, risk, false-recovery analogue (trigger coverage + performance).

## 8. Gates + verdict (frozen BEFORE outcomes; positive benefit required)

P-MAX primary unless noted; pp = ×100. DH vs C (equal-availability static):

- G1: CAGR_DH − CAGR_C ≥ +0.10pp (P-MAX) AND ≥ 0 (P-ETF).
- G2: Sharpe_DH − Sharpe_C ≥ +0.02 AND MaxDD_DH − MaxDD_C ≥ +1.0pp (P-MAX).
- G3: placebo Sharpe pct ≥ 75 AND MaxDD pct ≥ 75 (P-MAX, unconfounded) AND
  P-ETF Sharpe pct ≥ 50 (edge survives tradable window, weak form).
- G4: DH Sharpe − max(E1 policy legs Sharpe) ≥ +0.01 (P-MAX; projection excluded).
- G5: MaxDD_E2 − MaxDD_DH ≤ −1.0pp OR Sharpe_E2 ≤ Sharpe_DH − 0.01 (P-MAX).
- G6: CAGR_DH − CAGR_D ≥ +0.05 AND Sharpe_DH − Sharpe_D ≥ 0 (P-MAX, per panel D).
- G7: Shapley PE_share ≥ 50% AND PE > 0 (P-MAX).
- G8: bootstrap lower-5% of CAGR diff > 0 AND all 4 LOOO diffs > −0.05pp.

Verdict (exactly one, in order; gate-gaps reported, never overclaimed):
1. P-MAX valid < 600 or P-MAX placebo confounded → `..._mixed_or_inconclusive` (reason).
2. G1–G8 all pass → `deep_history_macro_information_supported`.
3. G1 holds AND G4 fails → `deep_history_reducible_to_simpler_defense`.
4. G6 fails OR G7 fails → `deep_history_exposure_or_availability_explained`.
5. Else → `deep_history_evidence_mixed_or_inconclusive`.
(Never "worthless" on a percentile alone — warning #6; never "supported"
without positive benefit — #187 lesson.)

## 9. Deliverables (all paths contain `issue-188`) + tests + finding

- `research/issue-188-edge-attribution-prereg.md` (this file)
- `research/issue_188_primitives.py` + `research/test_issue_188_primitives.py`
  (+ executed Node mirror test; mulberry32(188) both languages)
- `research/issue_188_build.mjs` (E0/E1/E2 legs, placebos, bootstrap, stress)
- `research/generated/issue-188/`: manifest, reproduction checks, monthly
  streams (A–F, ablations, E2, controls), placebo distributions + percentiles,
  attribution (family×era×crisis), bootstrap/LOOO, stress, era/crisis tables,
  policy + summary JSONs, chart-ready CSVs
- `research/decisions/issue-188-edge-attribution-finding.md` (branch/HEADs/
  verdict + 6 Traditional-Chinese manager answers with figures + ONE next step)
- No prior artifact overwritten. Deterministic reruns byte-identical.
- Tests: extractor/metric/percentile/gate unit tests on synthetic data (no
  parent returns in fixtures); full-tree suite still green or deltas explained.

## 10. Firewall + product boundary

After this prereg commit + first candidate outcome, do NOT change: inputs,
panels, legs A–F, projections, baskets, availability rules, timing, costs,
metrics, placebo/percentile protocol, bootstrap/LOOO/stress, thresholds,
verdict tree, or any frozen parent. Failure REPORTED, never repaired here.
Forbidden: threshold/budget searches, tranche/credit/valuation overlays, V6.6,
episode cherry-picking, hidden false positives/eras, leverage/shorts,
pristine-OOS claims, Pine/production edits, merging. If DH fails, report it;
no rescue rule in #188. Research only. Finding MUST contain
`production_authorized=false`. Do not merge.
