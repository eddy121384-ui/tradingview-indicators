# Macro vs classic trend/vol baselines — incremental value preregistration (2026-10-16)

**Status:** preregistered before calculating, inspecting, or writing any
macro-augmented P&L. Research only, `production_authorized=false`.
Planning round: NO backtest code is executed in this round.

## Motivation and frozen lineage

Classic baselines (branch `research/equity-risk-classic-baselines-20261015`,
findings `finding.md` + `volatility-managed-finding.md`) show price-only
de-risking already captures large drawdown reductions. The open question is
narrower than portfolio construction: does GPI/IPI/FCPI macro information
provide **incremental defensive timing information** — earlier defense at
matched exposure, and at what re-entry cost — beyond what trend/volatility
rules already do? This study tests timing information only, not allocation
budgets, and makes no general claim about standalone macro information from
the augmented comparison: an absolute equity cap would confound timing with
unconditional underweight, so the frozen combination below is deliberately
**relative**, anchored to the matrix's own neutral equity weight.

- Baselines reused byte-identical: BH, SMA10, MOM12, VolFair (expanding-mean
  [0,1]), Fixed50/60, exposure-matched fixed controls.
- Macro source: frozen #178 9×9 matrix + B-2 + #183 availability rule
  (matrixW), #177 tiers/caps/zeros. No threshold, weight, cap, or B-2 change.
- Literature anchors (verified, same as baseline preregs): Faber (2007)
  10-month SMA; Moskowitz-Ooi-Pedersen (2012) 12-month TSMOM (our long/cash
  adaptation, not futures); Moreira-Muir (2017) prior-month daily realized
  variance inverse with ex-post `c` (paper leg) and expanding-mean [0,1]
  deployable leg. No new literature claims in this study.

## Frozen vehicles and panels (unchanged, gap-aware)

- Single broad-US equity total returns (French/CRSP, NOT S&P500) + TB3MS/1200
  cash proxy (same files/columns, same publication-lag caveat, revised-vintage).
- Primary panel 1967-03..2026-08 (714 consecutive return months, economically
  continuous). Macro source `generated/issue-183/corrected-structural-monthly.csv`
  has 721 rows 1966-05..2026-08 with 3 calendar gaps (2025-10, 2025-11,
  2026-01); it is not calendar-complete. Primary augmented-vs-baseline
  comparison retains the full 714 months with disclosed stale-factor carry in
  those 3 months; all baselines use the same calendar convention. The 711
  months with observed #183 macro states are a completeness/secondary
  aligned-month diagnostic only; never concatenate non-consecutive returns,
  silently drop 3 months, or present 711-month MaxDD/CAGR as a continuous
  live record.
- Gap treatment (preregistered, time-ordered, consistent with frozen B-2
  hold-on-unconfirmed): `E_DH[m]` is the B-2 applied-state equity weight for
  month m only when that month exists in the #183 file; on the 3 missing
  months there is no new DH decision. Augmented legs carry forward only the
  last valid macro scale factor `s_last = min(1, E_DH_last/0.45)` and keep
  applying the current month's independently computed baseline weight:
  `w_aug[m] = w_base[m] × s_last`. This is zero new macro decision, not
  necessarily zero total strategy turnover; baseline-driven trades and their
  2bp costs continue, so `w_aug ≤ w_base` holds every month including gaps.
  DH-equity-only budget diagnostic holds the last known DH target through
  gaps. Never forward-fill from a future state, never compress the calendar,
  never reinitialize B-2 across gaps or use later states retrospectively.
  If weights cannot be reconstructed exactly, BLOCK that leg instead of
  substituting.
- Costs 2bp per 100% target-weight change (10bp sensitivity), initial
  deployment free, same rebalancing conventions. Eras E1–E4 and six crisis
  windows as preregistered.
- Full classic metric set per leg (CAGR, vol, Sharpe-like, MaxDD, worst-1m,
  switches, turnover, mean exposure, participation, missed/avoided sums).

## Frozen macro legs (new constructs, mechanically derived, no tuning)

1. **DH-equity-only** (macro-alone budget reference, same vehicle): month-t
   equity target = `sp500+nasdaq+russell` weights of the frozen matrixW row
   for the B-2 applied state (same availability rule, same costs/turnover).
   Cash remainder earns the proxy. This leg carries the frozen 9-sleeve
   budget (22.5%–60% equity); it is a **budget reference and diagnostic**,
   not the timing test — its absolute level must never be read as timing
   evidence on its own.
2. **Augmented legs** (ONE frozen relative rule — replaces any absolute-cap
   formulation; no variant; frozen before any augmented P&L is calculated):
   with `E_DH` the DH structural equity weight as a
   fraction and `0.45` the already-frozen neutral-state equity sum
   (25+12+8, from the #178 matrix, not fitted),
   `Final_w[t+1] = Baseline_w[t+1] × min(1, E_DH[t+1]/0.45)`
   for each baseline B in {SMA10, MOM12, VolFair} → `SMA10+DH`, `MOM12+DH`,
   `VolFair+DH`. At neutral macro the factor is exactly 1 (baseline
   untouched); at minimum-equity states the factor is 0.5. The rule scales
   the baseline's own shape down in defensive states — macro supplies timing,
   never a level. Residual average-exposure differences vs baselines are
   reported, not tuned away.
3. **Exposure-matched fixed controls** for DH-equity-only and each augmented
   leg at realized mean exposure (same descriptive-hindsight method/labels).

## Frozen evaluation (no outcome-informed edits)

- Head-to-head per augmented leg vs its baseline (primary: full 714-month
  continuous months with disclosed stale-factor carry in 3 gap months; secondary:
  711-month observed-macro diagnostic; full E1–E4 and crisis tables, no
  cherry-picking): Sharpe-like diff, MaxDD diff (pp), CAGR diff (pp/yr),
  turnover diff, crisis-window compounded diffs, era CAGRs.
- Vs exposure-matched control on Sharpe-like (descriptive hindsight only).
- Earlier-defense / re-entry-drag diagnostic only (no gate, no early
  re-entry claim): months from each #186 trough month to the first month
  each leg returns to ≥95% equity, augmented vs baseline (median over 8
  troughs; #186 troughs are S&P-dated while our vehicle is French broad
  market — disclosed ≤2-month reference mismatch). Under the frozen
  relative rule the scale factor is ≤1 every month, so `w_aug ≤ w_baseline`
  identically; augmented can only tie, lag, or never reach ≥95% vs its
  baseline. This statistic therefore measures re-entry drag/cost, never
  independent early re-entry. Early re-entry requires a separate future
  prereg and is out of scope here; no rule variant is added for it.
- Verdict framework (frozen before outcomes; descriptive scorecard only,
  not statistical evidence):
  - Per leg scorecard-PASS iff Sharpe diff ≥ +0.02 AND MaxDD diff ≥ +1.0pp
    AND CAGR diff ≥ −0.10pp/yr AND Sharpe ≥ its exposure-matched control.
    Thresholds are economic heuristics precommitted for description only.
  - Overall scorecard: descriptively favourable iff ≥2/3 augmented legs
    scorecard-PASS; mixed iff 1/3; unfavourable iff 0/3. This 2/3 count is
    not proof of an incremental edge, statistical significance, or live
    tradability. SMA10/MOM12/VolFair share the same vehicle, panel, and
    price-only long/cash structure and are correlated controls, not three
    independent replications.
  - Finding must show era/crisis consistency in plain tables alongside the
    scorecard, state correlation/multiple-look/overfit uncertainty, restate
    revised-vintage and non-PIT limits (#183/#188 already-studied data), and
    must not promote a scorecard majority to proof of edge or tradability.
    No success declared by any single metric in isolation.

## Integrity / limitations (frozen)

- Revised-vintage research only (French/CRSP revisions, TB3MS proxy timing,
  CIZ-era daily file, monthly file-decimal rounding MAE 0.047pp/mo as audited).
  No contemporaneous PIT certificate; macro inputs are revised reconstructions
  (#189: full PIT not identifiable, G5 unavailable). #183/#188 data are
  already-studied revised vintages; multiple looks and correlated controls
  mean scorecard counts carry no p-value. No live-trading claim.
- SMA10/MOM12/VolFair are correlated price-only controls on the same vehicle
  and panel, not independent replications; correlated outperformance across
  legs must not be read as independent confirmation.
- DH-equity-only changes vehicle semantics vs the 9-sleeve policy; any gap
  between it and full DH is disclosed, never patched.
- Stop conditions: if DH-equity weights cannot be reconstructed exactly
  (matrix/B-2/availability mismatch vs #183), BLOCK that leg with reason
  instead of substituting. If augmented legs degenerate (e.g. identical to
  baseline from lack of overlap), report degeneracy, do not redesign the rule.

## Deliverables (execution round, not this round)

- `macro_incremental_backtest.mjs` + mechanics tests (synthetic relative-scale
  rule, neutral-factor-1 behavior, timing t→t+1, stale-factor carry with
  baseline independence, determinism) reusing frozen baseline code paths.
- `macro-incremental-{results.json,monthly.csv,finding.md}` under
  `generated/classic-equity-baselines/`; summary table vs all baselines.
- No Pine, no main merge, no new Issue, no threshold search, no variant rules.

## Prohibitions

No re-tuning of SMA10/MOM12/vol parameters, no alternate combination rules
(averages, overrides, state filters), no macro threshold edits, no optimizer,
no outcome-informed warmup/era/window changes, no production authorization.
`production_authorized=false`.
