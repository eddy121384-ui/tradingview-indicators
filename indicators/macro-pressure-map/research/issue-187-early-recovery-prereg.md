# Issue #187 — Deep-History early-recovery Equity add — Preregistration (frozen)

- Issue: [#187](https://github.com/eddy121384-ui/tradingview-indicators/issues/187)
- Branch: `research/issue-187-deep-history-early-recovery-equity`
- Base (pre-prereg) HEAD: `a83836ce0453d890c4d00667d50c36767aa9278b` (#186 final)
- This prereg is the FIRST Issue #187 research commit on this branch.
- Status: PREREGISTRATION — frozen before ANY candidate overlay return
  (A/B/C/D leg, case P&L, false-start loss, stress number) is computed or viewed.
- `outcome_data_loaded=false` (at prereg commit; no overlay return exists)
- `production_authorized=false`
- `revised_macro_history=true` (DH inputs reconstructed, NOT vintage PIT)
- `real_time_vintage_claim=false`

## 0. Ordering attestation (firewall)

The GitHub Issue #187 body was read in full (authoritative; spec in prompt).
Parent artifacts (#177 tiers, #178 matrix/B-2, #180 proxies/costs, #183
corrected baseline, #184 exposure-control method, #186 events/prices) were read
as frozen INPUTS only. Pre-prereg work was limited to UNCONDITIONAL input
verification: file presence, matrix/B-2 code reading, DH coverage start
(valued from 1966-03-01), #186 event list reading (no new lag computed), #180
cost/proxy presence. No overlay weight, return, P&L, hit rate, or stress
number was computed or viewed.

Sequence: read issue → verify inputs → freeze §§1–13 → commit → record SHA →
ONLY THEN calculate candidate performance. Any later rule change needs a NEW issue.

## 1. Frozen parents and baseline (verified pre-prereg)

- #177 `bc652bd615f2c5e9137050d01c666dbcd9528cd3` (tiers/zeros)
- #178 `10dcdce0ec86b0493d6df6b916b720eba46dcbe6` (matrix, B-2, caps)
- #180 `ac251ad5149d9f550d82dfb34b3551fe01032367` (ETF map, cost 0.0002, strict panel)
- #183 `411835cc9e3a00d0f5d998df9fb2058d8a917e96` (AUTHORITATIVE corrected baseline)
- #184 `a3c6dbbdbcdbaf25129caf9bd5008b08947605e3` (exposure-control method precedent)
- #186 `a83836ce0453d890c4d00667d50c36767aa9278b` (events/prices; required base)
- Baseline A = corrected #183 structural portfolio ONLY (matrix-as-truth rows,
  #183 availability rule, B-2 timing). Buggy #178 stream NEVER used. V6.6
  EXCLUDED from primary legs (#184: specificity not supported).
- Constants verbatim: ORDER 9 sleeves; EQ = sp500/nasdaq/russell; sleeve caps
  35/20/15/15/25/15/12/8; family caps 60/50/15; CASH_MIN 2, CASH_MAX 60;
  ±10 bands; B-2 (month-m allocation from DH through m−1; hold unconfirmed);
  turnover = 0.5×Σ|Δ final applied weights|/100, first month 0; cost 0.0002.
- Price reference: #186 `spx-monthly.csv` (Yahoo ^GSPC month-end, 728 months)
  + `spx-daily.csv` for 2020 context; #186 8 bear events reused verbatim
  (troughs 1970-06 … 2022-09). No new event definition in this issue.

## 2. Primary signal (frozen; preselected hypothesis, never retuned)

DH monthly values are calendar-month series (`deep-history-v01-monthly.csv`,
valued from 1966-03-01; warmup rows NaN-skipped). At CLOSE of month t, with
completed months t/t−1/t−2 all present, ACTIVATE iff ALL hold:

1. `G(t) < -10` (Growth still LOW)
2. `G(t) > G(t−1) > G(t−2)` (strictly improved TWO consecutive completed months)
3. `I(t) <= +10` (Inflation not HIGH)
4. `I(t) − I(t−1) <= +5` (no sharp one-month acceleration)

First evaluable signal month: 1966-05 (needs t−2 = 1966-03). Allocation
effective no earlier than return month t+1 (no same-month look-ahead).
Primary analysis uses reconstructed values as-is (NOT PIT); §11 stresses delay.

## 3. Low-Growth episodes: one activation max (frozen)

- Raw Low episode = maximal run of calendar months with Growth_DH < −10
  (completed-month values; NaN breaks runs).
- At most ONE activation per episode. Activation consumes the episode.
- Rearm ONLY after raw Growth exits Low (≥ −10) and later re-enters (< −10).
- Signal months inside an already-consumed episode are logged as
  `suppressed_repeat` (counted, never acted on). No pyramiding.

## 4. Overlay sizing (frozen; partial funding recorded, never invented)

At activation (signal month t, first active return month m0 = t+1), with the
month-m0 STRUCTURAL base row wA:

- Requested add: +5pp total Equity from Cash, pro-rata over NON-ZERO Equity
  sleeves (frozen relative proportions): `take_s = 5 × wA[s]/E`.
- Feasible add: `X = min(5, cash−2, 60−E, Σ_{s:E>0}(cap_s − wA[s]))`, floored at 0.
  (Structural Equity never at 60 in Low states in practice, but the cap term is
  frozen in.) In Low-Low (cash 5) X = 3: the missing 2pp is RECORDED as
  `blocked_pp = 5 − X` with reason `cash_floor` (or `sleeve_cap`/`family_cap`);
  NEVER funded from Treasuries/Gold/Oil, NEVER invented.
- X is LOCKED for the activation. Each later active month m re-applies
  `add_m = min(X, feasible(wA_m))` to that month's structural base (same
  pro-rata/caps/zeros/cash-floor; non-Equity sleeves byte-identical to base;
  row sums 100; no leverage/shorts). Months with add_m < X logged partial.
- D builder (control) reuses this function with constant d (§9); C builder
  reads NO Growth/Inflation series (code-path assert).

## 5. Exits A–E (frozen; evaluated at close t, effective t+1; first firing wins)

Reference: E_ref = structural Equity target of first active month m0.
At each close t while active (t ≥ signal month), check in order A–E; ALL
firing conditions are recorded, exit takes effect return month t+1:

- A. `E_struct(t) ≥ E_ref + 5` (original policy caught up ≥5pp).
- B. `I(t) > 10` OR `I(t) − I(t−1) > 5` (inflation High or sharp acceleration).
- C. `G(t) − G(t−1) ≤ 0` AND `G(t−1) − G(t−2) ≤ 0` (two consecutive
  non-positive Growth changes; completed months, NaN-safe: missing → no fire).
- D. `E_struct(t) − E_struct(t−1) ≤ −5` (structural de-risked ≥5pp; overlay
  must not fight the defensive policy).
- E. Six portfolio return months completed active (active months m0..m0+5;
  exit effective m0+6).

No tuning. Exit month + reason + active-month count logged per activation.

## 6. Panels (frozen)

- FULL: #183 corrected structural engine verbatim (`matrixW` availability rule:
  full row when every sleeve has history, else #178 `computeWeights` on
  available sleeves with correct cash_bias) over B-2 timeline 1966-05 → 2026-08;
  month dropped from ALL legs if any HELD sleeve (weight ≠ 0) lacks a backbone
  return (researchRet: hardened-S&P/French fallback, investable oil, #174
  others — verbatim #183). A MUST reproduce frozen
  `corrected-structural-monthly.csv port_ret` with 0 mismatches (tol 1e-12)
  before any overlay leg runs.
- ETF STRICT: #180 rule verbatim (frozen row; missing-PROXY weight → Cash, no
  CASH_MAX re-derivation) on strict panel 2006-06-01 → 2026-08 with #180 proxy
  returns; 0 drops expected (asserted; any drop reported, never filled).
- S&P price panel for cases/false-starts: #186 monthly (1966-01 → 2026-08).

## 7. Legs A/B/C/D and costs (frozen)

- A (baseline, pre-cost): frozen #183 structural returns (FULL: reproduced
  `port_ret`; ETF: reproduced #180-style implementation leg per #183 Phase B
  `impl_pre`-equivalent recomputation, asserted vs frozen file).
- B (overlay, PRE-cost): A weights + §4 active-month overlay; returns on the
  same backbone/proxy semantics with the same missing-data rule.
- C (overlay, POST-cost): `C = B − turnover_B × 0.0002` (turnover on final
  applied B weights, first panel month 0, #180 primary rate).
- D (exposure-matched control, POST-cost): constant `+d` Equity tilt from Cash
  EVERY panel month (same sizing function as §4 with X := d, same caps/zeros/
  cash floor, no macro read), returns + same cost convention. `d` = mean over
  the FULL panel of (E_B − E_A) using WEIGHTS ONLY, frozen and recorded BEFORE
  D performance is viewed; acceptance `|avgEq(D) − avgEq(B)| ≤ 0.01pp`.
- Diagnostic A_post = A − turnover_A × 0.0002 (like-for-like transparency;
  primary incremental is C−A per #182 convention + C−D post-cost pair).
- Cash reference for Sharpe-like: backbone T-bill accrual (both panels).

## 8. False-recovery definitions (frozen; ALL activations, not just bears)

Per activation (first active month m0, reference price P_ref = month-end close
of the month BEFORE m0 = signal-month close, tradable at decision):

- max further decline = min over next 12 closes of (P/P_ref − 1); lower-low
  flag if any close < P_ref; dd10 flag if any ≤ 0.90 × P_ref.
- Overlay P&L: cumulative (B−A) [FULL pre-cost pair; ETF pair reported too]
  over active months; 1/3/6/12mo horizons from m0 (NaN if censored by data end).
- exited_at_loss flag if cumulative active-period (B−A) < 0.
- Growth-reversal flag if exit reason C fired; defensive flag if exit D fired.
- Worst episodes ranked by cumulative active-period (B−A); worst 5 reported
  individually. Structural-only counterfactual always shown alongside.

## 9. Bear-market cases (frozen; reuse #186, NO SIGNAL invented)

For each #186 trough (1970-06 … 2022-09): trough date/price; first Growth
up-tick month; signal month (or NO SIGNAL with reason: conditions unmet /
episode consumed / unevaluable); structural +5pp add month (or none in +12mo);
months-early = structural_add − early_add (NaN if either missing); S&P rebound
at early add (R20 fraction, #186 definition); actual deployed pp (X and
partial path); cumulative (B−A)/(C−A) over active span; lower-low after entry.
Daily 2020 context shown at monthly resolution (no intramonth execution claimed).

## 10. Metrics (frozen; verbatim #183/#184 formulas)

Per A/B/C/D (FULL + ETF): CAGR, ann vol, Cash-excess ann, Sharpe-like, MaxDD,
worst month, pos-month fraction, downside vol, turnover ann, cost drag ann,
avg Equity/Cash, activations, exits (by reason A–E), avg holding months,
active-month fraction, avg actual added pp. Incrementals: C−A and C−D (CAGR
pp, MaxDD pp, Sharpe diff, worst-month diff, downside diff, turnover diff,
B/C/D monthly corr); crisis P&L per bear active span; best-1..3 episode share
of positive overlay P&L (episodes = activations; null-safe as #182).

## 11. Availability-delay stress (frozen bound, NOT vintage)

Rerun the WHOLE engine with DH inputs shifted +1/+2/+3mo (signal/exit logic,
thresholds, episodes byte-identical; only the information timestamp moves):
trigger coverage, effective entry dates, rebound-at-entry, FULL/ETF returns,
risk/drawdown, false-recovery table. Sign-flip or gate-flip vs primary is
reported as fragility. Never promoted into the rule; never called PIT.

## 12. Gates and verdict (frozen BEFORE performance; raw numbers rule)

Post-cost FULL panel unless noted; pp = ×100; Sharpe unitless:

- G1: incr CAGR (C−A) ≥ −0.15pp/yr.
- G2: ΔMaxDD (C−A) ≥ −1.5pp.
- G3: ΔSharpe (C−A) ≥ −0.03.
- G4: worst single-activation cumulative (B−A) ≥ −3.0pp.
- G5: median (structural_add − early_add) over bear troughs with BOTH present
  ≥ +1mo (early-entry value; NaN → fail).
- G6: vs exposure-matched: CAGR_C − CAGR_D ≥ −0.05pp AND
  Sharpe_C − Sharpe_D ≥ −0.02.
- G7: turnover increment (C−A) ≤ 20pp/yr.
- G8: +2mo stress incr CAGR ≥ −0.25pp/yr (robustness).

Verdict tree (exactly one, in order):
1. <3 activations OR FULL overlap <10y → `..._not_assessable`.
2. All G1–G8 pass → `early_recovery_equity_overlay_supported`.
3. G1 holds AND ≤2 fails AND neither G2 nor G4 fails →
   `..._suggestive_with_limitations`.
4. Else → `..._not_supported`.
Support needs MORE than CAGR (downside, timing, turnover, beyond-constant-Equity).

## 13. Deliverables (all paths contain `issue-187`) + firewall + product boundary

- `research/issue-187-early-recovery-prereg.md` (this file)
- `research/issue_187_overlay.py` (frozen stdlib: signal/episodes/sizing/exits/metrics/gates)
- `research/test_issue_187_overlay.py` (+ executed Node mirror test)
- `research/issue_187_build.mjs` (A/B/C/D panels, cases, false-starts, stress)
- `research/generated/issue-187/` manifest, trigger-timeline, monthly streams,
  performance, control-exposure, case-cards, false-recovery table, stress,
  sensitivity, policy + summary JSONs
- `research/decisions/issue-187-early-recovery-finding.md` (branch/HEADs/verdict
  + 7 Traditional-Chinese answers with exact figures + denominators)
- Builder MUST reproduce A legs exactly, freeze d weights-only, evaluate EVERY
  Low episode, never touch Pine/parents/main.

Firewall: after this prereg commit + first overlay result, do NOT change
entries, exits, episodes, sizing, timing, panels, costs, controls, false-start
defs, gates, or any frozen parent. Failure REPORTED, never repaired here.
Forbidden: threshold/holding/budget searches, V6.6, duration tactics,
episode cherry-picking, hidden false positives/eras, leverage/shorts,
pristine-OOS claims, Pine/production edits, merging. A failed rule is reported
as failed; no rescue rule in this issue. Research only.
Finding MUST contain `production_authorized=false`. Do not merge.
