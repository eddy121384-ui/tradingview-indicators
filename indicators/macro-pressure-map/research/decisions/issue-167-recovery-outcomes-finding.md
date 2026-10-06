# Issue #167 — Deep-History 1966+ broad weak-state recovery × trajectory — Equity vs 10Y Treasury — Finding

- Issue: [#167](https://github.com/eddy121384-ui/tradingview-indicators/issues/167)
- Branch: `research/issue-167-deep-history-recovery-outcomes`
- Base HEAD before this issue: `9c7598bffaacda6d70264a83b42dca7e3a8dfb7e` (Issue #166 final)
- Preregistration commit (created and committed BEFORE any outcome file was opened):
  **`b88ff35358215057d6bf3e0375fed560eb61322c`**
- Formal verdict: **`deep_history_recovery_outcome_suggestive_not_robust`**
- `outcome_data_loaded=true`
- `production_authorized=false`
- `revised_macro_history=true`
- `real_time_vintage_claim=false`

Research only. Not a real-time-vintage trading claim. No Pine change. Do not merge without
explicit approval.

## 1. Bottom line

Using the frozen Deep-History v0.1 axes, the broad non-strong / disinflationary state
(`Growth_DH <= +10 AND Inflation_DH <= +10`) followed by a positive 3-month trajectory on
**both** axes is associated with a **directionally positive but not statistically robust**
excess return of US equity over ~10Y Treasury duration.

- Signal mean next-3M Equity-minus-Treasury spread: **+4.45pp**
- Control mean: **+2.11pp**
- Incremental (signal − control): **+2.35pp**
- Episode-cluster bootstrap 95% CI: **[-0.55pp, +5.53pp]** → **contains zero**

Eight of nine frozen gates pass. Gate 4 (bootstrap CI lower bound > 0) fails, so the
preregistered mapping yields `..._suggestive_not_robust`, **not** `..._supported`.
No discretionary rescue is applied.

## 2. Frozen inputs actually used

| Input | Path | SHA256 |
|---|---|---|
| Macro (frozen) | `research/generated/issue-160/deep-history-v01-monthly.csv` | `42516418ec8d1ce981d1b4bc05e2ae86809d6acbf5de63dccbad515db507dcfc` (canonical git blob — **verified**) |
| Equity | `research/generated/issue-166/equity-monthly-total-returns.csv` | `ff75a22aa1b620de37b34d09e2bf863b055607ab4dfd6e1c881cf0843705bdcd` |
| Treasury | `research/generated/issue-166/treasury-monthly-total-returns.csv` | `afb62d50cd151f707a55eda2a033bc5c306d93679de4ec3f101c76c9fac360e0` |

- Macro columns consumed: `date`, `growth_dh`, `inflation_dh` only (no `g1..g5`, `i1..i5`).
- Macro coverage in the study window: **723 valid months, 1966-03 → 2026-08**.
  Note the frozen series has **holes at 2025-10, 2025-11 and 2026-01**; those months are
  treated as macro-invalid (they cannot be in an episode and cannot supply `t-3`), per
  prereg sections 2 and 5.
- Windows-CRLF note: the frozen macro CSV hashes differently in a Windows working tree
  (`core.autocrlf=true`). The evaluator verifies the **git blob** hash, which matches the
  frozen value exactly; it aborts on mismatch.
- No new market data was fetched. TradingView MCP was not used, required, or repaired.
- Frozen model commit `cc331bf11591ab49c6f5a5023cfee39b2cf09fde` verified as an ancestor
  of the base HEAD.

## 3. Primary result (frozen 3M horizon, t+2 start)

Universe: primary-state months in 1966-01…2026-08, first-qualifying-month-per-episode
signals and pre-trigger / never-trigger controls, restricted to observations with a
complete 3M payoff (identical rule for both roles).

- Primary-state episodes: **70**; of these **27 triggered**.
- Signal observations: **27** (all with 3M payoff).
- Control observations: **193** total, **191** with 3M payoff.

| Statistic | Signal | Control |
|---|---|---|
| n (3M payoff) | 27 | 191 |
| mean 3M spread | **+4.45pp** | **+2.11pp** |
| median 3M spread | +4.68pp | +1.79pp |
| positive fraction | 66.7% | 60.7% |

Incremental mean (signal − control): **+2.35pp**.

Episode-cluster bootstrap (resamples whole primary-state episodes, 10,000 valid
replications, fixed seed `19660101`, 68 evaluable clusters): mean **+2.35pp**,
95% percentile CI **[-0.55pp, +5.53pp]**.

## 4. Frozen gates

| # | Gate | Result |
|---|---|---|
| 1 | ≥ 8 independent first-trigger episodes | **PASS** (27) |
| 2 | signal mean 3M spread > 0 | **PASS** (+4.45pp) |
| 3 | signal − control mean > 0 | **PASS** (+2.35pp) |
| 4 | bootstrap 95% CI lower bound > 0 | **FAIL** (-0.55pp) |
| 5 | ≥ 2 of 3 eras contain signal and control | **PASS** (3/3 evaluable) |
| 6 | ≥ 2 of 3 evaluable eras positive incremental | **PASS** (2/3) |
| 7 | every leave-one-trigger-episode-out incremental > 0 | **PASS** (27/27) |
| 8 | strongest positive trigger contributes ≤ 50% | **PASS** (15.96%) |
| 9 | one-month delayed implementation stays positive | **PASS** (+2.36pp) |

Per-era incremental mean (3M):

- 1966-1984: **+3.11pp**
- 1985-2004: **-0.60pp**
- 2005-2026: **+4.20pp**

Robustness detail:

- Leave-one-trigger-episode-out (whole episode removed, signal + its controls): 27
  evaluable, range **+1.62pp … +2.76pp**, all > 0.
- Strongest positive trigger contribution share: **15.96%** (episode 62) — well under
  the 50% gate; nine of 27 trigger episodes had a *negative* 3M spread, so the
  incremental mean is not a single-episode artifact.
- One-additional-month implementation delay (same 3M horizon, first payoff t+3, applied
  identically to signals and controls): incremental **+2.36pp** — sign preserved.

## 5. Pre-specified subgroup report (diagnostic only)

Split of the 27 primary triggers by trigger-month severity:

| Subgroup | n | mean 3M | median 3M | positive frac | equity mean | treasury mean | eras (66-84 / 85-04 / 05-26) |
|---|---|---|---|---|---|---|---|
| Deep dual-weak (`G<-10 AND I<-10`) | 5 | +3.07pp | **-0.77pp** | 40.0% | +9.51pp | +6.43pp | 1 / 2 / 2 |
| Mild / transition weak | 22 | +4.76pp | +4.85pp | 72.7% | +4.79pp | +0.03pp | 5 / 9 / 8 |

Neither subgroup is claimed as a validated rule. The Deep subgroup is 5 observations with
a **negative median**; nothing here should be read as evidence that deep dual-weak is the
better signal. No subgroup may be promoted to production or follow-up without a new
preregistered issue.

## 6. Secondary high-inflation slowdown cohort (descriptive only, no gate)

State `Growth_DH <= +10 AND Inflation_DH > +10`, same trajectory / timing rules:
**61 episodes, 25 first triggers** (1M), 24 with 3M/6M/12M payoff, 111 controls.

| Horizon | Signal mean | Control mean | Signal positive frac |
|---|---|---|---|
| 1M | +1.00pp | -0.23pp | 64.0% |
| 3M | **-0.55pp** | +0.10pp | 54.2% |
| 6M | **-1.02pp** | +1.98pp | 37.5% |
| 12M | +1.70pp | +4.10pp | 62.5% |

The stagflationary cohort shows **no** positive signal edge at 3M or 6M and a negative
one relative to controls. This is reported because the issue pre-specified it; it carries
no gate and cannot rescue or contradict the primary verdict.

## 7. Secondary descriptive 3×3 map (exploratory only)

3M Equity-minus-Treasury mean by frozen band (Low `< -10`, Neutral `[-10,+10]`, High `> +10`;
boundaries inclusive to Neutral). Months sum to 723 = all macro-valid months.

| Growth \ Inflation | Low | Neutral | High |
|---|---|---|---|
| **Low** | +1.48pp (62m) | +2.19pp (45m) | -0.61pp (83m) |
| **Neutral** | **+3.01pp** (116m) | +2.19pp (91m) | -0.06pp (112m) |
| **High** | +1.93pp (62m) | +1.72pp (80m) | +0.91pp (72m) |

Trajectory quadrants (exploratory, all macro-valid months with `t-3` available):

| Quadrant | months | 3M mean |
|---|---|---|
| `d3G>0 / d3I>0` | 186 | +0.98pp |
| `d3G>0 / d3I<=0` | 164 | +2.24pp |
| `d3G<=0 / d3I>0` | 183 | +0.65pp |
| `d3G<=0 / d3I<=0` | 185 | +1.85pp |

Note for the record: in this exploratory cut the *combined* positive-trajectory quadrant is
**not** the highest-mean cell. That is an observation about a table generated under a frozen
verdict, not a signal selection. **No new signal is selected from this table inside Issue
#167.**

## 8. Implementation decisions (prereg-consistent, non-tunable)

These were fixed by the prereg's wording and are recorded here for auditability. None was
chosen after seeing outcomes, and none changes a threshold, horizon, universe or gate.

1. **Payoff availability.** An observation enters the primary comparison only if all three
   payoff months (`t+2`, `t+3`, `t+4`) exist in both return series. No imputation, no
   partial compounding; the identical rule applies to signals and controls. This is why 2
   of 193 controls (and 0 of 27 signals) drop out: equity returns end 2026-08, so the
   theoretical last primary month with a complete 3M payoff is `t = 2026-04` (the actual
   last primary observation in this run is `2026-03`).
2. **Episode contiguity and macro holes.** An episode continues only if the immediately
   preceding *calendar* month is macro-valid and in-state (prereg §2). The frozen holes at
   2025-10, 2025-11 and 2026-01 therefore break episode contiguity and make `t-3`
   unavailable for 2026-02 and 2026-04.
3. **Bootstrap cluster set.** Whole episodes contributing at least one primary-universe
   observation (68 of 70). A draw containing no signal or no control observation is
   discarded and re-drawn until 10,000 **valid** replications are collected.
4. **Gate 1 count.** Independent first-trigger primary-state episodes evaluable in the
   primary comparison (27 here — identical to the raw trigger count).
5. **Leave-one-out.** Removes the entire trigger episode (its signal and its controls), so
   the check is cluster-level, not observation-level.
6. **Trigger contribution.** An episode's contribution is its signal's 3M spread; the share
   is the largest positive contribution over the sum of positive contributions.
7. **Era assignment** by macro state month `t`.
8. **Toolchain.** Implemented in the Python standard library only (no pandas/numpy), which
   removes any dependency on a locally-installed scientific stack and makes the fixed-seed
   bootstrap bit-reproducible. Verified: identical result JSON across reruns
   (`sha256(12)=178677cb8caa`).

## 9. Bugs caught before finalizing

Disclosed in the same spirit as Issue #166, because each was found by validation rather
than by the failing path being obvious:

1. `mean()` did not filter `None` late-window payoffs, crashing the 3×3 map builder on
   `NoneType`. Fixed; the fix does not touch any gate or the primary verdict.
2. The secondary high-inflation cohort reused the **primary** `qualifying` flag. Because a
   month with `Inflation_DH > +10` can never satisfy the primary state, this suppressed
   every secondary trigger (61 episodes, 0 signals — flagged as implausible). Fixed to
   gate qualification on the cohort's own state; regression test added. Primary result
   unaffected.
3. `main()` and the tests used two divergent episode builders, which left
   `trigger_severity` blank in the emitted episodes CSV. Consolidated to a single builder
   with an alias; regression test added. Primary result unaffected.

## 10. Limitations

- Historical association only. Deep-History is **revised** macro history, not real-time
  vintage data; the t+1 availability assumption cannot be validated from these inputs.
  `real_time_vintage_claim=false`.
- Equity is Fama-French/CRSP value-weight market return, not exactly the S&P 500.
- Treasury is a **synthetic** coupon-inclusive ~10Y CMT total return (single-yield,
  par-coupon, month-end, weekly-sampled yields) — not an observed index, and ~8y duration
  against a 10Y label.
- Both backbones carry CRSP/FRED vintage-revision policies (see Issue #166 §1–§2).
- The primary sample is 27 signals and 191 controls, and the controls are heavily
  serially overlapping months inside long episodes. The episode-cluster bootstrap is the
  preregistered answer to that dependence; the wide CI is the honest consequence.
- One of three eras (1985-2004) has a negative incremental mean.
- No multiple-testing adjustment is claimed beyond the frozen gate structure.

## 11. Artifacts

- `research/issue-167-deep-history-recovery-outcomes-prereg.md` (prereg commit `b88ff35…`)
- `research/issue_167_deep_history_recovery_outcomes.py` (frozen evaluator)
- `research/test_issue_167_deep_history_recovery_outcomes.py` (29 tests, all passing)
- `research/generated/issue-167/recovery-signal-control.csv` (220 observation rows: 27 signals, 193 controls)
- `research/generated/issue-167/recovery-primary-episodes.csv` (70 episodes)
- `research/generated/issue-167/recovery-primary-result.json`
- `research/generated/issue-167/recovery-severity-subgroups.csv`
- `research/generated/issue-167/recovery-high-inflation-slowdown.csv`
- `research/generated/issue-167/recovery-descriptive-3x3-map.csv`
- `research/generated/issue-167/recovery-trajectory-quadrants.csv`

## 12. Explicit confirmations

- The preregistration was written and committed (`b88ff35358215057d6bf3e0375fed560eb61322c`)
  **before** any Issue #166 return observation was opened, and the branch had zero Issue
  #167 commits before that commit. No contamination occurred.
- The CURRENT (revised) GitHub Issue #167 body was read in full via the GitHub MCP;
  no cached or older version was used. The issue body itself contains the broad-state
  definition (`Growth_DH <= +10 AND Inflation_DH <= +10`), with `< -10 / < -10` demoted to
  the Deep dual-weak subgroup.
- No frozen quantity was changed after outcomes were seen: thresholds, trajectory horizon,
  universe, subgroups, signal/control rules, publication lag, payoff horizon, asset pair,
  bootstrap method, seed, eras and gates all match the prereg.
- `production_authorized=false` — no production code, no Pine, no merge.
