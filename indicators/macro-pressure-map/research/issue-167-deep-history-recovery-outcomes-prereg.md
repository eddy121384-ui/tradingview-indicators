# Issue #167 — Deep-History 1966+ broad weak-state recovery × trajectory — Equity vs 10Y Treasury — Preregistration (frozen)

- Issue: [#167](https://github.com/eddy121384-ui/tradingview-indicators/issues/167)
- Branch: `research/issue-167-deep-history-recovery-outcomes`
- Base (pre-prereg) HEAD: `9c7598bffaacda6d70264a83b42dca7e3a8dfb7e` (Issue #166 final)
- This prereg is the FIRST Issue #167 commit on that branch.
- Status: PREREGISTRATION — frozen before any Issue #166 asset-return observation was loaded or viewed
- `outcome_data_loaded=false`
- `production_authorized=false`
- `revised_macro_history=true`
- `real_time_vintage_claim=false`

## 0. Non-contamination attestation (ordering mandate)

The issue body for #167 was revised **before any outcome inspection**. This prereg was
written from the revised Issue #167 text alone.

At the moment this file is committed:

- no Issue #166 equity return observation has been opened, loaded, parsed, or joined;
- no Issue #166 Treasury return observation has been opened, loaded, parsed, or joined;
- no macro × outcome join has been computed;
- only the frozen Issue #160 macro series has been read, and only its coverage/columns.

The Issue #166 return files are declared below by path so the frozen evaluator can be
specified, but their contents were **not** read in this session before this commit.
Exact file column names, coverage, and SHA256 values are to be recorded verbatim in the
finding **after** this commit exists.

Sequence (mandatory, non-negotiable):

1. write this prereg;
2. commit it;
3. record the prereg commit SHA;
4. only then load the Issue #166 return files.

Any later change to any frozen quantity below requires a **new issue**.

## 1. Research lineage (frozen inputs — do not alter)

### 1.1 Macro source — Deep-History v0.1 (Issue #160)

- Frozen model commit: `cc331bf11591ab49c6f5a5023cfee39b2cf09fde`
  (verified to be an ancestor of the branch HEAD at prereg time)
- Frozen monthly macro CSV path:
  `indicators/macro-pressure-map/research/generated/issue-160/deep-history-v01-monthly.csv`
- Frozen monthly macro CSV SHA256 (canonical git blob content):

  `42516418ec8d1ce981d1b4bc05e2ae86809d6acbf5de63dccbad515db507dcfc`

  Verification note: on a Windows checkout with `core.autocrlf=true` the
  working-tree file hashes differently (CRLF conversion) at
  `a2e9037d80f78fbccd549966d5b2716daf50c3a585e623a569fb33adb2a0583b`.
  The canonical frozen hash is the **git blob** hash, which matches the expected
  value exactly (`git show HEAD:<path> | sha256sum`). The evaluator MUST verify the
  blob hash, not the CRLF working-tree hash.
- Macro columns used: `date`, `growth_dh` (→ `Growth_DH`), `inflation_dh` (→ `Inflation_DH`).
  Components `g1..g5`, `i1..i5` are **not** used by this issue.
- Observed macro coverage (recorded at prereg time, macro only):
  both-axes-valid months = 723, first `1966-03`, last `2026-08`.
  Growth valid 723 (`1966-03`→`2026-08`); Inflation valid 735 (`1965-03`→`2026-08`).

Frozen usage rules — do NOT alter components, weights, axes, scaling, or smoothing.
Do NOT use the Issue #165 v0.2 turn layer. Use `Growth_DH` and `Inflation_DH` exactly
as stored in the frozen CSV.

### 1.2 Outcome backbone (Issue #166) — declared, NOT yet opened

- Issue #166 final commit: `9c7598bffaacda6d70264a83b42dca7e3a8dfb7e`
- Equity: Fama-French US market monthly total return.
- Treasury: frozen synthetic coupon-inclusive ~10Y CMT monthly total return.
- Declared paths (contents unread at prereg time):
  - `indicators/macro-pressure-map/research/generated/issue-166/equity-monthly-total-returns.csv`
  - `indicators/macro-pressure-map/research/generated/issue-166/treasury-monthly-total-returns.csv`
- No new market data is fetched. No TradingView MCP is used or repaired for this issue.
  All required inputs are already frozen in the repository.

## 2. Frozen PRIMARY macro universe and state

For a completed macro month `t`:

```
G_t = Growth_DH_t
I_t = Inflation_DH_t
```

Primary eligible state (`DH_NONSTRONG_DISINFLATIONARY_STATE`):

```
G_t <= +10
AND
I_t <= +10
```

Interpretation:

- Growth is weak-to-neutral, **not** strongly expansionary.
- Inflation is low-to-neutral, **not** strongly inflationary.

This intentionally includes mild slowdown / soft-landing / transition states.

**This is NOT a recession definition.**

A **primary-state episode** is a sequence of consecutive calendar months satisfying the
primary state. Episode boundaries are calendar-contiguous: a month is part of the same
episode only if the immediately preceding calendar month also satisfied the primary state
(and was macro-valid).

## 3. Pre-specified severity subgroups (diagnostic only)

Every primary-state month belongs to exactly one subgroup:

- **A. Deep dual-weak**: `G_t < -10 AND I_t < -10`
- **B. Mild / transition weak**: primary state is true, but Deep dual-weak is false.
  This includes Growth low + Inflation neutral, Growth neutral + Inflation low, and
  Growth neutral + Inflation neutral.

These subgroups are **diagnostic only**. They do NOT replace the combined primary
hypothesis and cannot rescue a failed primary verdict.

## 4. Pre-specified secondary high-inflation slowdown cohort

`G_t <= +10 AND I_t > +10`

Same 3-month trajectory and publication-lag rules. Analyzed separately, and only
**after** the primary verdict is frozen. Secondary/descriptive only; cannot rescue the
primary test.

## 5. Frozen trajectory definition

For each axis:

```
d3Growth_t    = Growth_DH_t    - Growth_DH_(t-3)
d3Inflation_t = Inflation_DH_t - Inflation_DH_(t-3)
```

Positive recovery trajectory:

```
d3Growth_t > 0
AND
d3Inflation_t > 0
```

A **PRIMARY signal** at macro month `t` requires all three:

1. primary macro state is true;
2. `d3Growth_t > 0`;
3. `d3Inflation_t > 0`.

No magnitude threshold. No asynchronous window. No local-turn requirement.
No smoothing optimization. `t-3` must be a macro-valid month; otherwise `t` is not
trajectory-eligible.

## 6. Frozen first-trigger rule

Within each contiguous primary-state episode, **only the FIRST qualifying month** is a
primary signal. Later qualifying months in the same episode are excluded as repeated
signals. Record for each trigger whether the trigger month's severity was:

- Deep dual-weak; or
- Mild / transition weak.

## 7. Frozen primary controls

- Eligible primary-state months **before** first trajectory completion are controls.
- For an otherwise-eligible primary-state episode that **never triggers**, all
  otherwise eligible months remain controls.
- For an episode that **triggers**, post-trigger months are **excluded** from the
  primary comparison (neither signal nor control).

## 8. Frozen publication-lag / availability rule

The Deep-History macro series are revised historical data. This is **not** a
real-time-vintage trading claim. This is an historical association study.

```
macro state month        = t
signal available month   = t+1
first payoff month       = t+2
```

No return from month `t` or `t+1` may enter the payoff. This timing applies
**identically** to signals and controls. Record `macro_state_month` and
`signal_available_month` for every observation row.

## 9. Frozen primary payoff

Primary: next 3 completed monthly compounded total-return spread beginning at `t+2`:

```
Equity_3M_TR - Treasury10Y_3M_TR
```

Report both legs separately.

Secondary descriptive horizons only: `1M`, `6M`, `12M`. Secondary horizons cannot
rescue the primary result.

## 10. Frozen inference

Primary comparison: first-trigger observations vs eligible pre-trigger / never-trigger
controls.

Deterministic **primary-state-episode cluster bootstrap**:

- resample whole primary-state episodes (with replacement);
- each resample draws episodes, not months;
- 10,000 **valid** replications (replications that cannot form a statistic are discarded
  and replaced until 10,000 valid ones exist);
- fixed seed: **`19660101`**;
- percentile 95% CI on the signal-minus-control incremental mean 3M spread.

No IID monthly bootstrap is permitted as primary inference.

## 11. Frozen eras (report all; do not select the best)

- `1966-01` through `1984-12`
- `1985-01` through `2004-12`
- `2005-01` through `2026-08`

## 12. Frozen robustness checks (after primary result)

1. leave-one-trigger-episode-out incremental mean;
2. strongest positive trigger contribution share
   (strongest positive trigger episode's share of total positive trigger contribution);
3. one-additional-month implementation delay:
   - normal first payoff `t+2`;
   - delayed first payoff `t+3`;
   - same 3M horizon;
   - same delay applied to signals and controls.

No robustness check may rescue a failed primary gate except as explicitly encoded in §13.

## 13. Primary gates and verdict mapping

Verdict `deep_history_recovery_outcome_supported` only if ALL are true:

1. at least 8 independent first-trigger primary-state episodes;
2. signal mean 3M Equity-minus-Treasury spread > 0;
3. signal minus control mean > 0;
4. episode-cluster bootstrap 95% CI lower bound > 0;
5. at least 2 of 3 fixed eras contain both signal and control observations;
6. at least 2 of 3 evaluable eras have positive incremental mean; if only 2 are
   evaluable, both must be positive;
7. every evaluable leave-one-trigger-episode-out incremental mean remains > 0;
8. strongest positive trigger episode contributes <= 50% of total positive trigger
   contribution;
9. one-additional-month delayed implementation preserves positive incremental sign.

Verdict mapping:

- if first-trigger episodes < 8 → `deep_history_recovery_outcome_inconclusive_sample`
- else if primary incremental direction is positive but one or more robustness gates fail
  → `deep_history_recovery_outcome_suggestive_not_robust`
- else → `deep_history_recovery_outcome_not_supported`

No discretionary rescue. Exactly one verdict is emitted.

## 14. Required pre-specified subgroup report

After the primary verdict is frozen, split PRIMARY triggers by trigger-month severity
(Deep dual-weak trigger / Mild-transition weak trigger). For each report:

- n
- 3M Equity-minus-Treasury mean / median / positive fraction
- Equity leg mean
- Treasury leg mean
- era distribution

Do NOT claim either subgroup as a validated rule from this issue. Do NOT select the
better subgroup for production or follow-up without a new preregistered issue.

## 15. Secondary high-inflation slowdown report

After the primary verdict and subgroup table are frozen, for `G<=+10 AND I>+10` apply
the same `d3G>0 and d3I>0`; first trigger per contiguous secondary-state episode;
`t+1` availability; payoff starting `t+2`; `1M/3M/6M/12M` descriptive outcomes.

No formal rescue gate. Purpose is to examine stagflationary / high-inflation recovery
states only.

## 16. Secondary descriptive 3×3 map (exploratory only)

Only AFTER the primary verdict is frozen, produce the full 3×3 map.

Growth bands: Low `< -10`, Neutral `[-10,+10]`, High `> +10`. (Boundaries inclusive as
written; a value of exactly `+10` is Neutral, exactly `-10` is Neutral.)
Inflation bands: same.

For each of the 9 states report: months; episodes; 3M Equity-minus-Treasury
mean / median / positive fraction; Equity leg mean; Treasury leg mean.

Also report trajectory quadrants: `d3Growth >0 / <=0` × `d3Inflation >0 / <=0`.

Exploratory only. Do NOT select a new signal from this table inside Issue #167.

## 17. Frozen evaluator, outputs, and flags

Deliverables (Issue #167):

- `indicators/macro-pressure-map/research/issue-167-deep-history-recovery-outcomes-prereg.md` (this file)
- `indicators/macro-pressure-map/research/issue_167_deep_history_recovery_outcomes.py` (frozen evaluator)
- `indicators/macro-pressure-map/research/test_issue_167_deep_history_recovery_outcomes.py` (tests)
- `indicators/macro-pressure-map/research/generated/issue-167/recovery-signal-control.csv`
- `indicators/macro-pressure-map/research/generated/issue-167/recovery-primary-episodes.csv`
- `indicators/macro-pressure-map/research/generated/issue-167/recovery-primary-result.json`
- `indicators/macro-pressure-map/research/generated/issue-167/recovery-severity-subgroups.csv`
- `indicators/macro-pressure-map/research/generated/issue-167/recovery-high-inflation-slowdown.csv`
- `indicators/macro-pressure-map/research/generated/issue-167/recovery-descriptive-3x3-map.csv`
- `indicators/macro-pressure-map/research/decisions/issue-167-recovery-outcomes-finding.md`

The evaluator MUST:

- verify the frozen macro CSV git-blob SHA256 before use and abort on mismatch;
- record the SHA256 of each Issue #166 return file actually used;
- import the frozen macro series without transformation of components/weights/scaling;
- emit `outcome_data_loaded=true` together with
  `production_authorized=false`, `revised_macro_history=true`,
  `real_time_vintage_claim=false` on every durable result;
- write generated files only under `generated/issue-167/` and never overwrite
  `research/decisions/` or other issues' artifacts.

## 18. Anti-tuning firewall

After this prereg commit and the first outcome inspection, do NOT change: state
thresholds; trajectory horizon; primary universe; subgroup definitions;
signal/control definitions; publication lag; payoff horizon; asset pair; bootstrap
method; the fixed bootstrap seed; temporal eras; or gates. Any such change requires a
new issue.

Prohibited inside Issue #167: reviewing outcomes and then re-cutting thresholds;
adding smoothing; using the #165 v0.2 turn layer; fetching new market data;
modifying Pine Script; merging automatically.

## 19. Product boundary

Research only. Even a positive result does NOT automatically authorize a V6.6/V6.7
production or Action Layer rule. Do not modify Pine. Do not merge automatically.
