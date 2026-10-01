# Issue #136 Preregistration — R7 Asynchronous Bottoming / Turning Point

Status: **FROZEN BEFORE ISSUE #136 OUTCOME ANALYSIS**

Issue: #136  
Branch: `research/issue-136-r7-async-turn`

## Research question

Within exact V6.6 Regime 7 — Slowdown / Disinflation — does **asynchronous completion of a recent GPI and IPI turning process** predict stronger forward Equity-vs-Duration performance than Regime-7 observations where that process has not yet completed?

This is a new hypothesis following Issue #133's frozen `trajectory_evidence_inconclusive` result. Issue #133 is not retuned or overwritten.

## Frozen source lineage

### Exact-modern signal source

Reuse the Issue #133 exact monthly snapshot.

- normalized CSV SHA256: `1d03923503e7fe82a69b033897484c48aa646279ecf70164d090ed62a5a70719`
- Issue #133 source head: `752755d423c1a13415d8ad3647c3def74adaa2d8`
- exact-modern primary window: 2007+
- pre-2007 partial-component history remains audit context only.

### Exact-modern asset source

Reuse the frozen Issue #127 / #64 adjusted-price backbone:

- source head: `4d48f58582a7cf5322adad0beda72dbe15545fed`
- primary assets: SPY and TLT
- no outcome forward-fill.

### Long-history source

Reuse frozen Issue #91 / #121 HMRA and underlying-asset pipeline:

- source head: `3d479f1255337587582627d95b7d5e3a2940599c`
- HMRA is a structural analogue, not exact V6.6.
- payoff assets: S&P 500 total return and 10Y U.S. Treasury total return.
- strict causal timing: `state_t -> return_(t+2)`.
- no ETF wrappers in the long-history primary analysis.

## Layer A — exact modern V6.6

For raw monthly axis X in {GPI, IPI}:

`dX_t = X_t - X_(t-1)`.

A causal axis turning event occurs at completed month t when:

- `dX_t > 0`; and
- `dX_(t-1) <= 0`.

No slope magnitude threshold is allowed.

### Frozen asynchronous completion signal

At completed month t, `R7_ASYNC_TURN` is true when:

1. exact V6.6 regime at t = Regime 7;
2. GPI has a turning event at t, t-1, or t-2;
3. IPI has a turning event at t, t-1, or t-2.

The two axes need not turn in the same month.

The modern completion window is frozen at **three completed monthly observations**.

### First-trigger rule

Within each contiguous Regime-7 episode, only the first month satisfying `R7_ASYNC_TURN` is a primary signal observation.

Later R7 months in that already-triggered episode cannot become additional primary signals.

### Primary control

Eligible Regime-7 months that occur before asynchronous completion are primary controls.

For an R7 episode that never triggers, all otherwise eligible R7 months may remain controls.

For an episode that triggers, months after its first trigger are excluded from primary control.

### Primary payoff

Primary:

next **3 completed monthly** total-return spread:

`SPY_3M_total_return - TLT_3M_total_return`.

Secondary, descriptive only:

- next 1M spread;
- next 6M spread.

Secondary horizons cannot rescue a failed 3M primary result.

### Primary inference

Inference must account for repeated observations within an R7 episode.

Use a deterministic **R7-episode cluster bootstrap** for the incremental primary mean. Resample whole R7 episodes with replacement, preserving all eligible observations belonging to a sampled episode.

The IID monthly bootstrap is not an allowed primary CI.

### Modern gate

Verdict `async_turn_candidate` only if all are true:

1. at least 8 first-trigger R7 episodes;
2. signal mean next-3M SPY-TLT > 0;
3. signal minus primary-control mean > 0;
4. episode-cluster bootstrap 95% CI lower bound > 0;
5. at least 2 inherited temporal segments are evaluable;
6. at least 2/3 evaluable segments are positive; if only 2 are evaluable, both are positive;
7. every evaluable leave-one-trigger-episode-out incremental mean remains positive;
8. strongest positive trigger episode contributes <=50% of total positive signal contribution;
9. one-month delayed implementation preserves positive incremental sign.

Inherited temporal segments:

- pre-2020;
- 2020–2022;
- 2023+.

If first-trigger episodes <8:

`inconclusive_async_turn_sample`.

If the incremental direction is positive but one or more robustness gates fail:

`async_turn_suggestive_not_robust`.

Otherwise:

`async_turn_not_confirmed`.

## Layer B — annual HMRA structural analogue

For annual HMRA score X in {growth_score, inflation_score}:

`dX_t = X_t - X_(t-1)`.

A causal annual turning event occurs when:

- `dX_t > 0`; and
- `dX_(t-1) <= 0`.

At HMRA year t, `HMRA_R7_ASYNC_TURN` is true when:

1. HMRA core regime at t = Slowdown / Disinflation;
2. Growth score has a turning event at t or t-1;
3. Inflation score has a turning event at t or t-1.

The annual completion window is frozen at **two annual observations**. A three-year window is intentionally not used because it would cease to represent an early-cycle turn at annual frequency.

Within a contiguous HMRA Slowdown / Disinflation episode, only the first completion year is a primary signal.

Long-history primary control follows the same before-trigger principle.

Primary payoff:

`S&P 500 total return - 10Y U.S. Treasury total return`

using frozen strict causal `state_t -> return_(t+2)` timing.

### Long-history gate

Verdict `long_history_async_turn_candidate` only if all are true:

1. at least 8 causal first-trigger observations;
2. signal mean Equity-Treasury spread > 0;
3. incremental mean vs eligible non-trigger R7 control > 0;
4. bootstrap 95% CI lower bound > 0;
5. at least 2 broad historical eras are evaluable;
6. at least 2 evaluable eras have positive incremental mean;
7. no evaluable era has incremental mean below -5pp;
8. every evaluable leave-one-era-out comparison remains positive;
9. strongest positive era contributes <=50% of total positive contribution proxy.

If n<8 or fewer than 2 eras are evaluable:

`inconclusive_long_history_async_turn_sample`.

If direction is positive but robustness fails:

`long_history_async_turn_era_dependent`.

Otherwise:

`long_history_async_turn_not_confirmed`.

## Cross-history synthesis

Allowed deterministic synthesis labels:

- `cross_history_async_turn_supported`
- `modern_only_async_turn_support`
- `long_history_only_async_turn_support`
- `async_turn_evidence_inconclusive`
- `async_turn_not_robust_across_history`

Modern exact and HMRA results remain separate. No combined p-value.

## Frozen secondary descriptions

After the primary evaluation is executed, report without promoting:

- GPI-first vs IPI-first ordering;
- lag between axis turns;
- same-month-turn subset;
- modern 1M and 6M outcomes;
- state transition after first trigger;
- temporal / historical-era concentration.

## Anti-data-mining boundary

After any Issue #136 outcomes are observed, do not:

- change the modern three-observation completion window;
- change the annual two-observation completion window;
- add magnitude thresholds;
- change the `>0 / <=0` sign-reversal definition;
- redefine Regime 7;
- require same-month turning;
- optimize which axis turns first;
- optimize allowed turn lag;
- change the 3M primary payoff;
- replace SPY-TLT as the exact-modern primary pair;
- add FCPI, price trend, moving average, valuation, or recession-date filters;
- count repeated trigger months from one R7 episode;
- use future regime transitions in current labels.

Any such hypothesis requires a new preregistered issue.

## Product boundary

Issue #136 is research-only.

Do not modify V6.6 or V6.7 production behavior.

Do not alter Issue #133 / PR #134 findings.

No positive finding here automatically authorizes an Action Layer rule.


## Pre-outcome implementation clarifications

These clarifications are frozen before the Issue #136 evaluator is implemented or executed.

### Eligibility history

Exact-modern months are eligible only when the complete lag history needed to evaluate the two turn-event windows exists inside the 2007+ exact-modern inference window.

Pre-2007 rows are not used to initialize the primary turning labels.

Long-history years are eligible only when the complete annual lag history needed for the two-observation completion rule exists.

### Episode definition

A Regime-7 episode is a sequence of monthly observations that are both:

- exact Regime 7; and
- consecutive calendar months.

The HMRA episode definition is the annual analogue using consecutive state years.

### Delayed implementation robustness

For an observation dated t, the one-month delayed modern payoff begins at t+1 and measures the same frozen three-month SPY-TLT total-return spread from t+1 through t+4.

The delayed robustness comparison applies the same delay to both signal and eligible control observations.

### Long-history bootstrap

The long-history incremental CI also uses a deterministic Regime-7-episode cluster bootstrap, resampling whole HMRA R7 episodes with replacement.

This is frozen before outcomes to avoid treating adjacent years from one macro episode as independent observations.

### Leave-one-trigger-episode-out

For both modern and HMRA layers, leaving out a trigger episode removes the **entire** corresponding R7 episode from both signal and control observations.

Any leaveout that makes either side of the comparison unevaluable fails closed for the robustness gate.


### Leaveout scope clarification

The modern Gate 7 robustness test is leave-one-**trigger-R7-episode**-out.

The long-history Gate 8 robustness test remains leave-one-**broad-historical-era**-out exactly as preregistered above.

A long-history leave-one-trigger-episode-out table may also be emitted as an additional fail-closed diagnostic, but it does not replace or relax the broad-era gate.
