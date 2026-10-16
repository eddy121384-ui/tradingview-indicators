# Macro vs classic trend/vol baselines — incremental value preregistration (2026-10-16)

**Status:** preregistered before calculating, inspecting, or writing any
macro-augmented P&L. Research only, `production_authorized=false`.
Planning round: NO backtest code is executed in this round.

## Motivation and frozen lineage

Classic baselines (branch `research/equity-risk-classic-baselines-20261015`,
findings `finding.md` + `volatility-managed-finding.md`) show price-only
de-risking already captures large drawdown reductions. The open question is
whether GPI/IPI/FCPI macro information adds **incremental** value on top —
earlier de-risking, faster re-entry, or better risk-adjusted returns — at
matched exposure and frozen rules.

- Baselines reused byte-identical: BH, SMA10, MOM12, VolFair (expanding-mean
  [0,1]), Fixed50/60, exposure-matched fixed controls.
- Macro source: frozen #178 9×9 matrix + B-2 + #183 availability rule
  (matrixW), #177 tiers/caps/zeros. No threshold, weight, cap, or B-2 change.
- Literature anchors (verified, same as baseline preregs): Faber (2007)
  10-month SMA; Moskowitz-Ooi-Pedersen (2012) 12-month TSMOM (our long/cash
  adaptation, not futures); Moreira-Muir (2017) prior-month daily realized
  variance inverse with ex-post `c` (paper leg) and expanding-mean [0,1]
  deployable leg. No new literature claims in this study.

## Frozen vehicles and panels (unchanged)

- Single broad-US equity total returns (French/CRSP, NOT S&P500) + TB3MS/1200
  cash proxy (same files/columns, same publication-lag caveat, revised-vintage).
- Common payoff panel 1967-03..2026-08 (714 months). Costs 2bp per 100%
  target-weight change (10bp sensitivity), initial deployment free, same
  rebalancing conventions. Eras E1–E4 and six crisis windows as preregistered.
- Full classic metric set per leg (CAGR, vol, Sharpe-like, MaxDD, worst-1m,
  switches, turnover, mean exposure, participation, missed/avoided sums).

## Frozen macro legs (new constructs, mechanically derived, no tuning)

1. **DH-equity-only** (macro alone, same vehicle): month-t equity target =
   `sp500+nasdaq+russell` weights of the frozen matrixW row for the B-2
   applied state (same availability rule, same costs/turnover). Cash remainder
   earns the proxy. This isolates the macro equity signal from the 9-sleeve
   rates/real allocation; it is a diagnostic leg, not a proposed portfolio.
2. **Augmented legs** (ONE frozen combination rule, defensive-only):
   `Final_w[t+1] = min(Baseline_w[t+1], DH_equity_w[t+1])` for each baseline
   B in {SMA10, MOM12, VolFair} → `SMA10+DH`, `MOM12+DH`, `VolFair+DH`.
   Macro may only cut equity, never add; re-entry timing comes from the
   baseline itself. No blended averages, no state overrides, no second rule.
3. **Exposure-matched fixed controls** for DH-equity-only and each augmented
   leg at realized mean exposure (same descriptive-hindsight method/labels).

## Frozen evaluation (no outcome-informed edits)

- Head-to-head per augmented leg vs its baseline (same panel/costs):
  Sharpe-like diff, MaxDD diff (pp), CAGR diff (pp/yr), turnover diff,
  crisis-window compounded diffs, era CAGRs.
- Vs exposure-matched control on Sharpe-like (descriptive).
- Re-entry timing diagnostic only (no gate): months from each #186 trough
  month to the first month each leg returns to ≥95% equity, augmented vs
  baseline (median over 8 troughs; #186 troughs are S&P-dated while our
  vehicle is French broad market — disclosed ≤2-month reference mismatch).
- Verdict framework (frozen before outcomes; modest by design):
  - Per leg PASS iff Sharpe diff ≥ +0.02 AND MaxDD diff ≥ +1.0pp AND
    CAGR diff ≥ −0.10pp/yr AND Sharpe ≥ its exposure-matched control.
  - Overall: macro adds value iff ≥2/3 augmented legs PASS; mixed iff 1/3;
    no incremental value iff 0/3. Re-entry medians reported alongside but
    gate nothing. No success declared by any single metric in isolation.

## Integrity / limitations (frozen)

- Revised-vintage research only (French/CRSP revisions, TB3MS proxy timing,
  CIZ-era daily file, monthly file-decimal rounding MAE 0.047pp/mo as audited).
  No contemporaneous PIT certificate; macro inputs are revised reconstructions
  (#189: full PIT not identifiable, G5 unavailable). No live-trading claim.
- DH-equity-only changes vehicle semantics vs the 9-sleeve policy; any gap
  between it and full DH is disclosed, never patched.
- Stop conditions: if DH-equity weights cannot be reconstructed exactly
  (matrix/B-2/availability mismatch vs #183), BLOCK that leg with reason
  instead of substituting. If augmented legs degenerate (e.g. identical to
  baseline from lack of overlap), report degeneracy, do not redesign the rule.

## Deliverables (execution round, not this round)

- `macro_incremental_backtest.mjs` + mechanics tests (synthetic min-rule,
  cap behavior, timing t→t+1, determinism) reusing frozen baseline code paths.
- `macro-incremental-{results.json,monthly.csv,finding.md}` under
  `generated/classic-equity-baselines/`; summary table vs all baselines.
- No Pine, no main merge, no new Issue, no threshold search, no variant rules.

## Prohibitions

No re-tuning of SMA10/MOM12/vol parameters, no alternate combination rules
(averages, overrides, state filters), no macro threshold edits, no optimizer,
no outcome-informed warmup/era/window changes, no production authorization.
`production_authorized=false`.
