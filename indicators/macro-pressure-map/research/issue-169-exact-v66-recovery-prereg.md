# Issue #169 — Exact V6.6 broad weak-state recovery — PREREGISTRATION (frozen)

- Issue: [#169](https://github.com/eddy121384-ui/tradingview-indicators/issues/169)
- Branch: `research/issue-169-exact-v66-recovery-translation`
- Base verified: `8749a4f451705401b90c2e6a0047dd8ed526a77f` (Issue #167 final)
  with zero Issue #169 commits at prereg time; worktree clean.
- Status: PREREGISTRATION — frozen BEFORE opening, loading, parsing, joining,
  or inspecting ANY asset-return observation in this task.
- This is repeated-sample semantic translation / robustness, NOT pristine OOS.
  A positive result must NOT be described as independent confirmation.
- `outcome_data_loaded=false` (at prereg time; true only after this commit)
- `production_authorized=false`
- `repeated_modern_sample=true`
- `pristine_oos_claim=false`

No outcome result is reported here. After this commit, nothing below may change
in response to results (thresholds, trajectory, rules, controls, horizons,
backbone, timing, bootstrap, segments, gates); any redesign needs a new issue.
No return file was opened to write this document; its content derives solely
from the Issue #169 contract. Do NOT reconstruct or retune V6.6.

## 1. Frozen inputs (read-only; hash-verified after this commit)

- Exact V6.6 monthly snapshot (Issue #133): SHA256
  `1d03923503e7fe82a69b033897484c48aa646279ecf70164d090ed62a5a70719`.
  Use `date` / `GPI` / `IPI` only (plus `regime` solely where descriptively
  needed). Snapshot schema/hash/coverage only may be checked pre-prereg; no
  conditioned outcomes.
- Equity backbone (Issue #166):
  `indicators/macro-pressure-map/research/generated/issue-166/equity-monthly-total-returns.csv`
  (Fama-French US market monthly TR, `Mkt-RF + RF`, decimal).
- Treasury backbone (Issue #166):
  `indicators/macro-pressure-map/research/generated/issue-166/treasury-monthly-total-returns.csv`
  (frozen synthetic coupon-inclusive ~10Y CMT monthly TR, decimal).

## 2. Frozen PRIMARY state (exact V6.6)

At completed exact month t: `G_t = GPI_t`, `I_t = IPI_t` (both finite required).

Primary eligible state `V66_NONSTRONG_DISINFLATIONARY_STATE`:
`G_t <= +10 AND I_t <= +10`. NOT a recession definition.
A state episode = maximal run of consecutive calendar months satisfying it
(a non-finite month breaks the run).

## 3. Frozen trajectory, triggers, controls, subgroups

- `d3G_t = GPI_t − GPI_{t−3}`, `d3I_t = IPI_t − IPI_{t−3}` (positional lags;
  missing neighbor ⇒ not positive, no interpolation).
- Completion at t: state true AND `d3G_t > 0` AND `d3I_t > 0`. No magnitude
  threshold, turn rule, asynchronous window, or smoothing.
- First trigger per contiguous episode only; later qualifiers excluded.
- Severity at signal month (diagnostic only): Deep dual-weak
  (`GPI < −10 AND IPI < −10`) vs Mild/transition weak (primary true, Deep
  false). Subgroups cannot replace or rescue the combined primary.
- Controls: eligible pre-trigger months in triggered episodes; all eligible
  months in never-triggered episodes; post-trigger months excluded.
  Eligibility = state true (finite G, I); d3 evaluability NOT required.

## 4. Frozen timing and payoffs (matched to #167)

Signal state month t; availability t+1; first payoff month t+2. No return from
t or t+1 enters the PRIMARY payoff. Record both months per observation.
Primary: next 3 completed monthly compounded `Equity_3M_TR − Treasury10Y_3M_TR`
from t+2; report both legs. A 3M payoff needs all 3 return months in BOTH
backbones. Secondary descriptive horizons (same t+2 start): 1M / 6M / 12M —
cannot rescue primary.

## 5. Frozen inference, segments, robustness

Episode-cluster bootstrap over whole primary-state episodes (triggered +
never-triggered, carrying eligible observations as §3): statistic = signal
mean − control mean; **10,000 valid replications** (valid = ≥1 signal and ≥1
control; redraw, max 1,000,000 draws; report valid count); 95% CI = 2.5/97.5
percentiles. Fixed seed **169**; mulberry32 RNG (see evaluator). No IID
monthly bootstrap as primary CI. Segments by signal month t: pre-2020,
2020–2022, 2023+ (report all; evaluable = ≥1 signal + ≥1 control,
3M-payoff-complete). Robustness: (1) leave-one-trigger-episode-out incremental
means (evaluable = remainder holds ≥1 signal + ≥1 control; report evaluable
count); (2) strongest-positive-trigger share = max positive trigger payoff /
sum of positive trigger payoffs (no positives ⇒ gate fails); (3) t+3 delayed
start, same 3M horizon, both arms.

## 6. Frozen gates and verdict mapping

Supported (`exact_v66_recovery_translation_supported`) only if ALL true:
1. ≥8 independent first-trigger episodes. 2. signal mean 3M spread > 0.
3. signal − control > 0. 4. bootstrap 95% CI lower > 0. 5. ≥2 segments hold
both signal and control. 6. ≥2/3 evaluable segments positive (if exactly 2
evaluable, both). 7. every evaluable LOO incremental > 0. 8. strongest
positive share ≤ 50%. 9. t+3 delay preserves positive incremental sign.
Mapping (exact): gate 1 fails ⇒
`exact_v66_recovery_translation_inconclusive_sample`. Else if all pass ⇒
supported. Else if gates 2 AND 3 pass with ≥1 of gates 4–9 failing ⇒
`exact_v66_recovery_translation_directionally_consistent_not_robust`.
Else ⇒ `exact_v66_recovery_translation_not_supported`. (Input-identity failure
aborts as inconclusive.) No discretionary rescue.

## 7. Post-verdict secondaries (frozen specs, exploratory only)

- Native-market timing: payoff from t+1 (t+1..t+3), descriptive; cannot rescue.
- SPY/TLT repeat ONLY if frozen modern SPY/TLT total-return data already exist
  in the repository (check post-verdict; fetch nothing new); secondary only.
- Deep vs Mild trigger diagnostics (n, means, legs, era split per group).
- Cross-layer (exact V6.6 vs frozen DH v0.1, common modern months, neither model
  changed): primary-state month agreement; exact vs DH trigger counts; matches
  ±1m / ±3m (greedy chronological, each trigger used once); median matched lag;
  matched vs unmatched exact-trigger outcome means (descriptive). High overlap
  is NOT required (#160: layers not interchangeable); the question is same
  rule → same outcome direction.

## 8. Required outputs (issue-169 paths)

- `indicators/macro-pressure-map/research/issue-169-exact-v66-recovery-prereg.md` (this file)
- `indicators/macro-pressure-map/research/issue_169_exact_v66_recovery.py` (frozen evaluator, pure stdlib)
- `indicators/macro-pressure-map/research/test_issue_169_exact_v66_recovery.py` (synthetic-only tests)
- `indicators/macro-pressure-map/research/generated/issue-169/recovery-signal-control.csv`
- `indicators/macro-pressure-map/research/generated/issue-169/recovery-episodes.csv`
- `indicators/macro-pressure-map/research/generated/issue-169/recovery-results.json`
- `indicators/macro-pressure-map/research/generated/issue-169/recovery-subgroups.csv`
- `indicators/macro-pressure-map/research/generated/issue-169/recovery-crosslayer.csv`
- `indicators/macro-pressure-map/research/decisions/issue-169-exact-v66-recovery-finding.md`

Every durable finding states: `outcome_data_loaded=true`,
`production_authorized=false`, `repeated_modern_sample=true`,
`pristine_oos_claim=false`. Research only; no production/Action-Layer
authorization. Do not modify Pine. Do not merge. Do not alter #167/#136.
