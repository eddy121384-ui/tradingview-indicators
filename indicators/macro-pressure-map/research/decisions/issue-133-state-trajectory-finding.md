# Issue #133 — State × Trajectory / Early-Recovery finding

Status: **research-only; no production authorization**

Branch: `research/issue-133-state-trajectory`  
Issue: #133  
Draft PR: #134  
Validated CI run: `36830940395`  
Validated head: `85cfbf5592ea7840b5cc5e3542cb5a5b8a319d45`  
Artifact digest: `sha256:7e44338211e859c8489841ca5777bdb735029f9b122e1aeee7ce8fa094f299d5`

## Executive finding

The preregistered State × Trajectory hypothesis cannot be confirmed or rejected from the available exact-modern or ultra-long-history evidence.

- Modern exact V6.6 verdict: `inconclusive_sample`.
- Long-history HMRA verdict: `inconclusive_long_history_trajectory_sample`.
- Cross-history synthesis: `trajectory_evidence_inconclusive`.
- `production_authorized=false`.

This is a sample-sufficiency result, not a negative finding. The preregistered trajectory definition was not changed after observing outcomes.

## Layer A — exact modern V6.6

Frozen primary definition:

`Regime 7` AND `3M Δ raw GPI > 0` AND `3M Δ raw IPI > 0`.

The 2007+ exact-modern sample contains 51 eligible Regime-7 months, but only 4 `R7_RECOVERING` months / 4 episodes:

- 2009-02-27
- 2011-12-30
- 2015-12-31
- 2020-05-29

Primary next-month SPY minus TLT results:

- recovering n = 4; mean = +0.0340%; median = +2.8602%; positive hit rate = 75.0%;
- nonrecovering n = 47; mean = +0.2165%; median = +1.2554%; positive hit rate = 59.57%;
- incremental mean = -0.1825 percentage points;
- bootstrap 95% CI = [-7.4207pp, +5.3372pp].

The preregistered minimum recovering sample is 12 observations. Gate 1 therefore fails immediately, so the formal verdict is `inconclusive_sample`. The negative incremental point estimate must not be interpreted as evidence against the hypothesis because the preregistered sample-sufficiency gate failed.

Modern robustness is also mixed: pre-2020 incremental mean is -0.2320pp, 2020–2022 is +2.7454pp, and 2023+ has no recovering observation. Leave-one-episode-out is not sign-stable. The one-month delayed signal has a positive +4.4255pp incremental mean, but its 95% CI includes zero and it cannot rescue the primary test.

## Layer B — ultra-long-history HMRA analogue

The evaluator reuses the frozen Issue #91 / #121 HMRA and asset pipeline. HMRA remains a historical structural analogue, not exact V6.6.

Frozen causal setup:

`HMRA Slowdown / Disinflation at t`
AND `Δ growth_score > 0`
AND `Δ inflation_score > 0`
→ full-calendar-year `S&P 500 total return - 10Y Treasury total return` at `t+2`.

The frozen pipeline validates the Issue #91 HMRA freeze before asset joining, uses Damodaran as the primary long-history asset source, preserves the strict `t+2` timing rule, and retains the frozen Damodaran raw SHA:

`127c772f0fea8763391dbf2c1c7d3ecd3a07ca2b23f81ab47af58b529e2b5647`

There are 15 causal HMRA Regime-7 years, but only **one** preregistered recovering year:

- state year 1931 → return year 1933.

The 14 nonrecovering control state years are:

1930, 1943, 1944, 1945, 1953, 1960, 1981, 1982, 1995, 1998, 2001, 2008, 2015, 2020.

Long-history Equity minus Treasury results:

- recovering n = 1; spread = +48.12%;
- nonrecovering n = 14; mean spread = +6.3371%; median = +5.32%; positive hit rate = 57.14%;
- incremental mean = +41.7829pp;
- deterministic bootstrap interval = [+31.8434pp, +51.8669pp].

That interval must **not** be treated as persuasive statistical evidence: with only one recovering observation, resampling the recovering group cannot represent uncertainty in the recovery state itself. The preregistered n>=8 gate is the controlling safeguard.

Only `Depression_WWII` is an evaluable broad era for the recovering/control comparison. It contains the sole recovering observation, so the strongest-era contribution is 100%. Removing that era leaves zero recovering observations; the leave-one-era-out comparison is therefore unevaluable and the fail-closed gate is False.

The long-history sample fails:

- recovering n>=8;
- at least two evaluable eras;
- at least two positive evaluable eras;
- leave-one-era-out evaluability/positivity;
- strongest-era contribution <=50%.

Formal verdict: `inconclusive_long_history_trajectory_sample`.

## Cross-history synthesis

Formal synthesis: `trajectory_evidence_inconclusive`.

The exact-modern layer is underpowered with four recovering months. The ultra-long-history analogue is even rarer under the frozen annual definition, with one recovering state year. Therefore Issue #133 does not establish that “Slowdown / Disinflation + improving Growth + improving Inflation” has a robust Equity-over-Duration edge, but it also does not establish the opposite.

No threshold may be loosened, no trajectory window shortened, no other regimes added, and no alternative asset pair selected inside this issue to manufacture more observations. Any broader or differently defined recovery concept requires a new preregistered study.

## Implementation / validation notes

Two implementation-only fixes were required before the frozen evaluator could complete:

1. `d8e6274d86cdebb56a29a1718471afde77679164` — explicit boolean cast for the delayed-signal mask under Pandas 3.0.
2. `85cfbf5592ea7840b5cc5e3542cb5a5b8a319d45` — fail closed when any long-history era leaveout makes the incremental comparison unevaluable.

Neither change modifies the preregistered signal, sample, payoff, timing, thresholds, or verdict rules.

GitHub Actions run `36830940395` completed successfully through evaluator execution, result-contract validation, and evidence upload.

## Product boundary

`production_authorized=false`.

Do not modify V6.6/V6.7 production behavior from this finding. PR #134 remains Draft and must not be merged as a production change.
